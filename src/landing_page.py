"""
Project Landing Page & Comprehensive Methodology Walkthrough.
Introduces the Procurement Optimization project: problem statement, why optimization matters,
step-by-step workflow, mathematical formulation (MILP), duality theory & shadow prices, and empirical benchmarks.
"""

from __future__ import annotations

import streamlit as st


def render_landing_page(lang: str = "vi") -> None:
    """Render the full comprehensive project landing page."""
    
    # Custom CSS for landing page styling
    st.markdown(
        """
        <style>
        .landing-hero {
            background: linear-gradient(135deg, #0F6E56 0%, #064E3B 100%);
            color: white;
            padding: 40px 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(15, 110, 86, 0.2);
        }
        .landing-hero h1 {
            color: #FFFFFF !important;
            font-size: 2.3rem !important;
            font-weight: 800 !important;
            margin-bottom: 12px !important;
        }
        .landing-hero p {
            font-size: 1.15rem;
            color: #E2E8F0;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        .step-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-top: 4px solid #0F6E56;
            border-radius: 8px;
            padding: 20px;
            height: 100%;
            box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        }
        .step-num {
            font-size: 0.85rem;
            font-weight: 700;
            color: #0F6E56;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }
        .step-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 8px;
        }
        .step-desc {
            font-size: 0.9rem;
            color: #475569;
            line-height: 1.5;
        }
        .highlight-box {
            background-color: #F8FAFC;
            border-left: 4px solid #378ADD;
            padding: 16px 20px;
            border-radius: 0 8px 8px 0;
            margin: 20px 0;
        }
        .stat-badge {
            display: inline-block;
            background-color: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if lang == "vi":
        _render_vietnamese()
    else:
        _render_english()


def _render_vietnamese() -> None:
    # --- HERO BANNER ---
    st.markdown(
        """
        <div class="landing-hero">
            <span class="stat-badge">📦 OR-Tools MILP Solver</span>
            <span class="stat-badge">🔍 Dual Shadow Price (Fix-and-Relax)</span>
            <span class="stat-badge">🤖 Gemini 3.5 Flash CPO Copilot</span>
            <span class="stat-badge">🎲 Monte Carlo Feasibility Sweep</span>
            <h1>Tối Ưu Hóa Thu Mua & Phân Bổ Đơn Hàng Đa Nhà Cung Cấp</h1>
            <p>
                Từ bảng tính thủ công rời rạc đến quyết định thu mua tối ưu toàn diện. 
                Hệ thống ứng dụng <b>Quy hoạch tuyến tính nguyên hỗn hợp (MILP)</b> và <b>Phân tích Đối ngẫu & Shadow Price</b> 
                để giải quyết bài toán chọn nhà cung cấp, cắt giảm chi phí, kiểm soát rủi ro giao hàng và tối ưu hóa đàm phán hợp đồng.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CTA Button
    c_btn1, c_btn2, _ = st.columns([1.5, 1.5, 3])
    with c_btn1:
        if st.button("📊 Mở Bảng Điều Khiển Tối Ưu Hóa (Dashboard)", type="primary", use_container_width=True):
            st.session_state["view_mode"] = "dashboard"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SECTION 1: BỐI CẢNH & NỖI ĐAU NGHIỆP VỤ ---
    st.header("1. Tại Sao Cần Tối Ưu Hóa Toán Học Trong Thu Mua?")
    st.markdown(
        """
        Trong sản xuất và chuỗi cung ứng, việc thu mua vật tư theo **Định mức nguyên vật liệu (Bill of Materials - BOM)** 
        cho một chu kỳ sản xuất là bài toán tổ hợp phức tạp mà phần lớn các doanh nghiệp vẫn đang giải quyết bằng **Excel và cảm tính con người**.
        """
    )

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Vấn đề 01</div>
                <div class="step-title">Bẫy Số Lượng Đặt Tối Thiểu (MOQ)</div>
                <div class="step-desc">
                    Nhà cung cấp giá rẻ thường áp đặt MOQ lớn. Người mua hàng thủ công dễ rơi vào bẫy: 
                    hoặc mua vượt quá nhu cầu thực tế (lãng phí vốn lưu động), hoặc bỏ qua NCC giá rẻ vì sợ vượt trần định mức BOM.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_p2:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Vấn đề 02</div>
                <div class="step-title">Giới Hạn Năng Lực Sản Xuất (Capacity)</div>
                <div class="step-desc">
                    Một nhà cung cấp không thể gánh toàn bộ đơn hàng. Việc chia tách đơn hàng (Split-sourcing) cho 2 hay 3 nhà cung cấp 
                    sao cho vừa thỏa mãn MOQ của từng bên, vừa không vượt quá công suất là bài toán phi lồi mà bảng tính không thể giải tối ưu.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_p3:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Vấn đề 03</div>
                <div class="step-title">Chi Phí Ẩn & Rủi Ro Giao Hàng</div>
                <div class="step-desc">
                    Chia nhỏ đơn hàng cho nhiều NCC làm tăng phí quản lý đơn hàng (50 - 100 USD/PO). 
                    Đồng thời, chọn NCC giá rẻ nhưng thời gian giao hàng (Lead time) dài hoặc từ nước ngoài tiềm ẩn nguy cơ đình trệ cả dây chuyền.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="highlight-box">
            <b>💥 Sự bùng nổ tổ hợp (Combinatorial Explosion):</b> Với <b>66 sản phẩm</b>, <b>23 nhà cung cấp</b> 
            và <b>323 báo giá cạnh tranh</b>, số lượng cách phân chia đơn hàng khả thi lên tới hàng tỷ tỷ phương án. 
            Phương pháp truyền thống <i>"chọn nhà cung cấp rẻ nhất trước (Greedy Heuristic)"</i> làm thất thoát tới 
            <b>8.91% chi phí (gần 50,000 USD)</b> và làm tăng rủi ro giao hàng thêm <b>27.7%</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # --- SECTION 2: QUY TRÌNH HOẠT ĐỘNG 5 BƯỚC ---
    st.header("2. Quy Trình 5 Bước Của Hệ Thống Tối Ưu Hóa")
    st.markdown("Hệ thống vận hành như một quy trình khép kín từ dữ liệu thô đến đề xuất hành động thực chiến:")

    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Bước 01</div>
                <div class="step-title">Tiền Xử Lý Dữ Liệu</div>
                <div class="step-desc">Nạp 4 bảng: Nhà cung cấp, Sản phẩm, Định mức BOM và Báo giá. Chuẩn hóa thang đo đơn giá và thời gian giao hàng.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Bước 02</div>
                <div class="step-title">Mô Hình Hóa MILP</div>
                <div class="step-desc">Thiết lập hệ biến số nguyên, nhị phân và các ràng buộc kỹ thuật (MOQ, Capacity, Trần BOM, Phí PO overhead).</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Bước 03</div>
                <div class="step-title">Giải Toán (SCIP Solver)</div>
                <div class="step-desc">Giải đồng thời 3 chiến lược: Tối ưu chi phí, Cân bằng rủi ro, và Duy trì toàn bộ quan hệ nhà cung cấp trong < 0.35s.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s4:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Bước 04</div>
                <div class="step-title">Phân Tích Đối Ngẫu</div>
                <div class="step-desc">Áp dụng Fix-and-Relax bằng solver GLOP để trích xuất Shadow Price và chi phí cơ hội đàm phán.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s5:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Bước 05</div>
                <div class="step-title">AI CPO & Sandbox</div>
                <div class="step-desc">Thẩm định Monte Carlo, tạo Executive Briefing bằng Gemini 3.5 Flash và giả định đàm phán What-If tức thời.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # --- SECTION 3: MÔ HÌNH TOÁN HỌC CHI TIẾT ---
    st.header("3. Chi Tiết Thuật Toán & Công Thức Toán Học (MILP Formulation)")
    st.markdown(
        """
        Bài toán được chuẩn hóa dưới dạng **Quy hoạch tuyến tính nguyên hỗn hợp (Mixed-Integer Linear Programming - MILP)** 
        sử dụng thư viện **Google OR-Tools** với backend **SCIP**:
        """
    )

    t_math1, t_math2, t_math3 = st.tabs(["Biến Quyết Định", "Hệ Ràng Buộc Kỹ Thuật", "Hàm Mục Tiêu Đa Chiến Lược"])

    with t_math1:
        st.markdown(
            r"""
            Hệ thống định nghĩa 3 nhóm biến quyết định chính:
            - **Biến sản lượng mua:** $x_{p,v} \ge 0$ là số lượng sản phẩm $p$ được phân bổ đặt mua từ nhà cung cấp $v$ (biến số nguyên không âm).
            - **Biến nhị phân đặt hàng:** $y_{p,v} \in \{0, 1\}$ chỉ thị việc có đặt hàng hay không ($y_{p,v} = 1$ nếu có mua sản phẩm $p$ từ NCC $v$, ngược lại bằng 0).
            - **Biến nhị phân kích hoạt NCC:** $z_v \in \{0, 1\}$ chỉ thị việc kích hoạt nhà cung cấp ($z_v = 1$ nếu NCC $v$ nhận ít nhất một đơn hàng cho bất kỳ sản phẩm nào).
            """
        )

    with t_math2:
        st.markdown(r"**1. Ràng buộc liên kết MOQ & Công suất (MOQ & Capacity Linking):**")
        st.latex(r"\text{MOQ}_{p,v} \cdot y_{p,v} \le x_{p,v} \le \text{Cap}_{p,v} \cdot y_{p,v} \quad \forall (p, v)")
        st.markdown(
            r"""
            *Ý nghĩa nghiệp vụ:* Nhà cung cấp $v$ hoặc không cung ứng gì ($y_{p,v}=0 \Rightarrow x_{p,v}=0$), 
            hoặc nếu được kích hoạt ($y_{p,v}=1$) thì sản lượng đặt mua phải nằm giữa số lượng đặt tối thiểu (MOQ) và trần công suất tối đa ($\text{Cap}_{p,v}$).
            """
        )

        st.markdown(r"**2. Ràng buộc đáp ứng định mức BOM & Dung sai cho phép (BOM Coverage & Tolerance):**")
        st.latex(r"\text{BOM}_{p} \le \sum_{v} x_{p,v} \le \text{BOM}_{p} \cdot (1 + \tau) \quad \forall p")
        st.markdown(
            r"""
            *Ý nghĩa nghiệp vụ:* Tổng sản lượng mua từ tất cả NCC cho từng sản phẩm $p$ phải đáp ứng đủ 100% định mức BOM, 
            và không được vượt quá trần dung sai $\tau$ (mặc định $+8\%$) để tránh tồn kho dư thừa do ràng buộc MOQ của NCC.
            """
        )

        st.markdown(r"**3. Ràng buộc kích hoạt nhà cung cấp & Phí PO (Vendor Activation Linking):**")
        st.latex(r"z_v \ge y_{p,v} \quad \forall (p, v)")
        st.latex(r"\sum_{p} y_{p,v} \ge z_v \quad \forall v")
        st.markdown(
            r"""
            *Ý nghĩa nghiệp vụ:* Biến nhị phân $z_v$ tự động bật lên 1 ngay khi NCC $v$ được phân bổ ít nhất 1 dòng sản phẩm, 
            kích hoạt chi phí quản lý hành chính đơn hàng ($\text{PO overhead}$).
            """
        )

    with t_math3:
        st.markdown(r"**Chiến lược 1: Tối ưu chi phí thuần túy (Cost-optimal)**")
        st.latex(r"\min \quad \sum_{p,v} c_{p,v} \cdot x_{p,v} + \sum_{v} f_v \cdot z_v")
        st.markdown(r"*Mục tiêu:* Giảm thiểu tối đa số tiền mặt chi trả ($c_{p,v}$ là đơn giá mua hàng, $f_v$ là phí quản lý PO: 50 USD trong nước, 100 USD nước ngoài).")

        st.markdown(r"**Chiến lược 2: Cân bằng rủi ro (Risk-balanced)**")
        st.latex(r"\min \quad \sum_{p,v} r_{p,v} \cdot x_{p,v} + \sum_{v} \lambda f_v \cdot z_v")
        st.markdown(r"Trong đó hệ số rủi ro $r_{p,v}$ là hàm kết hợp chuẩn hóa giữa đơn giá và thời gian giao hàng (Lead time):")
        st.latex(r"r_{p,v} = 0.40 \cdot p^{\text{norm}}_{p,v} + 0.60 \cdot lt^{\text{norm}}_v")
        st.markdown(r"*Mặc định:* $40\%$ trọng số đơn giá $+ 60\%$ trọng số Lead time nhằm bảo vệ dây chuyền sản xuất khỏi nguy cơ đứt gãy.")

        st.markdown(r"**Chiến lược 3: Duy trì quan hệ đối tác (Relationship-preserving)**")
        st.latex(r"z_v = 1 \quad \forall v")
        st.markdown(r"*Mục tiêu:* Bắt buộc toàn bộ nhà cung cấp trong danh mục báo giá đều phải nhận được ít nhất một đơn hàng, giữ ấm quan hệ hợp tác dài hạn.")

    st.markdown("---")

    # --- SECTION 4: GIẢI THÍCH CHI TIẾT ĐỐI NGẪU & SHADOW PRICE ---
    st.header("4. Bản Chất Lý Thuyết Đối Ngẫu & Phân Tích Shadow Price")
    st.markdown(
        """
        Phần này giải thích chi tiết **Lý thuyết Đối ngẫu (Duality Theory)** là gì, 
        tại sao nó lại là nền tảng của kinh tế học lượng hóa, và **ứng dụng thực chiến như thế nào** trong đàm phán thu mua:
        """
    )

    # 4.1 Đối ngẫu là gì?
    with st.container(border=True):
        st.subheader("4.1. Đối Ngẫu Là Gì? (Hai Mặt Của Một Bài Toán Kinh Doanh)")
        st.markdown(
            r"""
            Trong toán học tối ưu và kinh tế học (đoạt giải Nobel Kinh tế năm 1975 của Kantorovich & Koopmans), 
            mọi bài toán ra quyết định kinh doanh luôn tồn tại **hai góc nhìn đối xứng song song**:
            """
        )
        
        c_p, c_d = st.columns(2)
        with c_p:
            st.markdown(
                r"""
                **1. Mặt Thuận — Bài toán gốc (Primal Problem):**  
                *Góc nhìn Sản Lượng & Phân Bổ Vật Lý*
                - **Câu hỏi cốt lõi:** *"Mua cái gì? Mua từ ai? Mỗi người bao nhiêu đơn vị?"*
                - **Không gian tìm kiếm:** Số lượng hàng hóa cụ thể ($x_{p,v}$), quyết định ký hợp đồng ($y, z$).
                - **Mục tiêu:** Tối thiểu hóa tổng chi phí tiền mặt phải chi: $\min \text{Total Cost}$.
                """
            )
        with c_d:
            st.markdown(
                r"""
                **2. Mặt Nghịch — Bài toán đối ngẫu (Dual Problem):**  
                *Góc nhìn Định Giá Tài Nguyên & Chi Phí Cơ Hội*
                - **Câu hỏi cốt lõi:** *"Mỗi điều kiện ràng buộc trong hệ thống (công suất nhà máy, yêu cầu BOM) đang có giá trị kinh tế ẩn (Shadow Value) là bao nhiêu?"*
                - **Không gian tìm kiếm:** Giá trị kinh tế của từng đơn vị ràng buộc (Biến đối ngẫu $\lambda_i \ge 0$).
                - **Mục tiêu:** Tối đa hóa giá trị quy đổi của các tài nguyên khan hiếm.
                """
            )

        st.markdown(
            r"""
            > **Tại sao gọi là "Đối ngẫu"?**  
            > *"Đối"* nghĩa là đối xứng, đối ứng; *"Ngẫu"* nghĩa là cặp đôi luôn đi liền với nhau.  
            > Cứ mỗi một **điều kiện ràng buộc kỹ thuật** trong bài toán gốc (ví dụ: công suất trần của NCC, định mức BOM tối thiểu) 
            > sẽ sinh ra tương ứng một **biến số kinh tế** trong bài toán đối ngẫu — được gọi là **Biến đối ngẫu (Dual Variable)** hay **Shadow Price**.
            """
        )

    # 4.2 Định nghĩa toán học của Shadow Price
    with st.container(border=True):
        st.subheader("4.2. Ý Nghĩa Kinh Tế Của Biến Đối Ngẫu & Shadow Price")
        st.markdown(
            r"""
            Trong bài toán thu mua tối thiểu hóa chi phí, biến đối ngẫu ứng với một ràng buộc giới hạn $C$ chính là **Shadow Price**:
            """
        )
        st.latex(r"\lambda = -\frac{\partial \, \text{Total Cost}}{\partial \, \text{Constraint Limit}}")
        st.markdown(
            r"""
            - **Định nghĩa nôm na dễ hiểu:** Shadow Price là câu trả lời chính xác cho câu hỏi:  
              *"Nếu ai đó nới lỏng thêm đúng 1 đơn vị của điều kiện ràng buộc này, tổng chi phí của doanh nghiệp sẽ giảm được bao nhiêu tiền?"*
            - **Ý nghĩa biên (Marginal Value):** Nó phản ánh mức độ nhạy cảm của toàn bộ chuỗi cung ứng trước sự khan hiếm của từng nhà xưởng, từng hợp đồng và từng dòng sản phẩm.
            """
        )

    # 4.3 Ứng dụng thực chiến trong bài toán thu mua này
    with st.container(border=True):
        st.subheader("4.3. Ứng Dụng Trong Bài Toán Thu Mua Này Như Thế Nào?")
        st.markdown("Hệ thống ứng dụng lý thuyết đối ngẫu vào 3 nghiệp vụ đàm phán then chốt:")

        st.markdown(
            r"""
            #### Ứng dụng 1: Đàm phán mở rộng công suất nhà cung cấp (Capacity Shadow Price)
            - **Tình huống thực tế:** Khi giải tối ưu trên 323 báo giá, mô hình phát hiện sản phẩm `p_1` tại nhà cung cấp `v_10` có **Shadow Price = 772.50 USD/đơn vị**.
            - **Bản chất kinh tế:** NCC `v_10` có giá bán cực tốt cho sản phẩm `p_1`, nhưng công suất tối đa của họ bị kịch trần. Doanh nghiệp buộc phải mua phần còn thiếu từ NCC khác đắt hơn nhiều. Nếu NCC `v_10` mở thêm được 1 đơn vị công suất, doanh nghiệp tiết kiệm ngay **772.50 USD**.
            - **Chiến thuật đàm phán của Giám đốc Thu mua (CPO):**
              - Con số **772.50 USD/đơn vị** chính là mức **Willingness-to-Pay (Trần ngân sách đàm phán tối đa)** của doanh nghiệp.
              - Thay vì chỉ ép giá một cách truyền thống, CPO có thể chủ động đề xuất gói hợp tác chiến lược:  
                *"Chúng tôi sẵn sàng trả thêm 300 USD/đơn vị phụ phí tăng ca ca đêm hoặc tài trợ 5,000 USD tiền khuôn đúc để quý NCC tăng thêm 10 đơn vị công suất cho sản phẩm này."*
              - **Kết quả đôi bên cùng có lợi (Win-Win):**
                - Nhà cung cấp kiếm thêm lợi nhuận từ tiền phụ phí/tài trợ.
                - Doanh nghiệp vẫn tiết kiệm ròng: $7,725 - 3,000 = 4,725$ USD chi phí mua hàng!

            #### Ứng dụng 2: Đánh giá độ nhạy Định mức BOM & Trần Dung Sai (BOM Sensitivity)
            - **Biến đối ngẫu nhu cầu BOM ($\text{BOM}_p$):** Cho biết nếu xưởng sản xuất cần thêm 1 đơn vị linh kiện $p$, tổng chi phí mua hàng biên sẽ tăng thêm bao nhiêu tiền. Thông tin này giúp báo giá chính xác cho các đơn hàng B2B đột xuất mà không bị lỗ chi phí vật tư.
            - **Biến đối ngẫu dung sai trần ($\tau$):** Cho biết nếu doanh nghiệp cho phép nhận thêm hàng thừa do MOQ (+10% thay vì +8%), chi phí mua sắm tổng thể sẽ giảm bao nhiêu USD nhờ tận dụng được các mức chiết khấu số lượng lớn.

            #### Ứng dụng 3: Định giá cơ hội cho Nhà cung cấp bị loại (Excluded Vendor Opportunity Cost)
            - **Tình huống thực tế:** Có những nhà cung cấp không trúng bất kỳ đơn hàng nào trong kế hoạch tối ưu ($z_v = 0$).
            - **Cách tính:** Hệ thống cưỡng chế kích hoạt NCC dự phòng đó ($z_v = 1$) và giải lại bài toán.
            """
        )
        st.latex(r"\Delta C_v = \text{Cost}(z_v = 1) - \text{Cost}^*")
        st.markdown(
            r"""
            - **Đòn bẩy đàm phán:** $\Delta C_v$ chính là mức chênh lệch chi phí (Hurdle Rate).  
              Chuyên viên thu mua có thể gửi phản hồi trực tiếp cho NCC dự phòng:  
              *"Báo giá của quý vị hiện đang cao hơn phương án tối ưu của chúng tôi $\Delta C_v$ USD. Nếu quý vị muốn có đơn hàng trong đợt này, báo giá tổng thể cần được chiết khấu ít nhất đúng số tiền đó."*
            """
        )

    # 4.4 Hai định lý nền tảng
    with st.container(border=True):
        st.subheader("4.4. Hai Định Lý Nền Tảng: Strong Duality & Complementary Slackness")
        
        st.markdown(r"**1. Định Lý Đối Ngẫu Mạnh (Strong Duality Theorem):**")
        st.latex(r"\min Z_{\text{Primal}} = \max W_{\text{Dual}}")
        st.markdown(
            r"""
            Tại điểm tối ưu toàn cục, chi phí của bài toán gốc và giá trị của bài toán đối ngẫu trùng khít hoàn toàn. 
            Điều này chứng minh: *Toàn bộ số tiền chi cho việc mua hàng có thể được quy đổi và giải thích trọn vẹn thành giá trị kinh tế nội tại của các ràng buộc tài nguyên.*
            """
        )

        st.markdown(r"**2. Nguyên Lý Bù Trừ (Complementary Slackness Theorem):**")
        st.latex(r"\lambda_i \cdot s_i = 0 \quad \forall i")
        st.markdown(
            r"""
            Trong đó $s_i$ là độ dư thừa (khoảng cách đến giới hạn trần) của ràng buộc thứ $i$:
            - **Trường hợp 1 ($s_i > 0$ — Ràng buộc lỏng, còn dư công suất):**  
              Nhà cung cấp có công suất 1,000 đơn vị nhưng kế hoạch tối ưu chỉ mua 600 đơn vị (dư 400 đơn vị).  
              Theo nguyên lý bù trừ, bắt buộc $\lambda_i = 0 \Rightarrow \text{Shadow Price} = 0$.  
              *Kết luận thực chiến:* NCC này đang thừa công suất, việc đàm phán xin thêm công suất mang lại **0 USD giá trị kinh tế**, không cần bận tâm.
            - **Trường hợp 2 ($s_i = 0$ — Ràng buộc chạm trần, Binding Bottleneck):**  
              Toàn bộ công suất của NCC rẻ nhất đã bị mua sạch 100%, buộc hệ thống phải chuyển sang mua từ NCC đắt hơn.  
              Khi đó $\lambda_i > 0 \Rightarrow \text{Shadow Price} > 0$.  
              *Kết luận thực chiến:* Đây chính là **Nút thắt cổ chai vàng (Golden Bottleneck)** cần ưu tiên số 1 trên bàn đàm phán hợp đồng.
            """
        )

    # 4.5 Thách thức Non-convexity trong MILP & Fix-and-Relax
    with st.container(border=True):
        st.subheader("4.5. Thách Thức Non-Convexity Trong MILP & Kỹ Thuật Fix-and-Relax")
        st.markdown(
            r"""
            **Thách thức toán học:**  
            Lý thuyết đối ngẫu cổ điển đòi hỏi miền nghiệm phải là tập lồi liên tục (Convex Set).  
            Tuy nhiên, bài toán thu mua thực tế có các biến nhị phân ($y_{p,v}, z_v \in \{0, 1\}$) và biến số nguyên ($x_{p,v} \in \mathbb{Z}^+$). 
            Các biến này khiến không gian nghiệm bị chia cắt rời rạc (Non-convex) và tạo ra **Khoảng trống đối ngẫu (Duality Gap)**. 
            Vì vậy, các solver MILP thông thường (như SCIP) **không thể xuất trực tiếp biến đối ngẫu**.
            """
        )
        st.markdown(
            r"""
            **Giải pháp kỹ thuật Fix-and-Relax (GLOP Dual Relaxation):**
            1. **Bước 1 (Global MILP Solve):** Dùng solver **SCIP** giải bài toán MILP đầy đủ để tìm nghiệm nguyên và cấu hình nhị phân tối ưu toàn cục $(x^*, y^*, z^*)$.
            2. **Bước 2 (Fix Binary Decisions):** Cố định toàn bộ các biến nhị phân tại giá trị tối ưu: $y_{p,v} \equiv y_{p,v}^*$, $z_v \equiv z_v^*$. Các quyết định chọn NCC nào đã được chốt và trở thành hằng số.
            3. **Bước 3 (Continuous LP Relaxation):** Nới lỏng biến số lượng $x \ge 0$ sang miền số thực liên tục. Lúc này bài toán trở thành một bài toán Quy hoạch tuyến tính (Continuous LP) hoàn toàn lồi trên không gian phân bổ sản lượng.
            4. **Bước 4 (GLOP Dual Extraction):** Giải bài toán LP liên tục này bằng solver chuyên dụng **Google GLOP (Google Linear Optimization Program)**. GLOP trích xuất chuẩn xác các biến đối ngẫu (Shadow Price) của từng ràng buộc công suất và định mức BOM tại điểm cân bằng tối ưu.
            """
        )

    st.markdown("---")

    # --- SECTION 5: KẾT QUẢ THỰC NGHIỆM ---
    st.header("5. Hiệu Quả Thực Nghiệm & So Sánh Đối Đầu")
    st.markdown(
        """
        Đánh giá hiệu quả giữa **Mô hình Tối ưu hóa MILP (Google OR-Tools)** và 
        **Phương pháp Thủ công truyền thống (Greedy Heuristic)** trên bộ dữ liệu mua hàng gồm 
        **66 sản phẩm, 23 nhà cung cấp và 323 báo giá cạnh tranh**:
        """
    )

    res_table = {
        "Chỉ tiêu đánh giá": [
            "Tổng chi phí mua sắm (Total Cost)",
            "Tiền mua hàng thực tế (Purchase Spend)",
            "Phí quản lý đơn hàng (PO Overhead)",
            "Mức tiết kiệm chi phí ròng",
            "Điểm rủi ro thời gian giao hàng",
            "Số nhà cung cấp kích hoạt",
            "Phát hiện nút thắt công suất (Shadow Price)",
            "Thời gian giải toán"
        ],
        "Phương pháp Thủ công (Greedy)": [
            "559,711 USD",
            "558,111 USD",
            "1,600 USD (23 NCC)",
            "Mốc cơ sở (0%)",
            "10,968.8 điểm (Rủi ro cao)",
            "23 nhà cung cấp (Kích hoạt rời rạc)",
            "0 điểm nghẽn (Mù thông tin hoàn toàn)",
            "Nhiều giờ tính toán thủ công trên Excel"
        ],
        "Tối ưu hóa MILP (Google OR-Tools)": [
            "508,369 USD",
            "506,769 USD",
            "1,600 USD (23 NCC)",
            "+51,341 USD (+9.17%)",
            "10,252.8 điểm (Chi phí) / 7,409.6 điểm (Rủi ro)",
            "23 nhà cung cấp (Phối hợp công suất toàn cục)",
            "6 nút thắt (Top: 772.50 USD/đv)",
            "< 0.35 giây"
        ],
        "Giá trị mang lại cho doanh nghiệp": [
            "Cắt giảm trực tiếp hơn 51,000 USD dòng tiền chi tiêu",
            "Tối ưu hóa từng đồng vốn lưu động mua sắm",
            "Tính đủ phí PO thực tế, loại bỏ so sánh khập khiễng",
            "Hiệu quả vượt trội so với quy tắc ngón tay cái thủ công",
            "Chủ động bảo vệ dây chuyền khỏi nguy cơ chậm giao hàng",
            "Đa dạng hóa danh mục nguồn cung tối ưu toàn diện",
            "Xác định chính xác trần đàm phán hợp đồng (Shadow Price)",
            "Cho phép mô phỏng giả định What-If theo thời gian thực"
        ]
    }
    st.table(res_table)

    st.markdown(
        """
        <div class="highlight-box">
            <b>💡 Kết luận rút ra:</b> Trong môi trường thu mua đa nguồn cung cạnh tranh, 
            mô hình <b>MILP vượt trội hoàn toàn phương pháp thủ công, mang lại khoản tiết kiệm ròng lên tới 9.17% (51,341 USD)</b> 
            đồng thời <b>giảm thiểu rủi ro giao hàng tới 32.5%</b> nhờ khả năng phối hợp đồng thời hàng trăm ràng buộc MOQ và trần công suất phức tạp.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- CASE STUDY: VÌ SAO GREEDY CŨNG CHỌN 23 NCC NHƯNG LẠI ĐẮT HƠN $51,341? ---
    st.markdown("### 🔍 Case Study Chuyên Sâu: Tại sao cùng dùng 23 NCC nhưng MILP lại rẻ hơn Greedy tới $51,341 USD?")
    st.markdown(
        r"""
        Một câu hỏi chiến lược kinh điển trong quản trị thu mua: **"Nếu thuật toán thủ công (Greedy) cũng kích hoạt đầy đủ cả 23 nhà cung cấp và mua cùng tổng lượng 32,015 đơn vị hàng hóa, tại sao MILP lại tiết kiệm được hơn 51,000 USD tiền mặt?"**

        Dưới đây là lời giải chi tiết từ bản chất toán học tổ hợp:
        """
    )

    cs_c1, cs_c2 = st.columns(2)
    with cs_c1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">❓</div>
                <div class="feature-title">1. Tại sao Greedy chọn hết cả 23 NCC?</div>
                <div class="feature-desc">
                    Trong bộ dữ liệu gồm <b>66 sản phẩm</b> và <b>323 báo giá</b>, mỗi nhà cung cấp trong số 23 NCC đều có lợi thế cạnh tranh riêng và <b>sở hữu ít nhất 1 mã hàng có đơn giá rẻ nhất thị trường (Top 1 Cheapest)</b>:
                    <ul>
                        <li><code>VN-VD10</code> rẻ nhất ở 6 sản phẩm.</li>
                        <li><code>VN-VD12</code> rẻ nhất ở 5 sản phẩm.</li>
                        <li><code>VN-VD01</code>, <code>VN-VD11</code>, <code>VN-VD18</code>, <code>VN-VD22</code> rẻ nhất ở 4 sản phẩm mỗi NCC.</li>
                        <li>Ngay cả các NCC nhỏ như <code>VN-VD07</code>, <code>VN-VD21</code> cũng có 1 sản phẩm rẻ nhất.</li>
                    </ul>
                    Do Greedy đi nhặt đơn giá rẻ nhất theo từng mã hàng độc lập từ P01 đến P66, <b>toàn bộ 23 NCC đều có ít nhất 1 lần trúng thầu</b> và cùng phát sinh <b>$1,600 PO Overhead</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cs_c2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">⚠️</div>
                <div class="feature-title">2. "Bẫy MOQ & Trần Dung Sai" của Greedy</div>
                <div class="feature-desc">
                    Greedy chỉ nhìn thiển cận (myopic) vào từng mã hàng mà không có khả năng nhìn bức tranh tổng thể:
                    <ul>
                        <li>Khi NCC rẻ nhất bị đầy công suất, Greedy phải tìm NCC rẻ nhì.</li>
                        <li>Nếu NCC rẻ nhì có <b>MOQ lớn</b> khiến tổng lượng mua vượt trần dung sai BOM (<code>target_max</code>), Greedy <b>bắt buộc phải bỏ qua NCC rẻ nhì</b> và chấp nhận mua từ NCC đắt hơn rất nhiều có MOQ nhỏ hơn!</li>
                        <li>Ngược lại, <b>MILP điều phối biến số đồng thời</b>: giảm bớt một phần lượng mua ở NCC 1 để vừa vặn kích hoạt MOQ ở NCC 2, giữ cho toàn bộ đơn hàng ở mức giá rẻ nhất khả thi.</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        r"""
        #### 📌 Minh chứng thực tế từ dữ liệu: Mã hàng `VN-MT056` (Nhu cầu BOM = 30 đơn vị)
        Mã hàng `VN-MT056` có 4 nhà cung cấp chào giá cạnh tranh:
        * **`VN-VD18`**: Đơn giá **$2,080** *(rẻ nhất)*, Công suất = 13 đv, MOQ = 6 đv.
        * **`VN-VD19`**: Đơn giá **$2,496** *(rẻ nhì)*, Công suất = 45 đv, **MOQ = 21 đv**.
        * **`VN-VD11`**: Đơn giá **$3,200** *(đắt)*, Công suất = 36 đv, MOQ = 4 đv.
        * **`VN-VD22`**: Đơn giá **$4,000** *(rất đắt)*, Công suất = 45 đv, MOQ = 1 đv.
        """
    )

    cs_table = {
        "Chiến lược phân bổ": [
            "Phương pháp Thủ công (Greedy Heuristic)",
            "Mô hình Tối ưu hóa MILP (OR-Tools)",
            "Chênh lệch hiệu quả (Optimization Gain)"
        ],
        "Quyết định mua sắm cho mã VN-MT056": [
            "Mua kịch trần 13 đv từ VD18 ($2,080). Còn thiếu 17 đv. Do VD19 đòi MOQ 21 (13 + 21 = 34 > trần dung sai 32.4) nên Greedy buộc phải bỏ qua VD19 và mua 17 đv từ VD11 ($3,200).",
            "MILP điều phối đồng thời: mua 9 đv từ VD18 ($2,080) và mua đúng 21 đv từ VD19 ($2,496, khớp vừa khít MOQ 21). Tổng sản lượng đúng 30 đv.",
            "MILP tránh được việc bị ép mua giá $3,200 nhờ kỹ thuật chia tỷ lệ linh hoạt giữa 2 nhà cung cấp giá rẻ."
        ],
        "Tổng chi phí mua mã này": [
            "13 × $2,080 + 17 × $3,200 = 81,440 USD",
            "9 × $2,080 + 21 × $2,496 = 71,136 USD",
            "Tiết kiệm ngay 10,304 USD (-12.6%) trên 1 mã duy nhất!"
        ]
    }
    st.table(cs_table)

    st.markdown(
        r"""
        > **Tổng kết:** Trên toàn bộ dự án, có tới **59 / 66 mã hàng** xảy ra hiện tượng phối hợp tối ưu như mã `VN-MT056`. 
        > Đây chính là lý do vì sao **MILP tiết kiệm được tới \$51,341 USD** so với người mua hàng kinh nghiệm chọn theo cảm tính, 
        > dù cả hai phương án đều kích hoạt đủ 23 nhà cung cấp!
        """
    )

    # Bottom CTA
    b_col1, b_col2, _ = st.columns([2, 2, 2])
    with b_col1:
        if st.button("🚀 Bắt Đầu Trải Nghiệm Interactive Dashboard", type="primary", use_container_width=True):
            st.session_state["view_mode"] = "dashboard"
            st.rerun()


def _render_english() -> None:
    # --- HERO BANNER ---
    st.markdown(
        """
        <div class="landing-hero">
            <span class="stat-badge">📦 OR-Tools MILP Solver</span>
            <span class="stat-badge">🔍 Dual Shadow Price (Fix-and-Relax)</span>
            <span class="stat-badge">🤖 Gemini 3.5 Flash CPO Copilot</span>
            <span class="stat-badge">🎲 Monte Carlo Feasibility Sweep</span>
            <h1>Supplier Selection & Dynamic Order Allocation AI</h1>
            <p>
                From intuition-driven spreadsheets to mathematically proven global optimums. 
                Leverages <b>Mixed-Integer Linear Programming (MILP)</b> and <b>Duality Theory & Shadow Price Sensitivity</b> 
                to cut procurement spend, de-risk lead-time disruptions, and arm category managers with data-backed negotiation power.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CTA Button
    c_btn1, c_btn2, _ = st.columns([1.5, 1.5, 3])
    with c_btn1:
        if st.button("📊 Open Interactive Optimization Dashboard", type="primary", use_container_width=True):
            st.session_state["view_mode"] = "dashboard"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SECTION 1: THE PROCUREMENT PROBLEM ---
    st.header("1. Why Mathematical Optimization in Procurement?")
    st.markdown(
        """
        Fulfilling a Bill of Materials (BOM) across dozens of products and suppliers is a massive combinatorial challenge. 
        Most supply chain teams still rely on spreadsheets and greedy heuristics (*"buy from the cheapest quote first"*).
        """
    )

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Pain Point 01</div>
                <div class="step-title">The MOQ Trap</div>
                <div class="step-desc">
                    Discounted suppliers mandate large Minimum Order Quantities (MOQ). Spreadsheet buyers either over-buy 
                    (wasting working capital) or abandon discounts due to BOM over-delivery caps.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_p2:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Pain Point 02</div>
                <div class="step-title">Capacity & Split-Sourcing</div>
                <div class="step-desc">
                    No single vendor can fulfill the entire BOM. Intelligently splitting purchase volumes across vendors 
                    under non-convex MOQ and capacity bounds is mathematically impossible with manual sorting.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_p3:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Pain Point 03</div>
                <div class="step-title">Hidden PO Overhead & Lead Times</div>
                <div class="step-desc">
                    Fragmenting orders across too many vendors incurs 50 - 100 USD in administrative PO fees per supplier. 
                    Meanwhile, overseas cost savings are often wiped out by severe shipment delays.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="highlight-box">
            <b>💥 Combinatorial Explosion:</b> With <b>66 products</b>, <b>23 suppliers</b>, 
            and <b>323 competitive quotations</b>, the number of valid allocation plans is in the billions. 
            Greedy heuristics routinely leave <b>8.91% cash savings (~50,000 USD) on the table</b> 
            while incurring <b>27.7% higher delivery risk</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # --- SECTION 2: END-TO-END WORKFLOW ---
    st.header("2. End-to-End System Workflow")
    st.markdown("How raw quotation spreadsheets transform into executive procurement strategies:")

    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Step 01</div>
                <div class="step-title">Ingest & Clean</div>
                <div class="step-desc">Load 4 Excel sheets: vendors, products, BOM, and quotations. Cross-normalize prices and lead times.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Step 02</div>
                <div class="step-title">MILP Formulation</div>
                <div class="step-desc">Establish integer purchase quantities, binary order flags, and linking constraints (MOQ, Capacity, PO fees).</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Step 03</div>
                <div class="step-title">OR-Tools Solver</div>
                <div class="step-desc">Simultaneously solve Cost-optimal, Risk-balanced, and Relationship-preserving models in under 0.35s.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s4:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Step 04</div>
                <div class="step-title">Fix-and-Relax Duals</div>
                <div class="step-desc">Solve continuous LP relaxation via GLOP to extract economic shadow prices (USD/unit capacity saved).</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s5:
        st.markdown(
            """
            <div class="step-card">
                <div class="step-num">Step 05</div>
                <div class="step-title">AI CPO & Sandbox</div>
                <div class="step-desc">Validate against 100 random feasible plans, synthesize CPO briefing via Gemini 3.5 Flash, and test What-Ifs.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # --- SECTION 3: MATHEMATICAL FORMULATION ---
    st.header("3. Mathematical Formulation (Mixed-Integer Linear Program)")
    st.markdown("Formal mathematical specification solved via Google OR-Tools (SCIP backend):")

    t_math1, t_math2, t_math3 = st.tabs(["Decision Variables", "Core Constraints", "Multi-Strategy Objectives"])

    with t_math1:
        st.markdown(
            r"""
            Three primary variable families model the allocation space:
            - **Purchase quantity:** $x_{p,v} \ge 0$ is the non-negative integer quantity of product $p$ purchased from supplier $v$.
            - **Order indicator:** $y_{p,v} \in \{0, 1\}$ is a binary flag ($1$ if an order for product $p$ is placed with vendor $v$, 0 otherwise).
            - **Vendor activation:** $z_v \in \{0, 1\}$ is a binary flag ($1$ if vendor $v$ receives at least one order across the entire BOM).
            """
        )

    with t_math2:
        st.markdown(r"**1. MOQ & Capacity Linking:**")
        st.latex(r"\text{MOQ}_{p,v} \cdot y_{p,v} \le x_{p,v} \le \text{Cap}_{p,v} \cdot y_{p,v} \quad \forall (p, v)")
        st.markdown(r"*Meaning:* Vendor $v$ either sells nothing ($y_{p,v}=0 \Rightarrow x_{p,v}=0$) or must supply within its MOQ and capacity boundaries.")

        st.markdown(r"**2. BOM Coverage & Over-delivery Tolerance:**")
        st.latex(r"\text{BOM}_{p} \le \sum_{v} x_{p,v} \le \text{BOM}_{p} \cdot (1 + \tau) \quad \forall p")
        st.markdown(r"*Meaning:* Total allocated units must satisfy BOM requirements while staying within the tolerance ceiling $\tau$ (default $+8\%$).")

        st.markdown(r"**3. Vendor Activation Linking:**")
        st.latex(r"z_v \ge y_{p,v} \quad \forall (p, v)")
        st.latex(r"\sum_{p} y_{p,v} \ge z_v \quad \forall v")
        st.markdown(r"*Meaning:* $z_v$ flips to 1 as soon as vendor $v$ is used, activating the administrative PO fee.")

    with t_math3:
        st.markdown(r"**Strategy 1: Cost-optimal**")
        st.latex(r"\min \quad \sum_{p,v} c_{p,v} \cdot x_{p,v} + \sum_{v} f_v \cdot z_v")

        st.markdown(r"**Strategy 2: Risk-balanced**")
        st.latex(r"\min \quad \sum_{p,v} r_{p,v} \cdot x_{p,v} + \sum_{v} \lambda f_v \cdot z_v")
        st.markdown(r"Where normalized composite risk balances price and delivery time:")
        st.latex(r"r_{p,v} = 0.40 \cdot p^{\text{norm}}_{p,v} + 0.60 \cdot lt^{\text{norm}}_v")

        st.markdown(r"**Strategy 3: Relationship-preserving**")
        st.latex(r"z_v = 1 \quad \forall v")
        st.markdown(r"Ensures all vendors in the quotation pool receive at least one order.")

    st.markdown("---")

    # --- SECTION 4: DUALITY THEORY & SHADOW PRICES ---
    st.header("4. Duality Theory & Practical Applications in Procurement")
    st.markdown(
        """
        One of the core academic and commercial pillars of this system is recovering **Shadow Prices** 
        from non-convex integer models using **Duality Theory**:
        """
    )

    with st.container(border=True):
        st.subheader("4.1. What is Duality? (Physical Quantities vs Economic Resource Valuation)")
        c_p, c_d = st.columns(2)
        with c_p:
            st.markdown(
                r"""
                **Primal Problem — Allocation Perspective:**
                - *"How many units $x_{p,v}$ should we purchase from each supplier to satisfy the BOM at minimum total cost?"*
                - Focus: Physical goods, binary order events, and cash expenditures.
                """
            )
        with c_d:
            st.markdown(
                r"""
                **Dual Problem — Valuation Perspective:**
                - *"What is the imputed economic shadow value $\lambda_i$ of each constraint (supplier capacity, BOM demand)?"*
                - Focus: Marginal resource values and bottleneck pricing.
                """
            )

    with st.container(border=True):
        st.subheader("4.2. Economic Interpretation: Shadow Price as Willingness-to-Pay")
        st.latex(r"\lambda = -\frac{\partial \, \text{Total Cost}}{\partial \, \text{Constraint Limit}}")
        st.markdown(
            r"""
            - **Mathematical Meaning:** Partial derivative of the total cost objective with respect to constraint relaxation.
            - **Procurement Actionability:** For binding supplier capacities, the shadow price reveals the exact dollar savings 
              achieved per +1 unit expanded capacity. It defines the company's maximum **Willingness-to-Pay** to subsidize tooling, 
              expedite shifts, or offer overtime bonuses to high-value suppliers.
            """
        )

    with st.container(border=True):
        st.subheader("4.3. Fundamental Theorems: Strong Duality & Complementary Slackness")
        st.markdown(r"**Strong Duality Theorem:**")
        st.latex(r"\min Z_{\text{Primal}} = \max W_{\text{Dual}}")
        st.markdown(r"**Complementary Slackness Theorem:**")
        st.latex(r"\lambda_i \cdot s_i = 0 \quad \forall i")
        st.markdown(
            r"""
            - $s_i > 0$ (Surplus Capacity): $\lambda_i = 0 \Rightarrow \text{Shadow Price} = 0$. Expanding this supplier yields 0 USD business value.
            - $s_i = 0$ (Binding Bottleneck): $\lambda_i > 0 \Rightarrow \text{Shadow Price} > 0$. Critical negotiation target.
            """
        )

    with st.container(border=True):
        st.subheader("4.4. Integer Non-Convexity & The Fix-and-Relax Procedure")
        st.markdown(
            r"""
            **Why MILP Lacks Standard Duals:**  
            Integer decisions ($x_{p,v} \in \mathbb{Z}, y, z \in \{0, 1\}$) introduce non-convex feasible spaces with non-zero Duality Gaps.  
            Standard integer branch-and-bound solvers cannot provide valid shadow prices.
            
            **The Fix-and-Relax Solution:**
            1. **Global Solve:** Solve full MILP via SCIP to find global integer optimum $(x^*, y^*, z^*)$.
            2. **Fix Binaries:** Fix discrete decisions $y \equiv y^*, z \equiv z^*$ as constants.
            3. **LP Relaxation:** Relax $x \ge 0$ into a continuous convex Linear Program.
            4. **GLOP Dual Extraction:** Solve the continuous problem using **Google GLOP** to extract exact, local constraint duals.
            """
        )

    with st.container(border=True):
        st.subheader("4.5. Excluded Vendor Opportunity Cost (Hurdle Rate)")
        st.latex(r"\Delta C_v = \text{Cost}(z_v = 1) - \text{Cost}^*")
        st.markdown(
            r"""
            Forces inactive backup suppliers into the solution ($z_v=1$) to measure exact cost penalties $\Delta C_v$. 
            Represents the mandatory price concession needed for an excluded vendor to become viable.
            """
        )

    st.markdown("---")

    # --- SECTION 5: EMPIRICAL BENCHMARK ---
    st.header("5. Empirical Benchmarks")
    st.markdown(
        """
        Head-to-head performance benchmark comparing the **MILP Optimizer (Google OR-Tools)** against 
        the standard **Manual Heuristic (Greedy Baseline)** on the enterprise quotation dataset 
        (66 products, 23 suppliers, 323 competitive quotes):
        """
    )

    res_table = {
        "Evaluation Metric": [
            "Total Sourcing Cost",
            "Purchase Spend",
            "PO Overhead Cost",
            "Net Cost Savings",
            "Lead-Time Delivery Risk",
            "Active Suppliers",
            "Capacity Bottlenecks Identified",
            "Computation Runtime"
        ],
        "Manual Baseline (Greedy)": [
            "559,711 USD",
            "558,111 USD",
            "1,600 USD (23 vendors)",
            "Baseline (0%)",
            "10,968.8 pts (High Risk)",
            "23 vendors (Fragmented activation)",
            "0 bottlenecks (Blind)",
            "Hours of manual spreadsheet sorting"
        ],
        "MILP Optimizer (OR-Tools)": [
            "508,369 USD",
            "506,769 USD",
            "1,600 USD (23 vendors)",
            "+51,341 USD (+9.17%)",
            "10,252.8 pts (Cost) / 7,409.6 pts (Risk)",
            "23 vendors (Globally coordinated)",
            "6 bottlenecks (Top: 772.50 USD/unit)",
            "< 0.35 seconds"
        ],
        "Business Impact & Strategic Value": [
            "Direct bottom-line cash savings (+51,341 USD)",
            "Optimizes working capital down to the penny",
            "Fair accounting with true PO overhead inclusion",
            "Outperforms rule-of-thumb heuristics significantly",
            "Protects manufacturing lines from catastrophic lead-time stockouts",
            "Achieves robust multi-sourcing diversification",
            "Supplies rigorous Willingness-to-Pay for supplier negotiation",
            "Enables real-time What-If sandbox simulations"
        ]
    }
    st.table(res_table)

    st.markdown(
        """
        <div class="highlight-box">
            <b>💡 Key Takeaway:</b> In competitive multi-sourcing categories, 
            <b>MILP unlocks 9.17% (51,341 USD) in net bottom-line cash savings</b> and eliminates up to 32.5% delivery risk 
            by intelligently coordinating complex MOQ thresholds and capacity boundaries.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- CASE STUDY: WHY DOES GREEDY ALSO USE 23 VENDORS BUT COST $51,341 MORE? ---
    st.markdown("### 🔍 Deep-Dive Case Study: Why does Greedy cost $51,341 USD more than MILP despite both using 23 suppliers?")
    st.markdown(
        r"""
        A classic strategic procurement paradox: **"If naive human buyers (Greedy Heuristic) also activate all 23 suppliers and buy the exact same 32,015 units of goods, why does MILP still save over 51,000 USD in cash?"**

        Here is the exact combinatorial mathematics behind the savings:
        """
    )

    cs_c1, cs_c2 = st.columns(2)
    with cs_c1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">❓</div>
                <div class="feature-title">1. Why does Greedy pick all 23 suppliers?</div>
                <div class="feature-desc">
                    Across <b>66 BOM products</b> and <b>323 competitive quotations</b>, every single supplier in the 23-vendor pool specializes in specific categories and <b>holds the #1 cheapest quote for at least one item</b>:
                    <ul>
                        <li><code>VN-VD10</code> is cheapest for 6 products.</li>
                        <li><code>VN-VD12</code> is cheapest for 5 products.</li>
                        <li><code>VN-VD01</code>, <code>VN-VD11</code>, <code>VN-VD18</code>, <code>VN-VD22</code> are cheapest for 4 products each.</li>
                        <li>Even niche vendors like <code>VN-VD07</code> and <code>VN-VD21</code> win 1 item.</li>
                    </ul>
                    Because Greedy processes products one-by-one and awards the order to the cheapest available quote, <b>all 23 vendors win orders</b>, incurring the exact same <b>$1,600 PO Overhead</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cs_c2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">⚠️</div>
                <div class="feature-title">2. Greedy's "MOQ & Tolerance Trap"</div>
                <div class="feature-desc">
                    Greedy makes myopic, item-by-item decisions without systemic visibility:
                    <ul>
                        <li>When the cheapest supplier's capacity is exhausted, Greedy searches for the 2nd cheapest.</li>
                        <li>If the 2nd cheapest supplier has a <b>large MOQ</b> that pushes the order past the allowable BOM upper tolerance (<code>target_max</code>), Greedy is <b>forced to discard the 2nd cheapest quote completely</b> and buy from an exorbitant 3rd supplier with a smaller MOQ!</li>
                        <li>Conversely, <b>MILP adjusts decision variables simultaneously</b>: it trims the allocation at Vendor 1 just enough to unlock the MOQ threshold at Vendor 2, keeping the blended cost minimal.</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        r"""
        #### 📌 Real-World Evidence: Product `VN-MT056` (BOM Demand = 30 units)
        Product `VN-MT056` receives 4 competitive quotes:
        * **`VN-VD18`**: Unit price **$2,080** *(cheapest)*, Capacity = 13 units, MOQ = 6 units.
        * **`VN-VD19`**: Unit price **$2,496** *(2nd cheapest)*, Capacity = 45 units, **MOQ = 21 units**.
        * **`VN-VD11`**: Unit price **$3,200** *(expensive)*, Capacity = 36 units, MOQ = 4 units.
        * **`VN-VD22`**: Unit price **$4,000** *(exorbitant)*, Capacity = 45 units, MOQ = 1 unit.
        """
    )

    cs_table = {
        "Sourcing Strategy": [
            "Manual Greedy Heuristic",
            "MILP Mathematical Optimum (OR-Tools)",
            "Optimization Gain"
        ],
        "Procurement Allocation Decision (VN-MT056)": [
            "Buys maximum capacity 13 units from VD18 ($2,080). Remaining need: 17 units. Because VD19 demands MOQ 21 (13 + 21 = 34 > tolerance max 32.4), Greedy skips VD19 and is forced to buy 17 units from VD11 at $3,200.",
            "MILP simultaneously coordinates: buys 9 units from VD18 ($2,080) and exactly 21 units from VD19 ($2,496, satisfying MOQ 21). Total quantity: exactly 30 units.",
            "MILP circumvents the $3,200 supplier penalty by balancing order split across low-cost tiers."
        ],
        "Total Spend for this Item": [
            "13 × $2,080 + 17 × $3,200 = 81,440 USD",
            "9 × $2,080 + 21 × $2,496 = 71,136 USD",
            "Saves 10,304 USD (-12.6%) on this single item alone!"
        ]
    }
    st.table(cs_table)

    st.markdown(
        r"""
        > **Summary:** Across the enterprise BOM, **59 out of 66 products** exhibit this exact coordination opportunity. 
        > This explains why **MILP saves \$51,341 USD** over human intuition, even though both strategies utilize all 23 suppliers!
        """
    )
    if st.button("🚀 Open Optimization Dashboard", type="primary", use_container_width=True):
        st.session_state["view_mode"] = "dashboard"
        st.rerun()
