# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** TỪ HOÀNG GIANG
> **Mã Sinh Viên / Mã Học viên:** 2A202602363 
> **Chủ đề Lựa chọn:** [Điền tên chủ đề đã chọn từ docs/DANH_SACH_DE_TAI.md hoặc Đề tài Mở]  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 5/ 5 | Cần xử lý nhiều bước: phân tích case → xác định lỗi → tra guideline → tìm case tương tự → đánh giá mức độ → đề xuất xử lý → tạo Rework. |
| **2. Tool Interaction** | 5/ 5 |  Cần kết nối Database/API/MCP để lấy dữ liệu annotation, lịch sử QC, guideline, tìm case tương tự và tạo Rework Ticket.  |
| **3. Dynamic Decision** | 5/ 5 | Bước tiếp theo phụ thuộc kết quả trước đó: phân biệt lỗi 2D/3D, PASS/FAIL, mức độ lỗi và độ tin cậy để quyết định xử lý hoặc yêu cầu QC xác nhận. |
| **4. Long Horizon Goal** | 2/ 5 | Một case thường được xử lý trong thời gian ngắn. Nếu Agent theo dõi toàn bộ vòng đời Rework → sửa → QC lại → đóng case thì mức độ này sẽ cao hơn. |
| **TỔNG ĐIỂM AGENTIC FIT** | **17/ 20** | *Bài toán rất phù hợp triển khai Agentic System**, đặc biệt nhờ khả năng suy luận nhiều bước, sử dụng nhiều công cụ và tự quyết định hành động tiếp theo.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "gpa": 3.85
      }
    },
    "latency_ms": 120.5
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [ ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** ___ / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** ___ lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
