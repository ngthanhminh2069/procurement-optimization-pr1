"""
Main Streamlit Application: Procurement Optimization & Dynamic Order Allocation Dashboard.
Hybrid Decision Support System:
- Tier 1: Deterministic MILP Optimization & Shadow Price Analysis (OR-Tools SCIP/GLOP)
- Tier 2: Generative AI Strategic Advisor & Copilot (Google Gemini 3.5 Flash via google-genai)
"""

from __future__ import annotations

import io
import os
import pandas as pd
import streamlit as st

from src.ai_advisor import (
    chat_with_procurement_advisor,
    generate_executive_briefing,
    get_api_call_logs,
)
from src.duality import compute_shadow_prices, compute_unused_vendor_opportunity
from src.i18n import t
from src.insights import (
    analyze_capacity_bottlenecks,
    analyze_excluded_vendors,
    analyze_strategy_tradeoffs,
    validate_procurement_dataset,
)
from src.landing_page import render_landing_page
from src.simulation import run_feasible_solution_sweep
from src.solver import ProcurementProblem, SolveResult, solve_manual_baseline, solve_procurement
from src.visualizations import (
    create_monte_carlo_chart,
    create_shadow_price_chart,
    create_strategy_comparison_chart,
    create_unused_vendor_chart,
    create_vendor_allocation_chart,
)

DEFAULT_DATA_PATH = "data/procurement_data.xlsx"

