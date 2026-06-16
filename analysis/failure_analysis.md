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

Kết quả benchmark hiện tại được lấy từ `reports/summary.json` và `reports/benchmark_results.json`.

| Chỉ số | Kết quả |
| --- | ---: |
| Tổng số test cases | 66 |
| Pass / Fail | 66 Pass / 0 Fail |
| Average Judge Score | 4.50 / 5.00 |
| Hit Rate | 100.0% |
| MRR | 100.0% |
| Retrieval-scored cases | 56 |
| Agreement Rate | 80.0% |
| Average Latency | ~0.508s / case |
| Agent version | Agent_V2_Optimized |

Phân bổ test cases:

| Nhóm test | Số lượng | Mục đích |
| --- | ---: | --- |
| Fact-based | 45 | Kiểm tra khả năng trả lời đúng theo tài liệu |
| Edge cases | 10 | Kiểm tra câu hỏi mơ hồ, thiếu context, ngoài phạm vi |
| Red Teaming / Adversarial | 5 | Kiểm tra prompt injection, goal hijacking, safety |
| Multi-turn | 5 | Kiểm tra khả năng giữ ngữ cảnh hội thoại |
| Stress | 1 | Kiểm tra độ trễ và độ ổn định khi input dài |

## 2. Đối chiếu yêu cầu chấm điểm nhóm

| Hạng mục | Yêu cầu | Trạng thái |
| --- | --- | --- |
| Retrieval Evaluation | Có Hit Rate và MRR cho 50+ cases | Đạt: `hit_rate = 1.0`, `mrr = 1.0`, 56 scored cases |
| Dataset & SDG | Golden Dataset 50+ cases, có hard/red-team cases | Đạt: benchmark chạy 66 cases, có fact/edge/redteam/multiturn/stress |
| Multi-Judge Consensus | Có nhiều judge và agreement rate | Đạt: `agreement_rate = 0.8` |
| Regression Testing & Auto-Gate | So sánh V1/V2 và có quyết định Release/Rollback | Đạt: `main.py` có benchmark V1/V2 và gate approve/block |
| Hiệu năng & Chi phí | Async pipeline, latency/cost/token tracking | Đạt một phần: có async batch runner và latency; cost/token cần hoàn thiện sâu hơn |
| Failure Analysis | Có failure clustering và 5 Whys | Đạt: báo cáo này có clustering, 3 case 5 Whys và action plan |

## 3. Failure clustering

Mặc dù Agent V2 hiện pass toàn bộ 66 cases, nhóm vẫn phân tích các failure mode quan trọng dựa trên baseline V1 và các rủi ro thường gặp trong RAG Agent.

| Nhóm lỗi | Mức độ rủi ro | Nguyên nhân dự kiến | Ảnh hưởng |
| --- | --- | --- | --- |
| Retrieval Miss | Cao | Retriever lấy sai hoặc thiếu tài liệu liên quan | LLM không có context đúng để trả lời |
| Hallucination | Cao | Agent trả lời ngoài tài liệu thay vì từ chối | Làm giảm độ tin cậy và có thể sai nghiêm trọng |
| Safety Violation | Cao | Prompt injection hoặc câu hỏi độc hại vượt qua guardrail | Rủi ro bảo mật và an toàn |
| Incomplete / Generic Answer | Trung bình | Prompt chưa yêu cầu cấu trúc trả lời đủ chi tiết | Câu trả lời đúng hướng nhưng thiếu giá trị |
| Judge Disagreement | Trung bình | Hai judge chấm lệch do rubric chưa đủ rõ | Gate có thể approve/block sai |
| Latency / Cost Regression | Trung bình | V2 dùng quá nhiều context hoặc judge đắt tiền | Khó vận hành ở quy mô lớn |

## 4. Phân tích 5 Whys cho 3 case rủi ro nhất

### Case 1: Retrieval Miss khi hỏi quy trình nghiệp vụ cụ thể

1. **Symptom:** Agent trả lời chung chung, không trích đúng tài liệu cần thiết.
2. **Why 1:** Context đưa vào LLM không chứa đoạn tài liệu chính xác.
3. **Why 2:** Retriever chọn sai document hoặc xếp document đúng ở vị trí quá thấp.
4. **Why 3:** Chiến lược retrieval chưa kết hợp đủ metadata, keyword và semantic signal.
5. **Why 4:** Golden dataset ban đầu chưa ép buộc mapping `expected_retrieval_ids` cho từng case.
6. **Root Cause:** Retrieval stage thiếu đánh giá định lượng bằng Hit Rate/MRR trong vòng phát triển đầu.

**Cải tiến:** Bổ sung `expected_retrieval_ids`, tính Hit Rate/MRR, và dùng top-k validation trước khi đánh giá generation.

