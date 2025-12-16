import os
import re
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from scipy import stats

# --- Load credentials ---
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_TABLE = os.getenv("DB_TABLE")
print("Loaded from .env:", DB_HOST, DB_USER, DB_NAME)


# --- Connect to the database ---
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

try:
    # Load the table
    query = f"SELECT playername, team, timestamp, metric, data_source FROM {DB_TABLE}"
    df = pd.read_sql(query, engine)

    #  Clean data 
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in ["playername", "team", "metric", "data_source"]:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace({"": pd.NA, "None": pd.NA, "none": pd.NA, "nan": pd.NA, "NaN": pd.NA})
    
    # Display first 10 rows
    print("FIRST 10 ROWS FROM DATABASE")
    print(f"Table: {DB_TABLE}")
    print(f"Columns: {list(df.columns)}")
    print(f"Total records loaded: {len(df)}")

    
    print(df.head(10))
    
except Exception as e:
    print(f"Error connecting to database: {e}")