# --- Page Configuration ---
st.set_page_config(
    page_title="Procurement Optimization AI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #0F6E56;
        margin-top: 4px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #F8FAFC;
        border-radius: 6px 6px 0 0;
        padding: 10px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0F6E56 !important;
        color: white !important;
    }
    .ai-box {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Helper Functions ---
@st.cache_data(show_spinner=False)
def load_raw_sheets(file_or_path: str | bytes) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the four procurement sheets from file path or bytes."""
    xls = pd.ExcelFile(file_or_path)
    required = ["vendor_list", "product_list", "BOM", "quotation"]
    for s in required:
        if s not in xls.sheet_names:
            raise ValueError(f"Missing required sheet: '{s}'. Expected sheets: {required}")

    vendor_df = pd.read_excel(xls, "vendor_list")
    product_df = pd.read_excel(xls, "product_list")
    bom_df = pd.read_excel(xls, "BOM")
    quotation_df = pd.read_excel(xls, "quotation")
    return vendor_df, product_df, bom_df, quotation_df


def safe_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure dataframe columns are strictly typed and Arrow-compatible for Streamlit display."""
    if df.empty:
        return df
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == "object":
            out[col] = out[col].astype(str).replace({"nan": "", "None": "", "<NA>": ""})
    return out


def run_all_strategies(
    problem: ProcurementProblem,
) -> tuple[dict[str, SolveResult], pd.DataFrame, float]:
    """
    Run Cost, Risk, Relationship-preserving models and greedy manual baseline.
    Uncached to ensure 100% reactive execution (<0.35s runtime).
    """
    res_cost = solve_procurement(problem, objective_type="cost", require_all_vendors=False)
    res_risk = solve_procurement(problem, objective_type="risk", require_all_vendors=False)
    res_rel = solve_procurement(problem, objective_type="risk", require_all_vendors=True)
    res_baseline = solve_manual_baseline(problem)

    results = {
        "cost": res_cost,
        "risk": res_risk,
        "risk_all_vendors": res_rel,
        "baseline": res_baseline,
    }

    summary_rows = [
        {
            "Model": "Cost-optimal",
            "Total cost": res_cost.total_cost,
            "Purchase cost": res_cost.total_purchase_cost,
            "PO overhead": res_cost.total_po_cost,
            "Risk score": res_cost.total_risk,
            "Vendors used": f"{res_cost.n_vendors_used}/{res_cost.n_vendors_available}",
        },
        {
            "Model": "Risk-balanced",
            "Total cost": res_risk.total_cost,
            "Purchase cost": res_risk.total_purchase_cost,
            "PO overhead": res_risk.total_po_cost,
            "Risk score": res_risk.total_risk,
            "Vendors used": f"{res_risk.n_vendors_used}/{res_risk.n_vendors_available}",
        },
        {
            "Model": "Relationship-preserving",
            "Total cost": res_rel.total_cost,
            "Purchase cost": res_rel.total_purchase_cost,
            "PO overhead": res_rel.total_po_cost,
            "Risk score": res_rel.total_risk,
            "Vendors used": f"{res_rel.n_vendors_used}/{res_rel.n_vendors_available}",
        },
        {
            "Model": "Manual baseline (Greedy)",
            "Total cost": res_baseline.total_cost,
            "Purchase cost": res_baseline.total_purchase_cost,
            "PO overhead": res_baseline.total_po_cost,
            "Risk score": res_baseline.total_risk,
            "Vendors used": f"{res_baseline.n_vendors_used}/{res_baseline.n_vendors_available}",
        },
    ]

    return results, pd.DataFrame(summary_rows), res_baseline.total_cost


def get_shadow_price_report(problem: ProcurementProblem):
    """Compute fix-and-relax shadow prices and unused vendor opportunity costs."""
    sp_report = compute_shadow_prices(problem)
    unused_df = compute_unused_vendor_opportunity(problem)
    return sp_report, unused_df


# --- Sidebar Setup ---
with st.sidebar:
    st.image("assets/logo.png", width=72)
    st.title("Settings / Cài Đặt")

    # Language Toggle
    lang_choice = st.radio(
        "Language / Ngôn ngữ",
        options=["🇻🇳 Tiếng Việt", "🇬🇧 English"],
        index=0,
        horizontal=True,
    )
    lang = "vi" if "Tiếng Việt" in lang_choice else "en"

    st.markdown("---")

    # Navigation View Mode (Landing Page vs Interactive Dashboard)
    st.subheader("🧭 Chế độ xem / View" if lang == "vi" else "🧭 Navigation")
    landing_label = "📖 Giới Thiệu & Phương Pháp" if lang == "vi" else "📖 Project Guide & Methodology"
    dashboard_label = "📊 Bảng Điều Khiển Tối Ưu Hóa" if lang == "vi" else "📊 Interactive Dashboard"

    if "view_mode" not in st.session_state:
        st.session_state["view_mode"] = "landing"

    nav_index = 0 if st.session_state["view_mode"] == "landing" else 1
    selected_view = st.radio(
        "Navigation",
        options=[landing_label, dashboard_label],
        index=nav_index,
        label_visibility="collapsed",
    )
    if selected_view == landing_label:
        st.session_state["view_mode"] = "landing"
    else:
        st.session_state["view_mode"] = "dashboard"

    st.markdown("---")

    # Data Source Selection
    st.subheader(t("data_source", lang))
    data_source_mode = st.radio(
        t("data_source", lang),
        options=[t("default_dataset", lang), t("custom_upload", lang)],
        index=0,
        label_visibility="collapsed",
    )

    uploaded_file = None
    if data_source_mode == t("custom_upload", lang):
        uploaded_file = st.file_uploader(
            t("upload_btn_label", lang),
            type=["xlsx"],
            help=t("upload_instruction", lang),
        )

    st.markdown("---")

    # Model Parameters
    st.subheader(t("model_parameters", lang))
    bom_tol = st.slider(
        t("bom_tolerance", lang),
        min_value=0.00,
        max_value=0.25,
        value=0.08,
        step=0.01,
        format="%.2f",
        help=t("bom_tolerance_help", lang),
    )

    st.markdown(f"**{t('risk_weights', lang)}**")
    p_weight = st.slider(
        t("price_weight", lang),
        min_value=0.0,
        max_value=1.0,
        value=0.40,
        step=0.05,
    )
    lt_weight = round(1.0 - p_weight, 2)
    st.caption(f"{t('lead_time_weight', lang)}: **{lt_weight:.2f}**")

    st.markdown(f"**{t('po_overheads', lang)}**")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        po_loc = st.number_input(t("po_local", lang), min_value=0.0, value=50.0, step=10.0)
    with col_p2:
        po_ovs = st.number_input(t("po_oversea", lang), min_value=0.0, value=100.0, step=10.0)

    st.markdown("---")

    # AI Configuration (Secure API Key Input)
    st.subheader("🤖 AI Executive Advisor")
    user_api_key = st.text_input(
        "Gemini API Key (Tùy chọn)" if lang == "vi" else "Gemini API Key (Optional)",
        type="password",
        placeholder="AIzaSy...",
        help=(
            "Khóa được xử lý trực tiếp trong phiên trình duyệt, hoàn toàn bảo mật, không bao giờ lưu trữ trên đĩa hoặc commit vào mã nguồn."
            if lang == "vi"
            else "Key is processed securely in-memory for this session only. Never saved or committed."
        ),
    )

    st.caption("Powered by Google Gemini 3.5 Flash & OR-Tools")


# --- View Mode Routing ---
if st.session_state.get("view_mode") == "landing":
    render_landing_page(lang=lang)
    st.stop()


# --- Load Data & Deep Validation ---
try:
    if uploaded_file is not None:
        v_df, p_df, b_df, q_df = load_raw_sheets(uploaded_file.getvalue())
        data_source_name = uploaded_file.name
    else:
        if not os.path.exists(DEFAULT_DATA_PATH):
            st.error(f"Cannot find default dataset at {DEFAULT_DATA_PATH}")
            st.stop()
        v_df, p_df, b_df, q_df = load_raw_sheets(DEFAULT_DATA_PATH)
        data_source_name = "procurement_data.xlsx (66 products, 23 vendors, 323 quotes)"

    # Validate dataset integrity
    is_valid, critical_errors, warnings = validate_procurement_dataset(
        v_df, p_df, b_df, q_df, bom_tolerance=bom_tol, lang=lang
    )

    if not is_valid:
        st.error("🚨 **Lỗi dữ liệu đầu vào:** Dữ liệu tải lên không thỏa mãn các điều kiện kỹ thuật cơ bản:")
        for err in critical_errors:
            st.markdown(f"- {err}")
        st.info("Vui lòng tải về file mẫu tại tab 'Dữ Liệu & Cấu Trúc' để đối chiếu định dạng.")
        st.stop()

    if warnings:
        with st.expander("⚠️ Cảnh báo cấu trúc dữ liệu (Data Warnings)", expanded=False):
            for w in warnings:
                st.write(f"• {w}")

    problem = ProcurementProblem.from_raw_sheets(
        vendor_df=v_df,
        product_df=p_df,
        bom_df=b_df,
        quotation_df=q_df,
        bom_tolerance=bom_tol,
        price_weight=p_weight,
        lead_time_weight=lt_weight,
        po_cost_local=po_loc,
        po_cost_oversea=po_ovs,
    )

except Exception as e:
    st.error(f"Lỗi nạp dữ liệu: {e}")
    st.stop()


# --- Reactive State Fingerprinting ---
# Detect any change in data source or model parameters to invalidate stale simulation & AI cache
current_signature = f"{data_source_name}_{len(q_df)}_{bom_tol:.2f}_{p_weight:.2f}_{po_loc}_{po_ovs}"
if st.session_state.get("data_signature") != current_signature:
    st.session_state["data_signature"] = current_signature
    st.session_state.pop("monte_carlo_data", None)
    st.session_state.pop("executive_briefing_content", None)
    st.session_state.pop("chat_history", None)


# --- Run Optimization Models (Direct & Reactive) ---
results, summary_df, manual_cost = run_all_strategies(problem)
opt_res = results["cost"]
risk_res = results["risk"]
rel_res = results["risk_all_vendors"]

if not opt_res.is_feasible:
    st.error(
        "❌ **Không tìm được phương án tối ưu khả thi (Infeasible):** "
        "Bộ dữ liệu hoặc các ràng buộc hiện tại (MOQ, Capacity, BOM Tolerance) không thể thỏa mãn cùng lúc. "
        "Hãy thử tăng 'Dung sai giao hàng vượt BOM' ở Sidebar hoặc kiểm tra lại công suất các nhà cung cấp."
        if lang == "vi"
        else "❌ **Model Infeasible:** No constraint-satisfying plan exists with current MOQ, capacity, or BOM bounds. "
        "Try increasing BOM tolerance or checking supplier capacity."
    )
    st.stop()

sp_report, unused_df = get_shadow_price_report(problem)

# Generate Dynamic Insights
tradeoff_insight = analyze_strategy_tradeoffs(opt_res, risk_res, rel_res, manual_cost, lang=lang)
bottleneck_insight = analyze_capacity_bottlenecks(sp_report.capacity, lang=lang)
excluded_insight = analyze_excluded_vendors(unused_df, lang=lang)

# Grounding package for AI Advisor
grounding_data = {
    "total_cost": opt_res.total_cost,
    "purchase_cost": opt_res.total_purchase_cost,
    "po_overhead": opt_res.total_po_cost,
    "savings_dollars": tradeoff_insight.get("savings_dollars", 0.0),
    "savings_pct": tradeoff_insight.get("savings_pct", 0.0),
    "vendors_used": f"{opt_res.n_vendors_used}/{opt_res.n_vendors_available}",
    "cost_diff_pct": tradeoff_insight.get("cost_diff_pct", 0.0),
    "risk_diff_pct": tradeoff_insight.get("risk_diff_pct", 0.0),
    "top_prod": bottleneck_insight.get("top_product", "N/A"),
    "top_vendor": bottleneck_insight.get("top_vendor", "N/A"),
    "top_shadow_price": bottleneck_insight.get("shadow_price", 0.0),
    "top_savings_10pct": bottleneck_insight.get("potential_savings_10pct", 0.0),
    "best_unused": excluded_insight.get("best_vendor", "N/A"),
    "opp_cost": excluded_insight.get("opportunity_cost", 0.0),
}


# --- Main Dashboard Header ---
st.title(f"📦 {t('app_title', lang)}")
st.markdown(
    f"*{t('app_subtitle', lang)}* &nbsp;|&nbsp; "
    f"📁 **Data**: `{data_source_name}` &nbsp;|&nbsp; "
    f"⚙️ **BOM Tolerance**: `+{bom_tol*100:.0f}%` &nbsp;|&nbsp; "
    f"⚖️ **Weights**: `Price: {p_weight:.0%} / Lead-time: {lt_weight:.0%}`"
)

# Tabs
tab_overview, tab_shadow, tab_monte, tab_whatif, tab_ai, tab_data = st.tabs(
    [
        t("tab_overview", lang),
        t("tab_shadow_price", lang),
        t("tab_monte_carlo", lang),
        t("tab_what_if", lang),
        t("tab_ai", lang),
        t("tab_data", lang),
    ]
)


# ==============================================================================
# TAB 1: EXECUTIVE OVERVIEW & SOURCING STRATEGIES
# ==============================================================================
with tab_overview:
    savings_dollars = tradeoff_insight.get("savings_dollars", 0.0)
    savings_pct = tradeoff_insight.get("savings_pct", 0.0)

    # Top KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('kpi_total_cost', lang)}</div>
                <div class="metric-value">${opt_res.total_cost:,.0f}</div>
                <div class="metric-sub">{t('kpi_purchase_spend', lang)}: ${opt_res.total_purchase_cost:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('kpi_savings', lang)}</div>
                <div class="metric-value" style="color: #0F6E56;">${savings_dollars:,.2f}</div>
                <div class="metric-sub">{savings_pct:.2f}% {"tiết kiệm vs Thủ công" if lang=="vi" else "savings vs Greedy"}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('kpi_vendors_used', lang)}</div>
                <div class="metric-value">{opt_res.n_vendors_used} / {opt_res.n_vendors_available}</div>
                <div class="metric-sub">{t('kpi_po_overhead', lang)}: ${opt_res.total_po_cost:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{t('kpi_risk_score', lang)} ({t('strategy_risk', lang)})</div>
                <div class="metric-value" style="color: #D85A30;">{risk_res.total_risk:,.0f}</div>
                <div class="metric-sub">{"vs" if lang=="en" else "so với"} {opt_res.total_risk:,.0f} ({t('strategy_cost', lang)})</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Strategy Comparison Charts
    col_strat1, col_strat2 = st.columns([3, 2])
    with col_strat1:
        st.markdown(f"#### {t('cost_comparison_chart_title', lang)}")
        fig_strat = create_strategy_comparison_chart(summary_df, lang=lang)
        st.plotly_chart(fig_strat, width="stretch")

    with col_strat2:
        st.markdown(f"#### {'Bảng so sánh chi tiết' if lang=='vi' else 'Strategy Comparison Table'}")
        disp_summary = summary_df.copy()
        disp_summary["Total cost"] = disp_summary["Total cost"].map(lambda x: f"${x:,.2f}")
        disp_summary["Purchase cost"] = disp_summary["Purchase cost"].map(lambda x: f"${x:,.2f}")
        disp_summary["PO overhead"] = disp_summary["PO overhead"].map(lambda x: f"${x:,.2f}")
        disp_summary["Risk score"] = disp_summary["Risk score"].map(lambda x: f"{x:,.1f}" if x > 0 else "—")
        st.dataframe(safe_display_df(disp_summary), width="stretch", hide_index=True)

        # Dynamic Strategic Insights Callouts (Tier 1)
        st.info(f"💡 **Nhận định đánh đổi rủi ro:** {tradeoff_insight['tradeoff_text']}")
        st.caption(f"📌 {tradeoff_insight['baseline_text']}")
        st.caption(f"🤝 {tradeoff_insight['relationship_text']}")

    st.markdown("---")

    # Vendor Allocation Chart & Details
    col_alloc1, col_alloc2 = st.columns([3, 2])
    with col_alloc1:
        selected_model_view = st.selectbox(
            "Hiển thị phân bổ theo mô hình:" if lang == "vi" else "Display allocation for strategy:",
            options=["Cost-optimal", "Risk-balanced", "Relationship-preserving"],
            index=0,
        )
        active_alloc = (
            opt_res.allocation
            if selected_model_view == "Cost-optimal"
            else (risk_res.allocation if selected_model_view == "Risk-balanced" else rel_res.allocation)
        )
        fig_alloc = create_vendor_allocation_chart(active_alloc, lang=lang)
        st.plotly_chart(fig_alloc, width="stretch")

    with col_alloc2:
        st.markdown(f"#### {t('allocation_table_title', lang)}")
        if not active_alloc.empty:
            v_filter = st.multiselect(
                "Lọc nhà cung cấp:" if lang == "vi" else "Filter by Vendor:",
                options=sorted(active_alloc["vendor_id"].unique()),
                default=[],
            )
            filtered_alloc = active_alloc.copy()
            if v_filter:
                filtered_alloc = filtered_alloc[filtered_alloc["vendor_id"].isin(v_filter)]

            st.dataframe(
                safe_display_df(
                    filtered_alloc[["product_id", "vendor_id", "allocated_quantity", "unit_price", "total_cost"]]
                ),
                width="stretch",
                height=350,
                hide_index=True,
            )

            csv_buf = io.StringIO()
            filtered_alloc.to_csv(csv_buf, index=False)
            st.download_button(
                label=f"📥 {t('download_csv', lang)}",
                data=csv_buf.getvalue(),
                file_name=f"procurement_allocation_{selected_model_view.lower()}.csv",
                mime="text/csv",
                use_container_width=True,
            )


# ==============================================================================
# TAB 2: SHADOW PRICE & SENSITIVITY ANALYSIS
# ==============================================================================
with tab_shadow:
    st.subheader(f"🔍 {t('shadow_price_header', lang)}")
    st.markdown(t("shadow_price_intro", lang))

    col_sp1, col_sp2 = st.columns([3, 2])
    with col_sp1:
        st.markdown(f"#### {t('capacity_bottlenecks_title', lang)}")
        fig_cap = create_shadow_price_chart(sp_report.capacity, lang=lang)
        st.plotly_chart(fig_cap, width="stretch")

    with col_sp2:
        st.markdown(f"#### {'Top nút thắt chi tiết' if lang=='vi' else 'Binding Bottleneck Details'}")
        if not sp_report.capacity.empty:
            cap_display = sp_report.capacity.copy()
            cap_display["shadow_price"] = cap_display["shadow_price"].map(lambda x: f"${x:,.2f}")
            st.dataframe(safe_display_df(cap_display), width="stretch", height=280, hide_index=True)
            st.success(bottleneck_insight["headline"])
        else:
            st.info(bottleneck_insight["headline"])

    st.markdown("---")

    # Excluded vendor opportunity cost
    col_un1, col_un2 = st.columns([3, 2])
    with col_un1:
        st.markdown(f"#### {t('unused_vendor_title', lang)}")
        st.markdown(t("unused_vendor_desc", lang))
        fig_unused = create_unused_vendor_chart(unused_df, lang=lang)
        st.plotly_chart(fig_unused, width="stretch")

    with col_un2:
        st.markdown(f"#### {'Bảng chi phí cơ hội' if lang=='vi' else 'Opportunity Cost Table'}")
        if not unused_df.empty:
            un_disp = unused_df.copy()
            if "cost_if_forced_in" in un_disp.columns:
                un_disp["cost_if_forced_in"] = un_disp["cost_if_forced_in"].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "Infeasible")
            if "opportunity_cost" in un_disp.columns:
                un_disp["opportunity_cost"] = un_disp["opportunity_cost"].map(lambda x: f"+${x:,.2f}" if pd.notnull(x) else "—")
            st.dataframe(safe_display_df(un_disp[["vendor_id", "opportunity_cost", "interpretation"]]), width="stretch", height=260, hide_index=True)
            st.info(excluded_insight["headline"])
        else:
            st.info("Toàn bộ nhà cung cấp đã được sử dụng trong kế hoạch tối ưu." if lang == "vi" else "All available vendors are already utilized.")


