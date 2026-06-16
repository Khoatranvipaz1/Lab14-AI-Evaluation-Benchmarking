# Báo cáo cá nhân (Individual Reflection Report)
**Sinh viên:** Nguyễn Khánh Duy  
**Vai trò:** AI Engineer / DevOps  
**Nhánh Git:** `duy`  
**Dự án:** AI Evaluation Factory (Lab Day 14)

---

## 1. Đóng góp Kỹ thuật (Engineering Contribution)

Trong quá trình phát triển hệ thống AI Evaluation Factory, tôi đã đóng góp vào các module cốt lõi sau:

### A. Triển khai Multi-Judge Consensus Engine ([llm_judge.py](../../engine/llm_judge.py))
- Thiết kế hệ thống đánh giá sử dụng đồng thời 2 cấu hình/mô hình Judge khác nhau (`gpt-4o-mini` và `gpt-3.5-turbo` hoặc System Prompts khác nhau) để đảm bảo tính khách quan.
- Xây dựng logic **Consensus & Calibration**:
  - Khi điểm số chênh lệch giữa hai Judge $\le 1$, điểm cuối cùng sẽ là trung bình cộng.
  - Khi điểm số chênh lệch $> 1$ (ví dụ: Judge A cho 5 điểm nhưng Judge B chỉ cho 2 điểm), hệ thống tự động kích hoạt **Judge thứ 3** (Trọng tài - Tie-Breaker) để phân tích nguyên nhân và đưa ra điểm số quyết định cuối cùng kèm theo giải thích cụ thể (`reasoning`).
- Triển khai thuật toán kiểm tra thiên vị vị trí **Position Bias** bằng cách tráo đổi vị trí phản hồi đầu vào và đo đạc sự thay đổi điểm số của Judge.

### B. Tối ưu hóa Async Runner với Semaphore ([runner.py](../../engine/runner.py))
- Để tránh bị giới hạn băng thông (Rate Limit - HTTP 429) khi gọi nhiều LLM đồng thời cho 50+ test cases, tôi đã sử dụng `asyncio.Semaphore` để giới hạn số luồng xử lý song song tối đa (ví dụ: `batch_size=5`).
- Tích hợp công cụ đo đạc và báo cáo hiệu suất chi tiết:
  - **Latency**: Đo chính xác thời gian xử lý từng ca kiểm thử.
  - **Token Usage & Cost Tracking**: Theo dõi số lượng Input/Output Tokens sử dụng từ API Response, nhân với đơn giá của từng mô hình để tính toán chính xác chi phí của mỗi lượt Eval.

### C. Triển khai Retrieval Evaluation Metrics ([retrieval_eval.py](../../engine/retrieval_eval.py))
- Hoàn thiện cài đặt hai chỉ số đánh giá giai đoạn Retrieval:
  - **Hit Rate**: Xác định xem tài liệu kỳ vọng (`expected_ids`) có xuất hiện trong Top-K tài liệu lấy ra từ Vector DB hay không.
  - **MRR (Mean Reciprocal Rank)**: Tính toán thứ hạng của tài liệu chuẩn đầu tiên xuất hiện để chấm điểm độ chính xác của thứ tự hiển thị.

---

## 2. Chi tiết kỹ thuật & Lý thuyết (Technical Depth)

### A. Mean Reciprocal Rank (MRR)
- **Định nghĩa**: MRR đánh giá khả năng xếp hạng của công cụ tìm kiếm (Retriever). Công thức tính cho một tập câu hỏi $Q$ là:
  $$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
  Trong đó, $\text{rank}_i$ là thứ tự (1-indexed) của tài liệu liên quan chuẩn đầu tiên tìm thấy trong danh sách kết quả. Nếu không tìm thấy, $\frac{1}{\text{rank}_i} = 0$.
- **Ý nghĩa thực tế**: Hit Rate chỉ phản ánh "có tìm thấy tài liệu hay không" (nhị phân 0 hoặc 1), còn MRR phản ánh "tài liệu đó nằm ở vị trí thứ mấy". Nếu tài liệu chuẩn nằm ngay ở vị trí thứ nhất ($rank=1$), điểm đạt tối đa là $1.0$. Nếu bị trôi xuống vị trí thứ 3 ($rank=3$), điểm chỉ còn $0.33$. Điều này cực kỳ quan trọng vì LLM bị ảnh hưởng bởi *Lost in the Middle* (dễ bỏ sót thông tin ở giữa/cuối context).

