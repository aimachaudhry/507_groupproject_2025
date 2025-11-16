# Part 2: Data Cleaning & Transformation

import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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

# 2.1 Missing Data Analysis

# Selected metrics

selected_metrics = ["accel_load_accum", 
                    "distance_total",
                    "Jump Height(m)", 
                    "Peak Propulsive Force(N)", 
                    "RSI"]
                    

# Create a string for SQL
metrics_str = ", ".join([f"'{metric}'" for metric in selected_metrics])


# Load data
query = text(f"""
    SELECT 
        playername,
        team,
        metric,
        value,
        timestamp,
        data_source
    FROM research_experiment_refactor_test
    WHERE metric IN ({metrics_str})
""")
df = pd.read_sql(query, engine)

# Convert timestamp column to datetime type
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

# 2.1a — Metrics with the most NULL or zero values
df["is_missing"] = df["value"].isna() | (df["value"] == 0)

# Group and compute percentages
missing_summary = df.groupby("metric")["is_missing"].agg(
    total_missing="sum",
    total_records="count"
)

missing_summary["percent_missing"] = (
    missing_summary["total_missing"] / missing_summary["total_records"] * 100
)

print(missing_summary)


# 2.1b — Percentage of athletes with more than 5 measurements for each team

# Count how many measurements each athlete has per metric

counts = (
    df.groupby(["team", "playername", "metric"])
      .size()
      .reset_index(name="measurement_count")
)

counts["sufficient_measurements"] = counts["measurement_count"] >= 5

# Aggregate at team-metric level
team_metric_coverage = (
    counts.groupby(["team", "metric"])
          .agg(
              total_athletes=("playername", "count"),
              athletes_with_sufficient_measurements=("sufficient_measurements", "sum")
          )
)


# Calculate % of athletes per team-metric with ≥5 measurements
team_metric_coverage["percent_with_sufficient_measurements"] = (
    team_metric_coverage["athletes_with_sufficient_measurements"]
    / team_metric_coverage["total_athletes"] * 100
)

print("\n=== Team Metric Coverage (More than 5 measurements) ===")
print(team_metric_coverage)


# Calculate overall coverage across all team-metric combinations

avg_coverage = team_metric_coverage['percent_with_sufficient_measurements'].mean()

print("\n=== Athlete Measurement Coverage Summary ===")
print(f"Average % of athletes with ≥5 measurements: {avg_coverage:.1f}%")


# 2.1c — Athletes not tested within last 6 months

# Each athlete's most recent test date
latest_test_date = df["timestamp"].max()
cutoff_date = latest_test_date - pd.DateOffset(months=6)

# Filter athletes who are inactive
recent_tests = (
    df.groupby("playername")["timestamp"]
      .max()
      .reset_index(name="last_test")
)

inactive_athletes = recent_tests[recent_tests["last_test"] < cutoff_date]

print("\n=== Athletes Not Tested in Last 6 Months ===")
print(f"{len(inactive_athletes)} athletes not tested in the last 6 months")
print(inactive_athletes)


# 2.1d — Sufficient data to answer research question 


