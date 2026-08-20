from pathlib import Path
import pandas as pd

VALIDATION_DIR = Path("data/validation")

for csv_file in VALIDATION_DIR.glob("*.csv"):
    df = pd.read_csv(csv_file)

    # Create the column if it doesn't exist
    if "correct" not in df.columns:
        df["correct"] = "1"

    # If the column exists but is empty, fill with ?
    df["correct"] = df["correct"].fillna("1")

    df.to_csv(csv_file, index=False)

    print(f"Prepared: {csv_file.name}")