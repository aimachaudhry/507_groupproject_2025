# part1_exploration.py — Part 1.2 Data Quality Assessment 

import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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

# --- Connect to the database ---
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

try:
    # Load the table
    query = f"SELECT playername, team, timestamp, data_source FROM {DB_TABLE}"
    df = pd.read_sql(query, engine)

    #  Clean data 
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in ["playername", "team", "data_source"]:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace({"": pd.NA, "None": pd.NA, "none": pd.NA, "nan": pd.NA, "NaN": pd.NA})

    #  1) Unique athletes 
    unique_athletes = df["playername"].nunique(dropna=True)

    #  2) Unique teams 
    unique_teams = df["team"].nunique(dropna=True)

    #  3) Date range 
    date_start, date_end = df["timestamp"].min(), df["timestamp"].max()

    #  4) Data source with most records 
    source_counts = df["data_source"].value_counts()
    top_source = source_counts.idxmax() if not source_counts.empty else "N/A"

    #  5) Missing/invalid player names 
    missing_names = int(df["playername"].isna().sum())
    invalid_names = df.loc[
        df["playername"].notna() & ~df["playername"].str.match(r"^PLAYER_\d+$", na=False),
        "playername"
    ].unique()
    invalid_count = len(invalid_names)

    #  6) Athletes with data from multiple sources 
    per_player_sources = df.groupby("playername")["data_source"].nunique()
    multi_source_athletes = int((per_player_sources > 1).sum())

    # Print results 
    print("\n=== Part 1.2: Data Quality Assessment ===")
    print(f"Table: {DB_TABLE}")
    print(f"Total records: {len(df):,}")
    print(f"1. Unique athletes: {unique_athletes}")
    print(f"2. Unique teams: {unique_teams}")
    print(f"3. Date range: {date_start} → {date_end}")
    print(f"4. Data sources:\n{source_counts}")
    print(f"   → Top source: {top_source}")
    print(f"5. Missing player names: {missing_names}")
    print(f"   Invalid player names: {invalid_count}")
    if invalid_count:
        examples = list(invalid_names[:5])
        more = invalid_count - len(examples)
        print(f"   Examples: {examples}" + (f" ... (+{more} more)" if more else ""))
    print(f"6. Athletes with multiple sources: {multi_source_athletes}")

    # Save simple summary CSV 
    summary = pd.DataFrame([{
        "Unique Athletes": unique_athletes,
        "Unique Teams": unique_teams,
        "Date Start": date_start,
        "Date End": date_end,
        "Top Source": top_source,
        "Missing Names": missing_names,
        "Invalid Names": invalid_count,
        "Multi-Source Athletes": multi_source_athletes
    }])
    summary.to_csv("part1_summary.csv", index=False)
    print("\n✅ Saved summary: part1_summary.csv")

except Exception as e:
    print("Error:", e)

finally:
    engine.dispose()



# Part 1.3 Metric Discovery and Selection


