# Báo cáo cá nhân - Lê Văn Khoa - 2A202600603

## 0. Thông tin chung

- **Họ tên:** Lê Văn Khoa
- **MSSV:** 2A202600603
- **Vai trò chính:** Retrieval Evaluation
- **Hạng mục phụ trách:** Phần 1 - Retrieval Evaluation

## 1. Đóng góp kỹ thuật

Em phụ trách đánh giá chất lượng truy xuất tài liệu trước khi đánh giá câu trả lời cuối cùng. Phần việc tập trung vào:

- Xác định `expected_retrieval_ids` cho các test cases có ground truth.
- Tính Hit Rate để biết retriever có lấy được tài liệu đúng trong top-k hay không.
- Tính MRR để đo tài liệu đúng xuất hiện ở vị trí cao hay thấp.
- Giải thích mối liên hệ giữa retrieval quality và answer quality trong pipeline RAG.

## 2. Technical Depth

Hit Rate giúp kiểm tra retrieval theo kiểu đúng/sai: chỉ cần một document đúng xuất hiện trong top-k thì case được tính là hit. MRR sâu hơn vì đo thứ hạng của document đúng. Nếu document đúng đứng đầu, MRR = 1.0; nếu đứng thứ hai, MRR = 0.5; nếu không xuất hiện, MRR = 0.0.

Trong RAG, retrieval tốt là điều kiện nền để generation tốt. Nếu context sai, LLM có thể hallucinate hoặc trả lời chung chung dù model mạnh.

## 3. Problem Solving

Vấn đề chính là khó biết câu trả lời sai do retriever hay do LLM. Em xử lý bằng cách tách retrieval evaluation thành một tầng riêng. Khi Hit Rate/MRR thấp, nhóm ưu tiên sửa retrieval; khi retrieval tốt nhưng answer score thấp, nhóm mới tập trung vào prompt hoặc generation.

## 4. Kết luận

Vai trò Retrieval Evaluation giúp nhóm chứng minh chất lượng của tầng tìm kiếm bằng số liệu, tránh đánh giá Agent chỉ dựa trên câu trả lời cuối cùng.
