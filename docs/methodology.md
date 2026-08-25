# Methodology

## Problem statement

A manufacturer must fulfil a Bill of Materials (BOM) for an upcoming
production cycle. For each product in the BOM, one or more vendors have
submitted quotations specifying:

- **Unit price**
- **MOQ** (minimum order quantity) — the smallest amount that vendor will
  accept per order
- **Capacity** — the largest amount that vendor can supply

The buyer must decide **how much to buy from which vendor**, for every
product, such that:

- Total purchased quantity per product falls within the BOM's tolerance
  band (production plans typically allow ordering slightly over the exact
  requirement — this dataset uses +8%, but it's configurable)
- No vendor is asked for less than its MOQ or more than its capacity
- A chosen objective (cost, risk, or a hybrid) is minimized

This is a classic **supplier selection & order allocation** problem,
formulated here as a **Mixed-Integer Linear Program (MILP)**.

## Decision variables

| Variable | Type | Meaning |
|---|---|---|
| `x[p, v]` | Integer | Quantity of product `p` purchased from vendor `v` |
| `y[p, v]` | Binary | 1 if any quantity of `p` is purchased from `v` |
| `z[v]` | Binary | 1 if vendor `v` is activated (receives at least one order across any product) |

## Constraints

**MOQ / capacity linking** — a vendor either supplies nothing, or supplies
between its MOQ and its capacity:

```
MOQ[p,v] * y[p,v]  <=  x[p,v]  <=  Capacity[p,v] * y[p,v]
```

**BOM coverage** — total purchased quantity for a product must sit within
the tolerance band above the BOM requirement:

```
BOM_min[p]  <=  sum_v x[p,v]  <=  BOM_min[p] * (1 + tolerance)
```

**Vendor activation linking** — `z[v]` is 1 exactly when vendor `v` supplies
at least one product:

```
z[v] >= y[p,v]                      for every product p vendor v offers
sum_p y[p,v] >= z[v]
```

**Relationship-preserving mode (optional)** — forces every vendor in the
quotation pool to receive at least one order, modelling a sourcing policy
that intentionally keeps every vendor relationship "warm":

```
z[v] == 1   for every vendor v
```

## Objective functions

Three sourcing strategies are exposed, all solved by the same
`solve_procurement()` function with different parameters:

| Strategy | `objective_type` | `require_all_vendors` | Optimizes for |
|---|---|---|---|
| Cost-optimal | `cost` | `False` | Lowest total cash outlay |
| Risk-balanced | `risk` | `False` | Composite price + lead-time risk |
| Relationship-preserving | `risk` | `True` | Risk, subject to keeping every vendor active |

### Cost objective

```
minimize  sum_{p,v} unit_price[p,v] * x[p,v]  +  sum_v po_cost[v] * z[v]
```

`po_cost[v]` is a fixed administrative overhead incurred once a vendor is
activated (e.g. $50 for a domestic vendor, $100 for an overseas one) —
this captures the real cost of managing a purchase order beyond the unit
price, and is what makes `z[v]` more than a bookkeeping variable.

### Risk objective

Each vendor quote is scored on a normalized 0–1 scale blending price
competitiveness and delivery lead time:

```
p_norm[p,v]  = (price[p,v] - min_price[p]) / (max_price[p] - min_price[p])
lt_norm[v]   = (lead_time[v] - min_lead_time) / (max_lead_time - min_lead_time)
risk_coeff[p,v] = price_weight * p_norm[p,v] + lead_time_weight * lt_norm[v]
```

Default weights are 40% price / 60% lead time — lead time is weighted
higher because a stockout is typically more disruptive than a marginally
higher unit price. Both weights are configurable and must sum to 1.0.

```
minimize  sum_{p,v} risk_coeff[p,v] * x[p,v]  +  0.0001 * sum_v po_cost[v] * z[v]
```

(The PO cost term is scaled down in the risk objective so it acts as a
tie-breaker rather than dominating the risk signal, which lives on a much
smaller numeric scale than raw dollar costs.)

### Assumptions and limitations of the risk model

The risk score used here is a deliberately simple **deterministic proxy**,
not a statistical risk model — it does not use historical variance,
probability distributions, or stochastic demand/lead-time modeling. This
is a design choice, made explicit rather than hidden:

- **`price_weight = 0.4`, `lead_time_weight = 0.6` is a policy input, not
  a fitted parameter.** It encodes a judgment call — "a stockout costs the
  business more than a marginally higher unit price" — that a category
  manager should own, not something the model derives from data. There is
  no historical dataset here relating lead-time variance to actual
  stockout cost, so no weight could be "proven correct" without one.
  Treat the default as a starting point to be tuned per category (a
  single-source, long-lead-time electronic component justifies a much
  higher lead-time weight than a commodity raw material with many
  substitutable vendors).
- **Lead time is treated as a point estimate, not a distribution.** Real
  lead times vary (a vendor quoting "30 days" might mean anywhere from 20
  to 45 in practice). This model has no notion of that variance — it
  would require historical delivery data per vendor and a proper
  stochastic or robust-optimization formulation (e.g. chance constraints
  on on-time delivery, or minimizing a CVaR of total landed cost) to
  capture honestly. That is future work, not something this dataset can
  support without real delivery-performance history.
  <!-- If real vendor delivery-performance history becomes available, the
  next step here should be to replace `lt_norm` with a stochastic
  lead-time model rather than tune the weight further — see the
  "Future work" note in the README. -->
- **Price and lead time are normalized independently**, but in practice
  they are often negatively correlated (cheaper overseas vendors tend to
  quote longer lead times). Because `risk_coeff` sums two independently
  normalized scores, it implicitly assumes the two risks are additive and
  uncorrelated. That's a simplification worth flagging to a reader, not a
  hidden assumption.
- **Mixing dollar cost and a 0–1 risk score in one objective is not
  dimensionally clean.** The `po_scale = 1e-4` factor in `solve_procurement()`
  exists purely to keep the PO-cost term (denominated in dollars) from
  swamping the risk term (denominated in a normalized 0–1 score) — it is
  a pragmatic tie-breaker, not a principled unit conversion. The
  methodologically correct fix is goal programming or the
  epsilon-constraint method (see below) rather than scaling one term by
  an arbitrary constant.

None of this makes the risk-balanced model wrong to use — sourcing teams
make exactly this kind of qualitative trade-off call every day. The point
is that a single scalar "risk score" should be presented to a
decision-maker as a tunable policy lever, not as an objective measurement.

## Extending this: shadow price analysis and the Pareto frontier

Two natural next steps turn this from "a solver that returns one plan"
into a decision-support tool a procurement team could actually lean on:

**Shadow price / dual analysis.** For each binding constraint (BOM
coverage, vendor capacity, BOM tolerance), the dual value answers "what
would it be worth to relax this by one unit?" — e.g. "how much would
total cost drop if Vendor X's capacity increased by 100 units?" OR-Tools
does not expose duals directly for a MILP, since duality is only
well-defined for LPs. The standard technique is **fix-and-relax**: solve
the MILP, fix the binary `y`/`z` variables at their optimal values, then
re-solve the remaining problem (now a pure LP in `x`) to read off valid
shadow prices at that solution.

**Pareto frontier via epsilon-constraint.** The weighted-sum risk
objective here returns exactly one point on the cost-vs-risk trade-off
curve. Weighted-sum can also mathematically miss efficient solutions that
lie on non-convex regions of that curve. The epsilon-constraint method
instead sweeps a cost budget `ε` and, for each value, solves:

```
minimize  total_risk(x)
subject to total_cost(x) <= ε
           [all original MOQ / capacity / BOM constraints]
```

Repeating this across a range of `ε` (from the cost-optimal cost up to
the unconstrained risk-optimal cost) traces the full Pareto frontier —
letting a sourcing team pick a point on the curve directly, instead of
trusting a single fixed weight.

### Blind spot: fix-and-relax says nothing about excluded vendors

Fix-and-relax (above) only ever builds a relaxed LP out of the
`(product, vendor)` pairs that were **activated** in the MILP solution
(`y* = 1`). A vendor that was not selected at all has its variable
dropped from that relaxed LP entirely — there is no dual value to read
for it, by construction.

It's tempting to patch this by adding the excluded vendor's variable back
into the relaxed LP, bounded at zero, and reading its reduced cost. That
doesn't work cleanly here: MOQ makes the true feasible set for that
variable non-convex ("buy nothing, or buy at least MOQ") — exactly the
reason a binary `y` was needed for it in the first place. A reduced cost
read off a naively re-added continuous variable would not correspond to
a real economic quantity.

The honest way to answer "how close was this excluded vendor to being
worth using?" is direct re-optimization: force `z[v] = 1` for that
vendor and re-solve the *full* MILP from scratch. The cost increase over
the true optimum is the vendor's real opportunity cost at its current
quoted terms — implemented in `compute_unused_vendor_opportunity()` in
`src/duality.py`. It's more expensive computationally (one full MILP
re-solve per excluded vendor) but doesn't rely on any approximation.

## Validating optimality: the Monte Carlo sweep

MILP solvers (OR-Tools with the SCIP backend, here) are provably optimal —
there's no mathematical need to "double check" the result. But a chart
often convinces stakeholders faster than a proof does.

`src/simulation.py` re-solves the *same* constraint set 100 times, each
time with a **random** linear objective instead of the real cost/risk
objective. Every one of those 100 solutions is a genuinely feasible
purchase plan (it satisfies every MOQ, capacity, and BOM constraint) —
just not an optimal one. Plotting their true dollar cost against the real
optimum makes the value of optimization visually obvious: see
`assets/monte_carlo_optimality.png`.

## Manual baseline

To quantify savings in terms a non-technical stakeholder cares about, the
project also simulates how a human buyer typically sources: sort vendors
by unit price and greedily buy from the cheapest one first until the BOM
minimum is met, falling back to the next cheapest vendor when a vendor's
MOQ or capacity gets in the way. See `solve_manual_baseline()` in
`src/solver.py`.
