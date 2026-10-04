"""
Generative AI Strategic Procurement Advisor using Google Gemini API (gemini-3.5-flash).
Generates CPO-level executive briefings and provides an interactive AI copilot
to assist category managers in contract negotiations and risk mitigation.
Includes real-time API call auditing and structured logging.
"""

from __future__ import annotations

from datetime import datetime
import os
import time
from typing import Any

# Global session audit log registry for API inspection
API_CALL_LOGS: list[dict[str, Any]] = []


def get_api_call_logs() -> list[dict[str, Any]]:
    """Retrieve the chronological list of all AI API call audit records."""
    return list(API_CALL_LOGS)


def clear_api_call_logs() -> None:
    """Clear audit log history."""
    API_CALL_LOGS.clear()


def _get_api_key(explicit_key: str | None = None) -> str | None:
    """
    Securely resolve the Gemini API key in order of precedence:
    1. Explicit key passed from UI input (masked).
    2. Streamlit secrets (if deployed on Streamlit Cloud).
    3. Environment variable GEMINI_API_KEY.
    Never logs or exposes the raw key.
    """
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()

    # Try Streamlit secrets safely
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            key = st.secrets["GEMINI_API_KEY"]
            if key and str(key).strip():
                return str(key).strip()
    except Exception:
        pass

    # Try environment variable
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    return None


