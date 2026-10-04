# Supplier Selection & Dynamic Volume Allocation

A Mixed-Integer Linear Programming (MILP) system that decides how much to
purchase from which vendor — under MOQ, capacity, and BOM
tolerance constraints — while minimizing cost or a blended price/lead-time
risk score. Built with [OR-Tools](https://developers.google.com/optimization)
(SCIP backend).

![MILP optimum vs 100 random feasible plans](assets/monte_carlo_optimality.png)

*Every point above the dashed line is a valid, constraint-satisfying
purchase plan — none of them beat the optimizer. That gap is the cost of
sourcing decisions made without optimization.*

## Executive summary

Four analyses, four different business questions, run on the competitive multi-sourcing 66-product / 23-vendor / 323-quotation dataset in this repo:

| Analysis | Business question it answers | Headline number |
|---|---|---|
| [Cost vs Heuristic Baseline](#results) | How much does mathematical optimization save over manual Excel buying? | **+$49,741 (+8.91%)** cash savings |
| [Risk-balanced sourcing](#results) | How much lead-time risk reduction can we achieve? | **-27.7% delivery risk** score |
| [Relationship-preserving sourcing](#results) | What does keeping every vendor active cost? | Keeps all 23 vendors active and engaged |
| [Shadow price analysis](#shadow-price-analysis-real-dataset) | Which constraint is most valuable to renegotiate? | Up to **$772.50/unit** capacity expansion savings |

Each row is a different lever a procurement team can actually pull —
policy trade-off, negotiation priority, or supply-chain contingency —
not just a different way of looking at the same number. Details and
methodology for each below.

## Why this exists

Multi-vendor sourcing is a combinatorial problem: with dozens of products
and multiple vendors per product, the number of valid ways to split an
order explodes, and each vendor has its own price, MOQ, and capacity
constraints layered on top. Buyers typically solve this by hand — sort by
price, buy from the cheapest vendor first, adjust when MOQ or capacity gets
in the way. That heuristic is *fast*, but leaves money on the table and
carries hidden lead-time risk that a spreadsheet won't surface.

This project reformulates the problem as a MILP and solves it exactly,
then benchmarks the result against both a manual baseline and 100
random-but-feasible alternatives to make the value of optimization
concrete and visual.

## What it does

The solver runs three sourcing strategies over the same dataset:

| Strategy | Optimizes for | Vendor policy |
|---|---|---|
| **Cost-optimal** | Lowest total cash cost | Only vendors that help minimize cost are used |
| **Risk-balanced** | Composite score: 40% price + 60% lead time | Only vendors that help minimize risk are used |
| **Relationship-preserving** | Risk, with every vendor guaranteed at least one order | Every vendor in the pool stays active |

Full mathematical formulation: [`docs/methodology.md`](docs/methodology.md).

## Results

Ran against the 66-product / 23-vendor / 323-quotation procurement dataset (`data/procurement_data.xlsx`):

| Model | Total cost | Risk score | Vendors used |
|---|---|---|---|
| Cost-optimal | $508,369 | 10,252.8 | 23 / 23 |
| Risk-balanced | $564,802 | 7,409.6 | 19 / 23 |
| Relationship-preserving | $565,729 | 7,411.8 | 23 / 23 |
| Manual Baseline (Greedy) | $558,110 | 1,514.8 | 20 / 23 |

Against the manual (greedy, cheapest-first) baseline, the MILP solution saves **+$49,741.38 (+8.91%)** in hard cash. 
Under competitive multi-sourcing, mathematical optimization decisively outmaneuvers spreadsheet heuristics by navigating complex MOQ hurdles and multi-vendor capacity linking.

## Dataset

`data/procurement_data.xlsx` — 66 products, 23 vendors, 323 vendor-product quotations. This provides realistic multi-sourcing depth (averaging 4–6 quotes per product item).

## Shadow price analysis (nearly-real dataset)

Ran on `data/procurement_data.xlsx` — a nearly-real 23-vendor / 66-product
procurement dataset. Shadow prices were computed via **fix-and-relax**
(see [`docs/methodology.md`](docs/methodology.md#extending-this-shadow-price-analysis-and-the-pareto-frontier))
and independently validated by re-solving the full MILP after perturbing
each binding constraint by one unit — the reported shadow price matched
the actual cost change exactly in every case checked.

![Shadow price analysis](assets/shadow_price_analysis.png)

The highest-value finding: product `VN-MT041` is capacity-constrained at
vendor `VN-VD02` — every extra unit of capacity that vendor could supply
is worth **$740** in cost avoidance, by far the single most valuable
constraint to renegotiate in this dataset. Full per-product and
per-vendor tables: `assets/shadow_price_*.csv`. Reproduce with:

```bash
python -m src.run_shadow_price_analysis
```

**What about vendors that weren't selected at all?** Fix-and-relax duals
only cover constraints tied to vendors already in the optimal solution —
an excluded vendor's variable is dropped from the relaxed LP entirely, so
there's no dual to read. Answering "how close was this vendor to being
worth using?" instead requires re-optimization: `compute_unused_vendor_opportunity()`
forces each excluded vendor's `z[v] = 1` and re-solves the full MILP. On
this dataset, exactly one vendor (`VN-VD15`) was excluded — forcing it in
costs only **$70** more than the optimum, meaning a small price
concession or better terms could flip it into the optimal plan. See
`docs/methodology.md` for why this needs a different technique than the
dual-value approach above.



```
procurement-optimization/
├── src/
│   ├── solver.py                    # Core MILP formulation (OR-Tools / SCIP)
│   ├── duality.py                   # Shadow price analysis (fix-and-relax)
│   ├── simulation.py                # Monte Carlo feasible-solution sweep
│   ├── run_analysis.py              # End-to-end pipeline: solve, compare, plot
│   └── run_shadow_price_analysis.py # Shadow price report generator
├── notebooks/
│   └── exploration.ipynb            # Interactive walkthrough of the solver
├── tests/
│   ├── test_solver.py               # Unit tests for constraints & objectives
│   └── test_duality.py              # Shadow price tests, validated by re-solve
├── data/
│   └── procurement_data.xlsx        # 23-vendor / 66-product dataset
├── assets/                          # Generated charts (committed for README)
├── docs/
│   └── methodology.md               # Full MILP formulation & design notes
└── requirements.txt
```

## Getting started

### 1. Interactive Web Demo (Streamlit)

Run the full interactive dashboard locally:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Or deploy to **Streamlit Community Cloud** with 1 click:
1. Connect your GitHub repository at [share.streamlit.io](https://share.streamlit.io).
2. Select repository `ngthanhminh2069/procurement-optimization-pr1`, branch `main`, and main file `app.py`.
3. Click **Deploy**!

### 2. Command-Line Scripts & Analysis

```bash
# Run all three models + manual baseline + Monte Carlo sweep
python -m src.run_analysis

# Run shadow price analysis
python -m src.run_shadow_price_analysis

# Run tests
pytest tests/ -v
```

### Using your own data

To run this against a different dataset, replace `data/procurement_data.xlsx`
or point `DATA_PATH` in `src/run_analysis.py` at a different file. Bring an
Excel workbook with these four sheets:

| Sheet | Required columns |
|---|---|
| `vendor_list` | `vendor_id`, `Lead time`, `oversea_vendor` (0/1) |
| `product_list` | `product_id` |
| `BOM` | `product_id`, `quantity` |
| `quotation` | `product_id`, `vendor_id`, `unit_price`, `MOQ`, `Capacity` |

### Using the solver directly

```python
from src.solver import ProcurementProblem, solve_procurement
import pandas as pd

xls = pd.ExcelFile("data/procurement_data.xlsx")
problem = ProcurementProblem.from_raw_sheets(
    vendor_df=pd.read_excel(xls, "vendor_list"),
    product_df=pd.read_excel(xls, "product_list"),
    bom_df=pd.read_excel(xls, "BOM"),
    quotation_df=pd.read_excel(xls, "quotation"),
    bom_tolerance=0.08,      # allow ordering up to 8% over BOM minimum
    price_weight=0.4,        # risk score weighting
    lead_time_weight=0.6,
)

result = solve_procurement(problem, objective_type="risk", require_all_vendors=False)
print(result.total_cost, result.total_risk, result.n_vendors_used)
print(result.allocation.head())
```

## Design notes

- **One solver function, not four.** The original exploratory notebook
  this project grew out of had four near-identical solver functions, one
  per experiment. `src/solver.py` consolidates all of them into a single
  `solve_procurement()` parameterized by `objective_type` and
  `require_all_vendors`, so every strategy shares one tested code path.
- **Why SCIP.** OR-Tools' SCIP backend handles the mixed integer + linear
  combination this problem needs (integer quantities, binary
  activation/order flags, linear objective) and is free for commercial use.

## Known limitations & future work

The risk objective is a simple weighted proxy (40% price / 60% lead time),
not a statistical model — it's a policy input a category manager should
tune, not a fitted parameter. Full discussion of this and other modeling
assumptions: [`docs/methodology.md`](docs/methodology.md#assumptions-and-limitations-of-the-risk-model).

**Shadow price analysis is implemented** (`src/duality.py`,
`python -m src.run_shadow_price_analysis`) — see the section above.

Still open:

- **Pareto frontier (epsilon-constraint method)** — sweep a cost budget
  and re-solve for minimum risk at each budget level, instead of a single
  fixed weighted-sum point, to trace the full cost-vs-risk trade-off curve.
  See `docs/methodology.md` for the formulation.

## Tech stack

`Python` · `OR-Tools (SCIP)` · `pandas` · `matplotlib` / `seaborn` · `pytest`

## License

MIT — see [LICENSE](LICENSE).
