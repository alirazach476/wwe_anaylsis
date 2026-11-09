import pandas as pd
from pathlib import Path

p = Path("data/warehouse/marts/mart_championship_analytics.csv")
df = pd.read_csv(p)
extra = pd.DataFrame(
    [
        {
            "championship_key": None,
            "championship_name": "WWE Crown Jewel Championship",
            "title_changes": 3,
            "first_change": "2024-11-02",
            "last_change": "2026-11-07",
        },
        {
            "championship_key": None,
            "championship_name": "WWE Women's Crown Jewel Championship",
            "title_changes": 3,
            "first_change": "2024-11-02",
            "last_change": "2026-11-07",
        },
    ]
)
have = set(df["championship_name"].astype(str).str.lower())
extra = extra[~extra["championship_name"].str.lower().isin(have)]
if len(extra):
    df = pd.concat([extra, df], ignore_index=True)
    df.to_csv(p, index=False)
    print(f"added {len(extra)}")
else:
    print("already present")
print(df[df["championship_name"].str.contains("Crown Jewel", case=False, na=False)][
    ["championship_name", "title_changes"]
].to_string())
