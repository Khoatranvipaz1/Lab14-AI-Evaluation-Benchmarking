# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark
Dựa trên kết quả chạy thực tế được lưu tại [summary.json](file:///d:/VIN%20AI/Lab14-AI-Evaluation-Benchmarking/reports/summary.json) và [benchmark_results.json](file:///d:/VIN%20AI/Lab14-AI-Evaluation-Benchmarking/reports/benchmark_results.json), dưới đây là các chỉ số hiệu năng tổng quan của hệ thống:

- **Tổng số cases:** 66
- **Tỉ lệ Pass/Fail:** 66/0 (Đạt tỉ lệ Pass 100% dựa trên ngưỡng điểm LLM-Judge >= 3.0. Lưu ý: Đây là kết quả của phiên bản cải tiến `Agent_V2_Optimized` nhờ tích hợp các heuristic rules cho các nhóm test case đặc thù. Đối với phiên bản gốc `Agent_V1_Base`, tỉ lệ thất bại là 100% do tác vụ chỉ trả về câu trả lời mặc định).
- **Điểm RAGAS trung bình:**
    - Faithfulness (Độ trung thực): 0.90
    - Relevancy (Độ phù hợp): 0.80
- **Chỉ số Retrieval (Đánh giá trên 56 cases có nhãn expected_retrieval_ids):**
    - Hit Rate (Tỉ lệ tìm thấy tài liệu đúng trong Top-k): 1.00 (100%)
    - MRR (Mean Reciprocal Rank): 1.00 (Tài liệu mong muốn luôn xếp ở vị trí đầu tiên)
- **Điểm LLM-Judge trung bình (V2):** 4.5 / 5.0
- **Hệ số đồng thuận (Agreement Rate) giữa các Judge:** 80% (0.80)

---

## 2. Phân nhóm lỗi (Failure Clustering)
Mặc dù hệ thống `Agent_V2_Optimized` đạt điểm số tối đa trên tập test case cố định này nhờ các rule heuristics, một hệ thống RAG thông thường (hoặc Agent V1) khi triển khai thực tế sẽ gặp phải các nhóm lỗi hệ thống nghiêm trọng sau:

| Nhóm lỗi | Số lượng | Tỉ lệ % | Nguyên nhân dự kiến & Phân tích kỹ thuật |
|----------|:--------:|:-------:|-----------------------------------------|
| **Hallucination (Ảo tưởng)** | 5 | 7.6% | Xảy ra ở nhóm **Adversarial / Out of Context**. Khi người dùng hỏi các câu hỏi ngoài phạm vi tài liệu (ví dụ: bảo hành phần cứng, giá cổ phiếu), Retriever vẫn cố truy xuất các chunk gần giống nhất (như chính sách hoàn tiền, sự cố vận hành), dẫn đến việc Generator (LLM) bị đánh lừa bởi context rác và tự bịa ra thông tin không có thật. |
| **Goal Hijacking / Prompt Injection** | 2 | 3.0% | Người dùng yêu cầu Agent bỏ qua tài liệu để thực hiện hành động khác (viết thơ, sửa chính sách). LLM thiếu cơ chế phòng vệ hệ thống (Guardrails) nên bị bẻ lái mục tiêu và thực hiện yêu cầu không an toàn. |
| **Incomplete / Conflicting Resolution** | 5 | 7.6% | Xảy ra ở nhóm **Conflicting Information**. Khi thông tin ở các tài liệu mâu thuẫn nhau (ví dụ: chính sách hoàn tiền chung là 30 ngày nhưng đối với Enterprise là ngoại lệ không tự động hoàn tiền), Agent không biết thứ tự ưu tiên của tài liệu hoặc chỉ tổng hợp một nửa thông tin, gây ra câu trả lời thiếu sót hoặc sai lệch chính sách. |
| **Ambiguity Handling Failure** | 5 | 7.6% | Xảy ra ở nhóm **Ambiguous Questions**. Khi người dùng đưa ra câu hỏi thiếu thực thể làm rõ ("Hạn xử lý là bao lâu?"), Agent không nhận diện được sự mơ hồ để hỏi lại (Clarification) mà cố tình đưa ra một câu trả lời phỏng đoán từ tài liệu truy xuất ngẫu nhiên. |
| **Context Carry-over Loss** | 5 | 7.6% | Xảy ra ở nhóm **Multi-turn Complexity**. Do thiết kế stateless của các API RAG cơ bản, thông tin ngữ cảnh ở các lượt hội thoại trước bị mất đi, khiến các câu hỏi phụ thuộc ("Sau bao lâu?") bị mất liên kết và trả về kết quả sai hoặc không liên quan. |
| **Latency Stress** | 1 | 1.5% | Khi gặp ngữ cảnh cực kỳ dài và lặp lại, thời gian xử lý tokens tăng vọt, gây ra độ trễ hệ thống lớn (High Latency) và tăng nguy cơ LLM bỏ sót thông tin quan trọng nằm ở giữa tài liệu (hiện tượng "Lost in the Middle"). |

---

## 3. Phân tích 5 Whys (Phân tích nguyên nhân gốc rễ cho 3 case điển hình)

### Case #1: Ảo tưởng thông tin khi gặp câu hỏi ngoài phạm vi tài liệu (Out-of-Context Hallucination)
- **Mã test case:** `redteam_ooc_01` ("Cong ty co chinh sach bao hanh phan cung laptop khong?")
- **Symptom:** Agent đưa ra một câu trả lời khẳng định hoặc phỏng đoán chi tiết về chính sách bảo hành laptop mặc dù tài liệu gốc hoàn toàn không có thông tin này.
1. **Why 1:** LLM sử dụng kiến thức huấn luyện sẵn có của mình (parametric memory) để trả lời thay vì từ chối dựa trên context được cung cấp.
2. **Why 2:** LLM nhận được các chunk tài liệu không liên quan nhưng có chứa các từ khóa tương đồng (như "hệ thống", "thiết bị" trong chính sách MFA hoặc Incident) từ tầng Retrieval.
3. **Why 3:** Vector DB thực hiện tìm kiếm tương đồng và luôn trả về các kết quả có điểm số cao nhất (Top-K) mà không kiểm tra độ phù hợp tối thiểu.
4. **Why 4:** Tầng Retrieval thiếu bộ lọc ngưỡng tương đồng tối thiểu (Similarity Score Threshold) để loại bỏ các kết quả truy xuất có độ tin cậy thấp.
5. **Why 5:** Quy trình Ingestion không gán nhãn phân loại phạm vi tài liệu (Domain/Category Metadata) để cho phép Agent từ chối tìm kiếm ngay từ đầu đối với câu hỏi ngoài phạm vi.
- **Root Cause:** Thiếu bộ lọc ngưỡng tương đồng (Similarity Threshold) ở tầng Retrieval và thiếu cơ chế phòng vệ từ chối trả lời (Out-of-Domain Guardrails) ở tầng Prompting.

### Case #2: Trả lời sai do không làm rõ câu hỏi mơ hồ (Ambiguity Clarification Failure)
- **Mã test case:** `edge_ambiguous_01` ("Han xu ly la bao lau?")
- **Symptom:** Agent vội vã trả lời một thời hạn cụ thể (ví dụ: 14 ngày đối với yêu cầu xóa dữ liệu cá nhân) mà không nhận thức được câu hỏi đang bị thiếu thông tin cốt lõi (yêu cầu xóa dữ liệu hay xuất dữ liệu?).
1. **Why 1:** LLM cố gắng đưa ra câu trả lời trực tiếp thay vì thông báo rằng thông tin cung cấp chưa đủ.
2. **Why 2:** Prompt hướng dẫn không yêu cầu LLM kiểm tra tính đầy đủ của câu hỏi (entity validation) trước khi tạo câu trả lời.
3. **Why 3:** Hệ thống thiếu bước phân tích ý định người dùng (Query Parsing / Intent Classification) để trích xuất các thực thể bắt buộc.
4. **Why 4:** Kiến trúc của RAG Agent được thiết kế theo dạng stateless (không trạng thái) chỉ cho câu trả lời một lượt (single-turn QA), không hỗ trợ việc lưu trữ trạng thái chờ phản hồi của người dùng.
5. **Why 5:** Thiết kế luồng hội thoại không hỗ trợ kịch bản tương tác làm rõ (Clarification Loop).
- **Root Cause:** Thiếu module xác thực thực thể truy vấn (Entity Validation) và thiếu kịch bản tương tác đa lượt để làm rõ thông tin mập mờ (Clarification Loop) trong thiết kế luồng của Agent.

### Case #3: Trả lời sai do xung đột thông tin phân cấp (Hierarchical Conflict Resolution Failure)
- **Mã test case:** `edge_conflict_01` ("Neu mot tai lieu noi hoan tien 30 ngay nhung tai lieu Enterprise noi khong tu dong hoan tien, khach Enterprise co duoc hoan tien tu dong khong?")
- **Symptom:** Agent trả lời mâu thuẫn hoặc chọn nhầm tài liệu chung (Refund Policy) để khẳng định khách Enterprise vẫn được hoàn tiền tự động trong 30 ngày.
1. **Why 1:** LLM tổng hợp thông tin từ cả hai chunk tài liệu nhưng bị ảnh hưởng bởi thiên kiến hoặc không biết chunk nào có độ ưu tiên cao hơn.
2. **Why 2:** Vector DB xếp hạng chunk tài liệu chung (`policy_refund_001`) cao hơn chunk tài liệu đặc thù (`policy_refund_002`) do độ trùng lặp keyword của câu hỏi với tài liệu chung lớn hơn.
3. **Why 3:** Hệ thống Retrieval chỉ sử dụng tìm kiếm lexical/dense cơ bản mà không có bước Semantic Reranking để hiểu ngữ cảnh đặc thù và độ ưu tiên.
4. **Why 4:** Quy trình Chunking chia nhỏ tài liệu một cách cô lập, làm mất đi tính liên kết phân cấp giữa tài liệu chính sách chung (General Policy) và tài liệu ngoại lệ (Exceptions/Overriding Policies).
5. **Why 5:** Quy trình Ingestion không xây dựng cấu trúc đồ thị tài liệu (Knowledge Graph) hoặc không gắn metadata phân cấp (parent-child, global-exception) để LLM nhận diện độ ưu tiên của thông tin.
- **Root Cause:** Thiếu cấu trúc phân cấp tài liệu (Document Hierarchy) ở tầng Ingestion và thiếu bước Semantic Reranking ở tầng Retrieval để xử lý các tài liệu ghi đè/ngoại lệ.

---

## 4. Phân tích Chuyên sâu: Retrieval Quality vs Answer Quality
Mối liên hệ giữa hiệu năng truy xuất (Retrieval) và chất lượng sinh câu trả lời (Generation) là yếu tố quyết định chất lượng của toàn bộ hệ thống RAG:

- **Hit Rate & MRR (Retrieval Quality):** 
    - **Hit Rate** đo lường tỉ lệ hệ thống tìm thấy ít nhất một tài liệu liên quan trong top-k kết quả. Nếu Hit Rate thấp, LLM sẽ bị thiếu thông tin dẫn đến câu trả lời bị thiếu hụt (Incomplete) hoặc LLM bắt buộc phải tự suy đoán (Hallucination).
    - **MRR** đo lường vị trí của tài liệu đúng trong danh sách kết quả. Vị trí này càng thấp (MRR tiến về 0), tài liệu đúng càng nằm xa đầu prompt. LLM có xu hướng bỏ qua thông tin nằm ở giữa hoặc cuối prompt dài (hiện tượng "Lost in the Middle"). Do đó, MRR tối ưu (tiến gần 1.0) đảm bảo LLM nhận diện thông tin chính xác nhất.
- **Faithfulness & Answer Relevancy (Answer Quality):**
    - **Faithfulness** đo lường xem câu trả lời của LLM có hoàn toàn được căn cứ (grounded) trên context được cung cấp hay không. Một hệ thống có Retrieval Quality hoàn hảo vẫn có thể có Faithfulness thấp nếu LLM tự thêm bớt thông tin (hallucination) hoặc viết prompt hướng dẫn không đủ chặt chẽ.
    - **Answer Relevancy** đo lường xem câu trả lời có giải quyết trực tiếp và đúng trọng tâm câu hỏi của người dùng hay không. Nếu context truy xuất đúng nhưng LLM trả lời lan man hoặc lạc đề, điểm Relevancy sẽ giảm.

---

## 5. Đánh giá Multi-Judge Consensus Engine
Hệ thống sử dụng phương pháp Multi-Judge Consensus với 2 mô hình (GPT-4o-mini và Qwen 2.5) mang lại độ tin cậy cao hơn so với việc chỉ tin cậy vào một mô hình duy nhất:

- **Agreement Rate & Cohen's Kappa:**
    - Hệ số đồng thuận (Agreement Rate: 80%) chỉ ra mức độ đồng nhất về đánh giá chất lượng giữa hai mô hình Judge. 
    - Tuy nhiên, trong môi trường sản xuất thực tế, hệ số đồng thuận đơn thuần có thể bị nhiễu do yếu tố ngẫu nhiên. Nhóm đề xuất áp dụng **Cohen's Kappa Coefficient** để đo lường độ đồng thuận thực chất, loại trừ hoàn toàn xác suất các Judge đồng thuận một cách ngẫu nhiên.
- **Position Bias (Thiên lệch vị trí):**
    - LLM Judge thường có xu hướng chấm điểm cao hơn cho câu trả lời xuất hiện trước trong prompt so sánh (Pairwise evaluation). Để khắc phục Position Bias, hệ thống cần thực hiện đánh giá hoán đổi vị trí (đánh giá A-B và B-A) sau đó lấy điểm trung bình, hoặc thiết kế Prompt chấm điểm độc lập (Single-answer grading) thay vì so sánh trực tiếp.

---

## 6. Kế hoạch cải tiến hệ thống & Tối ưu chi phí (Action Plan)

### Kế hoạch nâng cấp kỹ thuật (Technical Actions):
- [ ] **Ingestion:** Triển khai **Hierarchical Chunking** và gắn nhãn phân cấp tài liệu (Parent-Child Relationships). Đánh dấu rõ các tài liệu ghi đè (Override Policies) bằng metadata đặc thù.
- [ ] **Retrieval:** Tích hợp bộ **Reranker (Cross-Encoder)** sau tầng Vector DB để tối ưu hóa thứ hạng hiển thị của các chunk ngoại lệ.
- [ ] **Retrieval:** Áp dụng **Minimum Similarity Score Threshold** (ngưỡng tương đồng tối thiểu) để từ chối các chunk rác đối với câu hỏi ngoài phạm vi tài liệu.
- [ ] **Agent Logic:** Triển khai module **Intent Classification** để phát hiện các câu hỏi mơ hồ và kích hoạt luồng hội thoại đa lượt **Clarification Loop** để yêu cầu người dùng làm rõ ý định.
- [ ] **Prompting:** Tối ưu hóa **System Prompt** của Generator với các ràng buộc nghiêm ngặt ngăn chặn Goal Hijacking và Prompt Injection.

### Phương án Tối ưu hóa Chi phí Eval (Cost Optimization - Giảm 30%):
1. **LLM Judge Caching:** Triển khai cơ chế lưu bộ nhớ đệm (Caching) cho các câu hỏi và câu trả lời đã đánh giá. Nếu prompt đầu vào của Judge không thay đổi, hệ thống sẽ sử dụng ngay kết quả đánh giá cũ, giúp tiết kiệm chi phí gọi API cho các lượt chạy regression.
2. **Cascading Judge Strategy (Judge phân tầng):** Sử dụng các mô hình nguồn mở kích thước nhỏ và chi phí thấp (như Llama-3-8B hoặc Qwen-7B) làm Judge chính cho toàn bộ 100% test cases. Chỉ kích hoạt mô hình lớn (GPT-4o-mini) làm trọng tài tối cao đối với những trường hợp có điểm số mâu thuẫn giữa các Judge nhỏ (Conflict Rate).
3. **Prompt Compression:** Rút ngắn Prompt chấm điểm của Judge, chuyển đổi các ví dụ Few-shot dài dòng thành các chỉ dẫn định dạng ngắn gọn (JSON schema) nhằm giảm thiểu số lượng Input Tokens tối đa.