# ==============================================================================
# TAB 3: MONTE CARLO & "COST OF NOT OPTIMIZING"
# ==============================================================================
with tab_monte:
    st.subheader(f"🎲 {t('monte_carlo_header', lang)}")
    st.markdown(t("monte_carlo_desc", lang))

    col_m_ctrl1, col_m_ctrl2 = st.columns([2, 3])
    with col_m_ctrl1:
        n_sims = st.select_slider(
            t("num_simulations", lang),
            options=[20, 50, 100],
            value=50,
        )
        run_sim = st.button(f"🚀 {t('run_sim_btn', lang)}", use_container_width=True)

    with col_m_ctrl2:
        st.caption(
            "Mỗi điểm trên đường biểu diễn là một phương án mua hàng thỏa mãn đầy đủ ràng buộc kỹ thuật (MOQ, Capacity, BOM). "
            "Khoảng cách giữa các phương án này với đường tối ưu MILP là số tiền mà doanh nghiệp sẽ lãng phí nếu lập kế hoạch thủ công."
            if lang == "vi"
            else "Every point represents a strictly feasible purchase plan satisfying all constraints (MOQ, Capacity, BOM). "
            "The gap between these plans and the MILP optimal line is the money left on the table."
        )

    # Automatic rerun if cached sweep is missing or user requests new sweep
    if "monte_carlo_data" not in st.session_state or run_sim:
        with st.spinner("Đang chạy mô phỏng Monte Carlo..." if lang == "vi" else "Running Monte Carlo feasible sweep..."):
            st.session_state["monte_carlo_data"] = run_feasible_solution_sweep(problem, n_simulations=n_sims)

    sim_costs = st.session_state.get("monte_carlo_data", [])
    opt_cost = opt_res.total_cost

    if sim_costs:
        fig_mc = create_monte_carlo_chart(sim_costs, opt_cost, lang=lang)
        st.plotly_chart(fig_mc, width="stretch")

        gaps = [c - opt_cost for c in sim_costs]
        min_gap = min(gaps)
        avg_gap = sum(gaps) / len(gaps)
        max_gap = max(gaps)

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(
                t("gap_min", lang),
                f"+${min_gap:,.0f}",
                f"+{(min_gap/opt_cost)*100:.1f}% vs Optimum",
            )
        with m2:
            st.metric(
                t("gap_avg", lang),
                f"+${avg_gap:,.0f}",
                f"+{(avg_gap/opt_cost)*100:.1f}% vs Optimum",
            )
        with m3:
            st.metric(
                t("gap_max", lang),
                f"+${max_gap:,.0f}",
                f"+{(max_gap/opt_cost)*100:.1f}% vs Optimum",
            )