def generate_executive_briefing(
    grounding_data: dict[str, Any],
    api_key: str | None = None,
    lang: str = "vi",
) -> tuple[bool, str]:
    """
    Generate a high-level CPO Executive Briefing synthesizing the optimization results.
    Returns (success: bool, content: str).
    """
    start_time = time.time()
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    resolved_key = _get_api_key(api_key)
    masked_key = (
        f"{resolved_key[:6]}...{resolved_key[-4:]}"
        if resolved_key and len(resolved_key) >= 10
        else ("Configured (Hidden)" if resolved_key else "None (Offline Fallback)")
    )

    prompt_vi = f"""
Bạn là một Giám đốc Thu mua Cấp cao (Chief Procurement Officer - CPO) dày dạn kinh nghiệm.
Dưới đây là dữ liệu thực tế đã được kiểm chứng (Ground Truth) từ mô hình tối ưu hóa toán học Mixed-Integer Linear Programming (MILP) vừa chạy:

=== DỮ LIỆU TỐI ƯU HÓA GROUND TRUTH ===
- Tổng chi phí tối ưu (Cost-optimal): ${grounding_data.get('total_cost', 0):,.2f}
- Tiền mua hàng: ${grounding_data.get('purchase_cost', 0):,.2f}
- Phí PO overhead: ${grounding_data.get('po_overhead', 0):,.2f}
- Tiết kiệm so với mua thủ công (Greedy baseline): ${grounding_data.get('savings_dollars', 0):,.2f} ({grounding_data.get('savings_pct', 0):.2f}%)
- Số nhà cung cấp kích hoạt: {grounding_data.get('vendors_used', 'N/A')}
- Đánh đổi chiến lược Cân bằng rủi ro: Chi phí tăng +{grounding_data.get('cost_diff_pct', 0):.2f}% để giảm {grounding_data.get('risk_diff_pct', 0):.2f}% điểm rủi ro giao hàng.
- Nút thắt công suất số 1 (Shadow Price): Sản phẩm {grounding_data.get('top_prod', 'N/A')} tại NCC {grounding_data.get('top_vendor', 'N/A')} có Shadow Price là ${grounding_data.get('top_shadow_price', 0):,.2f}/đơn vị. Nếu tăng 10% công suất sẽ tiết kiệm trực tiếp ${grounding_data.get('top_savings_10pct', 0):,.2f}.
- NCC dự phòng tiềm năng nhất bị loại: {grounding_data.get('best_unused', 'N/A')} (cần giảm chi phí ${grounding_data.get('opp_cost', 0):,.2f} để lọt vào kế hoạch).
=======================================

Hãy lập một bản **Báo Cáo Chiến Lược Điều Hành (CPO Executive Briefing)** ngắn gọn, súc tích và có tính hành động cao (Actionable) cho Ban Giám đốc gồm:
1. **Tóm tắt giá trị cốt lõi**: Khẳng định giá trị thực tế mang lại của kế hoạch tối ưu so với mua hàng thông thường.
2. **Khuyến nghị chính sách nguồn cung**: Có nên đánh đổi thêm chi phí để lấy an toàn lead-time trong bối cảnh dữ liệu này không?
3. **Kế hoạch đàm phán hợp đồng trọng tâm (Top Action Items)**: Nêu rõ chiến thuật thương thảo trực tiếp với các nhà cung cấp cụ thể (ví dụ NCC nghẽn công suất hoặc NCC dự phòng).
Format theo Markdown chuyên nghiệp, có bullet points rõ ràng.
"""

    prompt_en = f"""
You are a seasoned Chief Procurement Officer (CPO).
Below is verified ground-truth data from our Mixed-Integer Linear Programming (MILP) procurement optimizer:

=== GROUND TRUTH DATA ===
- Optimal Total Cost: ${grounding_data.get('total_cost', 0):,.2f}
- Purchase Spend: ${grounding_data.get('purchase_cost', 0):,.2f}
- PO Overhead: ${grounding_data.get('po_overhead', 0):,.2f}
- Savings vs Greedy Manual Baseline: ${grounding_data.get('savings_dollars', 0):,.2f} ({grounding_data.get('savings_pct', 0):.2f}%)
- Active Suppliers: {grounding_data.get('vendors_used', 'N/A')}
- Risk-balanced Trade-off: +{grounding_data.get('cost_diff_pct', 0):.2f}% cost cuts lead-time risk score by {grounding_data.get('risk_diff_pct', 0):.2f}%.
- #1 Capacity Bottleneck (Shadow Price): Product {grounding_data.get('top_prod', 'N/A')} at Vendor {grounding_data.get('top_vendor', 'N/A')} with shadow price ${grounding_data.get('top_shadow_price', 0):,.2f}/unit (10% expansion saves ${grounding_data.get('top_savings_10pct', 0):,.2f}).
- Best Backup Excluded Vendor: {grounding_data.get('best_unused', 'N/A')} (needs ${grounding_data.get('opp_cost', 0):,.2f} concession to enter plan).
=========================

Generate a concise, actionable **CPO Executive Strategic Briefing**:
1. **Core Value & Bottom-line Impact**: Quantify savings and efficiency gains.
2. **Sourcing Policy Recommendation**: Evaluate the cost-vs-risk trade-off.
3. **Contract Negotiation Playbook**: Specific tactics for bottleneck and backup suppliers.
Format cleanly in Markdown with bold key numbers and bullet points.
"""

    chosen_prompt = prompt_vi if lang == "vi" else prompt_en

    if not resolved_key:
        msg = (
            "🔒 **Chế độ Ngoại tuyến (Offline Mode):** Bạn chưa cấu hình `Gemini API Key`. "
            "Hệ thống đang sử dụng Lớp phân tích toán học nội bộ (Tier 1) để hiển thị nhận định. "
            "Để mở khóa bản tóm tắt chiến lược chuyên sâu từ Gemini 3.5 Flash, vui lòng nhập API Key tại thanh điều khiển Sidebar."
            if lang == "vi"
            else "🔒 **Offline Fallback Mode:** No `Gemini API Key` provided. "
            "Displaying deterministic mathematical insights (Tier 1). "
            "To unlock executive briefings from Gemini 3.5 Flash, enter an API Key in the sidebar."
        )

        # Record offline audit log
        API_CALL_LOGS.append({
            "timestamp": timestamp_str,
            "endpoint": "generate_executive_briefing",
            "model": "gemini-3.5-flash (Offline Simulation)",
            "status": "OFFLINE_FALLBACK (No Key)",
            "latency_ms": round((time.time() - start_time) * 1000),
            "api_key_masked": masked_key,
            "request_payload": {
                "model": "gemini-3.5-flash",
                "temperature": 0.2,
                "max_output_tokens": 3000,
                "thinking_level": "low",
                "prompt_length_chars": len(chosen_prompt),
                "grounding_data": grounding_data,
                "full_prompt": chosen_prompt.strip(),
            },
            "response": msg,
        })
        return False, msg

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=resolved_key)

        # Attempt generation with 1 auto-retry for transient Google 5xx ServerErrors
        attempts = 2
        response = None
        for att in range(1, attempts + 1):
            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=chosen_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=3000,
                        thinking_config=types.ThinkingConfig(thinking_level="low"),
                    ),
                )
                break
            except Exception as inner_err:
                if att < attempts and ("ServerError" in type(inner_err).__name__ or "503" in str(inner_err)):
                    time.sleep(1.5)
                    continue
                raise inner_err

        res_text = response.text or ""
        elapsed_ms = round((time.time() - start_time) * 1000)

        # Extract token usage and finish reason metadata if available
        usage_info = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            usage_info = {
                "prompt_tokens": getattr(usage, "prompt_token_count", None),
                "candidates_tokens": getattr(usage, "candidates_token_count", None),
                "total_tokens": getattr(usage, "total_token_count", None),
            }
        finish_reason = None
        if hasattr(response, "candidates") and response.candidates:
            finish_reason = str(getattr(response.candidates[0], "finish_reason", "UNKNOWN"))

        # Record success audit log
        API_CALL_LOGS.append({
            "timestamp": timestamp_str,
            "endpoint": "generate_executive_briefing",
            "model": "gemini-3.5-flash",
            "status": f"SUCCESS (200 OK - {finish_reason})" if finish_reason else "SUCCESS (200 OK)",
            "latency_ms": elapsed_ms,
            "api_key_masked": masked_key,
            "usage": usage_info,
            "request_payload": {
                "model": "gemini-3.5-flash",
                "temperature": 0.2,
                "max_output_tokens": 3000,
                "thinking_level": "low",
                "prompt_length_chars": len(chosen_prompt),
                "grounding_data": grounding_data,
                "full_prompt": chosen_prompt.strip(),
            },
            "response": res_text,
        })

        return True, res_text

    except Exception as e:
        elapsed_ms = round((time.time() - start_time) * 1000)
        error_msg = str(e)
        user_err = f"⚠️ Lỗi kết nối AI: {type(e).__name__}"
        is_google_server_err = "ServerError" in type(e).__name__ or "503" in error_msg or "500" in error_msg or "overloaded" in error_msg.lower()

        if "API_KEY_INVALID" in error_msg or "400" in error_msg:
            user_err = "❌ **Lỗi xác thực:** Gemini API Key không hợp lệ hoặc đã hết hạn." if lang == "vi" else "❌ **Authentication Error:** Invalid or expired Gemini API Key."
        elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            user_err = "⚠️ **Hạn mức API:** Tài khoản Gemini đã đạt giới hạn quota." if lang == "vi" else "⚠️ **Quota Exceeded:** Gemini rate limit reached."
        elif is_google_server_err:
            user_err = (
                "⚠️ **Lỗi từ phía máy chủ Google (503/500 ServerError):** "
                "Cụm máy chủ của Google hiện đang bị quá tải trong giờ cao điểm (High Demand). "
                "Hệ thống đã tự động thử lại nhưng Google server chưa kịp phản hồi. "
                "Dữ liệu và thuật toán tối ưu của dự án hoàn toàn bình thường. Vui lòng bấm thử lại sau 1-2 phút."
                if lang == "vi"
                else "⚠️ **Google Cloud Server Error (503/500 ServerError):** "
                "Google Gemini servers are currently overloaded during peak hours (High Demand). "
                "The project data and optimization solver are fully intact. Please retry in a moment."
            )

        # Record error audit log
        API_CALL_LOGS.append({
            "timestamp": timestamp_str,
            "endpoint": "generate_executive_briefing",
            "model": "gemini-3.5-flash",
            "status": f"ERROR ({type(e).__name__})",
            "error_origin": "GOOGLE_CLOUD_INFRASTRUCTURE (HTTP 5xx)" if is_google_server_err else "CLIENT_OR_QUOTA (HTTP 4xx)",
            "latency_ms": elapsed_ms,
            "api_key_masked": masked_key,
            "request_payload": {
                "model": "gemini-3.5-flash",
                "temperature": 0.2,
                "max_output_tokens": 3000,
                "thinking_level": "low",
                "prompt_length_chars": len(chosen_prompt),
                "grounding_data": grounding_data,
                "full_prompt": chosen_prompt.strip(),
            },
            "error_detail": error_msg[:300],
            "response": user_err,
        })

        return False, user_err


