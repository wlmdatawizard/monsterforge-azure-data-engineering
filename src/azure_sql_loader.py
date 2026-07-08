# src/azure_sql_loader.py

import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv


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

    return create_engine(connection_url, fast_executemany=True)


def load_monsters_clean_to_sql(csv_path: str):
    df = pd.read_csv(csv_path)

    engine = get_azure_sql_engine()

    df.to_sql(
        name="monsters_clean",
        con=engine,
        if_exists="append",
        index=False,
        method=None,
    )

    print(f"Loaded {len(df)} rows into Azure SQL table: monsters_clean")
