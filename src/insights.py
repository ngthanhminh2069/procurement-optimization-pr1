"""
Deterministic Mathematical & Rule-Based Strategic Insights Engine for Procurement Optimization.
Analyzes optimization outputs and classifies market dynamics into actionable business recommendations.
"""

from __future__ import annotations

from typing import Any
import pandas as pd


def validate_procurement_dataset(
    vendor_df: pd.DataFrame,
    product_df: pd.DataFrame,
    bom_df: pd.DataFrame,
    quotation_df: pd.DataFrame,
    bom_tolerance: float = 0.08,
    lang: str = "vi",
) -> tuple[bool, list[str], list[str]]:
    """
    Perform deep validation on raw procurement data before running optimization.
    Returns (is_valid, critical_errors, warnings).
    """
    critical_errors: list[str] = []
    warnings: list[str] = []

    # 1. Check required columns
    req_cols = {
        "vendor_list": {"vendor_id", "Lead time"},
        "product_list": {"product_id"},
        "BOM": {"product_id", "quantity"},
        "quotation": {"product_id", "vendor_id", "unit_price", "MOQ", "Capacity"},
    }

    for sheet, cols in req_cols.items():
        df_target = (
            vendor_df if sheet == "vendor_list"
            else product_df if sheet == "product_list"
            else bom_df if sheet == "BOM"
            else quotation_df
        )
        missing = cols - set(df_target.columns)
        if missing:
            critical_errors.append(
                f"Sheet '{sheet}' thiếu các cột bắt buộc: {missing}"
                if lang == "vi"
                else f"Sheet '{sheet}' is missing required columns: {missing}"
            )

    if critical_errors:
        return False, critical_errors, warnings

    # 2. Check for missing quotations for products in BOM
    bom_products = set(bom_df["product_id"].unique())
    quoted_products = set(quotation_df["product_id"].unique())
    unquoted = bom_products - quoted_products
    if unquoted:
        critical_errors.append(
            f"Các sản phẩm trong BOM chưa có bất kỳ báo giá nào: {sorted(list(unquoted))[:5]}..."
            if lang == "vi"
            else f"BOM products missing any quotations: {sorted(list(unquoted))[:5]}..."
        )

    # 3. Check for total vendor capacity vs BOM demand
    cap_by_prod = quotation_df.groupby("product_id")["Capacity"].sum().to_dict()
    for _, row in bom_df.iterrows():
        p_id = row["product_id"]
        qty = row["quantity"]
        total_cap = cap_by_prod.get(p_id, 0)
        if total_cap < qty:
            critical_errors.append(
                f"Sản phẩm '{p_id}': Tổng công suất toàn bộ NCC ({total_cap:,.0f} đv) không đủ đáp ứng nhu cầu BOM ({qty:,.0f} đv)."
                if lang == "vi"
                else f"Product '{p_id}': Total supplier capacity ({total_cap:,.0f}) is less than BOM requirement ({qty:,.0f})."
            )

    # 4. Check for MOQ constraints exceeding BOM ceiling
    moq_by_prod = quotation_df.groupby("product_id")["MOQ"].min().to_dict()
    for _, row in bom_df.iterrows():
        p_id = row["product_id"]
        bom_max = row["quantity"] * (1 + bom_tolerance)
        min_moq = moq_by_prod.get(p_id, 0)
        if min_moq > bom_max:
            warnings.append(
                f"Sản phẩm '{p_id}': MOQ nhỏ nhất của các NCC ({min_moq:,.0f}) lớn hơn trần BOM cho phép ({bom_max:,.0f}). Có thể gây bất khả thi nếu không nâng dung sai."
                if lang == "vi"
                else f"Product '{p_id}': Smallest supplier MOQ ({min_moq:,.0f}) exceeds BOM max ceiling ({bom_max:,.0f}). May cause infeasibility."
            )

    is_valid = len(critical_errors) == 0
    return is_valid, critical_errors, warnings


