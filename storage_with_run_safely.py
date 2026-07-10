from datetime import datetime
import logging
from pathlib import Path

from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from pyspark.sql import SparkSession
from pyspark.sql.functions import (col, lit, lower, upper, trim, regexp_replace, when, coalesce, expr, initcap, )

from src.config.settings import ACCOUNT_URL
from src.azure.authentication import get_credential
from src.azure_sql_loader import get_azure_sql_engine, load_monsters_clean_to_sql


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", )

LOCAL_FILE = ("C:\\Users\\willi\\OneDrive\\Desktop\\monsterfroge-azure-data-engineering" "\\data\\raw\\MonsterForge_monsters_raw_100.csv")


def run_safely(func, *args, default_return=None, error_message="Operation failed", **kwargs, ):
    try:
        return func(*args, **kwargs)

    except FileNotFoundError as e:
        logging.error(f"{error_message} | File not found: {e.filename}")
        return default_return

    except AzureError as e:
        logging.error(f"{error_message} | Azure error | {type(e).__name__}: {e}")
        return default_return

    except SQLAlchemyError as e:
        logging.error(f"{error_message} | SQL error | {type(e).__name__}: {e}")
        return default_return

    except Exception as e:
        logging.error(f"{error_message} | {type(e).__name__}: {e}")
        return default_return


def create_blob_service():
    credential = run_safely(get_credential, error_message="Failed to get Azure credential", )

    if credential is None:
        return None

    return run_safely(BlobServiceClient, account_url=ACCOUNT_URL, credential=credential, error_message="Failed to create BlobServiceClient", )


def create_spark_session():
    return run_safely(
        lambda: (SparkSession.builder .appName("Azure Pipeline") .master("local[*]") .getOrCreate()), error_message="Failed to create Spark session", )


def read_raw_csv(spark, local_file):
    return run_safely(spark.read.csv, local_file, header=True, inferSchema=True, error_message="Failed to read raw CSV into Spark DataFrame", )


def get_container(blob_service, container_name):
    return run_safely(blob_service.get_container_client, container_name, error_message=f"Failed to get container client: {container_name}", )


def safe_count(df, label):
    return run_safely(df.count, default_return=0, error_message=f"Failed to count rows for {label}", )


def safe_show(df, row_count=20, label="DataFrame"):
    return run_safely(df.show, row_count, default_return=None, error_message=f"Failed to display {label}", )


def damage_report(df):
    row_count = safe_count(df, "damage report source")

    print("\n========== FINDINGS ==========")

    if "Monster ID" in df.columns:
        id_column = "Monster ID"
    elif "monster_id" in df.columns:
        id_column = "monster_id"
    else:
        id_column = None

    if id_column:
        distinct_id_count = run_safely(
            lambda: df.select(id_column).distinct().count(),
            default_return=0,
            error_message=f"Failed to count distinct values for {id_column}",
        )

        duplicate_id_count = row_count - distinct_id_count

        if duplicate_id_count > 0:
            print(f"WARNING: {duplicate_id_count} duplicate {id_column} values detected")
        else:
            print(f"OK: No duplicate {id_column} values detected")

    for column_name in df.columns:
        null_count = run_safely(lambda column_name=column_name: df.filter(col(column_name).isNull()).count(),
                                default_return=0, error_message=f"Failed to count nulls for {column_name}", )

        if null_count > 0:
            print(f"WARNING: {null_count} null values detected in {column_name}")

    watch_columns = ["Monster Type", "monster_type", "Status", "status", "Danger Level", "danger_level", ]

    for column_name in watch_columns:
        if column_name in df.columns:
            distinct_count = run_safely(lambda column_name=column_name: df.select(column_name).distinct().count(),
                                        default_return=0, error_message=f"Failed to count distinct values for {column_name}", )
            print(f"INFO: {column_name} has {distinct_count} distinct values")

    print("\n========== COLUMN PROFILE ==========")

    rows = []

    for column_name, data_type in df.dtypes:
        null_count = run_safely(lambda column_name=column_name: df.filter(col(column_name).isNull()).count(),
                                default_return=0, error_message=f"Failed to count nulls for {column_name}", )

        if data_type == "string":
            blank_count = run_safely(lambda column_name=column_name: df.filter(trim(col(column_name)) == "").count(),
                                     default_return=0, error_message=f"Failed to count blanks for {column_name}", )
        else:
            blank_count = "N/A"

        distinct_count = run_safely(lambda column_name=column_name: df.select(column_name).distinct().count(),
                                    default_return=0, error_message=f"Failed to count distinct values for {column_name}", )

        rows.append({"column": column_name, "schema": data_type, "null_count": str(null_count),
                     "blank_count": str(blank_count), "distinct_count": str(distinct_count), })

    columns = ["column", "schema", "null_count", "blank_count", "distinct_count"]

    widths = {}
    for column_name in columns:
        widths[column_name] = max(len(column_name), max(len(str(row.get(column_name, ""))) for row in rows), )

    header = " | ".join(column_name.ljust(widths[column_name]) for column_name in columns)
    divider = "-+-".join("-" * widths[column_name] for column_name in columns)

    print(header)
    print(divider)

    for row in rows:
        line = " | ".join(
            str(row.get(column_name, "")).ljust(widths[column_name])
            for column_name in columns
        )
        print(line)

    print("\n")


