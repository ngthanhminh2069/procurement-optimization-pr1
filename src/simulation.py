"""
Monte Carlo validation: generate many random *feasible* purchase plans and
compare their total cost against the MILP-optimal plan. This is not needed
to trust the solver (MILP solvers are provably optimal), but it produces a
compelling, intuitive visual for stakeholders who are skeptical that a
"black box" optimizer really beats manual sourcing decisions.
"""

from __future__ import annotations

import random

from ortools.linear_solver import pywraplp

from .solver import ProcurementProblem


def _solve_with_random_objective(problem: ProcurementProblem, rng: random.Random) -> float | None:
    q_df = problem.prepared_quotation
    bom_dict = dict(zip(problem.bom["product_id"], problem.bom["quantity"]))

    solver = pywraplp.Solver.CreateSolver("SCIP")
    x, y, z = {}, {}, {}
    unique_vendors = q_df["vendor_id"].unique()

    for v_id in unique_vendors:
        z[v_id] = solver.IntVar(0, 1, f"z_{v_id}")

    for row in q_df.itertuples(index=False):
        p_id, v_id, moq, cap = row.product_id, row.vendor_id, row.MOQ, row.Capacity
        x[(p_id, v_id)] = solver.IntVar(0, int(cap), f"x_{p_id}_{v_id}")
        y[(p_id, v_id)] = solver.IntVar(0, 1, f"y_{p_id}_{v_id}")
        solver.Add(x[(p_id, v_id)] >= moq * y[(p_id, v_id)])
        solver.Add(x[(p_id, v_id)] <= cap * y[(p_id, v_id)])
        solver.Add(z[v_id] >= y[(p_id, v_id)])

    for v_id in unique_vendors:
        offered = q_df.loc[q_df["vendor_id"] == v_id, "product_id"].tolist()
        solver.Add(sum(y[(p_id, v_id)] for p_id in offered) >= z[v_id])

    for p_id in q_df["product_id"].unique():
        if p_id not in bom_dict:
            continue
        min_q = float(bom_dict[p_id])
        max_q = min_q * (1 + problem.bom_tolerance)
        vendors = q_df.loc[q_df["product_id"] == p_id, "vendor_id"].tolist()
        total_qty = sum(x[(p_id, v_id)] for v_id in vendors)
        solver.Add(total_qty >= min_q)
        solver.Add(total_qty <= max_q)

    # Random objective -> any feasible corner of the polytope, not the optimum
    objective = solver.Objective()
    for row in q_df.itertuples(index=False):
        objective.SetCoefficient(x[(row.product_id, row.vendor_id)], rng.uniform(1.0, 100.0))
    objective.SetMinimization()

    status = solver.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return None

    po_cost_dict = q_df.drop_duplicates("vendor_id").set_index("vendor_id")["po_cost"].to_dict()
    total_purchase_cost = 0.0
    selected_vendors = set()
    for (p_id, v_id), var in x.items():
        qty = var.solution_value()
        if qty <= 0:
            continue
        price = q_df[(q_df["product_id"] == p_id) & (q_df["vendor_id"] == v_id)]["unit_price"].iloc[0]
        total_purchase_cost += qty * price
        selected_vendors.add(v_id)

    total_po_cost = sum(po_cost_dict[v] for v in selected_vendors)
    return total_purchase_cost + total_po_cost


def run_feasible_solution_sweep(
    problem: ProcurementProblem, n_simulations: int = 100, seed: int = 0
) -> list[float]:
    """
    Solve the same constraint set n_simulations times with a random linear
    objective each time, collecting the resulting total cost of each
    feasible (but not optimal) purchase plan. Returns costs sorted
    descending, ready to plot against the true optimum.
    """
    rng = random.Random(seed)
    costs = []
    for _ in range(n_simulations):
        cost = _solve_with_random_objective(problem, rng)
        if cost is not None:
            costs.append(cost)
    return sorted(costs, reverse=True)