def analyze_strategy_tradeoffs(
    opt_res: Any,
    risk_res: Any,
    rel_res: Any,
    manual_cost: float,
    lang: str = "vi",
) -> dict[str, Any]:
    """
    Produce structured mathematical strategic commentary evaluating trade-offs
    between cost minimization, lead-time de-risking, and supplier relationship preservation.
    """
    if not opt_res.is_feasible:
        return {
            "status": "infeasible",
            "narrative": (
                "⚠️ Bài toán hiện không tìm được nghiệm khả thi (Infeasible). Hãy kiểm tra lại công suất hoặc dung sai BOM."
                if lang == "vi"
                else "⚠️ The optimization model is infeasible. Please review capacity or BOM tolerance."
            ),
        }

    cost_opt = opt_res.total_cost
    cost_risk = risk_res.total_cost
    risk_opt = opt_res.total_risk
    risk_risk = risk_res.total_risk

    cost_diff = cost_risk - cost_opt
    cost_diff_pct = (cost_diff / cost_opt) * 100 if cost_opt > 0 else 0.0
    risk_diff = risk_opt - risk_risk
    risk_diff_pct = (risk_diff / risk_opt) * 100 if risk_opt > 0 else 0.0

    savings = manual_cost - cost_opt
    savings_pct = (savings / manual_cost) * 100 if manual_cost > 0 else 0.0

    rel_diff = rel_res.total_cost - cost_opt if rel_res.is_feasible else 0.0

    # Determine market trade-off state
    if abs(cost_diff) < 1e-2 and abs(risk_diff) < 1e-2:
        tradeoff_state = "identical"
        tradeoff_text = (
            "Thị trường cung ứng hiện có tính ràng buộc cao: Phương án tối ưu chi phí và cân bằng rủi ro trùng khớp hoàn toàn. "
            "Điều này cho thấy phần lớn sản phẩm chỉ có 1 nhà cung cấp khả thi hoặc nhà cung cấp rẻ nhất đồng thời cũng có thời gian giao hàng tốt nhất."
            if lang == "vi"
            else "Highly constrained supplier pool: The Cost-optimal and Risk-balanced plans are identical. "
            "Most items have only 1 feasible supplier, or the lowest-cost supplier also boasts the shortest lead time."
        )
    elif cost_diff_pct <= 1.0 and risk_diff_pct >= 1.0:
        tradeoff_state = "highly_attractive"
        tradeoff_text = (
            f"Cơ hội đánh đổi cực kỳ hấp dẫn: Chỉ cần chi thêm **+{cost_diff_pct:.2f}%** chi phí (+${cost_diff:,.0f}), "
            f"doanh nghiệp cắt giảm được tới **{risk_diff_pct:.2f}%** rủi ro giao hàng trễ. Khuyến nghị áp dụng chiến lược Cân bằng rủi ro."
            if lang == "vi"
            else f"Highly attractive trade-off: Paying just **+{cost_diff_pct:.2f}%** more (+${cost_diff:,.0f}) "
            f"reduces delivery lead-time risk score by **{risk_diff_pct:.2f}%**. Recommended strategy."
        )
    else:
        tradeoff_state = "moderate"
        tradeoff_text = (
            f"Đánh đổi chi phí - an toàn: Chuyển sang mô hình an toàn tốn thêm **+{cost_diff_pct:.2f}%** (+${cost_diff:,.0f}) "
            f"để giảm **{risk_diff_pct:.2f}%** điểm rủi ro."
            if lang == "vi"
            else f"Cost-safety trade-off: Securing the supply chain requires **+{cost_diff_pct:.2f}%** (+${cost_diff:,.0f}) "
            f"to reduce risk score by **{risk_diff_pct:.2f}%**."
        )

    # Baseline comparison text
    if savings > 10.0:
        baseline_text = (
            f"Thuật toán MILP giúp tiết kiệm **${savings:,.2f}** ({savings_pct:.2f}%) so với phương pháp phân bổ thủ công theo giá rẻ nhất (Greedy). "
            f"Mô hình MILP đã tận dụng tối ưu kết hợp MOQ và công suất mà con người khó tính toán hết."
            if lang == "vi"
            else f"MILP optimizer saves **${savings:,.2f}** ({savings_pct:.2f}%) over greedy cheapest-first sourcing by optimally navigating MOQ and capacity trade-offs."
        )
    else:
        baseline_text = (
            "Phương pháp thủ công và MILP đạt kết quả xấp xỉ nhau do cấu trúc danh mục ít nhà cung cấp cạnh tranh trực tiếp."
            if lang == "vi"
            else "Greedy heuristic closely matches MILP optimum due to limited supplier alternatives per product."
        )

    relationship_text = (
        f"Chi phí để duy trì quan hệ với toàn bộ {rel_res.n_vendors_available} nhà cung cấp (mỗi NCC ít nhất 1 đơn) là **+${rel_diff:,.2f}**."
        if lang == "vi"
        else f"Cost to keep all {rel_res.n_vendors_available} vendors active is **+${rel_diff:,.2f}**."
    )

    return {
        "status": "optimal",
        "tradeoff_state": tradeoff_state,
        "tradeoff_text": tradeoff_text,
        "baseline_text": baseline_text,
        "relationship_text": relationship_text,
        "cost_diff_pct": cost_diff_pct,
        "risk_diff_pct": risk_diff_pct,
        "savings_dollars": savings,
        "savings_pct": savings_pct,
    }


