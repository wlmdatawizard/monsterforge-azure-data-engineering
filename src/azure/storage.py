from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobClient
from azure.core.exceptions import AzureError
import logging
from pprint import pprint
from src.config.settings import ACCOUNT_URL
from src.azure.authentication import get_credential
import inspect
from src.utils.object_explorer import build_azure_blob_storage_map, build_method_tree, build_object_map, explore, inspect_object, print_object, print_report, print_search_results, run_method_discovery, save_json, search_report, to_hierarchy
from pyspark.sql import SparkSession
from pyspark.sql.functions import (col, lit, lower, upper, trim, regexp_replace, when, coalesce, expr, initcap)


credential = get_credential()
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
run_key = f"raw/monsters/runs/run_id={run_id}/monsters.csv"
blob_service: BlobServiceClient = BlobServiceClient(account_url=ACCOUNT_URL, credential=credential, )
spark = (SparkSession.builder .appName("Azure Pipeline") .master("local[*]") .getOrCreate())
local_file = "C:\\Users\\willi\\OneDrive\\Desktop\\monsterfroge-azure-data-engineering\\data\\raw\\MonsterForge_monsters_raw_100.csv"
df = spark.read.csv(local_file, header=True, inferSchema=True)


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

# raw_blob_client = get_blob_client(raw, blob)
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


def explore1(obj):
    methods = []
    properties = []

    for name in sorted(dir(obj)):
        if name.startswith("_"):
            continue

        try:
            member = getattr(obj, name)

            if callable(member):
                try:
                    signature = str(inspect.signature(member))
                except (ValueError, TypeError):
                    signature = "(...)"

                methods.append((name, signature))

            else:
                properties.append(
                    (
                        name,
                        type(member).__name__,
                        repr(member)
                    )
                )

        except Exception as e:
            properties.append(
                (
                    name,
                    "ERROR",
                    str(e)
                )
            )

    print("=" * 120)
    print(f"Object Type : {type(obj).__name__}")
    print("=" * 120)

    print("\nProperties")
    print("-" * 120)
    print(f"{'Name':<35} {'Type':<20} Value")
    print("-" * 120)

    for name, kind, value in properties:
        print(f"{name:<35} {kind:<20} {value}")

    print("\nMethods")
    print("-" * 120)

    for name, signature in methods:
        print(f"{name:<35}{signature}")

    print("\nSummary")
    print("-" * 120)
    print(f"Properties : {len(properties)}")
    print(f"Methods    : {len(methods)}")
    print("=" * 120)


def upload_blob(local_file, container_client, blob_path):
    blob_client = container_client.get_blob_client(blob_path)
    with open(local_file, "rb") as file:
        blob_client.upload_blob(file, overwrite=True)
    print(f"✓ Uploaded {local_file} -> {blob_path}")
    return blob_client


def transform_dataframe(df):
    df.show()

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


if __name__ == "__main__":
    df.show()
    quarantine_df, clean_df = transform_dataframe(df)
    quarantine_df.show()
    clean_df.show()
