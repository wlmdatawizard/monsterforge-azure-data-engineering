# src/azure_sql_loader.py

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


load_dotenv()


def get_azure_sql_engine():
    connection_url = URL.create(
        "mssql+pyodbc",
        username=os.getenv("AZURE_SQL_USER"),
        password=os.getenv("AZURE_SQL_PASSWORD"),
        host="monsterforge-sql-wlm.database.windows.net",
        port=1433,
        database="monsterforge",
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "Encrypt": "yes",
            "TrustServerCertificate": "no",
        },
    )

    print("SQL loader file:", __file__)

    return create_engine(connection_url, fast_executemany=True)


def load_monsters_clean_to_sql(csv_path, run_id):
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df["run_id"] = run_id

    engine = get_azure_sql_engine()

    df.to_sql(
        name="monsters_clean",
        con=engine,
        if_exists="append",
        index=False,
    )

    print(f"Loaded {len(df)} rows into Azure SQL table: monsters_clean")
