from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobClient
from azure.core.exceptions import AzureError
import logging
from pprint import pprint

from sqlalchemy import text
from src.config.settings import ACCOUNT_URL
from src.azure.authentication import get_credential
import inspect
from src.utils.object_explorer import build_azure_blob_storage_map, build_method_tree, build_object_map, explore, inspect_object, print_object, print_report, print_search_results, run_method_discovery, save_json, search_report, to_hierarchy
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import (col, lit, lower, upper, trim, regexp_replace, when, coalesce, expr, initcap)
from src.azure_sql_loader import get_azure_sql_engine, load_monsters_clean_to_sql

credential = get_credential()
blob_service: BlobServiceClient = BlobServiceClient(account_url=ACCOUNT_URL, credential=credential, )
spark = (SparkSession.builder .appName("Azure Pipeline") .master("local[*]") .getOrCreate())
local_file = "C:\\Users\\willi\\OneDrive\\Desktop\\monsterfroge-azure-data-engineering\\data\\raw\\MonsterForge_monsters_raw_100.csv"

df = spark.read.csv(local_file, header=True, inferSchema=True)
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
run_key = f"raw/monsters/runs/run_id={run_id}/monsters.csv"


def run_safely(func, *args, default_return=None,
               error_message="Operation failed", **kwargs):
    try:
        return func(*args, **kwargs)

    except FileNotFoundError as e:
        logging.error(f"{error_message} | File not found: {e.filename}")
        return default_return

    except AzureError as e:
        logging.error(f"{error_message} | {type(e).__name__}: {e}")
        return default_return

    except Exception as e:
        logging.error(f"{error_message} | {type(e).__name__}: {e}")
        return default_return


def get_container(container_name):
    return blob_service.get_container_client(container_name)


raw = get_container("raw")
clean = get_container("clean")
quarantine = get_container("quarantine")
reports = get_container("reports")

# def flatten_recursive_paths(data, path=""):
#     result = {}

#     if isinstance(data, dict):

#         for key, value in data.items():
#             current_path = f'{path}["{key}"]'

#             if isinstance(value, (dict, list)):
#                 result.update(flatten_recursive_paths(value, current_path))
#             else:
#                 result[current_path] = value

#     elif isinstance(data, list):

#         result[path] = f"<list: {len(data)} items>"

#         for index, value in enumerate(data):
#             current_path = f'{path}[{index}]'

#             if isinstance(value, (dict, list)):
#                 result.update(flatten_recursive_paths(value, current_path))
#             else:
#                 result[current_path] = value

#     return result
# def explore1(obj):
#     methods = []
#     properties = []

#     for name in sorted(dir(obj)):
#         if name.startswith("_"):
#             continue

#         try:
#             member = getattr(obj, name)

#             if callable(member):
#                 try:
#                     signature = str(inspect.signature(member))
#                 except (ValueError, TypeError):
#                     signature = "(...)"

#                 methods.append((name, signature))

#             else:
#                 properties.append(
#                     (
#                         name,
#                         type(member).__name__,
#                         repr(member)
#                     )
#                 )

#         except Exception as e:
#             properties.append(
#                 (
#                     name,
#                     "ERROR",
#                     str(e)
#                 )
#             )

#     print("=" * 120)
#     print(f"Object Type : {type(obj).__name__}")
#     print("=" * 120)

#     print("\nProperties")
#     print("-" * 120)
#     print(f"{'Name':<35} {'Type':<20} Value")
#     print("-" * 120)

#     for name, kind, value in properties:
#         print(f"{name:<35} {kind:<20} {value}")

#     print("\nMethods")
#     print("-" * 120)

#     for name, signature in methods:
#         print(f"{name:<35}{signature}")

#     print("\nSummary")
#     print("-" * 120)
#     print(f"Properties : {len(properties)}")
#     print(f"Methods    : {len(methods)}")
#     print("=" * 120)


def damage_report(df):

    row_count = df.count()

    print("\n========== FINDINGS ==========")

    # Duplicate monster IDs
    if "Monster ID" in df.columns:
        id_column = "Monster ID"
    elif "monster_id" in df.columns:
        id_column = "monster_id"
    else:
        id_column = None

    if id_column:
        distinct_id_count = df.select(id_column).distinct().count()
        duplicate_id_count = row_count - distinct_id_count

        if duplicate_id_count > 0:
            print(f"WARNING: {duplicate_id_count} duplicate {id_column} values detected")
        else:
            print(f"OK: No duplicate {id_column} values detected")

    # Nulls by column
    for column_name in df.columns:
        null_count = df.filter(col(column_name).isNull()).count()

        if null_count > 0:
            print(f"WARNING: {null_count} null values detected in {column_name}")

    # Distinct info for watched columns
    watch_columns = [
        "Monster Type", "monster_type",
        "Status", "status",
        "Danger Level", "danger_level"
    ]

    for column_name in watch_columns:
        if column_name in df.columns:
            distinct_count = df.select(column_name).distinct().count()
            print(f"INFO: {column_name} has {distinct_count} distinct values")

    print("\n========== COLUMN PROFILE ==========")

    rows = []

    for column_name, data_type in df.dtypes:
        row = {"column": column_name, "schema": data_type, "null_count": str(df.filter(col(column_name).isNull()).count()),
               "blank_count": (str(df.filter(trim(col(column_name)) == "").count()) if data_type == "string" else "N/A"),
               "distinct_count": str(df.select(column_name).distinct().count())}

        rows.append(row)

    columns = ["column", "schema", "null_count", "blank_count", "distinct_count"]

    # calculate column widths
    widths = {}
    for column in columns:
        widths[column] = max(len(column), max(len(str(row.get(column, ""))) for row in rows))

    # print header
    header = " | ".join(column.ljust(widths[column]) for column in columns)
    divider = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(divider)

    # print rows
    for row in rows:
        line = " | ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns)
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
    damage_report(df)
    print("============================= Before Transformations =============================")
    df.show(30)
    print("\n========== Required Transformation Order ============================")
    for step_num, (transform_name, columns) in enumerate(pipeline_plan, start=1):
        print(f"{step_num:02d}. {transform_name:<20} {columns}")
    print("=======================================================================")


