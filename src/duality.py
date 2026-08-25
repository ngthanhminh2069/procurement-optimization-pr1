"""
Shadow price (dual value) analysis for the procurement MILP.

OR-Tools does not expose dual values for a Mixed-Integer Linear Program —
duality is only rigorously defined for a Linear Program. This module
implements the standard **fix-and-relax** technique to recover valid
shadow prices at a MILP's optimal solution:

    1. Solve the full MILP (integer x, binary y/z) to optimality.
    2. Fix every binary variable (y, z) at its optimal value — turning
       them into constants.
    3. Re-solve the remaining problem, now a pure LP in the continuous
       relaxation of x, using a solver that exposes dual values (GLOP).
    4. The dual values of that LP are valid shadow prices for the
       original MILP *at that specific solution* — i.e. the marginal
       value of relaxing a constraint by one unit, holding the vendor
       selection (y, z) fixed.

This is standard practice in OR: it does not extend duality theory to
integer programs in general, but gives an economically meaningful,
locally valid answer to "what would relaxing this constraint by one unit
be worth?" at the solution actually being used.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from ortools.linear_solver import pywraplp

from .solver import ProcurementProblem, SolveResult, solve_procurement


@dataclass
class ShadowPriceReport:
    bom_coverage: pd.DataFrame  # per-product: dual on the BOM minimum constraint
    capacity: pd.DataFrame      # per (product, vendor): dual on the capacity constraint
    bom_tolerance: pd.DataFrame  # per-product: dual on the BOM maximum (tolerance) constraint
    base_total_cost: float


def compute_unused_vendor_opportunity(problem: ProcurementProblem) -> pd.DataFrame:
    """
    Fix-and-relax duals are silent about vendors excluded from the optimal
    solution (y* = 0) — those (product, vendor) variables are dropped from
    the relaxed LP entirely, so there is no dual value to read for them.
    This is not an oversight to patch with a bound trick: MOQ makes the
    underlying set non-convex ("buy 0, or buy >= MOQ"), which is exactly
    why a binary y is needed in the first place — a reduced cost read off
    a naively re-added variable would not be economically meaningful.

    The honest way to answer "how far is this excluded vendor from being
    worth using?" is direct re-optimization: force z[v] = 1 (the vendor
    must receive at least one order) and re-solve the *full* MILP. The
    cost increase over the unconstrained optimum is the real opportunity
    cost of excluding that vendor at its current price/MOQ/capacity terms
    — and doubles as an approximate "how much of a concession would this
    vendor need to give (price cut, MOQ reduction, capacity increase) to
    become worth using".

    This does not attempt every price/MOQ/capacity combination — it
    answers the question at the vendor's *current* quoted terms. Testing
    specific concessions (e.g. "what if vendor X cut price by 10%?") is a
    separate what-if re-solve, not covered here.
    """
    base_result = solve_procurement(problem, objective_type="cost")
    if not base_result.is_feasible:
        raise ValueError("Base MILP is infeasible.")

    all_vendors = set(problem.prepared_quotation["vendor_id"].unique())
    used_vendors = set(base_result.allocation["vendor_id"].unique())
    unused_vendors = sorted(all_vendors - used_vendors)

    rows = []
    for v_id in unused_vendors:
        forced_result = _solve_with_forced_vendor(problem, v_id)
        if not forced_result.is_feasible:
            rows.append(
                {
                    "vendor_id": v_id,
                    "cost_if_forced_in": None,
                    "opportunity_cost": None,
                    "interpretation": "Infeasible to use this vendor at all under current MOQ/capacity/BOM constraints",
                }
            )
            continue
        delta = forced_result.total_cost - base_result.total_cost
        rows.append(
            {
                "vendor_id": v_id,
                "cost_if_forced_in": forced_result.total_cost,
                "opportunity_cost": delta,
                "interpretation": f"Using this vendor at current terms would cost ${delta:,.2f} more than the current optimum",
            }
        )

    return pd.DataFrame(rows).sort_values("opportunity_cost", na_position="last")


def _solve_with_forced_vendor(problem: ProcurementProblem, vendor_id: str) -> SolveResult:
    """
    Re-solve the full MILP with an added constraint forcing z[vendor_id] = 1.
    Reuses solve_procurement's model-building logic is avoided here for
    simplicity — instead we call the public solver twice: once normally,
    and the delta is computed by the caller. This helper just re-implements
    the single added constraint directly against a fresh OR-Tools model to
    keep solve_procurement's signature unchanged.
    """
    from ortools.linear_solver import pywraplp as _pywraplp

    q_df = problem.prepared_quotation
    bom_dict = dict(zip(problem.bom["product_id"], problem.bom["quantity"]))

    solver = _pywraplp.Solver.CreateSolver("SCIP")
    x, y, z = {}, {}, {}
    unique_vendors = q_df["vendor_id"].unique()

    for v in unique_vendors:
        z[v] = solver.IntVar(0, 1, f"z_{v}")

    for row in q_df.itertuples(index=False):
        p_id, v_id, moq, cap = row.product_id, row.vendor_id, row.MOQ, row.Capacity
        x[(p_id, v_id)] = solver.IntVar(0, int(cap), f"x_{p_id}_{v_id}")
        y[(p_id, v_id)] = solver.IntVar(0, 1, f"y_{p_id}_{v_id}")
        solver.Add(x[(p_id, v_id)] >= moq * y[(p_id, v_id)])
        solver.Add(x[(p_id, v_id)] <= cap * y[(p_id, v_id)])
        solver.Add(z[v_id] >= y[(p_id, v_id)])

    for v in unique_vendors:
        offered = q_df.loc[q_df["vendor_id"] == v, "product_id"].tolist()
        solver.Add(sum(y[(p_id, v)] for p_id in offered) >= z[v])

    for p_id in q_df["product_id"].unique():
        if p_id not in bom_dict:
            continue
        min_q = float(bom_dict[p_id])
        max_q = min_q * (1 + problem.bom_tolerance)
        vendors_for_p = q_df.loc[q_df["product_id"] == p_id, "vendor_id"].tolist()
        total_qty = sum(x[(p_id, v)] for v in vendors_for_p)
        solver.Add(total_qty >= min_q)
        solver.Add(total_qty <= max_q)

    # The one line that differs from the normal solve: force this vendor active
    solver.Add(z[vendor_id] == 1)

    objective = solver.Objective()
    for row in q_df.itertuples(index=False):
        objective.SetCoefficient(x[(row.product_id, row.vendor_id)], float(row.unit_price))
    po_cost_dict = q_df.drop_duplicates("vendor_id").set_index("vendor_id")["po_cost"].to_dict()
    for v in unique_vendors:
        objective.SetCoefficient(z[v], float(po_cost_dict[v]))
    objective.SetMinimization()

    status_code = solver.Solve()
    status = {
        _pywraplp.Solver.OPTIMAL: "OPTIMAL",
        _pywraplp.Solver.FEASIBLE: "FEASIBLE",
        _pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
    }.get(status_code, "UNKNOWN")

    if status not in ("OPTIMAL", "FEASIBLE"):
        return SolveResult(status, pd.DataFrame(), 0.0, 0.0, 0.0, 0.0, 0, len(unique_vendors))

    records = []
    total_purchase_cost = 0.0
    selected_vendors = set()
    for (p_id, v_id), var in x.items():
        qty = var.solution_value()
        if qty <= 0:
            continue
        price = q_df[(q_df["product_id"] == p_id) & (q_df["vendor_id"] == v_id)]["unit_price"].iloc[0]
        total_purchase_cost += qty * price
        selected_vendors.add(v_id)
        records.append({"product_id": p_id, "vendor_id": v_id, "allocated_quantity": qty})

    total_po_cost = sum(po_cost_dict[v] for v in selected_vendors)
    return SolveResult(
        status=status,
        allocation=pd.DataFrame(records),
        total_purchase_cost=total_purchase_cost,
        total_po_cost=total_po_cost,
        total_cost=total_purchase_cost + total_po_cost,
        total_risk=0.0,
        n_vendors_used=len(selected_vendors),
        n_vendors_available=len(unique_vendors),
    )


def compute_shadow_prices(problem: ProcurementProblem) -> ShadowPriceReport:
    """
    Run fix-and-relax on the cost-optimal MILP solution and return shadow
    prices for the three constraint families that matter most to a
    procurement decision-maker: BOM minimum coverage, vendor capacity, and
    BOM tolerance (the ceiling on how much can be over-ordered).
    """
    # Step 1: solve the full MILP to get the optimal y*, z*
    milp_result = solve_procurement(problem, objective_type="cost")
    if not milp_result.is_feasible:
        raise ValueError("Base MILP is infeasible — cannot compute shadow prices.")

    q_df = problem.prepared_quotation
    bom_dict = dict(zip(problem.bom["product_id"], problem.bom["quantity"]))

    # Which (product, vendor) pairs were "activated" (y*=1) in the optimal solution
    activated_pairs = set(
        zip(milp_result.allocation["product_id"], milp_result.allocation["vendor_id"])
    )

    # Step 2 & 3: rebuild the model as a pure LP, with y fixed at y* by
    # only creating an x variable (continuous now) for activated pairs,
    # and dropping the y/z binaries and their linking constraints entirely
    # — their effect is already baked into which x variables exist.
    solver = pywraplp.Solver.CreateSolver("GLOP")  # LP solver that exposes duals
    if solver is None:
        raise RuntimeError("Could not create OR-Tools GLOP solver.")

    x = {}
    bom_min_constraints = {}
    bom_max_constraints = {}
    moq_constraints = {}
    capacity_constraints = {}

    objective = solver.Objective()

    for row in q_df.itertuples(index=False):
        p_id, v_id = row.product_id, row.vendor_id
        if (p_id, v_id) not in activated_pairs:
            continue  # y* = 0 for this pair — fixed out of the model
        moq, cap = row.MOQ, row.Capacity
        # Leave the variable itself unbounded below/above so MOQ and
        # capacity are each enforced as their own row constraint — that's
        # what lets GLOP attach a distinct, correctly-signed dual to each
        # one instead of folding both into the variable's own bounds.
        var = solver.NumVar(0.0, solver.infinity(), f"x_{p_id}_{v_id}")
        x[(p_id, v_id)] = var
        objective.SetCoefficient(var, float(row.unit_price))

        moq_c = solver.Constraint(float(moq), solver.infinity(), f"moq_{p_id}_{v_id}")
        moq_c.SetCoefficient(var, 1.0)
        moq_constraints[(p_id, v_id)] = moq_c

        cap_c = solver.Constraint(-solver.infinity(), float(cap), f"cap_{p_id}_{v_id}")
        cap_c.SetCoefficient(var, 1.0)
        capacity_constraints[(p_id, v_id)] = cap_c

    for p_id, min_qty in bom_dict.items():
        vendors_for_p = [v for (p, v) in activated_pairs if p == p_id]
        if not vendors_for_p:
            continue
        max_qty = min_qty * (1 + problem.bom_tolerance)

        min_c = solver.Constraint(float(min_qty), solver.infinity(), f"bom_min_{p_id}")
        max_c = solver.Constraint(-solver.infinity(), float(max_qty), f"bom_max_{p_id}")
        for v_id in vendors_for_p:
            min_c.SetCoefficient(x[(p_id, v_id)], 1.0)
            max_c.SetCoefficient(x[(p_id, v_id)], 1.0)
        bom_min_constraints[p_id] = min_c
        bom_max_constraints[p_id] = max_c

    objective.SetMinimization()
    status = solver.Solve()

    if status != pywraplp.Solver.OPTIMAL:
        raise RuntimeError(
            f"Fix-and-relax LP did not solve to optimality (status={status}). "
            "This can happen if the MOQ lower bounds make the fixed-y LP "
            "infeasible in isolation — see docs/methodology.md."
        )

    # Step 4: read off dual values
    bom_coverage_rows = []
    for p_id, constraint in bom_min_constraints.items():
        bom_coverage_rows.append(
            {
                "product_id": p_id,
                "bom_min_qty": bom_dict[p_id],
                "shadow_price": constraint.dual_value(),
                "interpretation": (
                    "$ saved per unit the BOM requirement could be reduced"
                    if constraint.dual_value() > 0
                    else "constraint not binding"
                ),
            }
        )

    bom_tolerance_rows = []
    for p_id, constraint in bom_max_constraints.items():
        dual = constraint.dual_value()
        bom_tolerance_rows.append(
            {
                "product_id": p_id,
                "bom_max_qty": bom_dict[p_id] * (1 + problem.bom_tolerance),
                "shadow_price": dual,
                "interpretation": (
                    "$ saved per unit the tolerance ceiling could be raised"
                    if dual < 0
                    else "constraint not binding"
                ),
            }
        )

    capacity_rows = []
    for (p_id, v_id), constraint in capacity_constraints.items():
        dual = constraint.dual_value()
        if abs(dual) < 1e-9:
            continue  # only report binding (non-zero dual) capacity constraints
        capacity_rows.append(
            {
                "product_id": p_id,
                "vendor_id": v_id,
                "capacity": q_df[(q_df["product_id"] == p_id) & (q_df["vendor_id"] == v_id)]["Capacity"].iloc[0],
                "shadow_price": abs(dual),
                "interpretation": "$ saved per extra unit of this vendor's capacity",
            }
        )

    return ShadowPriceReport(
        bom_coverage=pd.DataFrame(bom_coverage_rows).sort_values("shadow_price", ascending=False),
        capacity=pd.DataFrame(capacity_rows).sort_values("shadow_price", ascending=False) if capacity_rows else pd.DataFrame(columns=["product_id", "vendor_id", "capacity", "shadow_price", "interpretation"]),
        bom_tolerance=pd.DataFrame(bom_tolerance_rows).sort_values("shadow_price"),
        base_total_cost=milp_result.total_cost,
    )
