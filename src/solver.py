"""
Supplier selection & dynamic volume allocation solver.

Formulates and solves a Mixed-Integer Linear Program (MILP) that decides,
for every product in the BOM, how much quantity to purchase from which
vendor(s) — subject to MOQ, capacity, and BOM tolerance constraints — while
minimizing either total cash cost or a composite price/lead-time risk score.

Decision variables
-------------------
x[p, v] : integer, quantity of product p purchased from vendor v
y[p, v] : binary,  1 if any quantity of p is purchased from v
z[v]    : binary,  1 if vendor v is "activated" (used for at least one product)

Constraints
-----------
1. MOQ / capacity linking:      MOQ * y[p,v] <= x[p,v] <= Capacity * y[p,v]
2. BOM coverage:                 bom_min <= sum_v x[p,v] <= bom_min * (1 + tolerance)
3. Vendor activation linking:    z[v] >= y[p,v]   and   sum_p y[p,v] >= z[v]
4. (optional) relationship:      z[v] == 1  for every vendor  (force full vendor base)

Objective
---------
Minimize sum(weight[p,v] * x[p,v]) + sum(po_cost[v] * z[v])

where weight is either unit_price (cost objective) or a normalized
risk_coeff blending price and lead time (risk objective), and po_cost is a
fixed per-purchase-order overhead that only applies once a vendor is
activated (captures the real administrative cost of onboarding/using a
vendor — local vs. overseas).

This single function replaces the four near-duplicate solver functions
found in the original exploratory notebook.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd
from ortools.linear_solver import pywraplp

ObjectiveType = Literal["cost", "risk"]


@dataclass
class SolveResult:
    status: str
    allocation: pd.DataFrame
    total_purchase_cost: float
    total_po_cost: float
    total_cost: float
    total_risk: float
    n_vendors_used: int
    n_vendors_available: int

    @property
    def is_feasible(self) -> bool:
        return self.status in ("OPTIMAL", "FEASIBLE")

    def __iter__(self):
        """Support backward-compatible tuple unpacking: allocation, total_cost = result."""
        return iter((self.allocation, self.total_cost))


@dataclass
class ProcurementProblem:
    """
    Pre-processed inputs shared across all solves. Building this once and
    reusing it avoids recomputing normalized risk scores on every call.
    """

    quotation: pd.DataFrame
    bom: pd.DataFrame
    bom_tolerance: float = 0.08
    price_weight: float = 0.4
    lead_time_weight: float = 0.6
    po_cost_local: float = 50.0
    po_cost_oversea: float = 100.0

    _prepared: pd.DataFrame = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if abs((self.price_weight + self.lead_time_weight) - 1.0) > 1e-9:
            raise ValueError("price_weight + lead_time_weight must sum to 1.0")
        self._prepared = self._prepare()

    def _prepare(self) -> pd.DataFrame:
        df = self.quotation.copy()

        if "po_cost" not in df.columns:
            if "oversea_vendor" in df.columns:
                df["po_cost"] = df["oversea_vendor"].map(
                    lambda flag: self.po_cost_oversea if flag == 1 else self.po_cost_local
                )
            else:
                df["po_cost"] = self.po_cost_local

        # Normalize price within each product (cross-vendor comparison)
        p_min = df.groupby("product_id")["unit_price"].transform("min")
        p_max = df.groupby("product_id")["unit_price"].transform("max")
        df["p_norm"] = (df["unit_price"] - p_min) / (p_max - p_min).replace(0, 1)

        # Normalize lead time across the whole vendor pool
        if "lead_time" in df.columns:
            lt_min, lt_max = df["lead_time"].min(), df["lead_time"].max()
            df["lt_norm"] = (df["lead_time"] - lt_min) / max(lt_max - lt_min, 1e-9)
        else:
            df["lt_norm"] = 0.0

        df["risk_coeff"] = self.price_weight * df["p_norm"] + self.lead_time_weight * df["lt_norm"]
        return df

    @property
    def prepared_quotation(self) -> pd.DataFrame:
        return self._prepared

    @classmethod
    def from_raw_sheets(
        cls,
        vendor_df: pd.DataFrame,
        product_df: pd.DataFrame,
        bom_df: pd.DataFrame,
        quotation_df: pd.DataFrame,
        **kwargs,
    ) -> "ProcurementProblem":
        """Build a ProcurementProblem from the four raw Excel sheets."""
        vendor_lt = dict(zip(vendor_df["vendor_id"], vendor_df["Lead time"]))
        vendor_oversea = dict(zip(vendor_df["vendor_id"], vendor_df.get("oversea_vendor", 0)))

        q = quotation_df.copy()
        q["lead_time"] = q["vendor_id"].map(vendor_lt)
        q["oversea_vendor"] = q["vendor_id"].map(vendor_oversea)

        return cls(quotation=q, bom=bom_df, **kwargs)


def solve_procurement(
    problem: ProcurementProblem,
    objective_type: ObjectiveType = "cost",
    require_all_vendors: bool = False,
    solver_name: str = "SCIP",
) -> SolveResult:
    """
    Solve one procurement allocation scenario.

    Parameters
    ----------
    problem: pre-processed ProcurementProblem (quotation + BOM + weights)
    objective_type: "cost" to minimize cash spend, "risk" to minimize the
        composite price/lead-time risk score
    require_all_vendors: if True, forces every vendor in the quotation pool
        to receive at least one order (models a "keep every relationship
        alive" sourcing policy)
    solver_name: OR-Tools backend, defaults to SCIP (handles MILP)
    """
    q_df = problem.prepared_quotation
    bom_dict = dict(zip(problem.bom["product_id"], problem.bom["quantity"]))

    solver = pywraplp.Solver.CreateSolver(solver_name)
    if solver is None:
        raise RuntimeError(f"Could not create OR-Tools solver backend '{solver_name}'")

    x: dict[tuple, pywraplp.Variable] = {}
    y: dict[tuple, pywraplp.Variable] = {}
    z: dict[str, pywraplp.Variable] = {}

    unique_vendors = q_df["vendor_id"].unique()
    for v_id in unique_vendors:
        z[v_id] = solver.IntVar(0, 1, f"z_{v_id}")

    # --- Decision variables + MOQ/capacity linking ---
    for row in q_df.itertuples(index=False):
        p_id, v_id, moq, cap = row.product_id, row.vendor_id, row.MOQ, row.Capacity
        x[(p_id, v_id)] = solver.IntVar(0, int(cap), f"x_{p_id}_{v_id}")
        y[(p_id, v_id)] = solver.IntVar(0, 1, f"y_{p_id}_{v_id}")
        solver.Add(x[(p_id, v_id)] >= moq * y[(p_id, v_id)])
        solver.Add(x[(p_id, v_id)] <= cap * y[(p_id, v_id)])
        solver.Add(z[v_id] >= y[(p_id, v_id)])

    # --- Vendor activation linking (z[v] can only be 1 if v actually sells something) ---
    for v_id in unique_vendors:
        offered_products = q_df.loc[q_df["vendor_id"] == v_id, "product_id"].tolist()
        solver.Add(sum(y[(p_id, v_id)] for p_id in offered_products) >= z[v_id])

    # --- BOM coverage constraints ---
    for p_id in q_df["product_id"].unique():
        if p_id not in bom_dict:
            continue
        min_qty = float(bom_dict[p_id])
        max_qty = min_qty * (1 + problem.bom_tolerance)
        vendors_for_p = q_df.loc[q_df["product_id"] == p_id, "vendor_id"].tolist()
        total_qty_expr = sum(x[(p_id, v_id)] for v_id in vendors_for_p)
        solver.Add(total_qty_expr >= min_qty)
        solver.Add(total_qty_expr <= max_qty)

    # --- Optional "keep every vendor active" constraint ---
    if require_all_vendors:
        for v_id in unique_vendors:
            solver.Add(z[v_id] == 1)

    # --- Objective ---
    objective = solver.Objective()
    weight_col = "unit_price" if objective_type == "cost" else "risk_coeff"
    for row in q_df.itertuples(index=False):
        weight = float(getattr(row, weight_col))
        objective.SetCoefficient(x[(row.product_id, row.vendor_id)], weight)

    po_cost_dict = q_df.drop_duplicates("vendor_id").set_index("vendor_id")["po_cost"].to_dict()
    po_scale = 1.0 if objective_type == "cost" else 1e-4  # keep PO cost from dominating the risk objective
    for v_id in unique_vendors:
        objective.SetCoefficient(z[v_id], float(po_cost_dict[v_id]) * po_scale)

    objective.SetMinimization()
    status_code = solver.Solve()
    status = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FEASIBLE",
        pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
    }.get(status_code, "UNKNOWN")

    if status not in ("OPTIMAL", "FEASIBLE"):
        return SolveResult(
            status=status,
            allocation=pd.DataFrame(),
            total_purchase_cost=0.0,
            total_po_cost=0.0,
            total_cost=0.0,
            total_risk=0.0,
            n_vendors_used=0,
            n_vendors_available=len(unique_vendors),
        )

    records = []
    total_purchase_cost = 0.0
    total_risk = 0.0
    selected_vendors: set[str] = set()

    for (p_id, v_id), var in x.items():
        qty = var.solution_value()
        if qty <= 0:
            continue
        row_data = q_df[(q_df["product_id"] == p_id) & (q_df["vendor_id"] == v_id)].iloc[0]
        cost = qty * row_data["unit_price"]
        risk = qty * row_data["risk_coeff"]
        total_purchase_cost += cost
        total_risk += risk
        selected_vendors.add(v_id)
        records.append(
            {
                "product_id": p_id,
                "vendor_id": v_id,
                "allocated_quantity": qty,
                "unit_price": row_data["unit_price"],
                "lead_time": row_data.get("lead_time"),
                "total_cost": cost,
                "risk_contribution": risk,
            }
        )

    total_po_cost = sum(po_cost_dict[v] for v in selected_vendors)

    return SolveResult(
        status=status,
        allocation=pd.DataFrame(records),
        total_purchase_cost=total_purchase_cost,
        total_po_cost=total_po_cost,
        total_cost=total_purchase_cost + total_po_cost,
        total_risk=total_risk,
        n_vendors_used=len(selected_vendors),
        n_vendors_available=len(unique_vendors),
    )


def solve_manual_baseline(problem: ProcurementProblem) -> SolveResult:
    """
    Simulate a naive human "buy from the cheapest vendor first" heuristic,
    used as the baseline the MILP result is benchmarked against.
    Computes true total cost including PO overhead, risk score, and active vendor counts.
    """
    q_df = problem.prepared_quotation.sort_values(by=["product_id", "unit_price"])
    bom_df = problem.bom

    allocation = []
    total_purchase_cost = 0.0
    total_risk = 0.0
    selected_vendors: set[str] = set()

    risk_dict = dict(zip(zip(q_df["product_id"], q_df["vendor_id"]), q_df["risk_coeff"]))
    po_cost_dict = q_df.groupby("vendor_id")["po_cost"].first().to_dict()
    unique_vendors = set(q_df["vendor_id"].unique())

    for row in bom_df.itertuples(index=False):
        p_id = row.product_id
        target_min = float(row.quantity)
        target_max = target_min * (1 + problem.bom_tolerance)

        vendors = q_df[q_df["product_id"] == p_id]
        allocated_for_p = 0.0

        for v_row in vendors.itertuples(index=False):
            if allocated_for_p >= target_min:
                break

            need_to_buy = target_min - allocated_for_p
            if need_to_buy <= v_row.Capacity:
                actual_buy = v_row.MOQ if need_to_buy < v_row.MOQ else need_to_buy
            else:
                actual_buy = v_row.Capacity

            if (allocated_for_p + actual_buy) <= target_max:
                cost = actual_buy * v_row.unit_price
                risk = actual_buy * risk_dict.get((p_id, v_row.vendor_id), 0.0)
                allocation.append(
                    {
                        "product_id": p_id,
                        "vendor_id": v_row.vendor_id,
                        "allocated_quantity": actual_buy,
                        "unit_price": v_row.unit_price,
                        "lead_time": getattr(v_row, "lead_time", None),
                        "total_cost": cost,
                        "risk_contribution": risk,
                    }
                )
                allocated_for_p += actual_buy
                total_purchase_cost += cost
                total_risk += risk
                selected_vendors.add(v_row.vendor_id)

    total_po_cost = sum(po_cost_dict.get(v, 0.0) for v in selected_vendors)

    return SolveResult(
        status="FEASIBLE",
        allocation=pd.DataFrame(allocation),
        total_purchase_cost=total_purchase_cost,
        total_po_cost=total_po_cost,
        total_cost=total_purchase_cost + total_po_cost,
        total_risk=total_risk,
        n_vendors_used=len(selected_vendors),
        n_vendors_available=len(unique_vendors),
    )
