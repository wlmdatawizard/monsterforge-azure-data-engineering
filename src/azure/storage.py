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

credential = get_credential()
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

blob: BlobServiceClient = BlobServiceClient(account_url=ACCOUNT_URL, credential=credential, )


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
    return blob.get_container_client(container_name)


def get_blob_client(container_client, blob):
    return container_client.get_blob_client(blob)


raw = get_container("raw")
# clean = get_container("clean")
# quarantine = get_container("quarantine")
# reports = get_container("reports")

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

local_file = "C:\\Users\\willi\\OneDrive\\Desktop\\monsterfroge-azure-data-engineering\\data\\raw\\MonsterForge_monsters_raw_100.csv"


# def upload_blob(local_file, container, blob_path):
#     container_client = blob.get_container_client(container)
#     blob_client = container_client.get_blob_client(blob_path)
#     with open(local_file, "rb") as file:
#         blob_client.upload_blob(file, overwrite=True)
#     print(f"✓ Uploaded {local_file} -> {container}/{blob_path}")


if __name__ == "__main__":

    with open(local_file, "rb") as data:
        raw.upload_blob(name="blob2.csv", data=data)