def after_transformations(df, clean_df, quarantine_df):
    print("\n========== After Transformations ==========")
    clean_df.show(30)
    print("\n========== CLEAN / QUARANTINE SUMMARY ==================")
    print(f"Total Rows: {df.count()}")
    print(f"Clean Rows: {clean_df.count()}")
    print(f"Quarantine Rows: {quarantine_df.count()}")
    damage_report(clean_df)


def pipeline_complete(clean_df, quarantine_df, run_id):
    print("\n========== PIPELINE COMPLETE ==========")

    print(f"Run ID: {run_id}")
    print("--------------------------------")

    print(f"{'Clean Rows':<22} {clean_df.count()}")
    print(f"{'Quarantine Rows':<22} {quarantine_df.count()}")
    print(f"{'Blob Upload':<22} SUCCESS")
    print(f"{'After SQL Load':<22} SUCCESS")
    print(f"{'Azure SQL Validation':<22} SUCCESS")

    print("--------------------------------")
    print("✓ MonsterForge ETL pipeline completed successfully")
    return


def upload_blob(local_file, container_client, blob_path):
    blob_client = container_client.get_blob_client(blob_path)
    with open(local_file, "rb") as file:
        blob_client.upload_blob(file, overwrite=True)
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
            df = df.withColumn(column_name, when(trim(col(column_name)) == "", None) .otherwise(col(column_name)))

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
    df = df.withColumn("original_price_negative", when(col("base_price") < 0, True).otherwise(False))
    df = df.withColumn("base_price", when(col("base_price") < 0, col("base_price") * -1) .otherwise(col("base_price")))
    df = df.withColumn("created_date", coalesce(expr("try_to_date(`created_date`, 'M/d/yy')"), expr("try_to_date(`created_date`, 'yyyy-MM-dd')"),
                                                expr("try_to_date(`created_date`, 'yyyy/MM/dd')"), expr("try_to_date(`created_date`, 'MMM d yyyy')"), expr("try_to_date(`created_date`, 'MM-dd-yyyy')")))
    df = df.withColumn("danger_level", expr("try_cast(danger_level as int)"))
    df = df.withColumn("danger_level", when((col("danger_level") < 1) | (col("danger_level") > 10), None).otherwise(col("danger_level")))
    duplicate_rows = (df.groupBy(df.columns) .count() .filter(col("count") > 1) .drop("count"))
    duplicate_rows = duplicate_rows.withColumn("duplicate_row", lit(True))
    df = (df.join(duplicate_rows, on=df.columns, how="left") .fillna(False, subset=["duplicate_row"]))

    quarantine_condition = (col("monster_name").isNull() | col("created_date").isNull() |
                            col("danger_level").isNull() | col("duplicate_row"))
    quarantine_df = df.filter(quarantine_condition)
    clean_condition = (col("monster_name").isNotNull() & col("created_date").
                       isNotNull() & col("danger_level").isNotNull() & (col("duplicate_row") == False))
    clean_df = df.filter(clean_condition)
    return quarantine_df, clean_df


def export_to_local(clean_df, quarantine_df, run_id):
    output_root = Path.cwd() / "output" / f"run_id={run_id}"
    output_root.mkdir(parents=True, exist_ok=True)

    clean_local_file = output_root / "monsters_clean.csv"
    quarantine_local_file = output_root / "monsters_quarantine.csv"

    print(f"\nExporting files to: {output_root}")

    clean_df.toPandas().to_csv(clean_local_file, index=False)
    quarantine_df.toPandas().to_csv(quarantine_local_file, index=False)

    print("CSV export complete.")
    print(f"✓ {clean_local_file.name}")
    print(f"✓ {quarantine_local_file.name}")
    return clean_local_file, quarantine_local_file


def upload_after_transform(clean_local_file, quarantine_local_file, run_id):
    upload_blob(clean_local_file, clean, "monsters/latest/monsters_clean.csv")
    upload_blob(clean_local_file, clean, f"monsters/runs/run_id={run_id}/monsters_clean.csv")

    upload_blob(quarantine_local_file, quarantine, "monsters/latest/monsters_quarantine.csv")
    upload_blob(quarantine_local_file, quarantine, f"monsters/runs/run_id={run_id}/monsters_quarantine.csv")


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

    engine = get_azure_sql_engine()

    with engine.connect() as connection:
        result = connection.execute(query, {"run_id": run_id})
        row = result.fetchone()

    if row is None:
        print("No validation results returned.")
        return

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


def run_all(df, run_id):
    damage_report(df)
    before_transformations(df)
    quarantine_df, clean_df = transform_dataframe(df)
    clean_local_file, quarantine_local_file = export_to_local(clean_df, quarantine_df, run_id)
    after_transformations(df, clean_df, quarantine_df)
    upload_after_transform(clean_local_file, quarantine_local_file, run_id)
    load_monsters_clean_to_sql(clean_local_file, run_id)
    run_azure_sql_validation(run_id)
    pipeline_complete(clean_df, quarantine_df, run_id)


if __name__ == "__main__":
    run_all(df, run_id)