def chat_with_procurement_advisor(
    user_message: str,
    chat_history: list[dict[str, str]],
    grounding_data: dict[str, Any],
    api_key: str | None = None,
    lang: str = "vi",
) -> str:
    """
    Interactive Q&A with the Gemini 3.5 Flash AI Procurement Copilot.
    """
    start_time = time.time()
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    resolved_key = _get_api_key(api_key)
    masked_key = (
        f"{resolved_key[:6]}...{resolved_key[-4:]}"
        if resolved_key and len(resolved_key) >= 10
        else ("Configured (Hidden)" if resolved_key else "None (Offline Fallback)")
    )

    system_instruction = (
        f"Bạn là Trợ lý AI Cố vấn Chiến lược Thu mua (AI Procurement Strategic Advisor). "
        f"Bạn đang hỗ trợ chuyên viên thu mua phân tích kết quả bài toán tối ưu hóa với các thông số hiện tại: "
        f"Tổng chi phí ${grounding_data.get('total_cost', 0):,.0f}, "
        f"tiết kiệm ${grounding_data.get('savings_dollars', 0):,.0f} so với thủ công, "
        f"top nút thắt công suất là {grounding_data.get('top_prod', 'N/A')} tại {grounding_data.get('top_vendor', 'N/A')} "
        f"(Shadow Price ${grounding_data.get('top_shadow_price', 0):,.2f}/đv). "
        f"Hãy trả lời chính xác, thực tế, dựa trên số liệu kinh tế và nguyên lý chuỗi cung ứng. Trả lời bằng {'Tiếng Việt' if lang=='vi' else 'English'}."
    )

    if not resolved_key:
        msg = (
            "Vui lòng cung cấp Gemini API Key tại thanh điều khiển Sidebar để trò chuyện với Trợ lý AI Chiến Lược Thu Mua."
            if lang == "vi"
            else "Please provide a Gemini API Key in the sidebar to chat with the AI Procurement Advisor."
        )
        API_CALL_LOGS.append({
            "timestamp": timestamp_str,
            "endpoint": "chat_with_procurement_advisor",
            "model": "gemini-3.5-flash (Offline Simulation)",
            "status": "OFFLINE_FALLBACK (No Key)",
            "latency_ms": round((time.time() - start_time) * 1000),
            "api_key_masked": masked_key,
            "request_payload": {
                "model": "gemini-3.5-flash",
                "system_instruction": system_instruction,
                "user_message": user_message,
                "history_turns": len(chat_history),
            },
            "response": msg,
        })
        return msg

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=resolved_key)

        # Build contents from history
        contents = []
        for msg in chat_history[-6:]:  # Keep recent context
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        # Attempt generation with 1 auto-retry for transient Google 5xx ServerErrors
        attempts = 2
        response = None
        for att in range(1, attempts + 1):
            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3,
                        max_output_tokens=1500,
                        thinking_config=types.ThinkingConfig(thinking_level="low"),
                    ),
                )
                break
            except Exception as inner_err:
                if att < attempts and ("ServerError" in type(inner_err).__name__ or "503" in str(inner_err)):
                    time.sleep(1.5)
                    continue
                raise inner_err

        res_text = response.text or "Không nhận được phản hồi từ mô hình AI."
        elapsed_ms = round((time.time() - start_time) * 1000)

        # Extract token usage and finish reason metadata if available
        usage_info = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            usage_info = {
                "prompt_tokens": getattr(usage, "prompt_token_count", None),
                "candidates_tokens": getattr(usage, "candidates_token_count", None),
                "total_tokens": getattr(usage, "total_token_count", None),
            }
        finish_reason = None
        if hasattr(response, "candidates") and response.candidates:
            finish_reason = str(getattr(response.candidates[0], "finish_reason", "UNKNOWN"))

        API_CALL_LOGS.append({
            "timestamp": timestamp_str,
            "endpoint": "chat_with_procurement_advisor",
            "model": "gemini-3.5-flash",
            "status": f"SUCCESS (200 OK - {finish_reason})" if finish_reason else "SUCCESS (200 OK)",
            "latency_ms": elapsed_ms,
            "api_key_masked": masked_key,
            "usage": usage_info,
            "request_payload": {
                "model": "gemini-3.5-flash",
                "system_instruction": system_instruction,
                "user_message": user_message,
                "history_turns": len(chat_history),
                "max_output_tokens": 1500,
                "thinking_level": "low",
            },
            "response": res_text,
        })

        return res_text

    except Exception as e:
        elapsed_ms = round((time.time() - start_time) * 1000)
        error_msg = str(e)
        err_res = f"Xin lỗi, không thể kết nối tới dịch vụ AI lúc này: {type(e).__name__}"
        is_google_server_err = "ServerError" in type(e).__name__ or "503" in error_msg or "500" in error_msg or "overloaded" in error_msg.lower()

        if "API_KEY_INVALID" in error_msg:
            err_res = "Khóa API không hợp lệ. Vui lòng kiểm tra lại." if lang == "vi" else "Invalid API key. Please check your credentials."
        elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            err_res = "Hạn mức API Gemini của bạn đã đạt giới hạn (Quota Exceeded)." if lang == "vi" else "Gemini API quota exceeded."
        elif is_google_server_err:
            err_res = (
                "⚠️ Máy chủ Google Gemini hiện đang quá tải (503 ServerError - High Demand). Vui lòng thử lại sau giây lát."
                if lang == "vi"
                else "⚠️ Google Gemini server is temporarily overloaded (503 ServerError). Please retry shortly."
            )

        API_CALL_LOGS.append({
            "timestamp": timestamp_str,
            "endpoint": "chat_with_procurement_advisor",
            "model": "gemini-3.5-flash",
            "status": f"ERROR ({type(e).__name__})",
            "error_origin": "GOOGLE_CLOUD_INFRASTRUCTURE (HTTP 5xx)" if is_google_server_err else "CLIENT_OR_QUOTA (HTTP 4xx)",
            "latency_ms": elapsed_ms,
            "api_key_masked": masked_key,
            "request_payload": {
                "model": "gemini-3.5-flash",
                "system_instruction": system_instruction,
                "user_message": user_message,
                "history_turns": len(chat_history),
                "max_output_tokens": 1500,
                "thinking_level": "low",
            },
            "error_detail": error_msg[:300],
            "response": err_res,
        })

        return err_res
