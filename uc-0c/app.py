"""
UC-0C app.py — Budget Growth Calculator
Computes MoM/YoY growth at per-ward, per-category granularity only.
Enforces null flagging, formula display, and refusal of cross-ward/cross-category aggregation.
See README.md for run command and enforcement rules.
"""
import argparse
import pandas as pd
import sys
from pathlib import Path

# Known null rows from README
NULL_ROWS = {
    ("2024-03", "Ward 2 – Shivajinagar", "Drainage & Flooding"): "Data not submitted by ward office",
    ("2024-07", "Ward 4 – Warje", "Roads & Pothole Repair"): "Audit freeze — figures under review",
    ("2024-05", "Ward 5 – Hadapsar", "Streetlight Maintenance"): "Equipment procurement delay",
    ("2024-08", "Ward 3 – Kothrud", "Parks & Greening"): "Project suspended — pending approval",
    ("2024-11", "Ward 1 – Kasba", "Waste Management"): "Unexpected absence"
}

def load_dataset(filepath):
    """Load CSV and report null rows before returning."""
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read CSV: {e}")
        sys.exit(1)
    
    # Validate columns
    required_cols = ["period", "ward", "category", "budgeted_amount", "actual_spend", "notes"]
    missing = set(required_cols) - set(df.columns)
    if missing:
        print(f"ERROR: Missing columns: {missing}")
        sys.exit(1)
    
    # Find null rows
    null_mask = df["actual_spend"].isna()
    null_rows = df[null_mask][["period", "ward", "category", "notes"]].to_dict('records')
    
    print(f"\n{'='*80}")
    print(f"NULL ROWS REPORT: {len(null_rows)} rows with missing actual_spend")
    print(f"{'='*80}")
    for row in null_rows:
        print(f"  [{row['period']}] {row['ward']} / {row['category']}")
        print(f"    → Reason: {row['notes']}")
    print(f"{'='*80}\n")
    
    return df, null_rows

def filter_by_ward_category(df, ward, category):
    """Filter to specified ward and category."""
    filtered = df[(df["ward"] == ward) & (df["category"] == category)].copy()
    filtered = filtered.sort_values("period").reset_index(drop=True)
    
    if filtered.empty:
        print(f"ERROR: No data found for ward='{ward}', category='{category}'")
        sys.exit(1)
    
    print(f"Loaded {len(filtered)} months of data for {ward} / {category}")
    return filtered

def compute_growth_mom(series):
    """Compute month-over-month growth."""
    results = []
    
    for idx, row in series.iterrows():
        period = row["period"]
        actual_spend = row["actual_spend"]
        
        if pd.isna(actual_spend):
            results.append({
                "period": period,
                "actual_spend": None,
                "growth_rate": None,
                "formula": "N/A",
                "flag": "NULL — not computed"
            })
        elif idx == 0:
            # First month has no prior
            results.append({
                "period": period,
                "actual_spend": f"{actual_spend:.1f}",
                "growth_rate": None,
                "formula": "No prior month",
                "flag": ""
            })
        else:
            prior_spend = series.iloc[idx - 1]["actual_spend"]
            if pd.isna(prior_spend):
                # Prior month is null, cannot compute
                results.append({
                    "period": period,
                    "actual_spend": f"{actual_spend:.1f}",
                    "growth_rate": None,
                    "formula": "(prior is NULL)",
                    "flag": "Cannot compute — prior month null"
                })
            else:
                # Compute MoM: (current - prior) / prior × 100%
                growth = ((actual_spend - prior_spend) / prior_spend) * 100
                formula_str = f"({actual_spend:.1f} - {prior_spend:.1f}) / {prior_spend:.1f} × 100%"
                results.append({
                    "period": period,
                    "actual_spend": f"{actual_spend:.1f}",
                    "growth_rate": f"{growth:+.1f}%",
                    "formula": formula_str,
                    "flag": ""
                })
    
    return pd.DataFrame(results)

def compute_growth_yoy(series):
    """Compute year-over-year growth."""
    results = []
    df_dict = {row["period"]: row for _, row in series.iterrows()}
    
    for idx, row in series.iterrows():
        period = row["period"]
        year = period[:4]
        month = period[5:7]
        actual_spend = row["actual_spend"]
        
        if pd.isna(actual_spend):
            results.append({
                "period": period,
                "actual_spend": None,
                "growth_rate": None,
                "formula": "N/A",
                "flag": "NULL — not computed"
            })
        else:
            # Try to find prior year
            prior_year = str(int(year) - 1)
            prior_period = f"{prior_year}-{month}"
            
            if prior_period in df_dict:
                prior_spend = df_dict[prior_period]["actual_spend"]
                if pd.isna(prior_spend):
                    results.append({
                        "period": period,
                        "actual_spend": f"{actual_spend:.1f}",
                        "growth_rate": None,
                        "formula": f"(prior year {prior_period} is NULL)",
                        "flag": "Cannot compute — prior year null"
                    })
                else:
                    growth = ((actual_spend - prior_spend) / prior_spend) * 100
                    formula_str = f"({actual_spend:.1f} - {prior_spend:.1f}) / {prior_spend:.1f} × 100%"
                    results.append({
                        "period": period,
                        "actual_spend": f"{actual_spend:.1f}",
                        "growth_rate": f"{growth:+.1f}%",
                        "formula": formula_str,
                        "flag": ""
                    })
            else:
                results.append({
                    "period": period,
                    "actual_spend": f"{actual_spend:.1f}",
                    "growth_rate": None,
                    "formula": f"No prior year ({prior_period} not found)",
                    "flag": ""
                })
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(
        description="UC-0C: Calculate MoM/YoY budget growth per ward and category"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to ward_budget.csv (e.g., ../data/budget/ward_budget.csv)"
    )
    parser.add_argument(
        "--ward",
        required=True,
        help="Ward name (e.g., 'Ward 1 – Kasba')"
    )
    parser.add_argument(
        "--category",
        required=True,
        help="Category (e.g., 'Roads & Pothole Repair')"
    )
    parser.add_argument(
        "--growth-type",
        required=True,
        choices=["MoM", "YoY"],
        help="Growth type: MoM (month-over-month) or YoY (year-over-year)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output CSV path (e.g., growth_output.csv)"
    )
    
    args = parser.parse_args()
    
    # Step 1: Load and report nulls
    print(f"Loading dataset from: {args.input}")
    df, null_rows = load_dataset(args.input)
    
    # Step 2: Filter
    print(f"Filtering for: ward='{args.ward}', category='{args.category}'")
    filtered = filter_by_ward_category(df, args.ward, args.category)
    
    # Step 3: Compute growth
    print(f"Computing {args.growth_type} growth...\n")
    if args.growth_type == "MoM":
        result_df = compute_growth_mom(filtered)
    else:  # YoY
        result_df = compute_growth_yoy(filtered)
    
    # Step 4: Write output
    try:
        result_df.to_csv(args.output, index=False)
        print(f"✓ Output written to: {args.output}")
    except IOError as e:
        print(f"ERROR: Could not write output file: {e}")
        sys.exit(1)
    
    # Step 5: Display results
    print(f"\n{'='*120}")
    print(f"GROWTH CALCULATION RESULTS: {args.ward} / {args.category}")
    print(f"Growth Type: {args.growth_type}")
    print(f"{'='*120}")
    print(result_df.to_string(index=False))
    print(f"{'='*120}\n")
    
    print("✓ Computation complete. All formulas shown. No cross-ward/cross-category aggregation.")
    sys.exit(0)

if __name__ == "__main__":
    main()