pipeline_plan = [
    ("normalize_headers", "all_columns"),
    ("trim", "all_string_columns"),
    ("blank_to_null", "all_string_columns"),
    ("upper", ["monster_id"]),
    ("initcap", ["monster_name"]),
    ("lower", ["monster_type", "status"]),
    ("preserve_original", ["created_date", "danger_level", "base_price"]),
    ("clean_currency", ["base_price"]),
    ("try_cast_double", ["base_price"]),
    ("flag_negative", ["base_price"]),
    ("fix_negative", ["base_price"]),
    ("try_parse_date", ["created_date"]),
    ("try_cast_int", ["danger_level"]),
    ("range_check", ["danger_level"]),
    ("null_check", ["monster_name", "created_date"]),
]


def before_transformations(df):
    print("\n-------------------------------Before Transformations--------------------------------")
    run_safely(
        damage_report,
        df,
        error_message="Before-transformation damage report failed",
    )

    print("============================= Before Transformations =============================")
    safe_show(df, 30, "before-transformations DataFrame")

    print("\n========== Required Transformation Order ============================")
    for step_num, (transform_name, columns) in enumerate(pipeline_plan, start=1):
        print(f"{step_num:02d}. {transform_name:<20} {columns}")
    print("=======================================================================")


def after_transformations(df, clean_df, quarantine_df):
    print("\n========== After Transformations ==========")
    safe_show(clean_df, 30, "clean DataFrame")

    total_rows = safe_count(df, "source DataFrame")
    clean_rows = safe_count(clean_df, "clean DataFrame")
    quarantine_rows = safe_count(quarantine_df, "quarantine DataFrame")

    print("\n========== CLEAN / QUARANTINE SUMMARY ==================")
    print(f"Total Rows: {total_rows}")
    print(f"Clean Rows: {clean_rows}")
    print(f"Quarantine Rows: {quarantine_rows}")

    run_safely(
        damage_report,
        clean_df,
        error_message="After-transformation damage report failed",
    )


def pipeline_complete(clean_rows, quarantine_rows, run_id):
    print("\n========== PIPELINE COMPLETE ==========")
    print(f"Run ID: {run_id}")
    print("--------------------------------")

    print(f"{'Clean Rows':<22} {clean_rows}")
    print(f"{'Quarantine Rows':<22} {quarantine_rows}")
    print(f"{'Blob Upload':<22} SUCCESS")
    print(f"{'Azure SQL Load':<22} SUCCESS")
    print(f"{'Azure SQL Validation':<22} SUCCESS")

    print("--------------------------------")
    print("✓ MonsterForge Azure pipeline completed successfully")


def upload_blob(local_file, container_client, blob_path):
    def _upload():
        blob_client = container_client.get_blob_client(blob_path)

        with open(local_file, "rb") as file:
            blob_client.upload_blob(file, overwrite=True)

        return blob_client

    blob_client = run_safely(
        _upload,
        error_message=f"Failed to upload {local_file} to {blob_path}",
    )

    if blob_client is not None:
        print(f"✓ Uploaded {local_file} -> {blob_path}")

    return blob_client


