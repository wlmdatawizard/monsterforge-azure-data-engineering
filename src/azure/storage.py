from os import name
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError
import logging
from pprint import pprint
from src.config.settings import ACCOUNT_URL


credential = DefaultAzureCredential()

blob: BlobServiceClient = BlobServiceClient(account_url=ACCOUNT_URL, credential=credential, )


def run_safely(func, *args, default_return=None,
               error_message="Operation failed", **kwargs):
    try:
        return func(*args, **kwargs)

    except AzureError as e:
        logging.error(f"{error_message} | {type(e).__name__}: {e}")
        return default_return

    except Exception as e:
        logging.error(f"{error_message} | {type(e).__name__}: {e}")
        return default_return


def flatten_recursive_paths(data, path=""):
    result = {}

    if isinstance(data, dict):

        for key, value in data.items():
            current_path = f'{path}["{key}"]'

            if isinstance(value, (dict, list)):
                result.update(flatten_recursive_paths(value, current_path))
            else:
                result[current_path] = value

    elif isinstance(data, list):

        result[path] = f"<list: {len(data)} items>"

        for index, value in enumerate(data):
            current_path = f'{path}[{index}]'

            if isinstance(value, (dict, list)):
                result.update(flatten_recursive_paths(value, current_path))
            else:
                result[current_path] = value

    return result


if __name__ == "__main__":
    containers = run_safely(blob.list_containers, default_return=[], error_message="Failed to list containers", )
    for container in containers:
        pprint(container.name)