# ==============================================================================
# TAB 4: WHAT-IF NEGOTIATION SANDBOX
# ==============================================================================
with tab_whatif:
    st.subheader(f"🛠️ {t('what_if_header', lang)}")
    st.markdown(t("what_if_desc", lang))

    quotes = problem.prepared_quotation.copy()

    w_col1, w_col2, w_col3 = st.columns(3)
    with w_col1:
        sel_vendor = st.selectbox(t("select_vendor", lang), options=sorted(quotes["vendor_id"].unique()))
    with w_col2:
        available_products = quotes.loc[quotes["vendor_id"] == sel_vendor, "product_id"].unique()
        sel_product = st.selectbox(t("select_product", lang), options=sorted(available_products))

    curr_quote = quotes[(quotes["vendor_id"] == sel_vendor) & (quotes["product_id"] == sel_product)].iloc[0]

    with w_col3:
        st.markdown(f"**{t('current_terms', lang)}:**")
        st.write(
            f"• Price: **${curr_quote['unit_price']:.2f}** | "
            f"Capacity: **{curr_quote['Capacity']:,.0f}** | "
            f"MOQ: **{curr_quote['MOQ']:,.0f}**"
        )

    st.markdown("##### " + ("Nhập các điều khoản mới sau đàm phán:" if lang == "vi" else "Enter renegotiated quotation terms:"))
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        new_price = st.number_input(
            t("adjusted_price", lang),
            min_value=0.01,
            value=float(curr_quote["unit_price"]),
            step=1.0,
            format="%.2f",
        )
    with sc2:
        new_cap = st.number_input(
            t("adjusted_cap", lang),
            min_value=1.0,
            value=float(curr_quote["Capacity"]),
            step=50.0,
            format="%.0f",
        )
    with sc3:
        new_moq = st.number_input(
            t("adjusted_moq", lang),
            min_value=0.0,
            value=float(curr_quote["MOQ"]),
            step=10.0,
            format="%.0f",
        )

    if st.button(f"⚡ {t('simulate_btn', lang)}", type="primary"):
        mod_q_df = q_df.copy()
        mask = (mod_q_df["vendor_id"] == sel_vendor) & (mod_q_df["product_id"] == sel_product)
        mod_q_df.loc[mask, "unit_price"] = new_price
        mod_q_df.loc[mask, "Capacity"] = new_cap
        mod_q_df.loc[mask, "MOQ"] = new_moq

        mod_problem = ProcurementProblem.from_raw_sheets(
            vendor_df=v_df,
            product_df=p_df,
            bom_df=b_df,
            quotation_df=mod_q_df,
            bom_tolerance=bom_tol,
            price_weight=p_weight,
            lead_time_weight=lt_weight,
            po_cost_local=po_loc,
            po_cost_oversea=po_ovs,
        )

        mod_res = solve_procurement(mod_problem, objective_type="cost")

        st.markdown(f"#### {t('before_after_comparison', lang)}")
        comp1, comp2, comp3 = st.columns(3)
        delta_cost = mod_res.total_cost - opt_res.total_cost
        with comp1:
            st.metric(
                "Chi phí trước đàm phán" if lang == "vi" else "Pre-negotiation Spend",
                f"${opt_res.total_cost:,.2f}",
            )
        with comp2:
            st.metric(
                "Chi phí sau đàm phán" if lang == "vi" else "Post-negotiation Spend",
                f"${mod_res.total_cost:,.2f}",
                delta=f"${delta_cost:,.2f}" if delta_cost != 0 else "0",
                delta_color="inverse",
            )
        with comp3:
            old_qty = 0.0
            old_match = opt_res.allocation[
                (opt_res.allocation["vendor_id"] == sel_vendor) & (opt_res.allocation["product_id"] == sel_product)
            ]
            if not old_match.empty:
                old_qty = old_match["allocated_quantity"].iloc[0]

            new_qty = 0.0
            new_match = mod_res.allocation[
                (mod_res.allocation["vendor_id"] == sel_vendor) & (mod_res.allocation["product_id"] == sel_product)
            ]
            if not new_match.empty:
                new_qty = new_match["allocated_quantity"].iloc[0]

            st.metric(
                f"Sản lượng giao cho {sel_vendor}" if lang == "vi" else f"Allocated to {sel_vendor}",
                f"{new_qty:,.0f} đv",
                delta=f"{new_qty - old_qty:,.0f} đv",
            )

        if delta_cost < -1e-2:
            st.balloons()
            st.success(
                f"🎉 Đàm phán thành công! Phương án mới giúp tiết kiệm thêm **${abs(delta_cost):,.2f}** cho doanh nghiệp."
                if lang == "vi"
                else f"🎉 Successful negotiation! The new terms save an additional **${abs(delta_cost):,.2f}**."
            )
        elif abs(delta_cost) <= 1e-2:
            st.warning(
                "Điều khoản mới chưa đủ sức thay đổi phương án tối ưu hoặc không mang lại thêm tiết kiệm chi phí."
                if lang == "vi"
                else "The concession does not alter the optimal allocation or impact total spend."
            )


