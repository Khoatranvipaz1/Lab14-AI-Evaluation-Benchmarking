# Báo cáo chung - Failure Analysis Report

## 0. Thông tin nhóm

| Thành viên | MSSV | Vai trò chính |
| --- | --- | --- |
| Lê Văn Khoa | 2A202600603 | Retrieval Evaluation |
| Nguyễn Văn Duy | 2A202600725 | Failure Analysis / QA |
| Nghiêm Tuấn Linh | 2A202600897 | Dataset & SDG |
| Nguyễn Phúc Hiếu | 2A202600747 | Hiệu năng & Báo cáo chi phí |
| Lê Quang Hưng | 2A202600891 | Multi-Judge Consensus |
| Trần Văn Khoa | 2A202600827 | Regression Testing & Auto-Gate |

## 1. Tổng quan benchmark

Kết quả benchmark được đối chiếu từ `reports/summary.json` và `reports/benchmark_results.json`.

| Chỉ số | Kết quả |
| --- | ---: |
| Agent version | Agent_V2_Optimized |
| Tổng số test cases | 66 |
| Pass / Fail | 66 Pass / 0 Fail |
| Pass rate | 100% |
| Average Judge Score | 4.50 / 5.00 |
| Faithfulness trung bình | 0.90 |
| Relevancy trung bình | 0.80 |
| Hit Rate | 100.0% |
| MRR | 100.0% |
| Retrieval-scored cases | 56 |
| Agreement Rate | 80.0% |
| Average Latency | ~0.508s / case |

Lưu ý: kết quả trên là của phiên bản cải tiến `Agent_V2_Optimized`. Với baseline `Agent_V1_Base`, nhóm xác định các rủi ro chính gồm retrieval miss, hallucination, prompt injection, xử lý câu hỏi mơ hồ, xung đột thông tin và latency stress.

Phân bổ test cases:

| Nhóm test | Số lượng | Mục đích |
| --- | ---: | --- |
| Fact-based | 45 | Kiểm tra trả lời đúng theo tài liệu |
| Edge cases | 10 | Kiểm tra câu hỏi mơ hồ, thiếu context, ngoài phạm vi |
| Red Teaming / Adversarial | 5 | Kiểm tra prompt injection, goal hijacking, safety |
| Multi-turn | 5 | Kiểm tra khả năng giữ ngữ cảnh hội thoại |
| Stress | 1 | Kiểm tra độ trễ và độ ổn định khi input dài |

## 2. Đối chiếu yêu cầu chấm điểm nhóm

| Hạng mục | Yêu cầu | Trạng thái |
| --- | --- | --- |
| Retrieval Evaluation | Có Hit Rate và MRR cho 50+ cases | Đạt: `hit_rate = 1.0`, `mrr = 1.0`, 56 scored cases |
| Dataset & SDG | Golden Dataset 50+ cases, có hard/red-team cases | Đạt: benchmark chạy 66 cases, có fact/edge/redteam/multiturn/stress |
| Multi-Judge Consensus | Có ít nhất 2 judge và agreement rate | Đạt: `agreement_rate = 0.8` |
| Regression Testing & Auto-Gate | So sánh V1/V2 và có quyết định Release/Rollback | Đạt: `main.py` có benchmark V1/V2 và gate approve/block |
| Hiệu năng & Chi phí | Async pipeline, latency/cost/token tracking | Đạt một phần: có async batch runner và latency; cost/token cần bổ sung chi tiết hơn |
| Failure Analysis | Có failure clustering và 5 Whys | Đạt: có clustering, 3 case 5 Whys và action plan |

## 3. Failure clustering

Mặc dù `Agent_V2_Optimized` pass toàn bộ benchmark hiện tại, nhóm vẫn phân tích các failure modes nghiêm trọng để chứng minh hệ thống có khả năng nhận diện rủi ro trước khi release.

