skills:
  - name: load_dataset
    description: Reads ward_budget.csv, validates required columns, and reports null rows with reasons before returning data.
    input: File path (string) to ward_budget.csv.
    output: Dictionary containing {data: DataFrame, null_rows: list of dicts with period/ward/category/reason, null_count: int}.
    error_handling: If file not found, raise FileNotFoundError. If columns missing, raise ValueError listing missing columns. If actual_spend is all null, log warning but return data.

  - name: filter_by_ward_category
    description: Filters dataset to rows matching specified ward and category pair only.
    input: DataFrame from load_dataset, ward (string), category (string).
    output: Filtered DataFrame with only matching rows, sorted by period. Count of matching rows.
    error_handling: If ward or category not found, return empty DataFrame and log "No data for [ward]/[category]". If both empty, refuse computation.

  - name: compute_growth
    description: Calculates MoM or YoY growth rate for a single ward-category series, showing formula for each row.
    input: Filtered DataFrame (period sorted), growth_type ("MoM" or "YoY").
    output: DataFrame with columns [period, actual_spend, growth_rate, formula, notes]. Growth rates as percentages. Null rows show NULL in growth_rate and flagged in notes.
    error_handling: If growth_type not in ("MoM", "YoY"), raise ValueError "growth_type must be 'MoM' or 'YoY'". If no prior period exists for comparison, set growth_rate to NULL and note "No prior period".
