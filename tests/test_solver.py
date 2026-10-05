import pandas as pd
import pytest

from src.solver import ProcurementProblem, solve_manual_baseline, solve_procurement


@pytest.fixture
def toy_problem() -> ProcurementProblem:
    """
    Minimal hand-checkable scenario:
      - 1 product, BOM requires 100 units (tolerance 10% -> max 110)
      - 2 vendors: A is cheaper but has a low MOQ threshold issue,
        B is more expensive but abundant capacity
    """
    quotation = pd.DataFrame(
        {
            "product_id": ["P1", "P1"],
            "vendor_id": ["A", "B"],
            "unit_price": [10.0, 12.0],
            "MOQ": [20, 20],
            "Capacity": [60, 200],
            "lead_time": [30, 10],
            "oversea_vendor": [0, 0],
        }
    )
    bom = pd.DataFrame({"product_id": ["P1"], "quantity": [100]})
    return ProcurementProblem(quotation=quotation, bom=bom, bom_tolerance=0.10)


def test_cost_model_meets_bom_bounds(toy_problem):
    result = solve_procurement(toy_problem, objective_type="cost")
    assert result.is_feasible
    total_qty = result.allocation["allocated_quantity"].sum()
    assert 100 <= total_qty <= 110


def test_cost_model_prefers_cheaper_vendor(toy_problem):
    result = solve_procurement(toy_problem, objective_type="cost")
    # Vendor A is cheaper (10 < 12) but capped at 60 units, so the solver
    # must still use some of B to reach the 100-unit BOM minimum.
    vendors_used = set(result.allocation["vendor_id"])
    assert "A" in vendors_used


def test_infeasible_when_capacity_below_bom_minimum():
    quotation = pd.DataFrame(
        {
            "product_id": ["P1"],
            "vendor_id": ["A"],
            "unit_price": [10.0],
            "MOQ": [5],
            "Capacity": [50],
        }
    )
    bom = pd.DataFrame({"product_id": ["P1"], "quantity": [100]})
    problem = ProcurementProblem(quotation=quotation, bom=bom, bom_tolerance=0.08)

    result = solve_procurement(problem, objective_type="cost")
    assert not result.is_feasible
    assert result.status == "INFEASIBLE"


def test_require_all_vendors_activates_every_vendor(toy_problem):
    result = solve_procurement(toy_problem, objective_type="risk", require_all_vendors=True)
    assert result.is_feasible
    assert result.n_vendors_used == result.n_vendors_available


def test_manual_baseline_meets_minimum_quantity(toy_problem):
    res = solve_manual_baseline(toy_problem)
    assert res.is_feasible
    assert res.total_cost > 0
    assert res.total_cost == res.total_purchase_cost + res.total_po_cost
    assert res.total_risk >= 0
    assert res.n_vendors_used > 0
    assert res.allocation["allocated_quantity"].sum() >= 100

    # Test backward-compatible tuple unpacking
    allocation, cost = solve_manual_baseline(toy_problem)
    assert cost == res.total_cost
    assert len(allocation) == len(res.allocation)


def test_risk_weights_must_sum_to_one():
    quotation = pd.DataFrame(
        {"product_id": ["P1"], "vendor_id": ["A"], "unit_price": [10.0], "MOQ": [1], "Capacity": [100]}
    )
    bom = pd.DataFrame({"product_id": ["P1"], "quantity": [10]})
    with pytest.raises(ValueError):
        ProcurementProblem(quotation=quotation, bom=bom, price_weight=0.5, lead_time_weight=0.6)
