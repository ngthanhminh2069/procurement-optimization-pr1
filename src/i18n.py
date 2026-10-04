"""
Internationalization (i18n) dictionary for the Procurement Optimization Streamlit app.
Supports dynamic switching between English (en) and Vietnamese (vi).
"""

from typing import Any

TRANSLATIONS: dict[str, dict[str, str]] = {
    # --- Header & General ---
    "app_title": {
        "en": "Procurement Optimization & Dynamic Order Allocation",
        "vi": "Tối Ưu Hóa Thu Mua & Phân Bổ Đơn Hàng Đa Nhà Cung Cấp",
    },
    "app_subtitle": {
        "en": "Interactive MILP decision support system with dual-value shadow price analysis & risk balancing.",
        "vi": "Hệ thống hỗ trợ ra quyết định thu mua MILP với phân tích Shadow Price & cân bằng rủi ro.",
    },
    "language": {
        "en": "Language",
        "vi": "Ngôn ngữ",
    },
    "data_source": {
        "en": "Data Source",
        "vi": "Nguồn dữ liệu",
    },
    "default_dataset": {
        "en": "Enterprise Procurement Dataset (66 products, 23 vendors, 323 quotes)",
        "vi": "Dữ liệu mua hàng chuẩn (66 SP, 23 NCC, 323 báo giá)",
    },
    "custom_upload": {
        "en": "Upload custom Excel (.xlsx)",
        "vi": "Tải lên file Excel tùy chỉnh (.xlsx)",
    },

    # --- Sidebar Parameters ---
    "model_parameters": {
        "en": "Model Parameters",
        "vi": "Tham số mô hình",
    },
    "bom_tolerance": {
        "en": "BOM Over-delivery Tolerance",
        "vi": "Dung sai giao hàng vượt BOM",
    },
    "bom_tolerance_help": {
        "en": "Maximum allowed order quantity above BOM requirement (e.g. 0.08 = +8%).",
        "vi": "Tỷ lệ tối đa cho phép đặt hàng vượt định mức BOM (VD: 0.08 = +8%).",
    },
    "risk_weights": {
        "en": "Risk Objective Weights",
        "vi": "Trọng số hàm mục tiêu rủi ro",
    },
    "price_weight": {
        "en": "Price Weight (Cost focus)",
        "vi": "Trọng số Giá (Tối ưu chi phí)",
    },
    "lead_time_weight": {
        "en": "Lead Time Weight (Safety focus)",
        "vi": "Trọng số Thời gian giao hàng (An toàn)",
    },
    "po_overheads": {
        "en": "PO Administrative Overhead ($/vendor)",
        "vi": "Phí quản lý đơn hàng ($/nhà cung cấp)",
    },
    "po_local": {
        "en": "Domestic vendor PO fee ($)",
        "vi": "Phí đơn hàng NCC trong nước ($)",
    },
    "po_oversea": {
        "en": "Overseas vendor PO fee ($)",
        "vi": "Phí đơn hàng NCC nước ngoài ($)",
    },
    "recalculate_btn": {
        "en": "Re-run Optimization",
        "vi": "Chạy lại tối ưu hóa",
    },

    # --- Tabs ---
    "tab_overview": {
        "en": "📊 Strategy Comparison",
        "vi": "📊 So Sánh Chiến Lược",
    },
    "tab_shadow_price": {
        "en": "🔍 Shadow Price & Bottlenecks",
        "vi": "🔍 Shadow Price & Điểm Nghẽn",
    },
    "tab_monte_carlo": {
        "en": "🎲 Monte Carlo Validation",
        "vi": "🎲 Mô Phỏng Monte Carlo",
    },
    "tab_what_if": {
        "en": "🛠️ What-If Sandbox",
        "vi": "🛠️ Giả Định What-If",
    },
    "tab_ai": {
        "en": "🤖 AI Strategic Advisor",
        "vi": "🤖 Trợ Lý AI Chiến Lược",
    },
    "tab_data": {
        "en": "📁 Data & Schema",
        "vi": "📁 Dữ Liệu & Cấu Trúc",
    },

    # --- Tab 1: Strategies ---
    "kpi_total_cost": {
        "en": "Optimal Total Cost",
        "vi": "Tổng Chi Phí Tối Ưu",
    },
    "kpi_purchase_spend": {
        "en": "Purchase Spend",
        "vi": "Tiền Mua Hàng",
    },
    "kpi_po_overhead": {
        "en": "PO Overhead Cost",
        "vi": "Chi Phí Quản Lý PO",
    },
    "kpi_risk_score": {
        "en": "Risk Score",
        "vi": "Điểm Rủi Ro",
    },
    "kpi_vendors_used": {
        "en": "Active Vendors",
        "vi": "NCC Được Kích Hoạt",
    },
    "kpi_savings": {
        "en": "Savings vs Greedy Manual",
        "vi": "Tiết Kiệm vs Phân Bổ Thủ Công",
    },
    "strategy_cost": {
        "en": "Cost-optimal",
        "vi": "Tối ưu chi phí",
    },
    "strategy_risk": {
        "en": "Risk-balanced",
        "vi": "Cân bằng rủi ro",
    },
    "strategy_relationship": {
        "en": "Relationship-preserving",
        "vi": "Duy trì toàn bộ NCC",
    },
    "strategy_manual": {
        "en": "Manual Baseline (Greedy)",
        "vi": "Thủ công (Tham lam theo giá)",
    },
    "cost_comparison_chart_title": {
        "en": "Cost & Risk Trade-off Across Sourcing Strategies",
        "vi": "Đánh Đổi Giữa Chi Phí & Rủi Ro Qua Các Chiến Lược Thu Mua",
    },
    "vendor_allocation_chart_title": {
        "en": "Procurement Spend Allocated per Vendor",
        "vi": "Phân Bổ Giá Trị Đơn Hàng Theo Từng Nhà Cung Cấp",
    },
    "allocation_table_title": {
        "en": "Detailed Product Sourcing Allocation",
        "vi": "Bảng Chi Tiết Phân Bổ Đơn Hàng Từng Sản Phẩm",
    },
    "download_csv": {
        "en": "Download Allocation as CSV",
        "vi": "Tải kết quả phân bổ (CSV)",
    },

    # --- Tab 2: Shadow Price ---
    "shadow_price_header": {
        "en": "Dual-Value Sensitivity & Negotiation Priorities",
        "vi": "Phân Tích Shadow Price & Thứ Tự Ưu Tiên Đàm Phán",
    },
    "shadow_price_intro": {
        "en": "Shadow price (dual value) indicates the marginal cost change if a binding constraint is relaxed by 1 unit. Obtained via LP relaxation (Fix-and-Relax with GLOP) around the optimal integer solution.",
        "vi": "Shadow Price thể hiện mức tiết kiệm chi phí cận biên khi nới lỏng 1 đơn vị ràng buộc. Được trích xuất qua phương pháp Fix-and-Relax bằng GLOP tại nghiệm nguyên tối ưu.",
    },
    "capacity_bottlenecks_title": {
        "en": "Top Vendor Capacity Bottlenecks (Where extra capacity saves the most cash)",
        "vi": "Top Nút Thắt Công Suất NCC (Nơi nới rộng công suất mang lại tiết kiệm lớn nhất)",
    },
    "capacity_table_cols": {
        "en": "Product | Vendor | Quoted Cap | Shadow Price ($/unit) | Economic Meaning",
        "vi": "Sản phẩm | Nhà cung cấp | Công suất | Shadow Price ($/đv) | Ý nghĩa kinh tế",
    },
    "bom_sensitivities_title": {
        "en": "BOM Requirement & Tolerance Sensitivities",
        "vi": "Độ Nhạy Yêu Cầu Định Mức & Trần Dung Sai BOM",
    },
    "unused_vendor_title": {
        "en": "Excluded Vendor Opportunity Cost (Backup supplier activation hurdle)",
        "vi": "Chi Phí Cơ Hội Của NCC Bị Loại (Rào cản để kích hoạt NCC dự phòng)",
    },
    "unused_vendor_desc": {
        "en": "Cost penalty if forcing an excluded vendor into the purchasing plan. Indicates how large a price/terms concession that vendor must offer to become competitive.",
        "vi": "Mức chi phí chênh lệch tăng thêm nếu bắt buộc phải đưa NCC bị loại vào kế hoạch. Thể hiện mức giảm giá/ưu đãi mà NCC đó cần đưa ra để lọt vào kế hoạch tối ưu.",
    },

    # --- Tab 3: Monte Carlo ---
    "monte_carlo_header": {
        "en": "Monte Carlo Optimality Proof vs Random Feasible Sourcing Plans",
        "vi": "Chứng Minh Tính Tối Ưu Monte Carlo So Với Kế Hoạch Ngẫu Nhiên Khả Thi",
    },
    "monte_carlo_desc": {
        "en": "Demonstrates the 'Cost of Not Optimizing'. Solves the exact constraints with random linear objectives to sample valid feasible purchasing plans that a spreadsheet buyer might produce.",
        "vi": "Chứng minh 'Chi phí của việc không tối ưu'. Giải hệ ràng buộc thực tế với hàm mục tiêu ngẫu nhiên để mô phỏng các phương án hợp lệ mà người thu mua có thể chọn bừa.",
    },
    "num_simulations": {
        "en": "Number of Monte Carlo simulations",
        "vi": "Số lần mô phỏng Monte Carlo",
    },
    "run_sim_btn": {
        "en": "Run Monte Carlo Sweep",
        "vi": "Chạy mô phỏng Monte Carlo",
    },
    "gap_stats_title": {
        "en": "Quantifying the Cost of Inefficient Sourcing",
        "vi": "Định Lượng Tổn Thất Do Mua Hàng Không Tối Ưu",
    },
    "gap_min": {
        "en": "Minimum Feasible Gap",
        "vi": "Chênh lệch nhỏ nhất",
    },
    "gap_avg": {
        "en": "Average Money Left on Table",
        "vi": "Tổn thất trung bình",
    },
    "gap_max": {
        "en": "Worst Feasible Plan Gap",
        "vi": "Chênh lệch lớn nhất",
    },

    # --- Tab 4: What-If ---
    "what_if_header": {
        "en": "Interactive Sourcing Negotiation Sandbox",
        "vi": "Khu Vực Giả Định Đàm Phán Mua Hàng (What-If)",
    },
    "what_if_desc": {
        "en": "Simulate vendor concessions: modify price, MOQ, or capacity for a specific vendor quotation to see immediate allocation and spend impact.",
        "vi": "Mô phỏng đàm phán: thay đổi giá, MOQ hoặc công suất của một báo giá để thấy ngay tác động đến phân bổ đơn hàng và chi phí tổng thể.",
    },
    "select_vendor": {
        "en": "Select Vendor to Negotiate",
        "vi": "Chọn Nhà cung cấp cần đàm phán",
    },
    "select_product": {
        "en": "Select Product",
        "vi": "Chọn Sản phẩm",
    },
    "current_terms": {
        "en": "Current Quoted Terms",
        "vi": "Điều khoản báo giá hiện tại",
    },
    "adjusted_price": {
        "en": "Adjusted Unit Price ($)",
        "vi": "Giá đơn vị điều chỉnh ($)",
    },
    "adjusted_cap": {
        "en": "Adjusted Capacity (units)",
        "vi": "Công suất điều chỉnh (đơn vị)",
    },
    "adjusted_moq": {
        "en": "Adjusted MOQ (units)",
        "vi": "MOQ điều chỉnh (đơn vị)",
    },
    "simulate_btn": {
        "en": "Simulate Re-solve",
        "vi": "Chạy giải mô phỏng",
    },
    "before_after_comparison": {
        "en": "Before vs After Negotiation Comparison",
        "vi": "So Sánh Kế Hoạch Trước & Sau Đàm Phán",
    },

    # --- Tab 5: Data ---
    "data_sheets_preview": {
        "en": "Data Sheets Inspector",
        "vi": "Kiểm Tra Các Bảng Dữ Liệu",
    },
    "upload_instruction": {
        "en": "Upload an Excel (.xlsx) file containing 4 sheets: vendor_list, product_list, BOM, quotation.",
        "vi": "Tải lên file Excel (.xlsx) bao gồm đủ 4 sheet: vendor_list, product_list, BOM, quotation.",
    },
    "upload_btn_label": {
        "en": "Drop or browse your Excel procurement file",
        "vi": "Kéo thả hoặc duyệt tìm file Excel thu mua của bạn",
    },
}


def t(key: str, lang: str = "vi") -> str:
    """Retrieve translated text for a given key and language code ('en' or 'vi')."""
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("en", key))