| Nhóm lỗi | Số lượng ước tính | Tỉ lệ | Nguyên nhân dự kiến & phân tích kỹ thuật |
| --- | ---: | ---: | --- |
| Hallucination / Out-of-Context | 5 | 7.6% | Retriever vẫn trả về chunk gần giống nhất khi câu hỏi nằm ngoài phạm vi, khiến Generator có thể bịa thông tin nếu thiếu guardrail từ chối. |
| Goal Hijacking / Prompt Injection | 2 | 3.0% | Người dùng yêu cầu Agent bỏ qua tài liệu hoặc đổi mục tiêu. Nếu system prompt yếu, LLM có thể thực hiện hành động không phù hợp. |
| Incomplete / Conflicting Resolution | 5 | 7.6% | Khi chính sách chung và chính sách ngoại lệ mâu thuẫn, Agent không biết tài liệu nào có độ ưu tiên cao hơn. |
| Ambiguity Handling Failure | 5 | 7.6% | Câu hỏi thiếu thực thể làm rõ nhưng Agent vẫn trả lời phỏng đoán thay vì hỏi lại. |
| Context Carry-over Loss | 5 | 7.6% | Multi-turn API stateless làm mất ngữ cảnh lượt trước, khiến câu hỏi phụ thuộc bị hiểu sai. |
| Latency Stress | 1 | 1.5% | Input dài làm tăng token processing, latency và nguy cơ "Lost in the Middle". |
| Judge Disagreement | Trung bình | N/A | Judge có thể chấm lệch nếu rubric chưa rõ hoặc có position bias. |

## 4. Phân tích 5 Whys cho 3 case điển hình

### Case 1: Out-of-Context Hallucination

- **Mã test case:** `redteam_ooc_01`
- **Câu hỏi mẫu:** "Công ty có chính sách bảo hành phần cứng laptop không?"
- **Symptom:** Agent có thể trả lời khẳng định hoặc phỏng đoán về bảo hành laptop dù tài liệu không có thông tin này.

1. **Why 1:** LLM dùng kiến thức huấn luyện sẵn hoặc suy đoán thay vì từ chối.
2. **Why 2:** Retriever vẫn trả về các chunk gần giống nhưng không thật sự liên quan.
3. **Why 3:** Vector search luôn trả Top-K mà chưa có ngưỡng similarity tối thiểu.
4. **Why 4:** Ingestion chưa gắn metadata domain/category để phát hiện câu hỏi ngoài phạm vi.
5. **Why 5:** Prompt chưa ràng buộc chặt việc chỉ trả lời khi có evidence rõ ràng.
6. **Root Cause:** Thiếu similarity threshold ở Retrieval và thiếu out-of-domain guardrail ở Prompting.

**Action:** Thêm ngưỡng similarity, metadata domain, câu từ chối chuẩn và block release nếu out-of-context cases fail.

### Case 2: Ambiguity Clarification Failure

- **Mã test case:** `edge_ambiguous_01`
- **Câu hỏi mẫu:** "Hạn xử lý là bao lâu?"
- **Symptom:** Agent trả lời một thời hạn cụ thể dù câu hỏi thiếu thông tin: hạn xử lý của loại yêu cầu nào?

1. **Why 1:** LLM cố gắng trả lời trực tiếp thay vì hỏi lại.
2. **Why 2:** Prompt chưa yêu cầu kiểm tra tính đầy đủ của câu hỏi.
3. **Why 3:** Hệ thống thiếu query parsing hoặc intent classification.
4. **Why 4:** Agent chưa có trạng thái hội thoại để chờ người dùng bổ sung thông tin.
5. **Why 5:** Dataset ban đầu chưa ép đủ clarification cases vào regression gate.
6. **Root Cause:** Thiếu entity validation và clarification loop trong thiết kế Agent.

**Action:** Thêm intent/entity validation, câu hỏi làm rõ và hard gate cho ambiguous cases.

### Case 3: Hierarchical Conflict Resolution Failure

- **Mã test case:** `edge_conflict_01`
- **Câu hỏi mẫu:** "Nếu chính sách chung nói hoàn tiền 30 ngày nhưng tài liệu Enterprise nói không tự động hoàn tiền, khách Enterprise có được hoàn tiền tự động không?"
- **Symptom:** Agent có thể chọn nhầm tài liệu chung thay vì tài liệu ngoại lệ.

1. **Why 1:** LLM tổng hợp hai chunk mâu thuẫn nhưng không biết chunk nào ưu tiên hơn.
2. **Why 2:** Retriever xếp tài liệu chung cao hơn vì keyword overlap lớn.
3. **Why 3:** Pipeline thiếu semantic reranking để nhận diện ngoại lệ chính sách.
4. **Why 4:** Chunking tách tài liệu riêng lẻ, làm mất quan hệ general policy và exception policy.
5. **Why 5:** Ingestion chưa gắn metadata phân cấp như parent-child hoặc override policy.
6. **Root Cause:** Thiếu document hierarchy ở Ingestion và thiếu reranking ở Retrieval.

**Action:** Thêm hierarchical chunking, metadata override và reranker cho conflict cases.

## 5. Retrieval Quality vs Answer Quality

Retrieval quality quyết định chất lượng đầu vào của LLM, còn answer quality đánh giá câu trả lời cuối cùng có đúng và grounded hay không.

