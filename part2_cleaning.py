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


# 2.2 Data Transformation (Group)

# The dataset is currently in long format, meaning each row represents one metric for a given timestamp. 
# For analysis, we need to convert it into wide format so that each row represents a single test session with all selected metrics.
# This function:
# - Takes a player name and the selected metrics
# - Filters only the relevant player's data
# - Pivots long → wide format (timestamp as rows, metrics as columns)
# - Handles missing values
# - Returns a clean DataFrame ready for part 3 modeling/visualization

def transform_player_data(df, player_name, metric_list):
    """
    Transform long-format player data into wide-format for selected metrics.

    Parameters:
        df (DataFrame): Original long-format dataset
        player_name (str): Player name string as stored in DB (e.g., "PLAYER_001")
        metric_list (list): List of selected metric names

    Returns:
        DataFrame: Wide-format table (timestamp, metrics)
    """

    # Filter for selected player
    player_df = df[df["playername"] == player_name]

    # Only keep selected metrics
    player_df = player_df[player_df["metric"].isin(metric_list)]

    # Pivot table from long → wide format
    wide_df = player_df.pivot_table(
        index="timestamp",
        columns="metric",
        values="value",
        aggfunc="first"
    ).reset_index()

    # Handle missing values
    # Drop rows with all missing metrics
    wide_df = wide_df.dropna(how="all", subset=metric_list)

    # Fill remaining missing values using forward/backward fill
    wide_df = wide_df.fillna(method="ffill").fillna(method="bfill")

    return wide_df


# ---- Test function on 3 different athletes ----
test_players = [
    df["playername"].unique()[0],
    df["playername"].unique()[1],
    df["playername"].unique()[2]
]

print("\n=== Testing transformation on 3 athletes ===")

for p in test_players:
    print(f"\nPlayer: {p}")
    transformed = transform_player_data(df, p, selected_metrics)
    print(transformed.head())


# 2.3 Derived Metric in Colab
import pandas as pd
from scipy.stats import zscore

print("\n=== 2.3 Derived Metric: Team Means & Relative Performance ===")

# 2.3a — Calculate team mean for each metric
team_metric_means = (
    df.groupby(["metric", "team"])["value"]
      .mean()
      .reset_index(name="team_mean")
)

print("\n=== Team Means by Metric ===")
for metric_name in selected_metrics:
    metric_means = team_metric_means[team_metric_means["metric"] == metric_name]
    print(f"\n{metric_name}:")
    for _, row in metric_means.iterrows():
        print(f"  {row['team']:<30}: {row['team_mean']:>10.2f}")

# Merge into full dataset
df_derived = df.merge(team_metric_means, on=["metric", "team"], how="left")

# 2.3b — Percent difference from team mean
df_derived["percent_diff"] = (
    (df_derived["value"] - df_derived["team_mean"]) / df_derived["team_mean"]
) * 100

# 2.3c — Z-scores
df_derived["z_score"] = (
    df_derived.groupby(["metric", "team"])["value"].transform(zscore)
)

# 2.3d — Top 5 and Bottom 5 Performers (Unique Athletes)
top_bottom_records = []
top_performers_only = []

for metric_name in selected_metrics:
    metric_data = df_derived[df_derived["metric"] == metric_name].copy()

    # Get the best performance for each unique athlete for this metric
    athlete_best = metric_data.loc[metric_data.groupby("playername")["percent_diff"].idxmax()]
    
    # Now get top 5 and bottom 5 unique athletes
    top5 = athlete_best.sort_values("percent_diff", ascending=False).head(5)
    bottom5 = athlete_best.sort_values("percent_diff", ascending=True).head(5)

    print(f"\n--- Metric: {metric_name} ---")
    print("Top 5 performers (unique athletes):")
    print(top5[["playername", "team", "value", "team_mean", "percent_diff","z_score", "session_type"]])

    print("Bottom 5 performers (unique athletes):")
    print(bottom5[["playername", "team", "value", "team_mean", "percent_diff","z_score", "session_type"]])

    top_bottom_records.append(top5)
    top_bottom_records.append(bottom5)
    
    # Store only top performers for separate CSV
    top_performers_only.append(top5)

# 2.3e — Save results
if top_bottom_records:
    top_bottom_df = pd.concat(top_bottom_records, ignore_index=True)
    top_performers_df = pd.concat(top_performers_only, ignore_index=True)

    df_derived.to_csv("part2_derived_metrics_full.csv", index=False)
    top_bottom_df.to_csv("part2_top_bottom_performers.csv", index=False)
    top_performers_df.to_csv("part2_top_five_performers.csv", index=False)

    print("\nSaved part2_derived_metrics_full.csv")
    print("Saved part2_top_bottom_performers.csv")
    print("Saved part2_top_five_performers.csv")