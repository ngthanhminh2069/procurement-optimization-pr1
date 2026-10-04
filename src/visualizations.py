"""
Interactive Plotly visualizations for the Procurement Optimization Streamlit app.
Clean, modern, supply-chain tailored styling matching the repo's palette.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .i18n import t

# Palette
COLOR_OPTIMAL = "#0F6E56"    # Deep Teal
COLOR_SECONDARY = "#378ADD"  # Steel Blue
COLOR_ACCENT = "#D85A30"     # Warm Rust
COLOR_BG_SHADE = "rgba(216, 90, 48, 0.15)"
COLOR_NEUTRAL = "#64748B"


def create_strategy_comparison_chart(summary_df: pd.DataFrame, lang: str = "vi") -> go.Figure:
    """Grouped bar chart comparing Total Cost ($) and Risk Score across sourcing strategies."""
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "<b>" + ("Tổng chi phí (USD)" if lang == "vi" else "Total Cost (USD)") + "</b>",
            "<b>" + ("Điểm rủi ro tổng hợp (Thấp hơn = Tốt hơn)" if lang == "vi" else "Composite Risk Score (Lower = Safer)") + "</b>",
        ),
        horizontal_spacing=0.12,
    )

    models = summary_df["Model"].tolist()
    costs = summary_df["Total cost"].tolist()
    risks = summary_df.get("Risk score", [0] * len(models)).tolist()

    # Cost bar chart
    fig.add_trace(
        go.Bar(
            x=models,
            y=costs,
            marker_color=[COLOR_OPTIMAL if "cost" in m.lower() else COLOR_SECONDARY for m in models],
            text=[f"${c:,.0f}" for c in costs],
            textposition="auto",
            name="Total Cost ($)" if lang == "en" else "Tổng chi phí ($)",
            hovertemplate="<b>%{x}</b><br>Chi phí: $%{y:,.2f}<extra></extra>" if lang == "vi" else "<b>%{x}</b><br>Cost: $%{y:,.2f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Risk bar chart
    fig.add_trace(
        go.Bar(
            x=models,
            y=risks,
            marker_color=[COLOR_ACCENT if r > 0 else COLOR_NEUTRAL for r in risks],
            text=[f"{r:,.0f}" if r > 0 else "N/A" for r in risks],
            textposition="auto",
            name="Risk Score" if lang == "en" else "Điểm rủi ro",
            hovertemplate="<b>%{x}</b><br>Điểm rủi ro: %{y:,.1f}<extra></extra>" if lang == "vi" else "<b>%{x}</b><br>Risk Score: %{y:,.1f}<extra></extra>",
        ),
        row=1,
        col=2,
    )

    fig.update_layout(
        template="plotly_white",
        height=380,
        margin=dict(l=40, r=40, t=50, b=40),
        showlegend=False,
        font=dict(family="sans-serif", size=12),
    )
    fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0")
    fig.update_xaxes(tickangle=-10)
    return fig


def create_vendor_allocation_chart(allocation_df: pd.DataFrame, lang: str = "vi") -> go.Figure:
    """Interactive bar chart of procurement spend allocated per vendor."""
    if allocation_df.empty:
        return go.Figure()

    vendor_summary = (
        allocation_df.groupby("vendor_id")
        .agg(
            total_spend=("total_cost", "sum"),
            product_count=("product_id", "nunique"),
            total_units=("allocated_quantity", "sum"),
        )
        .reset_index()
        .sort_values("total_spend", ascending=True)
    )

    total_procurement = vendor_summary["total_spend"].sum()
    vendor_summary["share_pct"] = (vendor_summary["total_spend"] / total_procurement) * 100

    fig = go.Figure(
        go.Bar(
            x=vendor_summary["total_spend"],
            y=vendor_summary["vendor_id"],
            orientation="h",
            marker=dict(
                color=vendor_summary["total_spend"],
                colorscale=[[0, "#A7F3D0"], [1, COLOR_OPTIMAL]],
                showscale=False,
            ),
            text=[f"${s:,.0f} ({p:.1f}%)" for s, p in zip(vendor_summary["total_spend"], vendor_summary["share_pct"])],
            textposition="outside",
            customdata=vendor_summary[["product_count", "total_units", "share_pct"]].values,
            hovertemplate=(
                "<b>Nhà cung cấp: %{y}</b><br>"
                + "Chi tiêu: $%{x:,.2f}<br>"
                + "Tỷ trọng: %{customdata[2]:.1f}%<br>"
                + "Số loại sản phẩm: %{customdata[0]}<br>"
                + "Tổng sản lượng: %{customdata[1]:,.0f} đv<extra></extra>"
                if lang == "vi"
                else "<b>Vendor: %{y}</b><br>"
                + "Spend: $%{x:,.2f}<br>"
                + "Share: %{customdata[2]:.1f}%<br>"
                + "Products: %{customdata[0]}<br>"
                + "Units: %{customdata[1]:,.0f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text="<b>" + ("Giá trị đặt hàng phân bổ theo từng nhà cung cấp" if lang == "vi" else "Procurement Value Allocated per Vendor") + "</b>",
            font=dict(size=14),
        ),
        xaxis=dict(
            title="USD",
            showgrid=True,
            gridcolor="#E2E8F0",
        ),
        yaxis=dict(title="Vendor ID"),
        height=max(400, len(vendor_summary) * 24),
        margin=dict(l=60, r=120, t=50, b=40),
    )
    return fig


def create_monte_carlo_chart(feasible_costs: list[float], optimal_cost: float, lang: str = "vi") -> go.Figure:
    """Line chart showing MILP optimum vs 100 random feasible plans."""
    x_vals = list(range(1, len(feasible_costs) + 1))
    gaps = [c - optimal_cost for c in feasible_costs]
    gap_pcts = [(g / optimal_cost) * 100 for g in gaps]

    fig = go.Figure()

    # Shaded area representing the cost of not optimizing
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=feasible_costs,
            mode="lines+markers",
            name="Random Feasible Plans" if lang == "en" else "Phương án ngẫu nhiên khả thi",
            line=dict(color=COLOR_ACCENT, width=2),
            marker=dict(size=4),
            customdata=list(zip(gaps, gap_pcts)),
            hovertemplate=(
                "<b>Phương án #%{x}</b><br>"
                + "Chi phí: $%{y:,.0f}<br>"
                + "Tổn thất vs Tối ưu: +$%{customdata[0]:,.0f} (+%{customdata[1]:.1f}%)<extra></extra>"
                if lang == "vi"
                else "<b>Plan #%{x}</b><br>"
                + "Total Cost: $%{y:,.0f}<br>"
                + "Gap vs Optimum: +$%{customdata[0]:,.0f} (+%{customdata[1]:.1f}%)<extra></extra>"
            ),
        )
    )

    # Optimum benchmark line
    fig.add_trace(
        go.Scatter(
            x=[1, len(feasible_costs)],
            y=[optimal_cost, optimal_cost],
            mode="lines",
            name=f"MILP Optimum (${optimal_cost:,.0f})" if lang == "en" else f"Tối ưu MILP (${optimal_cost:,.0f})",
            line=dict(color=COLOR_OPTIMAL, width=3, dash="dash"),
            hoverinfo="name+y",
        )
    )

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text="<b>" + ("Khoảng cách chi phí: Nghiệm tối ưu MILP vs Các kế hoạch ngẫu nhiên khả thi" if lang == "vi" else "MILP Optimum vs. Random Feasible Purchase Plans (Cost Gap)") + "</b>",
            font=dict(size=14),
        ),
        xaxis=dict(
            title="Các phương án sắp xếp theo chi phí giảm dần" if lang == "vi" else "Feasible Plans (Sorted Descending)",
            showgrid=True,
            gridcolor="#E2E8F0",
        ),
        yaxis=dict(
            title="Tổng chi phí sở hữu (USD)" if lang == "vi" else "Total Cost of Ownership (USD)",
            showgrid=True,
            gridcolor="#E2E8F0",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=450,
        margin=dict(l=50, r=40, t=70, b=40),
    )
    return fig


def create_shadow_price_chart(capacity_df: pd.DataFrame, lang: str = "vi") -> go.Figure:
    """Horizontal bar chart for binding capacity constraints (shadow price $/unit)."""
    if capacity_df.empty:
        return go.Figure()

    df = capacity_df.copy().head(10).sort_values("shadow_price", ascending=True)
    df["label"] = df["vendor_id"] + " (" + df["product_id"] + ")"

    fig = go.Figure(
        go.Bar(
            x=df["shadow_price"],
            y=df["label"],
            orientation="h",
            marker=dict(
                color=df["shadow_price"],
                colorscale=[[0, "#FED7AA"], [1, COLOR_ACCENT]],
                showscale=False,
            ),
            text=[f"${sp:,.2f}/đv" if lang == "vi" else f"${sp:,.2f}/unit" for sp in df["shadow_price"]],
            textposition="outside",
            customdata=df[["capacity", "vendor_id", "product_id"]].values,
            hovertemplate=(
                "<b>%{customdata[1]} - %{customdata[2]}</b><br>"
                + "Shadow Price (tiết kiệm): $%{x:,.2f}/đv<br>"
                + "Công suất hiện tại: %{customdata[0]:,.0f} đv<extra></extra>"
                if lang == "vi"
                else "<b>%{customdata[1]} - %{customdata[2]}</b><br>"
                + "Shadow Price (saving): $%{x:,.2f}/unit<br>"
                + "Current Capacity: %{customdata[0]:,.0f} units<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text="<b>" + ("Top nút thắt công suất: Mức tiết kiệm khi đàm phán thêm 1 đơn vị công suất" if lang == "vi" else "Top Capacity Bottlenecks: Cost Avoidance per +1 Unit Capacity") + "</b>",
            font=dict(size=14),
        ),
        xaxis=dict(
            title="USD / unit" if lang == "en" else "USD / đơn vị nới lỏng",
            showgrid=True,
            gridcolor="#E2E8F0",
        ),
        yaxis=dict(title="Vendor (Product)"),
        height=max(320, len(df) * 36),
        margin=dict(l=100, r=100, t=50, b=40),
    )
    return fig


def create_unused_vendor_chart(unused_df: pd.DataFrame, lang: str = "vi") -> go.Figure:
    """Bar chart for opportunity cost of forcing excluded vendors into optimal plan."""
    if unused_df.empty or "opportunity_cost" not in unused_df.columns:
        return go.Figure()

    df = unused_df.dropna(subset=["opportunity_cost"]).sort_values("opportunity_cost", ascending=True)
    if df.empty:
        return go.Figure()

    fig = go.Figure(
        go.Bar(
            x=df["vendor_id"],
            y=df["opportunity_cost"],
            marker_color=COLOR_SECONDARY,
            text=[f"+${oc:,.2f}" for oc in df["opportunity_cost"]],
            textposition="outside",
            hovertemplate=(
                "<b>Nhà cung cấp: %{x}</b><br>"
                + "Chi phí phụ thêm nếu kích hoạt: +$%{y:,.2f}<extra></extra>"
                if lang == "vi"
                else "<b>Vendor: %{x}</b><br>"
                + "Cost Penalty if Forced: +$%{y:,.2f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text="<b>" + ("Chi phí cơ hội để kích hoạt nhà cung cấp bị loại (Opportunity Cost)" if lang == "vi" else "Opportunity Cost of Activating Excluded Backup Vendors") + "</b>",
            font=dict(size=14),
        ),
        xaxis=dict(title="Vendor ID"),
        yaxis=dict(
            title="Chi phí đội thêm (USD)" if lang == "vi" else "Additional Cost (USD)",
            showgrid=True,
            gridcolor="#E2E8F0",
        ),
        height=320,
        margin=dict(l=50, r=40, t=50, b=40),
    )
    return fig