### B. Cohen's Kappa
- **Định nghĩa**: Hệ số Cohen's Kappa ($\kappa$) đo lường mức độ đồng thuận giữa hai người chấm điểm (ở đây là hai LLM Judges) cho các biến phân loại, có tính đến khả năng đồng thuận ngẫu nhiên.
  $$\kappa = \frac{p_o - p_e}{1 - p_e}$$
  Trong đó:
  - $p_o$: Tỉ lệ đồng thuận thực tế quan sát được (Observed Agreement).
  - $p_e$: Tỉ lệ đồng thuận kỳ vọng ngẫu nhiên (Expected Agreement).
- **Phân loại mức độ**:
  - $\kappa < 0$: Không đồng thuận.
  - $0.0 - 0.20$: Đồng thuận rất thấp.
  - $0.21 - 0.40$: Đồng thuận trung bình thấp.
  - $0.41 - 0.60$: Đồng thuận vừa phải.
  - $0.61 - 0.80$: Đồng thuận cao (Substantial).
  - $0.81 - 1.00$: Đồng thuận gần như tuyệt đối.
- **Ý nghĩa trong Eval**: Giúp kiểm tra xem hệ thống Judge của chúng ta có thực sự tin cậy và khách quan hay không. Nếu $\kappa$ quá thấp, chứng tỏ các Judge đang chấm điểm lệch nhau rất nhiều, báo hiệu Prompt chấm điểm hoặc Rubric cần được tinh chỉnh lại.

### C. Position Bias (Thiên vị vị trí)
- **Định nghĩa**: Hiện tượng LLM Judge có xu hướng ưu ái cho câu trả lời xuất hiện ở một vị trí cụ thể (thường là Option A hoặc Option đầu tiên) bất kể chất lượng thực tế.
- **Cách xử lý**:
  1. **Tạo phiên bản đảo ngược (Pairwise Swapping)**: Thay vì chỉ chạy `eval(Response A, Response B)`, ta chạy thêm `eval(Response B, Response A)`.
  2. **Consensus Logic**: Nếu kết quả thay đổi khi đổi chỗ, ta kết luận có Position Bias xảy ra và tiến hành lấy trung bình điểm hoặc yêu cầu Judge giải thích rõ lý do thay đổi trước khi chấm điểm cuối.

### D. Trade-off giữa Chi phí và Chất lượng (Cost vs Quality)
- **Vấn đề**: Sử dụng các mô hình lớn (như GPT-4o, Claude 3.5 Sonnet) làm Judge mang lại độ chính xác cao và lý luận sắc bén, nhưng chi phí rất đắt đỏ (khoảng $5.00 - $15.00 cho mỗi triệu token) và giới hạn tốc độ thấp (RPM thấp). Ngược lại, các mô hình nhỏ (gpt-4o-mini, Haiku) rất rẻ và nhanh nhưng dễ bỏ qua các lỗi tinh vi và có mức độ đồng thuận thấp hơn.
- **Giải pháp tối ưu**:
  - Triển khai **Tiered Evaluation** (Đánh giá phân tầng): 
    - Bước 1: Cho các mô hình giá rẻ (như `gpt-4o-mini`) đánh giá ban đầu.
    - Bước 2: Chỉ khi xảy ra xung đột lớn (điểm số lệch giữa các Judge nhỏ $> 1$), ta mới gọi mô hình lớn hơn (`gpt-4o` hoặc `Claude 3.5 Sonnet`) làm trọng tài phân xử.
  - Giải pháp này giúp **giảm chi phí eval khoảng 30% - 50%** nhưng vẫn đảm bảo độ tin cậy tương đương việc sử dụng mô hình đắt tiền cho toàn bộ bộ dữ liệu.

---

## 3. Giải quyết vấn đề (Problem Solving)

Trong quá trình triển khai hệ thống, tôi đã trực tiếp xử lý các bài toán kỹ thuật sau:
1. **Lỗi Rate Limit (HTTP 429)**: Ban đầu khi chạy song song 50 cases bằng `asyncio.gather` mà không có kiểm soát, API liên tục trả về lỗi quá tải. Tôi đã khắc phục bằng cách sử dụng `asyncio.Semaphore` để tạo hàng đợi kiểm soát số lượng tác vụ đồng thời, kết hợp với cơ chế **Exponential Backoff** (tự động thử lại sau khoảng thời gian tăng dần khi gặp lỗi).
2. **LLM Judge chấm điểm quá lỏng lẻo (Leniency Bias)**: Các mô hình LLM có xu hướng chấm điểm cao (4 hoặc 5) cho các câu trả lời trông trôi chảy dù nội dung bị thiếu hoặc sai lệch nhẹ. Tôi đã giải quyết bằng cách thiết kế lại System Prompt của Judge với một **Rubric chấm điểm chi tiết từng bậc điểm (1 đến 5)** cùng ví dụ cụ thể cho mỗi mức điểm, buộc LLM phải trích dẫn bằng chứng (evidence) từ context và so sánh trực tiếp với Ground Truth trước khi đưa ra điểm số.
