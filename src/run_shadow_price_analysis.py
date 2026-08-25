"""
Run shadow price (dual value) analysis on the real procurement dataset and
export a report. See src/duality.py for the fix-and-relax methodology.

Usage:
    python -m src.run_shadow_price_analysis
"""

from __future__ import annotations

import os

import pandas as pd

from .duality import compute_shadow_prices, compute_unused_vendor_opportunity
from .solver import ProcurementProblem

DATA_PATH = "data/procurement_data.xlsx"
OUTPUT_DIR = "assets"


def load_problem(path: str) -> ProcurementProblem:
    xls = pd.ExcelFile(path)
    vendor_df = pd.read_excel(xls, "vendor_list")
    product_df = pd.read_excel(xls, "product_list")
    bom_df = pd.read_excel(xls, "BOM")
    quotation_df = pd.read_excel(xls, "quotation")
    return ProcurementProblem.from_raw_sheets(vendor_df, product_df, bom_df, quotation_df)


def main() -> None:
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"{DATA_PATH} not found.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    problem = load_problem(DATA_PATH)
    report = compute_shadow_prices(problem)

    print(f"Base cost-optimal total cost: ${report.base_total_cost:,.2f}\n")

    print("=== BOM minimum coverage: top 10 most expensive units to be forced to buy ===")
    print(report.bom_coverage.head(10).to_string(index=False))
    report.bom_coverage.to_csv(f"{OUTPUT_DIR}/shadow_price_bom_coverage.csv", index=False)

    print(f"\n=== Vendor capacity constraints worth relaxing ({len(report.capacity)} binding) ===")
    if not report.capacity.empty:
        print(report.capacity.head(10).to_string(index=False))
    report.capacity.to_csv(f"{OUTPUT_DIR}/shadow_price_capacity.csv", index=False)

    nonzero_tolerance = report.bom_tolerance[report.bom_tolerance["shadow_price"].abs() > 1e-9]
    print(f"\n=== BOM tolerance ceilings worth raising ({len(nonzero_tolerance)} binding) ===")
    if not nonzero_tolerance.empty:
        print(nonzero_tolerance.head(10).to_string(index=False))
    else:
        print("None binding at current tolerance level.")
    report.bom_tolerance.to_csv(f"{OUTPUT_DIR}/shadow_price_bom_tolerance.csv", index=False)

    print("\n=== Opportunity cost of vendors excluded from the optimal solution ===")
    unused_report = compute_unused_vendor_opportunity(problem)
    print(unused_report.to_string(index=False) if not unused_report.empty else "All vendors are used in the optimal solution.")
    unused_report.to_csv(f"{OUTPUT_DIR}/shadow_price_unused_vendors.csv", index=False)

    print(f"\nFull reports saved to {OUTPUT_DIR}/shadow_price_*.csv")


if __name__ == "__main__":
    main()
