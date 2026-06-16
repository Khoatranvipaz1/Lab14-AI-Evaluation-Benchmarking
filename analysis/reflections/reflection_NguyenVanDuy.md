# Báo cáo cá nhân - Nguyễn Văn Duy - 2A202600725

## 0. Thông tin chung

- **Họ tên:** Nguyễn Văn Duy
- **MSSV:** 2A202600725
- **Vai trò chính:** Failure Analysis / QA
- **Hạng mục phụ trách:** Phần 6 - Failure Analysis

## 1. Đóng góp kỹ thuật

Em phụ trách phân tích kết quả benchmark, gom nhóm lỗi và viết phần 5 Whys trong báo cáo chung `analysis/failure_analysis.md`. Công việc chính gồm:

- Phân loại các lỗi thường gặp của Agent V1: Retrieval Miss, Hallucination, Safety Violation, Generic Answer.
- Phân tích nguyên nhân gốc bằng phương pháp 5 Whys cho 3 nhóm case rủi ro nhất.
- Đề xuất action plan để Agent V2 giảm lỗi retrieval, giảm hallucination và tăng safety.
- Đối chiếu kết quả benchmark với yêu cầu nộp bài để đảm bảo báo cáo chung có số liệu cụ thể.

## 2. Technical Depth

Em tập trung vào Root Cause Analysis cho RAG Agent. Khi một câu trả lời sai, nguyên nhân không nhất thiết nằm ở LLM mà có thể đến từ retrieval, chunking, prompt, guardrail hoặc judge rubric. Vì vậy failure analysis cần tách lỗi theo tầng hệ thống thay vì chỉ ghi "agent trả lời sai".

Em cũng sử dụng MRR, Hit Rate và Agreement Rate như tín hiệu hỗ trợ phân tích:

- Hit Rate thấp thường chỉ ra lỗi retrieval.
- MRR thấp cho thấy tài liệu đúng bị xếp quá xa.
- Agreement Rate thấp cho thấy judge chưa đủ ổn định để kết luận chắc chắn.

## 3. Problem Solving

Vấn đề lớn nhất là báo cáo failure dễ bị chung chung nếu không gắn với metric. Em xử lý bằng cách liên kết từng nhóm lỗi với nguyên nhân hệ thống và hướng cải tiến cụ thể. Ví dụ, hallucination được gắn với thiếu strict grounding; safety violation được gắn với thiếu guardrail; retrieval miss được gắn với thiếu đánh giá Hit Rate/MRR.

## 4. Kết luận

Vai trò của em giúp nhóm biến kết quả benchmark thành insight kỹ thuật có thể hành động. Thay vì chỉ biết Agent V2 pass/fail, nhóm biết rõ cần cải tiến retrieval, grounding, safety và judge reliability ở đâu.
