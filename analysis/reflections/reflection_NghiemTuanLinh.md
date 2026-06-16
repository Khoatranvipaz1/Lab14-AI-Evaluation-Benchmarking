# Báo cáo cá nhân - Nghiêm Tuấn Linh - 2A202600897

## 0. Thông tin chung

- **Họ tên:** Nghiêm Tuấn Linh
- **MSSV:** 2A202600897
- **Vai trò chính:** Dataset & SDG
- **Hạng mục phụ trách:** Phần 2 - Dataset & Synthetic Data Generation

## 1. Đóng góp kỹ thuật

Em phụ trách thiết kế golden dataset và nhóm hard cases để benchmark Agent. Phần việc chính gồm:

- Tạo bộ test cases đủ lớn, vượt yêu cầu tối thiểu 50 cases.
- Bổ sung nhiều nhóm test: fact-based, edge cases, red-team/adversarial, multi-turn và stress.
- Đảm bảo các retrieval cases có ground truth IDs để phục vụ Hit Rate và MRR.
- Thiết kế hard cases nhằm kiểm tra hallucination, out-of-context, prompt injection và câu hỏi mơ hồ.

## 2. Technical Depth

Golden dataset quyết định chất lượng benchmark. Nếu dataset chỉ gồm câu hỏi dễ, Agent có thể đạt điểm cao nhưng vẫn fail khi gặp tình huống thực tế. Vì vậy dataset cần có cả case bình thường và case khó.

Các nhóm hard cases quan trọng:

- Prompt injection để kiểm tra khả năng chống lệnh độc hại.
- Out-of-context để kiểm tra Agent có biết từ chối hay không.
- Ambiguous questions để kiểm tra khả năng xử lý câu hỏi thiếu thông tin.
- Multi-turn để kiểm tra giữ ngữ cảnh hội thoại.

## 3. Problem Solving

Vấn đề là tạo dataset nhiều nhưng vẫn phải đo được. Em xử lý bằng cách gắn metadata và ground truth IDs cho test cases, giúp các module khác có thể tính retrieval metrics và phân tích lỗi.

## 4. Kết luận

Vai trò Dataset & SDG giúp nhóm có nền benchmark đủ rộng, đủ khó và có thể đo lường được thay vì chỉ kiểm thử thủ công vài câu hỏi đơn giản.