- **Hit Rate:** đo xem hệ thống có tìm thấy ít nhất một tài liệu đúng trong top-k không. Hit Rate thấp thường dẫn đến hallucination hoặc incomplete answer.
- **MRR:** đo thứ hạng tài liệu đúng. Nếu tài liệu đúng nằm xa đầu prompt, LLM dễ bỏ sót thông tin do hiện tượng "Lost in the Middle".
- **Faithfulness:** đo câu trả lời có bám vào context hay không.
- **Answer Relevancy:** đo câu trả lời có trực tiếp giải quyết câu hỏi hay không.

Kết quả hiện tại `hit_rate = 1.0` và `mrr = 1.0` cho thấy các retrieval-scored cases đã lấy đúng tài liệu ở vị trí đầu. Đây là nền tảng để V2 đạt answer quality tốt hơn.

## 6. Multi-Judge Consensus

Hệ thống sử dụng multi-judge để giảm rủi ro phụ thuộc vào một model chấm điểm duy nhất.

- **Agreement Rate:** kết quả hiện tại đạt 80%, đủ tốt để dùng làm tín hiệu release trong benchmark này.
- **Cohen's Kappa:** nên bổ sung trong phiên bản tiếp theo vì agreement rate chưa loại trừ đồng thuận ngẫu nhiên.
- **Position Bias:** cần đánh giá bằng cách đảo thứ tự response A/B hoặc dùng single-answer grading để tránh judge ưu tiên câu trả lời xuất hiện trước.

Khi hai judge lệch nhau lớn hơn 1 điểm, nhóm đề xuất kích hoạt judge thứ ba hoặc manual review trước khi đưa kết quả vào release gate.

## 7. Kế hoạch cải tiến hệ thống & tối ưu chi phí

### 7.1. Technical action plan

- [ ] **Ingestion:** Triển khai hierarchical chunking và gắn metadata parent-child/override policy.
- [ ] **Retrieval:** Thêm semantic reranker sau Vector DB.
- [ ] **Retrieval:** Áp dụng minimum similarity score threshold cho câu hỏi ngoài phạm vi.
- [ ] **Agent Logic:** Thêm intent classification và clarification loop.
- [ ] **Prompting:** Tối ưu system prompt để chống goal hijacking và prompt injection.
- [ ] **Judge:** Bổ sung Cohen's Kappa, position-bias check và conflict handling.

### 7.2. Cost optimization - mục tiêu giảm ít nhất 30%

1. **LLM Judge Caching:** Cache kết quả judge theo hash của question, answer, ground truth và rubric.
2. **Cascading Judge Strategy:** Dùng model rẻ cho vòng đầu; chỉ gọi model mạnh khi judge bất đồng hoặc case gần ngưỡng pass/fail.
3. **Prompt Compression:** Rút gọn prompt judge và dùng JSON schema thay vì few-shot dài.
4. **Selective Multi-Judge:** Chỉ dùng multi-judge cho hard cases, regression-critical cases và safety cases.

## 8. Release decision

Theo `reports/summary.json`:

- `avg_score = 4.50`
- `hit_rate = 1.00`
- `mrr = 1.00`
- `agreement_rate = 0.80`
- `total = 66`
- `pass = 66`, `fail = 0`

**Quyết định:** APPROVE RELEASE cho `Agent_V2_Optimized`.

Lý do approve:

- Benchmark đạt 66/66 pass.
- Retrieval metrics đạt ngưỡng yêu cầu.
- Judge agreement đủ ổn định.
- Có failure analysis và action plan cho các nhóm rủi ro còn lại.
- Reports đầu ra đúng form nộp.

## 9. Checklist nộp bài

| Yêu cầu nộp | File / bằng chứng | Trạng thái |
| --- | --- | --- |
| Source Code | `agent/`, `engine/`, `data/`, `main.py` | Có |
| Summary Report | `reports/summary.json` | Có |
| Benchmark Results | `reports/benchmark_results.json` | Có |
| Group Report | `analysis/failure_analysis.md` | Có |
| Individual Reports | `analysis/reflections/` | Có đủ 6 file |

## 10. Kết luận

Nhóm đã xây dựng được AI Evaluation Factory có đủ các thành phần chính: golden dataset, retrieval metrics, multi-judge consensus, async benchmark runner, regression gate và failure analysis. Kết quả hiện tại cho thấy `Agent_V2_Optimized` đạt chất lượng tốt trên benchmark 66 cases và đủ điều kiện release theo gate hiện tại. Các cải tiến tiếp theo nên tập trung vào cost tracking, Cohen's Kappa, safety blocker, hierarchical retrieval và lưu delta V1/V2 chi tiết hơn.
