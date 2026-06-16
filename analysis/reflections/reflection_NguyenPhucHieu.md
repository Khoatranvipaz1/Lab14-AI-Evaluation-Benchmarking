# Báo cáo cá nhân - Nguyễn Phúc Hiếu - 2A202600747

## 0. Thông tin chung

- **Họ tên:** Nguyễn Phúc Hiếu
- **MSSV:** 2A202600747
- **Vai trò chính:** Hiệu năng & Báo cáo chi phí
- **Hạng mục phụ trách:** Phần 5 - Performance & Cost Report

## 1. Đóng góp kỹ thuật

Em phụ trách theo dõi hiệu năng pipeline benchmark và đề xuất cách kiểm soát chi phí khi chạy evaluation. Phần việc chính gồm:

- Theo dõi latency từng test case trong benchmark results.
- Đánh giá lợi ích của async runner khi chạy nhiều cases.
- Đề xuất batch execution để giảm tổng thời gian benchmark.
- Đề xuất bổ sung token usage và cost tracking vào report.

## 2. Technical Depth

Pipeline evaluation dùng LLM judge thường tốn thời gian và chi phí. Nếu chạy tuần tự 50+ cases, thời gian có thể tăng rất nhanh. Async benchmark giúp chạy song song nhiều case, nhưng cần batch size để tránh rate limit.

Về chi phí, nhóm nên dùng tiered evaluation:

- Model nhỏ/giá rẻ cho vòng đánh giá đầu.
- Model mạnh hơn cho case khó hoặc case judge bất đồng.
- Cache kết quả judge theo hash của question, answer và ground truth.

## 3. Problem Solving

Vấn đề chính là cân bằng chất lượng với tốc độ và chi phí. Em đề xuất gate không chỉ nhìn `avg_score` mà còn theo dõi latency, token usage và cost. Nếu Agent V2 tốt hơn nhưng chậm hoặc đắt hơn quá nhiều, nhóm cần cân nhắc trước khi release.

## 4. Kết luận

Vai trò Performance & Cost giúp benchmark có khả năng vận hành thực tế, không chỉ đúng về mặt chất lượng mà còn hợp lý về thời gian và chi phí.
