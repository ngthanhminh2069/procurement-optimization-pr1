"""
Unit tests and Quality Control (QC) for the Dynamic Strategic Insights Engine and AI Security.
"""

import pandas as pd
import pytest

from src.ai_advisor import _get_api_key, generate_executive_briefing
from src.insights import (
    analyze_capacity_bottlenecks,
    analyze_excluded_vendors,
    analyze_strategy_tradeoffs,
    validate_procurement_dataset,
)
from src.solver import SolveResult


def test_validate_procurement_dataset_valid():
    """Verify validation passes on well-formed procurement tables."""
    vendor_df = pd.DataFrame({"vendor_id": ["V1", "V2"], "Lead time": [5, 10]})
    product_df = pd.DataFrame({"product_id": ["P1"]})
    bom_df = pd.DataFrame({"product_id": ["P1"], "quantity": [100]})
    quotation_df = pd.DataFrame({
        "product_id": ["P1", "P1"],
        "vendor_id": ["V1", "V2"],
        "unit_price": [10.0, 12.0],
        "MOQ": [10, 10],
        "Capacity": [80, 80],
    })

    is_valid, errors, warnings = validate_procurement_dataset(
        vendor_df, product_df, bom_df, quotation_df, bom_tolerance=0.08
    )
    assert is_valid is True
    assert len(errors) == 0


def test_validate_procurement_dataset_capacity_shortage():
    """Verify validation detects capacity shortage before calling solver."""
    vendor_df = pd.DataFrame({"vendor_id": ["V1"], "Lead time": [5]})
    product_df = pd.DataFrame({"product_id": ["P1"]})
    bom_df = pd.DataFrame({"product_id": ["P1"], "quantity": [500]})
    quotation_df = pd.DataFrame({
        "product_id": ["P1"],
        "vendor_id": ["V1"],
        "unit_price": [10.0],
        "MOQ": [10],
        "Capacity": [200],  # Shortage: 200 < 500
    })

    is_valid, errors, warnings = validate_procurement_dataset(
        vendor_df, product_df, bom_df, quotation_df, bom_tolerance=0.08
    )
    assert is_valid is False
    assert any("không đủ đáp ứng" in err or "less than BOM" in err for err in errors)


def test_analyze_strategy_tradeoffs_normal():
    """Verify dynamic trade-off logic when models produce different costs/risks."""
    res_cost = SolveResult(
        status="OPTIMAL",
        allocation=pd.DataFrame(),
        total_purchase_cost=10000.0,
        total_po_cost=100.0,
        total_cost=10100.0,
        total_risk=500.0,
        n_vendors_used=3,
        n_vendors_available=5,
    )
    res_risk = SolveResult(
        status="OPTIMAL",
        allocation=pd.DataFrame(),
        total_purchase_cost=10150.0,
        total_po_cost=100.0,
        total_cost=10250.0,
        total_risk=450.0,
        n_vendors_used=3,
        n_vendors_available=5,
    )
    res_rel = SolveResult(
        status="OPTIMAL",
        allocation=pd.DataFrame(),
        total_purchase_cost=10300.0,
        total_po_cost=200.0,
        total_cost=10500.0,
        total_risk=460.0,
        n_vendors_used=5,
        n_vendors_available=5,
    )

    insight = analyze_strategy_tradeoffs(res_cost, res_risk, res_rel, manual_cost=10400.0, lang="vi")
    assert insight["status"] == "optimal"
    assert insight["cost_diff_pct"] > 0
    assert insight["risk_diff_pct"] > 0
    assert insight["savings_dollars"] == 300.0


def test_analyze_capacity_bottlenecks():
    """Verify top bottleneck identification and potential savings calculations."""
    cap_df = pd.DataFrame([
        {"product_id": "P1", "vendor_id": "V1", "capacity": 1000.0, "shadow_price": 50.0},
        {"product_id": "P2", "vendor_id": "V2", "capacity": 500.0, "shadow_price": 10.0},
    ])
    result = analyze_capacity_bottlenecks(cap_df, lang="vi")
    assert result["has_bottlenecks"] is True
    assert result["top_vendor"] == "V1"
    assert result["top_product"] == "P1"
    assert result["potential_savings_10pct"] == 100 * 50.0


def test_ai_security_offline_fallback():
    """
    QC Security Test: Ensure generate_executive_briefing gracefully returns
    an offline message and NEVER raises an unhandled exception or leaks keys
    when no API key is set.
    """
    grounding = {"total_cost": 50000.0, "savings_dollars": 500.0}
    success, msg = generate_executive_briefing(grounding, api_key=None, lang="vi")
    # Must securely fall back
    assert success is False
    assert "Ngoại tuyến" in msg or "Offline" in msg