def transform_dataframe(df):
    for old_name in df.columns:
        new_name = old_name.lower().replace(" ", "_")
        df = df.withColumnRenamed(old_name, new_name)

    for column_name, data_type in df.dtypes:
        if data_type == "string":
            df = df.withColumn(column_name, trim(col(column_name)))

    for column_name, data_type in df.dtypes:
        if data_type == "string":
            df = df.withColumn(
                column_name,
                when(trim(col(column_name)) == "", None).otherwise(col(column_name)),
            )

    df = df.withColumn("monster_id", upper(col("monster_id")))
    df = df.withColumn("monster_name", initcap(col("monster_name")))
    df = df.withColumn("monster_type", lower(col("monster_type")))
    df = df.withColumn("status", lower(col("status")))

    df = df.withColumn("preserve_date", col("created_date"))
    df = df.withColumn("preserve_danger", col("danger_level"))
    df = df.withColumn("preserve_price", col("base_price"))

    df = df.withColumn("base_price", regexp_replace("base_price", r"[$,]", ""))
    df = df.withColumn("base_price", regexp_replace("base_price", r"USD\s", ""))
    df = df.withColumn("base_price", col("base_price").cast("double"))

    df = df.withColumn(
        "original_price_negative",
        when(col("base_price") < 0, True).otherwise(False),
    )

    df = df.withColumn(
        "base_price",
        when(col("base_price") < 0, col("base_price") * -1).otherwise(col("base_price")),
    )

    df = df.withColumn(
        "created_date",
        coalesce(
            expr("try_to_date(`created_date`, 'M/d/yy')"),
            expr("try_to_date(`created_date`, 'yyyy-MM-dd')"),
            expr("try_to_date(`created_date`, 'yyyy/MM/dd')"),
            expr("try_to_date(`created_date`, 'MMM d yyyy')"),
            expr("try_to_date(`created_date`, 'MM-dd-yyyy')"),
        ),
    )

    df = df.withColumn("danger_level", expr("try_cast(danger_level as int)"))

    df = df.withColumn(
        "danger_level",
        when((col("danger_level") < 1) | (col("danger_level") > 10), None)
        .otherwise(col("danger_level")),
    )

    duplicate_rows = (
        df.groupBy(df.columns)
        .count()
        .filter(col("count") > 1)
        .drop("count")
    )

    duplicate_rows = duplicate_rows.withColumn("duplicate_row", lit(True))

    df = (
        df.join(duplicate_rows, on=df.columns, how="left")
        .fillna(False, subset=["duplicate_row"])
    )

    quarantine_condition = (
        col("monster_name").isNull()
        | col("created_date").isNull()
        | col("danger_level").isNull()
        | col("duplicate_row")
    )

    clean_condition = (
        col("monster_name").isNotNull()
        & col("created_date").isNotNull()
        & col("danger_level").isNotNull()
        & (col("duplicate_row") == False)
    )

    quarantine_df = df.filter(quarantine_condition)
    clean_df = df.filter(clean_condition)

    return quarantine_df, clean_df


def export_to_local(clean_df, quarantine_df, run_id):
    output_root = Path.cwd() / "output" / f"run_id={run_id}"

    created = run_safely(
        lambda: output_root.mkdir(parents=True, exist_ok=True),
        default_return=False,
        error_message=f"Failed to create output directory: {output_root}",
    )

    if created is False:
        return None, None

    clean_local_file = output_root / "monsters_clean.csv"
    quarantine_local_file = output_root / "monsters_quarantine.csv"

    print(f"\nExporting files to: {output_root}")

    clean_pandas_df = run_safely(
        clean_df.toPandas,
        error_message="Failed to convert clean Spark DataFrame to pandas",
    )

    if clean_pandas_df is None:
        return None, None

    quarantine_pandas_df = run_safely(
        quarantine_df.toPandas,
        error_message="Failed to convert quarantine Spark DataFrame to pandas",
    )

    if quarantine_pandas_df is None:
        return None, None

    clean_export_result = run_safely(
        clean_pandas_df.to_csv,
        clean_local_file,
        index=False,
        error_message=f"Failed to export clean CSV: {clean_local_file}",
    )

    quarantine_export_result = run_safely(
        quarantine_pandas_df.to_csv,
        quarantine_local_file,
        index=False,
        error_message=f"Failed to export quarantine CSV: {quarantine_local_file}",
    )

    if clean_export_result is None or quarantine_export_result is None:
        return None, None

    print("CSV export complete.")
    print(f"✓ {clean_local_file.name}")
    print(f"✓ {quarantine_local_file.name}")

    return clean_local_file, quarantine_local_file


