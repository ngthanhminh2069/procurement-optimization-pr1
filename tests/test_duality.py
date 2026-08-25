import pandas as pd
import pytest

from src.duality import compute_shadow_prices, compute_unused_vendor_opportunity
from src.solver import ProcurementProblem, solve_procurement


@pytest.fixture
def toy_problem() -> ProcurementProblem:
    """
    2 products, 2 vendors each, with one deliberately tight capacity so we
    have a known binding constraint to check the shadow price against.
    """
    quotation = pd.DataFrame(
        {
            "product_id": ["P1", "P1", "P2", "P2"],
            "vendor_id": ["A", "B", "A", "C"],
            "unit_price": [10.0, 12.0, 8.0, 9.0],
            "MOQ": [10, 10, 10, 10],
            "Capacity": [55, 200, 200, 200],  # A's capacity for P1 is tight
            "lead_time": [30, 10, 30, 20],
            "oversea_vendor": [0, 0, 0, 0],
        }
    )
    bom = pd.DataFrame({"product_id": ["P1", "P2"], "quantity": [100, 50]})
    return ProcurementProblem(quotation=quotation, bom=bom, bom_tolerance=0.10)


def test_shadow_prices_are_non_negative_for_bom_min(toy_problem):
    report = compute_shadow_prices(toy_problem)
    assert (report.bom_coverage["shadow_price"] >= 0).all()


def test_capacity_shadow_price_matches_resolve(toy_problem):
    """
    The reported shadow price for a binding capacity constraint must equal
    the actual cost change from relaxing that capacity by exactly 1 unit
    and re-solving the full MILP — this is the ground-truth check for the
    fix-and-relax technique.
    """
    report = compute_shadow_prices(toy_problem)
    binding = report.capacity[(report.capacity["product_id"] == "P1") & (report.capacity["vendor_id"] == "A")]
    assert not binding.empty, "Expected vendor A's capacity on P1 to be binding"
    shadow_price = binding["shadow_price"].iloc[0]

    # Relax capacity by 1 and re-solve the real MILP
    perturbed_quotation = toy_problem.quotation.copy()
    mask = (perturbed_quotation["product_id"] == "P1") & (perturbed_quotation["vendor_id"] == "A")
    perturbed_quotation.loc[mask, "Capacity"] += 1
    perturbed_problem = ProcurementProblem(
        quotation=perturbed_quotation, bom=toy_problem.bom, bom_tolerance=toy_problem.bom_tolerance
    )

    base_result = solve_procurement(toy_problem, objective_type="cost")
    perturbed_result = solve_procurement(perturbed_problem, objective_type="cost")
    actual_delta = base_result.total_cost - perturbed_result.total_cost

    assert shadow_price == pytest.approx(actual_delta, abs=1e-6)


def test_bom_min_shadow_price_matches_resolve(toy_problem):
    report = compute_shadow_prices(toy_problem)
    row = report.bom_coverage[report.bom_coverage["product_id"] == "P1"]
    shadow_price = row["shadow_price"].iloc[0]

    perturbed_bom = toy_problem.bom.copy()
    perturbed_bom.loc[perturbed_bom["product_id"] == "P1", "quantity"] -= 1
    perturbed_problem = ProcurementProblem(
        quotation=toy_problem.quotation, bom=perturbed_bom, bom_tolerance=toy_problem.bom_tolerance
    )

    base_result = solve_procurement(toy_problem, objective_type="cost")
    perturbed_result = solve_procurement(perturbed_problem, objective_type="cost")
    actual_delta = base_result.total_cost - perturbed_result.total_cost

    assert shadow_price == pytest.approx(actual_delta, abs=1e-6)


def test_unused_vendor_opportunity_cost_is_never_negative(toy_problem):
    """
    Forcing an excluded vendor into the solution can only match or exceed
    the unconstrained optimum's cost — the base solve was already free to
    use that vendor and chose not to, so opportunity_cost >= 0 always.
    """
    report = compute_unused_vendor_opportunity(toy_problem)
    numeric = report["opportunity_cost"].dropna()
    assert (numeric >= -1e-6).all()