# ==============================================================================
# TAB 5: AI STRATEGIC ADVISOR & COPILOT (GEMINI 3.5 FLASH)
# ==============================================================================
with tab_ai:
    st.subheader("🤖 Trợ Lý AI Chiến Lược Thu Mua (AI Strategic Advisor)")
    st.markdown(
        "Tận dụng sức mạnh suy luận của **Google Gemini 3.5 Flash** kết hợp cùng dữ liệu tối ưu hóa toán học thực tế "
        "để cung cấp góc nhìn của một Giám Đốc Thu Mua (CPO) và hỗ trợ trả lời các câu hỏi tình huống phức tạp."
        if lang == "vi"
        else "Leverages **Google Gemini 3.5 Flash** grounded on verified MILP optimization data to generate "
        "CPO-level executive strategic briefings and answer procurement negotiation inquiries."
    )

    ai_col1, ai_col2 = st.columns([1, 1])
    with ai_col1:
        if st.button("📑 Tạo Báo Cáo Chiến Lược Điều Hành (CPO Briefing)", type="primary", use_container_width=True):
            with st.spinner("Đang tổng hợp báo cáo chiến lược từ Gemini 3.5 Flash..." if lang == "vi" else "Generating CPO Briefing via Gemini 3.5 Flash..."):
                success, content = generate_executive_briefing(grounding_data, api_key=user_api_key, lang=lang)
                st.session_state["executive_briefing_content"] = (success, content)

    # Display Executive Briefing if generated
    if "executive_briefing_content" in st.session_state:
        success, content = st.session_state["executive_briefing_content"]
        if success:
            with st.container(border=True):
                st.markdown("### 📑 CPO Executive Strategic Briefing")
                st.markdown(content)
                st.download_button(
                    label="📥 Tải Báo Cáo (.md)" if lang == "vi" else "📥 Download Briefing (.md)",
                    data=content,
                    file_name="cpo_executive_briefing.md",
                    mime="text/markdown",
                    key="download_cpo_briefing",
                )
        else:
            st.warning(content)

    st.markdown("---")
    st.markdown("#### 💬 Trò Chuyện Cùng Cố Vấn AI Thu Mua (AI Procurement Copilot)")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Display chat history
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User chat input
    user_prompt = st.chat_input(
        "Hỏi về chiến lược đàm phán, lý do chọn nhà cung cấp, hoặc cách giảm thiểu rủi ro..."
        if lang == "vi"
        else "Ask about negotiation strategy, supplier rationale, or risk mitigation..."
    )

    if user_prompt:
        st.session_state["chat_history"].append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("AI đang phân tích..." if lang == "vi" else "AI is analyzing..."):
                ai_reply = chat_with_procurement_advisor(
                    user_message=user_prompt,
                    chat_history=st.session_state["chat_history"],
                    grounding_data=grounding_data,
                    api_key=user_api_key,
                    lang=lang,
                )
                st.markdown(ai_reply)
                st.session_state["chat_history"].append({"role": "assistant", "content": ai_reply})

    st.markdown("---")
    with st.expander("📜 Nhật Ký & Chi Tiết Kỹ Thuật Gọi API AI (AI API Call Audit Log)", expanded=False):
        api_logs = get_api_call_logs()
        if not api_logs:
            st.info(
                "Chưa có lượt gọi API nào được thực hiện trong phiên làm việc này. "
                "Nhấn nút 'Tạo Báo Cáo Chiến Lược Điều Hành' hoặc gửi câu hỏi tại ô chat bên trên để ghi nhận log."
                if lang == "vi"
                else "No AI API calls have been made in this session yet. "
                "Click 'Generate CPO Briefing' or send a chat message above to trigger an API call."
            )
        else:
            for i, l in enumerate(reversed(api_logs), 1):
                status_color = "🟢" if "SUCCESS" in l["status"] else ("🔒" if "OFFLINE" in l["status"] else "🔴")
                origin_badge = f" — *Nguồn gốc:* `{l.get('error_origin')}`" if l.get("error_origin") else ""
                st.markdown(f"**Lượt gọi #{len(api_logs) - i + 1}**: {status_color} `{l['endpoint']}` — `{l['timestamp']}` ({l['latency_ms']} ms){origin_badge}")
                st.json(l)



