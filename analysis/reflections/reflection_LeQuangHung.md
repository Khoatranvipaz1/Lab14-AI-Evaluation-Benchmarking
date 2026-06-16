# Báo cáo cá nhân - Lê Quang Hưng - 2A202600891

## 0. Thông tin chung

- **Họ tên:** Lê Quang Hưng
- **MSSV:** 2A202600891
- **Vai trò chính:** Multi-Judge Consensus
- **Hạng mục phụ trách:** Phần 3 - Multi-Judge Consensus

## 1. Đóng góp kỹ thuật

Em phụ trách thiết kế hướng đánh giá câu trả lời bằng nhiều judge thay vì một judge duy nhất. Phần việc chính gồm:

- Thiết kế cấu trúc kết quả gồm điểm từng judge, điểm cuối cùng và agreement rate.
- Đề xuất logic xử lý khi các judge chấm lệch nhau.
- Tách các tiêu chí chấm: accuracy, grounding, tone và safety.
- Đề xuất dùng judge thứ ba hoặc median score khi độ lệch vượt ngưỡng.

## 2. Technical Depth

Multi-judge giúp giảm rủi ro phụ thuộc vào một model judge. Agreement Rate cho biết các judge có đồng thuận hay không. Tuy nhiên, Agreement Rate chưa loại trừ đồng thuận ngẫu nhiên, nên hệ thống production nên bổ sung Cohen's Kappa.

Position Bias cũng là rủi ro quan trọng. Nếu judge ưu tiên response A chỉ vì vị trí, kết quả so sánh V1/V2 có thể sai. Cách giảm bias là đảo thứ tự response, ẩn tên model và lấy trung bình nhiều lượt chấm.

## 3. Problem Solving

Vấn đề chính là hai judge có thể chấm lệch. Nếu chỉ lấy trung bình, lỗi nghiêm trọng có thể bị làm mờ. Em đề xuất conflict handling: khi độ lệch > 1 điểm, hệ thống cần gọi judge thứ ba hoặc chuyển sang manual review.

## 4. Kết luận

Vai trò Multi-Judge Consensus giúp điểm benchmark đáng tin cậy hơn, đặc biệt khi kết quả được dùng làm điều kiện release trong regression gate.