def test_unused_vendor_opportunity_cost_matches_manual_forced_resolve():
    """
    Vendor C is deliberately priced out of contention for both products.
    Its reported opportunity cost must equal the actual cost difference
    between the base optimum and a MILP re-solve with vendor C's z forced
    to 1 by hand, built independently of compute_unused_vendor_opportunity.
    """
    from ortools.linear_solver import pywraplp

    quotation = pd.DataFrame(
        {
            "product_id": ["P1", "P1", "P2", "P2"],
            "vendor_id": ["A", "B", "A", "C"],
            "unit_price": [10.0, 12.0, 8.0, 50.0],  # C is deliberately expensive
            "MOQ": [10, 10, 10, 10],
            "Capacity": [200, 200, 200, 200],
        }
    )
    bom = pd.DataFrame({"product_id": ["P1", "P2"], "quantity": [100, 50]})
    problem = ProcurementProblem(quotation=quotation, bom=bom, bom_tolerance=0.10)

    base_result = solve_procurement(problem, objective_type="cost")
    assert "C" not in set(base_result.allocation["vendor_id"])  # C should be excluded

    report = compute_unused_vendor_opportunity(problem)
    reported_delta = report.loc[report["vendor_id"] == "C", "opportunity_cost"].iloc[0]

    # Manually force C's y=1 for P2 (its only offered product) and re-solve,
    # independently of the internal _solve_with_forced_vendor implementation.
    q_df = problem.prepared_quotation
    bom_dict = dict(zip(problem.bom["product_id"], problem.bom["quantity"]))
    solver = pywraplp.Solver.CreateSolver("SCIP")
    x, y = {}, {}
    for row in q_df.itertuples(index=False):
        x[(row.product_id, row.vendor_id)] = solver.IntVar(0, int(row.Capacity), f"x_{row.product_id}_{row.vendor_id}")
        y[(row.product_id, row.vendor_id)] = solver.IntVar(0, 1, f"y_{row.product_id}_{row.vendor_id}")
        solver.Add(x[(row.product_id, row.vendor_id)] >= row.MOQ * y[(row.product_id, row.vendor_id)])
        solver.Add(x[(row.product_id, row.vendor_id)] <= row.Capacity * y[(row.product_id, row.vendor_id)])
    for p_id, min_qty in bom_dict.items():
        max_qty = min_qty * 1.10
        vendors_for_p = q_df.loc[q_df["product_id"] == p_id, "vendor_id"].tolist()
        total = sum(x[(p_id, v)] for v in vendors_for_p)
        solver.Add(total >= min_qty)
        solver.Add(total <= max_qty)
    solver.Add(y[("P2", "C")] == 1)  # force C to be used
    objective = solver.Objective()
    for row in q_df.itertuples(index=False):
        objective.SetCoefficient(x[(row.product_id, row.vendor_id)], float(row.unit_price))
    objective.SetMinimization()
    solver.Solve()
    forced_purchase_cost = sum(var.solution_value() * q_df[(q_df["product_id"] == p) & (q_df["vendor_id"] == v)]["unit_price"].iloc[0] for (p, v), var in x.items())
    forced_vendors_used = {v for (p, v), var in x.items() if var.solution_value() > 0}
    # ProcurementProblem defaults every quote to po_cost_local ($50) when no
    # oversea_vendor column is present — match that here so the manual
    # total is computed the same way solve_procurement computes it.
    forced_po_cost = len(forced_vendors_used) * problem.po_cost_local
    forced_cost = forced_purchase_cost + forced_po_cost

    manual_delta = forced_cost - base_result.total_cost
    assert reported_delta == pytest.approx(manual_delta, abs=1e-6)