# ==============================================================================
# TAB 6: DATA MANAGEMENT & SCHEMA INSPECTOR
# ==============================================================================
with tab_data:
    st.subheader(f"📁 {t('data_sheets_preview', lang)}")
    st.markdown(t("upload_instruction", lang))

    s_tab1, s_tab2, s_tab3, s_tab4 = st.tabs(["quotation", "BOM", "vendor_list", "product_list"])
    with s_tab1:
        st.markdown(f"**Quotation Sheet** ({len(q_df)} rows)")
        st.dataframe(safe_display_df(q_df), width="stretch", height=350)
    with s_tab2:
        st.markdown(f"**BOM Sheet** ({len(b_df)} products)")
        st.dataframe(safe_display_df(b_df), width="stretch", height=350)
    with s_tab3:
        st.markdown(f"**Vendor List Sheet** ({len(v_df)} vendors)")
        st.dataframe(safe_display_df(v_df), width="stretch", height=350)
    with s_tab4:
        st.markdown(f"**Product List Sheet** ({len(p_df)} products)")
        st.dataframe(safe_display_df(p_df), width="stretch", height=350)

    output_buf = io.BytesIO()
    with pd.ExcelWriter(output_buf, engine="openpyxl") as writer:
        v_df.to_excel(writer, sheet_name="vendor_list", index=False)
        p_df.to_excel(writer, sheet_name="product_list", index=False)
        b_df.to_excel(writer, sheet_name="BOM", index=False)
        q_df.to_excel(writer, sheet_name="quotation", index=False)

    st.download_button(
        label="📥 Tải xuống file Excel mẫu (Procurement Template)" if lang == "vi" else "📥 Download Excel Template",
        data=output_buf.getvalue(),
        file_name="procurement_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
