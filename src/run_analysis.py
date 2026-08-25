"""
End-to-end analysis pipeline: loads the sample dataset, runs the three
sourcing strategies, benchmarks against a manual baseline, runs the Monte
Carlo optimality check, prints a summary table, and saves all charts used
in the README to assets/.

Usage:
    python -m src.run_analysis
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .simulation import run_feasible_solution_sweep
from .solver import ProcurementProblem, solve_manual_baseline, solve_procurement

ASSETS_DIR = "assets"
DATA_PATH = "data/procurement_data.xlsx"

sns.set_theme(style="whitegrid")


def load_problem(path: str = DATA_PATH) -> ProcurementProblem:
    xls = pd.ExcelFile(path)
    vendor_df = pd.read_excel(xls, "vendor_list")
    product_df = pd.read_excel(xls, "product_list")
    bom_df = pd.read_excel(xls, "BOM")
    quotation_df = pd.read_excel(xls, "quotation")
    return ProcurementProblem.from_raw_sheets(vendor_df, product_df, bom_df, quotation_df)


def run_three_models(problem: ProcurementProblem) -> dict:
    results = {
        "cost": solve_procurement(problem, objective_type="cost", require_all_vendors=False),
        "risk": solve_procurement(problem, objective_type="risk", require_all_vendors=False),
        "risk_all_vendors": solve_procurement(problem, objective_type="risk", require_all_vendors=True),
    }
    return results


def print_summary(results: dict, manual_cost: float) -> pd.DataFrame:
    rows = []
    for label, res in results.items():
        rows.append(
            {
                "Model": label,
                "Purchase cost": res.total_purchase_cost,
                "PO overhead": res.total_po_cost,
                "Total cost": res.total_cost,
                "Risk score": res.total_risk,
                "Vendors used": f"{res.n_vendors_used}/{res.n_vendors_available}",
            }
        )
    summary = pd.DataFrame(rows)

    print("\n=== Model comparison ===")
    print(summary.to_string(index=False))

    best_milp_cost = results["cost"].total_cost
    savings = manual_cost - best_milp_cost
    savings_pct = (savings / manual_cost) * 100 if manual_cost else 0
    print(f"\nManual (greedy) baseline cost: ${manual_cost:,.2f}")
    print(f"MILP cost-optimal cost:        ${best_milp_cost:,.2f}")
    print(f"Savings from optimization:     ${savings:,.2f} ({savings_pct:.1f}%)")

    return summary


def plot_vendor_allocation(result, path: str) -> None:
    if result.allocation.empty:
        return
    vendor_costs = (
        result.allocation.groupby("vendor_id")["total_cost"].sum().sort_values(ascending=False)
    )
    plt.figure(figsize=(10, 4.5))
    sns.barplot(x=vendor_costs.index, y=vendor_costs.values, color="#0F6E56")
    plt.title("Order value allocated per vendor (cost-optimal model)")
    plt.ylabel("Allocated value (USD)")
    plt.xlabel("Vendor")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_strategy_comparison(summary: pd.DataFrame, path: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    sns.barplot(data=summary, x="Model", y="Total cost", ax=axes[0], color="#378ADD")
    axes[0].set_title("Total cost by strategy")
    axes[0].set_ylabel("USD")
    axes[0].tick_params(axis="x", rotation=15)

    sns.barplot(data=summary, x="Model", y="Risk score", ax=axes[1], color="#D85A30")
    axes[1].set_title("Risk score by strategy")
    axes[1].set_ylabel("Composite risk (lower = safer)")
    axes[1].tick_params(axis="x", rotation=15)

    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_monte_carlo(feasible_costs: list[float], optimal_cost: float, path: str) -> None:
    plt.figure(figsize=(11, 5))
    x = range(1, len(feasible_costs) + 1)
    plt.plot(x, feasible_costs, color="#D85A30", marker="o", markersize=3, linewidth=1.5, label="Random feasible plans")
    plt.axhline(y=optimal_cost, color="#0F6E56", linestyle="--", linewidth=2.5, label=f"MILP optimum (${optimal_cost:,.0f})")
    plt.fill_between(x, feasible_costs, optimal_cost, color="#FADBD8", alpha=0.4, label="Cost of not optimizing")
    plt.title("MILP optimum vs. 100 random feasible purchase plans")
    plt.xlabel("Feasible plan (sorted by cost, descending)")
    plt.ylabel("Total cost of ownership (USD)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def main() -> None:
    os.makedirs(ASSETS_DIR, exist_ok=True)

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"{DATA_PATH} not found.")

    problem = load_problem()

    print("Solving cost, risk, and relationship-preserving models...")
    results = run_three_models(problem)

    print("Computing manual baseline...")
    _, manual_cost = solve_manual_baseline(problem)

    summary = print_summary(results, manual_cost)
    summary.to_csv(f"{ASSETS_DIR}/model_comparison.csv", index=False)

    plot_vendor_allocation(results["cost"], f"{ASSETS_DIR}/vendor_allocation.png")
    plot_strategy_comparison(summary, f"{ASSETS_DIR}/strategy_comparison.png")

    print("Running Monte Carlo feasibility sweep (100 random plans)...")
    feasible_costs = run_feasible_solution_sweep(problem, n_simulations=100)
    plot_monte_carlo(feasible_costs, results["cost"].total_cost, f"{ASSETS_DIR}/monte_carlo_optimality.png")

    print(f"\nAll charts saved to {ASSETS_DIR}/")


if __name__ == "__main__":
    main()