def upload_after_transform(clean_local_file, quarantine_local_file, run_id, clean, quarantine):
    uploads = [
        upload_blob(clean_local_file, clean, "monsters/latest/monsters_clean.csv"),
        upload_blob(clean_local_file, clean, f"monsters/runs/run_id={run_id}/monsters_clean.csv"),
        upload_blob(quarantine_local_file, quarantine, "monsters/latest/monsters_quarantine.csv"),
        upload_blob(quarantine_local_file, quarantine, f"monsters/runs/run_id={run_id}/monsters_quarantine.csv"),
    ]

    return all(upload is not None for upload in uploads)


def run_azure_sql_validation(run_id):
    print("\n========== AZURE SQL VALIDATION ==========")

    query = text("""
        SELECT
            COUNT(*) AS clean_rows,
            COUNT(DISTINCT monster_type) AS monster_types,
            COUNT(DISTINCT status) AS statuses,
            ROUND(AVG(base_price), 2) AS average_price
        FROM monsters_clean
        WHERE run_id = :run_id;
    """)

    engine = run_safely(
        get_azure_sql_engine,
        error_message="Failed to create Azure SQL engine for validation",
    )

    if engine is None:
        return None

    def _run_query():
        with engine.connect() as connection:
            result = connection.execute(query, {"run_id": run_id})
            return result.fetchone()

    row = run_safely(
        _run_query,
        error_message="Azure SQL validation query failed",
    )

    if row is None:
        print("No validation results returned.")
        return None

    validation_results = {
        "clean_rows": row.clean_rows,
        "monster_types": row.monster_types,
        "statuses": row.statuses,
        "average_price": row.average_price,
    }

    print("\nValidation Results")
    print("--------------------------------")

    for key, value in validation_results.items():
        print(f"{key:<18} {value}")

    print("\n✓ Azure SQL validation completed")

    return validation_results


def run_all(df, run_id, clean, quarantine):
    run_safely(
        damage_report,
        df,
        error_message="Initial damage report failed",
    )

    run_safely(
        before_transformations,
        df,
        error_message="Before-transformations report failed",
    )

    transform_result = run_safely(
        transform_dataframe,
        df,
        error_message="DataFrame transformation failed",
    )

    if transform_result is None:
        print("Pipeline stopped: transformation failed.")
        return False

    quarantine_df, clean_df = transform_result

    clean_rows = safe_count(clean_df, "clean DataFrame")
    quarantine_rows = safe_count(quarantine_df, "quarantine DataFrame")

    export_result = run_safely(
        export_to_local,
        clean_df,
        quarantine_df,
        run_id,
        error_message="Local export failed",
    )

    if export_result is None:
        print("Pipeline stopped: local export failed.")
        return False

    clean_local_file, quarantine_local_file = export_result

    if clean_local_file is None or quarantine_local_file is None:
        print("Pipeline stopped: local export did not produce expected files.")
        return False

    run_safely(
        after_transformations,
        df,
        clean_df,
        quarantine_df,
        error_message="After-transformations report failed",
    )

    uploads_succeeded = run_safely(
        upload_after_transform,
        clean_local_file,
        quarantine_local_file,
        run_id,
        clean,
        quarantine,
        default_return=False,
        error_message="Blob upload step failed",
    )

    if not uploads_succeeded:
        print("Pipeline stopped: Blob upload step failed.")
        return False

    sql_load_result = run_safely(
        load_monsters_clean_to_sql,
        clean_local_file,
        run_id,
        error_message="Azure SQL load failed",
    )

    if sql_load_result is None:
        print("Pipeline stopped: Azure SQL load failed.")
        return False

    validation_results = run_safely(
        run_azure_sql_validation,
        run_id,
        error_message="Azure SQL validation failed",
    )

    if validation_results is None:
        print("Pipeline stopped: Azure SQL validation failed.")
        return False

    run_safely(
        pipeline_complete,
        clean_rows,
        quarantine_rows,
        run_id,
        error_message="Failed to print pipeline completion summary",
    )

    return True


def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    blob_service = create_blob_service()
    if blob_service is None:
        print("Pipeline stopped: Azure Blob service could not be created.")
        return False

    clean = get_container(blob_service, "clean")
    quarantine = get_container(blob_service, "quarantine")

    if clean is None or quarantine is None:
        print("Pipeline stopped: required Blob containers could not be reached.")
        return False

    spark = create_spark_session()
    if spark is None:
        print("Pipeline stopped: Spark session could not be created.")
        return False

    df = read_raw_csv(spark, LOCAL_FILE)
    if df is None:
        print("Pipeline stopped: raw CSV could not be read.")
        return False

    return run_all(df, run_id, clean, quarantine)


if __name__ == "__main__":
    main()
