import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load database credentials
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

OUTPUT_FILE = "part4_flagged_athletes.csv"

# THRESHOLD 1 (CMJ / RSI)
CMJ_RSI_ROLLING_TESTS = 4                # number of previous tests used as baseline
CMJ_RSI_DROP_THRESHOLD = 0.10            # 10% drop

# THRESHOLD 2 (AAL)
AAL_ROLLING_WINDOW_DAYS = "7D"           # rolling weekly window per player
AAL_SPIKE_RATIO_THRESHOLD = 1.5          # 150% of rolling weekly mean

# THRESHOLD 3 (LOW MOVEMENT OUTPUT)
LOW_DIST_RATIO_THRESHOLD = 0.80          # 20% below team median


def main():

    # Connect to database
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
    
    # Query data from database
    query = text("""
        SELECT 
            playername,
            team,
            timestamp as date,
            CASE 
                WHEN metric = 'Jump Height(m)' THEN value 
                ELSE NULL 
            END as cmj_height,
            CASE 
                WHEN metric = 'RSI' THEN value 
                ELSE NULL 
            END as rsi,
            CASE 
                WHEN metric = 'accel_load_accum' THEN value 
                ELSE NULL 
            END as aal,
            CASE 
                WHEN metric = 'distance_total' THEN value 
                ELSE NULL 
            END as total_distance
        FROM research_experiment_refactor_test
        WHERE metric IN ('Jump Height(m)', 'RSI', 'accel_load_accum', 'distance_total')
        ORDER BY playername, timestamp
    """)
    
    df_raw = pd.read_sql(query, engine)
    
    # Pivot data so each row has all metrics for a single timestamp/player
    df = df_raw.groupby(['playername', 'team', 'date']).agg({
        'cmj_height': 'first',
        'rsi': 'first', 
        'aal': 'first',
        'total_distance': 'first'
    }).reset_index()
    
    # Remove rows where all metric values are null
    df = df.dropna(subset=['cmj_height', 'rsi', 'aal', 'total_distance'], how='all')

    # Make sure date is datetime
    df["date"] = pd.to_datetime(df["date"])

    # Sort per player by date
    df = df.sort_values(by=["playername", "date"]).reset_index(drop=True)
    
    print(f"Loaded {len(df)} records from database for analysis")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Unique athletes: {df['playername'].nunique()}")

    # List to store all flags from all thresholds
    flagged_rows = []

    # ============================================================
    # THRESHOLD 1:
    # NEUROMUSCULAR FATIGUE (CMJ HEIGHT / RSI DROP >= 10%)
    # ============================================================

    # Rolling baseline for CMJ height (exclude current with shift)
    df["cmj_baseline"] = df.groupby("playername")["cmj_height"].transform(
        lambda x: x.shift(1).rolling(
            window=CMJ_RSI_ROLLING_TESTS,
            min_periods=1
        ).mean()
    )

    # Rolling baseline for RSI
    df["rsi_baseline"] = df.groupby("playername")["rsi"].transform(
        lambda x: x.shift(1).rolling(
            window=CMJ_RSI_ROLLING_TESTS,
            min_periods=1
        ).mean()
    )

    # Percent drops from baseline
    df["cmj_drop_pct"] = (df["cmj_baseline"] - df["cmj_height"]) / df["cmj_baseline"]
    df["rsi_drop_pct"] = (df["rsi_baseline"] - df["rsi"]) / df["rsi_baseline"]

    # Loop rows and create flags for THRESHOLD 1
    for _, row in df.iterrows():
        player = row["playername"]
        team = row["team"]
        date = row["date"]

        # CMJ fatigue flag
        if pd.notna(row["cmj_baseline"]) and row["cmj_baseline"] > 0:
            if row["cmj_drop_pct"] >= CMJ_RSI_DROP_THRESHOLD:
                flagged_rows.append({
                    "playername": player,
                    "team": team,
                    "flag_reason": f"CMJ height drop {row['cmj_drop_pct']:.1%} vs baseline",
                    "metric_value": row["cmj_height"],
                    "last_test_date": date.date().isoformat()
                })

        # RSI fatigue flag
        if pd.notna(row["rsi_baseline"]) and row["rsi_baseline"] > 0:
            if row["rsi_drop_pct"] >= CMJ_RSI_DROP_THRESHOLD:
                flagged_rows.append({
                    "playername": player,
                    "team": team,
                    "flag_reason": f"RSI drop {row['rsi_drop_pct']:.1%} vs baseline",
                    "metric_value": row["rsi"],
                    "last_test_date": date.date().isoformat()
                })

    # ============================================================
    # THRESHOLD 2:
    # ACUTE AAL SPIKE (AAL > 150% OF ROLLING WEEKLY AVERAGE)
    # ============================================================

    def add_weekly_aal_mean(group: pd.DataFrame) -> pd.DataFrame:
        """
        Compute rolling weekly mean AAL per player, excluding current day.
        Uses a time-based rolling window (e.g., '7D').
        """
        group = group.set_index("date")
        group["weekly_aal_mean"] = (
            group["aal"]
            .shift(1)
            .rolling(AAL_ROLLING_WINDOW_DAYS, min_periods=1)
            .mean()
        )
        return group.reset_index()

    # Apply per player
    df = df.groupby("playername", group_keys=False).apply(add_weekly_aal_mean)

    # AAL ratio (current vs weekly mean)
    df["aal_ratio"] = df["aal"] / df["weekly_aal_mean"]

    # Create flags for THRESHOLD 2
    for _, row in df.iterrows():
        if pd.isna(row.get("weekly_aal_mean")) or row["weekly_aal_mean"] <= 0:
            continue

        if row["aal_ratio"] > AAL_SPIKE_RATIO_THRESHOLD:
            flagged_rows.append({
                "playername": row["playername"],
                "team": row["team"],
                "flag_reason": f"AAL spike {row['aal_ratio']:.2f}x weekly mean",
                "metric_value": row["aal"],
                "last_test_date": row["date"].date().isoformat()
            })

    # ============================================================
    # THRESHOLD 3:
    # LOW MOVEMENT OUTPUT (TOTAL DISTANCE < 80% OF TEAM MEDIAN)
    # ============================================================

    # Compute team-specific median total distance
    df["team_median_dist"] = df.groupby("team")["total_distance"].transform("median")

    # Flag where today's/session's total distance is < 80% of that median
    for _, row in df.iterrows():
        median_dist = row.get("team_median_dist")
        total_dist = row.get("total_distance")
        
        if pd.isna(median_dist) or pd.isna(total_dist) or median_dist <= 0:
            continue

        ratio = total_dist / median_dist

        if ratio < LOW_DIST_RATIO_THRESHOLD:
            flagged_rows.append({
                "playername": row["playername"],
                "team": row["team"],
                "flag_reason": f"Low movement output {ratio:.1%} of team median",
                "metric_value": total_dist,
                "last_test_date": row["date"].date().isoformat()
            })

    # ============================================================
    # SAVE ALL FLAGS TO CSV
    # ============================================================

    if flagged_rows:
        flagged_df = pd.DataFrame(flagged_rows)
        flagged_df.to_csv(OUTPUT_FILE, index=False)
        print(f"Flagged athlete file created: {OUTPUT_FILE}")
        print(f"Total flagged rows: {len(flagged_df)}")
    else:
        print("No athletes met the flag criteria. No CSV created.")


if __name__ == "__main__":
    main()