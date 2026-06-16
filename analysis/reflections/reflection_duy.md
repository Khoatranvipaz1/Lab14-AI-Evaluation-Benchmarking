# Báo cáo cá nhân (Individual Reflection Report)
**Sinh viên:** Nguyễn Khánh Duy  
**Vai trò:** Business Analyst / QA / Document Lead (Phụ trách Phần 6)  
**Nhánh Git:** `duy`  
**Dự án:** AI Evaluation Factory (Lab Day 14)

---

## 1. Đóng góp Kỹ thuật (Engineering Contribution)

Trong dự án AI Evaluation Factory, tôi đảm nhận vai trò **Business Analyst & QA Lead**, chịu trách nhiệm chính về kiểm định chất lượng, phân tích lỗi và đề xuất kế hoạch hành động tối ưu cho Agent. Các đóng góp cụ thể bao gồm:

### A. Phân tích kết quả Benchmark & Gom cụm lỗi (Failure Clustering)
- Thiết lập quy trình thu thập dữ liệu sau khi chạy Benchmark để phân loại và định lượng các lỗi của RAG Agent.
- Thực hiện gom cụm lỗi của phiên bản Base V1 thành 4 nhóm chính trong tệp [failure_analysis.md](../failure_analysis.md):
  * **Hallucination (Bịa đặt thông tin)**: Khi người dùng hỏi thông tin không có trong context.
  * **Safety Violation (Vi phạm an toàn)**: Khi Agent bị lừa bởi Prompt Injection (viết thơ chính trị) hoặc trả lời thông tin nguy hiểm (hướng dẫn chế thuốc nổ).
  * **Retrieval Miss (Lấy sai tài liệu)**: Nguyên nhân cốt lõi khiến Agent trả lời sai hoặc chung chung.
  * **Incomplete / Generic Answer**: Câu trả lời ở dạng mẫu thô sơ, chưa cá nhân hóa theo ngữ cảnh.

### B. Phân tích nguyên nhân gốc rễ bằng phương pháp 5 Whys
- Trực tiếp thực hiện quy trình phân tích **5 Whys** cho 3 ca lỗi nghiêm trọng nhất của Agent V1 để tìm ra nguyên nhân sâu xa nhất ở tầng hệ thống (chất lượng Chunking, chiến lược định tuyến Prompt, và thiết kế guardrail bảo mật).
- Phối hợp với thành viên phụ trách code để đề xuất giải pháp kỹ thuật cụ thể cho Agent V2.

### C. Biên soạn Báo cáo Phân tích Thất bại chung của nhóm ([failure_analysis.md](../failure_analysis.md))
- Thiết kế cấu trúc và hoàn thiện toàn bộ báo cáo phân tích thất bại nhóm, đảm bảo đáp ứng đầy đủ các tiêu chí chấm điểm và thống kê trực quan sự cải thiện vượt bậc của V2 so với V1 (Hit Rate tăng từ 20% lên 100%, Điểm Judge tăng từ 3.28 lên 4.33).

---

## 2. Chi tiết kỹ thuật & Lý thuyết (Technical Depth)

### A. Phương pháp luận 5 Whys và Root Cause Analysis (RCA)
- **Khái niệm**: 5 Whys là kỹ thuật lặp câu hỏi "Tại sao" năm lần để bóc tách các lớp triệu chứng bên ngoài, từ đó tìm ra nguyên nhân gốc rễ của một lỗi phần mềm hoặc hệ thống AI.
- **Ý nghĩa trong RAG Eval**: Trong hệ thống RAG, lỗi ở kết quả cuối cùng (Answer Quality) thường bị đổ lỗi cho LLM. Tuy nhiên, qua phân tích 5 Whys, ta phát hiện ra lỗi thực tế có thể nằm ở:
  1. *Ingestion Stage*: Định dạng tài liệu bị lỗi (mất bảng biểu, ký tự lạ).
  2. *Chunking Strategy*: Kích thước chunk quá nhỏ làm mất tính toàn vẹn của thông tin.
  3. *Retrieval Stage*: Trình cắm Vector DB thiếu cơ chế lọc meta hoặc Reranking.
  4. *Prompting Stage*: Hệ thống System Prompt quá lỏng lẻo.