def analyze_capacity_bottlenecks(capacity_df: pd.DataFrame, lang: str = "vi") -> dict[str, Any]:
    """Analyze dual shadow prices to provide prioritized procurement negotiation guidance."""
    if capacity_df.empty:
        return {
            "has_bottlenecks": False,
            "headline": (
                "Toàn bộ nhà cung cấp hiện có dư thừa năng lực sản xuất (không có ràng buộc công suất nào chạm trần). "
                "Khuyến nghị tập trung đàm phán giảm đơn giá và điều khoản thanh toán thay vì yêu cầu tăng công suất."
                if lang == "vi"
                else "All suppliers currently have surplus capacity. Focus contract negotiations on unit pricing and payment terms rather than volume expansion."
            ),
            "top_bottlenecks": [],
        }

    # Extract non-zero duals
    active_caps = capacity_df[capacity_df["shadow_price"] > 1e-4].sort_values("shadow_price", ascending=False)
    if active_caps.empty:
        return {
            "has_bottlenecks": False,
            "headline": "Không có điểm nghẽn công suất nào đang phát sinh chi phí cận biên.",
            "top_bottlenecks": [],
        }

    top_row = active_caps.iloc[0]
    sp_value = top_row["shadow_price"]
    cap_val = top_row["capacity"]
    v_id = top_row["vendor_id"]
    p_id = top_row["product_id"]

    # Calculate 10% capacity expansion potential savings
    expansion_units = max(1.0, round(cap_val * 0.10))
    potential_savings = expansion_units * sp_value

    headline = (
        f"🎯 **Điểm đàm phán ưu tiên số 1:** Sản phẩm `{p_id}` tại nhà cung cấp `{v_id}` "
        f"có Shadow Price là **${sp_value:,.2f}/đơn vị**. Nếu đàm phán tăng thêm 10% công suất (+{expansion_units:,.0f} đv), "
        f"doanh nghiệp sẽ tiết kiệm trực tiếp tới **${potential_savings:,.2f}**!"
        if lang == "vi"
        else f"🎯 **Top Negotiation Priority:** Product `{p_id}` with vendor `{v_id}` "
        f"carries a shadow price of **${sp_value:,.2f}/unit**. Expanding capacity by 10% (+{expansion_units:,.0f} units) "
        f"yields direct savings of **${potential_savings:,.2f}**!"
    )

    return {
        "has_bottlenecks": True,
        "headline": headline,
        "top_vendor": v_id,
        "top_product": p_id,
        "shadow_price": sp_value,
        "potential_savings_10pct": potential_savings,
        "expansion_units": expansion_units,
    }


def analyze_excluded_vendors(unused_df: pd.DataFrame, lang: str = "vi") -> dict[str, Any]:
    """Analyze opportunity cost of vendors left out of optimal plan."""
    if unused_df.empty or "opportunity_cost" not in unused_df.columns:
        return {
            "has_excluded": False,
            "headline": "Toàn bộ nhà cung cấp trong danh mục đã được sử dụng.",
        }

    valid_unused = unused_df.dropna(subset=["opportunity_cost"]).sort_values("opportunity_cost", ascending=True)
    if valid_unused.empty:
        return {
            "has_excluded": False,
            "headline": "Các nhà cung cấp bị loại hiện không thể kích hoạt do vi phạm kỹ thuật (MOQ/Công suất).",
        }

    best_vendor = valid_unused.iloc[0]
    opp_cost = best_vendor["opportunity_cost"]
    v_id = best_vendor["vendor_id"]

    headline = (
        f"💡 **Nhà cung cấp dự phòng tiềm năng nhất:** `{v_id}` chỉ cách phương án tối ưu **+${opp_cost:,.2f}**. "
        f"Chỉ cần nhà cung cấp này giảm giá hoặc đưa ra ưu đãi chi phí tương đương con số trên, "
        f"họ sẽ lập tức lọt vào kế hoạch mua hàng chính thức."
        if lang == "vi"
        else f"💡 **Best Backup Candidate:** Vendor `{v_id}` is only **+${opp_cost:,.2f}** away from entering the optimal plan. "
        f"A pricing concession of this magnitude will flip this supplier into the active supply base."
    )

    return {
        "has_excluded": True,
        "best_vendor": v_id,
        "opportunity_cost": opp_cost,
        "headline": headline,
    }
