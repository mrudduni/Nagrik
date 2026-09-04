"""
ingestion/clean.py
------------------
Step 1: Load, deduplicate, and normalize the raw government-schemes CSV.

Usage:
    python ingestion/clean.py
Output:
    ingestion/data/cleaned.csv
"""

import re
import sys
import pathlib
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).parent.parent
RAW_CSV = ROOT / "updated_data.csv"
OUT_CSV = pathlib.Path(__file__).parent / "data" / "cleaned.csv"
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# ── Category alias map ────────────────────────────────────────────────────────
CATEGORY_ALIASES: dict[str, str] = {
    # SC/ST variants
    "sc/st": "SC/ST",
    "sc st": "SC/ST",
    "sc-st": "SC/ST",
    "scheduled caste": "Scheduled Caste",
    "scheduled tribe": "Scheduled Tribe",
    "obc": "OBC",
    "other backward class": "OBC",
    # Minor normalizations for existing values
    "agriculture,rural & environment": "Agriculture, Rural & Environment",
    "agriculture rural environment": "Agriculture, Rural & Environment",
    "social welfare & empowerment": "Social Welfare & Empowerment",
    "social welfare and empowerment": "Social Welfare & Empowerment",
    "business & entrepreneurship": "Business & Entrepreneurship",
    "education & learning": "Education & Learning",
    "health & wellness": "Health & Wellness",
    "women and child": "Women & Child",
    "skills & employment": "Skills & Employment",
    "banking,financial services and insurance": "Banking, Financial Services & Insurance",
    "banking financial services and insurance": "Banking, Financial Services & Insurance",
    "science, it & communications": "Science, IT & Communications",
    "transport & infrastructure": "Transport & Infrastructure",
    "travel & tourism": "Travel & Tourism",
    "housing & shelter": "Housing & Shelter",
    "sports & culture": "Sports & Culture",
    "utility & sanitation": "Utility & Sanitation",
    "law & justice": "Law & Justice",
}

# ── State name normalization map (common misspellings/variants) ───────────────
STATE_ALIASES: dict[str, str] = {
    "j&k": "Jammu & Kashmir",
    "j & k": "Jammu & Kashmir",
    "jammu and kashmir": "Jammu & Kashmir",
    "jammu & kashmir": "Jammu & Kashmir",
    "ladakh": "Ladakh",
    "andaman": "Andaman & Nicobar Islands",
    "andaman and nicobar": "Andaman & Nicobar Islands",
    "andaman & nicobar": "Andaman & Nicobar Islands",
    "andaman & nicobar islands": "Andaman & Nicobar Islands",
    "chandigarh": "Chandigarh",
    "dadra and nagar haveli": "Dadra & Nagar Haveli and Daman & Diu",
    "daman and diu": "Dadra & Nagar Haveli and Daman & Diu",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "lakshadweep": "Lakshadweep",
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
    "central": "All India",
    "all states": "All India",
    "pan india": "All India",
    "india": "All India",
    "all india": "All India",
}


def normalize_category(raw: str) -> list[str]:
    """Split a comma-separated category string, normalize each part."""
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    normalized = []
    for p in parts:
        key = p.lower().strip()
        normalized.append(CATEGORY_ALIASES.get(key, p.strip()))
    return normalized


def normalize_state(raw: str) -> str:
    """Normalize a single state string."""
    key = raw.lower().strip()
    return STATE_ALIASES.get(key, raw.strip().title())


def clean(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    print(f"[clean] Rows before cleaning: {before}")

    # 1. Drop the unnamed empty column
    unnamed_cols = [c for c in df.columns if str(c).startswith("Unnamed")]
    df = df.drop(columns=unnamed_cols, errors="ignore")

    # 2. Deduplicate on scheme_name + slug
    df = df.drop_duplicates(subset=["scheme_name", "slug"])
    print(f"[clean] After dedup on (scheme_name, slug): {len(df)}")

    # 3. Drop rows with missing scheme_name or eligibility
    df = df.dropna(subset=["scheme_name", "eligibility"])
    df = df[df["scheme_name"].str.strip().ne("")]
    df = df[df["eligibility"].str.strip().ne("")]
    print(f"[clean] After dropping null scheme_name/eligibility: {len(df)}")

    # 4. Strip all text fields
    text_cols = ["scheme_name", "slug", "details", "benefits", "eligibility",
                 "application", "documents", "level", "schemeCategory", "tags"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # 5. Normalize schemeCategory → normalized_categories (list → joined str)
    df["normalized_categories"] = df["schemeCategory"].apply(
        lambda x: " | ".join(normalize_category(x)) if x else ""
    )

    # 6. Normalize level
    df["level"] = df["level"].str.strip().str.title()

    # 7. Derive source_url from slug
    df["source_url"] = df["slug"].apply(
        lambda s: f"https://www.myscheme.gov.in/schemes/{s}" if s else ""
    )

    # 8. Generate a stable scheme_id from slug (alphanumeric + hyphens)
    df["scheme_id"] = df["slug"].apply(
        lambda s: re.sub(r"[^a-z0-9\-]", "-", s.lower())
    )

    after = len(df)
    print(f"[clean] OK Rows surviving cleaning: {after} (dropped {before - after})")
    return df.reset_index(drop=True)


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(f"[clean] Reading {RAW_CSV} ...")
    df = pd.read_csv(RAW_CSV, encoding="utf-8", on_bad_lines="skip")
    print(f"[clean] Shape: {df.shape}")
    print(f"[clean] Columns: {list(df.columns)}")

    df_clean = clean(df)

    df_clean.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"[clean] Saved -> {OUT_CSV}")

    # Print sample
    pd.set_option("display.max_colwidth", 60)
    print("\n[clean] Sample (3 rows):")
    print(df_clean[["scheme_id", "scheme_name", "level", "normalized_categories"]].head(3).to_string())


if __name__ == "__main__":
    main()