- RCA giúp nhóm phát triển sửa đúng chỗ thay vì chỉnh sửa Prompt một cách mù quáng.

### B. Mean Reciprocal Rank (MRR) - Góc nhìn QA
- **Định nghĩa**: 
  $$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
- **Phân tích từ góc độ kiểm thử**: Đối với QA, Hit Rate chỉ cho biết tài liệu có xuất hiện hay không (nhị phân). MRR đo lường sự tối ưu hóa của trải nghiệm người dùng và giới hạn ngữ cảnh của LLM. Do LLM gặp hiện tượng *Lost in the Middle* (dễ bỏ qua thông tin nằm ở giữa context dài), việc tài liệu chuẩn xuất hiện ở vị trí số 1 ($rank=1$) có chất lượng câu trả lời cao hơn hẳn khi tài liệu đó xuất hiện ở vị trí số 3 ($rank=3$, $MRR=0.33$).

### C. Cohen's Kappa & Độ tin cậy của Giám khảo (Rater Reliability)
- **Định nghĩa**: Hệ số Cohen's Kappa ($\kappa$) đo lường sự đồng thuận giữa 2 Judge (LLM) sau khi loại trừ khả năng đồng thuận ngẫu nhiên:
  $$\kappa = \frac{p_o - p_e}{1 - p_e}$$
- **Ứng dụng thực tế**: Là một QA, tôi sử dụng $\kappa$ để đánh giá xem hệ thống chấm điểm tự động có đáng tin cậy không. Nếu $\kappa < 0.4$, điều đó có nghĩa là các Judge đang chấm điểm không nhất quán, Rubric chấm điểm của hệ thống chưa rõ ràng hoặc Prompt của Judge quá mơ hồ. Mục tiêu của nhóm là tinh chỉnh Rubric chấm điểm sao cho $\kappa \ge 0.6$ (đồng thuận cao).

### D. Sự đánh đổi giữa Chi phí và Chất lượng (Cost vs Quality)
- **Phân tích nghiệp vụ**: Việc sử dụng các mô hình hàng đầu (như GPT-4o) để chấm điểm mang lại chất lượng rất cao nhưng chi phí vận hành sẽ tăng phi mã.
- **Giải pháp tối ưu hóa chi phí (Tiered Evaluation)**: 
  - Đánh giá sơ bộ bằng mô hình giá rẻ như `gpt-4o-mini` (tiết kiệm 95% chi phí).
  - Hệ thống tự động theo dõi độ lệch điểm. Nếu độ chênh lệch giữa các Judge $> 1.0$, hệ thống mới kích hoạt mô hình cao cấp `gpt-4o` đóng vai trò Trọng tài (Referee) để đưa ra phán quyết cuối cùng.
  - Chiến lược này giúp tiết kiệm khoảng 40% chi phí chạy eval mà vẫn giữ nguyên độ chính xác của kết quả.

---

## 3. Giải quyết vấn đề (Problem Solving)

Trong quá trình thực hiện kiểm thử và phân tích hệ thống, tôi đã xử lý các vấn đề thực tế sau:
1. **Lỗi Thiên vị Chấm điểm (Leniency Bias) của LLM**: LLM có xu hướng chấm điểm rất cao (4 hoặc 5) cho các câu trả lời trôi chảy dù nội dung có lỗi nhỏ. Tôi đã đề xuất và phối hợp thiết kế lại **Rubric phân cấp chi tiết từ 1 đến 5 điểm** cho từng tiêu chí, yêu cầu Judge trích xuất bằng chứng (evidence) và so sánh trực tiếp với Ground Truth trước khi cho điểm, giúp hệ thống đánh giá trở nên khách quan và khắt khe hơn.
2. **Xử lý bất đồng ý kiến của Judge**: Khi hai Judge chấm điểm lệch nhau nhiều, việc lấy trung bình đơn giản sẽ làm lu mờ lỗi nghiêm trọng (ví dụ một Judge chấm 5, một Judge chấm 1 do phát hiện lỗi bảo mật). Tôi đã thiết kế cơ chế **Trọng tài phân xử (Tie-breaker)** để đảm bảo mọi lỗ hổng bảo mật nghiêm trọng đều được trọng tài xem xét và hạ điểm thích đáng.
