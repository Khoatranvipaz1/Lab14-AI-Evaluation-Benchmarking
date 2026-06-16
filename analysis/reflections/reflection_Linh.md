# Reflection Report - Lab 14: AI Evaluation Benchmarking

## 1. Vai trò và đóng góp cá nhân

Trong bài lab này, tôi tập trung triển khai phần SDG (Synthetic Data Generation) để tạo Golden Dataset phục vụ benchmark AI Agent. Mục tiêu chính của phần này là biến file `data/synthetic_gen.py` từ bản placeholder chỉ tạo 1 case mẫu thành một bộ sinh dữ liệu kiểm thử có cấu trúc, đủ số lượng và có thể dùng trực tiếp trong pipeline benchmark.

Kết quả triển khai:
- Tạo được `data/golden_set.jsonl` với 66 test cases, vượt yêu cầu tối thiểu 50 cases.
- Mỗi case có đầy đủ `question`, `expected_answer`, `context`, `expected_retrieval_ids` và `metadata`.
- Dataset bao gồm nhiều nhóm kiểm thử: fact-check, out-of-context, ambiguous, conflicting-information, multi-turn và latency-stress.
- Các case có `expected_retrieval_ids` để hỗ trợ tính Hit Rate và MRR cho bước Retrieval Evaluation.

## 2. Thiết kế SDG và Golden Dataset

Tôi thiết kế SDG theo hướng deterministic, tức là có thể chạy lại nhiều lần và tạo ra cùng một Golden Dataset mà không phụ thuộc API key hoặc model bên ngoài. Cách này phù hợp với môi trường lab vì giúp kết quả ổn định, dễ debug và dễ chấm tự động.

Dataset được xây từ một corpus nội bộ gồm các chính sách giả lập như refund, MFA, SLA, billing, API limit, privacy request, data retention và security disclosure. Từ mỗi tài liệu, generator tạo nhiều câu hỏi kiểm tra khả năng trả lời dựa trên nguồn.

Ngoài các câu hỏi thông thường, tôi bổ sung các nhóm hard cases:
- `out-of-context`: kiểm tra agent có biết nói không có thông tin thay vì hallucinate hay không.
- `ambiguous`: kiểm tra agent có biết hỏi lại khi câu hỏi thiếu ngữ cảnh hay không.
- `conflicting-information`: kiểm tra agent xử lý ngoại lệ hoặc thông tin dễ mâu thuẫn như thế nào.
- `multi-turn`: kiểm tra khả năng dùng ngữ cảnh hội thoại.
- `latency-stress`: kiểm tra phản ứng với context dài.

Điểm quan trọng nhất là mỗi case có mapping ground truth retrieval. Ví dụ câu hỏi về chính sách hoàn tiền sẽ map về `policy_refund_001`, còn câu hỏi về giới hạn API sẽ map về `policy_api_limit_001`. Mapping này giúp hệ thống không chỉ chấm câu trả lời cuối cùng, mà còn kiểm tra agent có lấy đúng tài liệu trước khi sinh câu trả lời hay không.

## 3. Hiểu biết kỹ thuật

Hit Rate cho biết trong top-k tài liệu được retrieval có ít nhất một tài liệu đúng hay không. Đây là metric quan trọng để phát hiện lỗi retrieval. Nếu Hit Rate thấp, agent có thể trả lời sai dù prompt và LLM tốt, vì nó không nhận được context đúng.

MRR (Mean Reciprocal Rank) đo tài liệu đúng xuất hiện ở vị trí thứ mấy trong danh sách retrieved documents. Nếu tài liệu đúng đứng đầu, điểm là 1.0; nếu đứng thứ hai, điểm là 0.5. MRR giúp đánh giá chất lượng xếp hạng, không chỉ đánh giá có tìm thấy hay không.

Multi-Judge Consensus giúp giảm rủi ro phụ thuộc vào một judge duy nhất. Nếu hai judge cho điểm lệch nhau quá nhiều, hệ thống nên đánh dấu conflict hoặc dùng cơ chế xử lý lại. Trong benchmark hiện tại, `agreement_rate` đạt 0.8, cho thấy pipeline đã có trường đo độ đồng thuận, dù phần judge vẫn còn là mô phỏng.

Position Bias là hiện tượng judge thiên vị câu trả lời ở vị trí A hoặc B khi so sánh hai response. Để kiểm tra, có thể đảo vị trí response và chấm lại. Nếu kết quả thay đổi mạnh chỉ vì đổi vị trí, judge chưa đáng tin cậy.

## 4. Kết quả chạy benchmark

Sau khi triển khai SDG, tôi chạy lại pipeline:

```bash
python data/synthetic_gen.py
$env:PYTHONIOENCODING='utf-8'; python main.py
$env:PYTHONIOENCODING='utf-8'; python check_lab.py
```

Kết quả trong `reports/summary.json`:
- Tổng số cases: 66
- Điểm trung bình: 4.5 / 5.0
- Hit Rate: 1.0
- Agreement Rate: 0.8
- Phiên bản benchmark: `Agent_V2_Optimized`

`check_lab.py` xác nhận bài có đủ `reports/summary.json`, `reports/benchmark_results.json` và `analysis/failure_analysis.md`.

Một vấn đề nhỏ khi chạy trên PowerShell/Windows là `main.py` có emoji, nên console mặc định có thể gặp lỗi encoding `cp1252`. Tôi xử lý bằng cách đặt `PYTHONIOENCODING=utf-8` trước khi chạy script.

## 5. Bài học và hướng cải tiến

Qua phần SDG, tôi nhận ra chất lượng benchmark phụ thuộc rất lớn vào chất lượng Golden Dataset. Nếu dataset chỉ có câu hỏi dễ, agent có thể đạt điểm cao nhưng không phản ánh năng lực thật. Vì vậy, cần có cả câu hỏi thường, câu hỏi khó, câu hỏi bẫy và câu hỏi thiếu thông tin.

Hướng cải tiến tiếp theo:
- Kết nối SDG với LLM thật để sinh thêm paraphrase và adversarial cases đa dạng hơn.
- Bổ sung trường `expected_behavior` để phân biệt rõ giữa trả lời trực tiếp, hỏi lại và từ chối.
- Mở rộng `expected_retrieval_ids` thành chunk-level IDs thay vì doc-level IDs để đo retrieval chính xác hơn.
- Tính thêm chi phí token cho từng case để đánh giá trade-off giữa chất lượng và chi phí.
- Cập nhật failure analysis dựa trên các nhóm case mới để chỉ ra lỗi thuộc ingestion, chunking, retrieval hay prompting.

Tổng kết lại, phần SDG đã cung cấp nền tảng dữ liệu đủ tốt để các module Retrieval Evaluation, Multi-Judge và Regression Gate có dữ liệu đầu vào thực tế hơn. Đây là bước quan trọng vì một evaluation system chỉ đáng tin khi bộ đề kiểm thử đủ rộng, có ground truth rõ ràng và có các tình huống đủ khó để làm lộ lỗi của agent.
