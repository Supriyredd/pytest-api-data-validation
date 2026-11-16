"""API-to-database reconciliation with pandas.

Compares two data sets on a key and returns rows that are missing on either side
or whose values differ. Used by the tests and writes a CSV report for triage.
"""
from pathlib import Path

import pandas as pd


def reconcile(api_rows: list[dict], db_rows: list[dict], key: str, columns: list[str]) -> pd.DataFrame:
    api = pd.DataFrame(api_rows)[[key, *columns]]
    db = pd.DataFrame(db_rows)[[key, *columns]]
    merged = api.merge(db, on=key, how="outer", suffixes=("_api", "_db"), indicator=True)

    issues = []
    for _, row in merged.iterrows():
        if row["_merge"] == "left_only":
            issues.append({key: row[key], "column": "*", "api": "present", "db": "missing"})
        elif row["_merge"] == "right_only":
            issues.append({key: row[key], "column": "*", "api": "missing", "db": "present"})
        else:
            for col in columns:
                a, d = row[f"{col}_api"], row[f"{col}_db"]
                if a != d:
                    issues.append({key: row[key], "column": col, "api": a, "db": d})
    return pd.DataFrame(issues, columns=[key, "column", "api", "db"])


def write_report(df: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