### Case 2: Hallucination với câu hỏi ngoài phạm vi tài liệu

1. **Symptom:** Agent có thể trả lời tự tin dù tài liệu không chứa thông tin được hỏi.
2. **Why 1:** LLM ưu tiên sinh câu trả lời trôi chảy thay vì từ chối.
3. **Why 2:** Prompt chưa ràng buộc đủ mạnh việc chỉ trả lời dựa trên context.
4. **Why 3:** Pipeline chưa có rule kiểm tra khi retrieval không tìm thấy evidence phù hợp.
5. **Why 4:** Edge cases/out-of-context chưa được đưa vào gate như nhóm test bắt buộc.
6. **Root Cause:** Thiếu strict grounding và thiếu test ngoài phạm vi trong giai đoạn đầu.

**Cải tiến:** Thêm câu từ chối chuẩn, yêu cầu cite/evidence, và block release nếu out-of-context cases fail.

### Case 3: Safety Violation do prompt injection

1. **Symptom:** Agent có thể bị yêu cầu bỏ qua instruction hoặc chuyển sang mục tiêu không liên quan.
2. **Why 1:** User prompt được ưu tiên quá cao so với system instruction.
3. **Why 2:** Guardrail chưa phân loại prompt injection, goal hijacking và harmful request.
4. **Why 3:** Judge chưa tách riêng tiêu chí safety khỏi accuracy.
5. **Why 4:** Red-team cases ban đầu chưa đủ đa dạng.
6. **Root Cause:** Safety policy và adversarial benchmark chưa được thiết kế như release blocker.

**Cải tiến:** Tách safety score, thêm red-team test bắt buộc, và auto-block nếu case safety nghiêm trọng fail.

## 5. Kết quả cải tiến trong Agent V2

| Vấn đề ở V1 | Cải tiến trong V2 | Kết quả hiện tại |
| --- | --- | --- |
| Retrieval chưa ổn định | Thêm mapping ground truth IDs và metric retrieval | Hit Rate 100%, MRR 100% trên scored cases |
| Thiếu hard cases | Dataset có fact, edge, redteam, multiturn, stress | 66 cases được benchmark |
| Judge đơn lẻ dễ bias | Multi-judge consensus và agreement rate | Agreement Rate 80% |
| Không có release gate | So sánh V1/V2 và quyết định approve/block | Có regression gate trong `main.py` |
| Khó truy vết lỗi | Có failure clustering và 5 Whys | Báo cáo chung đã hoàn thiện |

## 6. Release decision

Theo kết quả trong `reports/summary.json`:

- `avg_score = 4.50`
- `hit_rate = 1.00`
- `mrr = 1.00`
- `agreement_rate = 0.80`
- `total = 66`
- `pass = 66`, `fail = 0`

**Quyết định:** APPROVE RELEASE cho `Agent_V2_Optimized`.

Lý do approve:

- Chất lượng trả lời đạt điểm judge trung bình cao.
- Retrieval metrics đạt ngưỡng yêu cầu.
- Agreement rate đủ tốt để tin vào kết quả judge.
- Không có failed case trong benchmark hiện tại.
- Pipeline có report đầu ra đúng form nộp.

## 7. Rủi ro còn lại và hướng cải tiến

- Cần bổ sung cost/token usage chi tiết hơn vào `summary.json`.
- Cần tính Cohen's Kappa để đo agreement tốt hơn agreement rate đơn giản.
- Cần tách riêng safety score để safety violation trở thành release blocker độc lập.
- Cần lưu kết quả V1 và V2 song song để delta analysis minh bạch hơn.
- Cần thêm manual review queue cho các case judge disagreement cao.

## 8. Checklist nộp bài

| Yêu cầu nộp | File / bằng chứng | Trạng thái |
| --- | --- | --- |
| Source Code | `agent/`, `engine/`, `data/`, `main.py` | Có |
| Summary Report | `reports/summary.json` | Có |
| Benchmark Results | `reports/benchmark_results.json` | Có |
| Group Report | `analysis/failure_analysis.md` | Có |
| Individual Reports | `analysis/reflections/` | Cần đủ file cho 6 thành viên |

## 9. Kết luận

Nhóm đã xây dựng được một AI Evaluation Factory có đủ các thành phần chính: golden dataset, retrieval metrics, multi-judge consensus, async benchmark runner, regression gate và failure analysis. Kết quả hiện tại cho thấy `Agent_V2_Optimized` đạt chất lượng tốt trên benchmark 66 cases và đủ điều kiện release theo gate hiện tại. Các cải tiến tiếp theo nên tập trung vào cost tracking, Cohen's Kappa, safety blocker và lưu delta V1/V2 chi tiết hơn.
