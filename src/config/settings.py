from dotenv import load_dotenv
import os

load_dotenv()

STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT")

if not STORAGE_ACCOUNT_NAME:
    raise ValueError("AZURE_STORAGE_ACCOUNT not found in .env")

ACCOUNT_URL = (
    f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
)
