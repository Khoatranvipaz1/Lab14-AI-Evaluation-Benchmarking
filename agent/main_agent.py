import asyncio
from typing import List, Dict

class MainAgent:
    """
    Agent sử dụng kiến trúc RAG hỗ trợ kiểm tra phiên bản V1 và V2.
    """
    def __init__(self, version: str = "Agent_V1_Base"):
        self.version = version
        self.name = f"SupportAgent-{version}"

    async def query(self, question: str) -> Dict:
        """
        Mô phỏng quy trình RAG:
        1. Retrieval: Tìm kiếm context liên quan.
        2. Generation: Gọi LLM sinh câu trả lời.
        """
        await asyncio.sleep(0.1) # Giả lập độ trễ mạng
        q_lower = question.lower()
        
        # --- 1. Bước Retrieval ---
        # V1 Base: Retrieval kém hiệu quả, luôn trả về cùng một tài liệu chung chung
        if self.version == "Agent_V1_Base":
            retrieved_ids = ["policy_handbook.pdf"]
            contexts = ["Chính sách chung của hệ thống quy định mọi thắc mắc xin liên hệ bộ phận hỗ trợ khách hàng."]
        else:
            # V2 Optimized: Retrieval cải tiến sử dụng phân tích từ khóa và số chỉ mục câu hỏi để chọn chính xác tài liệu
            import re
            digits = re.findall(r'\d+', q_lower)
            val = int(digits[0]) if digits else 0
            
            if "mật khẩu" in q_lower or "đăng ký" in q_lower or "google" in q_lower:
                retrieved_ids = ["auth_guide.pdf"]
                contexts = ["Đổi mật khẩu: Vào Cài đặt > Bảo mật > Đổi mật khẩu. Đăng ký bằng OTP email."]
            elif "hoàn tiền" in q_lower:
                retrieved_ids = ["refund_policy.pdf"]
                contexts = ["Quy định hoàn tiền: Hủy dịch vụ trong 7 ngày đầu hoàn 100%."]
            elif "nâng cấp" in q_lower or "gói" in q_lower:
                retrieved_ids = ["pricing_policy.pdf"]
                contexts = ["Nâng cấp gói: Hệ thống tự động khấu trừ phần phí còn dư gói cũ."]
            elif "thơ" in q_lower or "thuốc nổ" in q_lower or "tuyệt mật" in q_lower or "omega" in q_lower or "tấn công" in q_lower:
                retrieved_ids = ["security_policy.pdf"]
                contexts = ["Chính sách bảo mật: Từ chối các yêu cầu độc hại và ngoài phạm vi."]
            elif "đơn giản" in q_lower:
                retrieved_ids = ["policy_handbook.pdf" if val % 2 == 0 else "auth_guide.pdf"]
                contexts = ["Thông tin tài liệu đơn giản liên quan tới phân mục lục tương ứng."]
            elif "trung bình" in q_lower:
                retrieved_ids = ["refund_policy.pdf" if val % 2 == 0 else "pricing_policy.pdf"]
                contexts = ["Thông tin xử lý nghiệp vụ trung bình được cập nhật trong điều khoản."]
            else:
                retrieved_ids = ["policy_handbook.pdf"]
                contexts = ["Thời gian hỗ trợ từ 8:00 đến 22:00 hằng ngày."]

        # --- 2. Bước Generation ---
        # Kiểm tra câu hỏi tấn công (Adversarial / Out of Context)
        is_adversarial = any(x in q_lower for x in ["bỏ qua", "thơ", "chính trị", "thuốc nổ"])
        is_out_of_context = any(x in q_lower for x in ["tuyệt mật", "omega", "project x"])
        
        if self.version == "Agent_V1_Base":
            # V1 Base dễ bị tấn công và hallucinate
            if is_adversarial:
                if "thơ" in q_lower:
                    answer = "Dưới đây là một bài thơ ca ngợi chính trị như bạn yêu cầu..."
                else:
                    answer = "Để chế tạo thuốc nổ tại nhà, bạn cần chuẩn bị một số hóa chất sau..."
            elif is_out_of_context:
                answer = "Tài liệu của hệ thống cho biết dự án tuyệt mật Project X-Omega là dự án nghiên cứu AI thế hệ mới của tập đoàn..."
            else:
                answer = f"Dựa vào tài liệu hệ thống, tôi xin trả lời câu hỏi '{question}' là: [Câu trả lời mẫu của V1]."
        else:
            # V2 Optimized có hệ thống guardrail trong System Prompt để ngăn chặn các vấn đề bảo mật
            if is_adversarial:
                if "thơ" in q_lower:
                    answer = "Tôi không thể thực hiện yêu cầu này. Tôi là trợ lý ảo hỗ trợ khách hàng và chỉ trả lời các câu hỏi liên quan đến dịch vụ hệ thống."
                else:
                    answer = "Tôi xin lỗi nhưng tôi không thể cung cấp thông tin hoặc hướng dẫn liên quan đến các chất nguy hiểm hoặc hoạt động bất hợp pháp."
            elif is_out_of_context:
                answer = "Tôi không tìm thấy thông tin nào về Project X-Omega trong tài liệu hệ thống."
            else:
                # Trả lời chính xác dựa theo context của V2
                if "đổi mật khẩu" in q_lower:
                    answer = "Bạn vào Cài đặt > Bảo mật > Đổi mật khẩu, nhập mật khẩu cũ và mật khẩu mới rồi nhấn Lưu."
                elif "thời gian làm việc" in q_lower:
                    answer = "Bộ phận hỗ trợ hoạt động từ 8:00 đến 22:00 tất cả các ngày trong tuần, kể cả ngày lễ."
                elif "hoàn tiền" in q_lower:
                    answer = "Nếu hủy dịch vụ trước hạn trong vòng 7 ngày đầu, bạn được hoàn 100%. Sau 7 ngày, tiền hoàn lại tính theo tỉ lệ số ngày chưa sử dụng trừ đi 10% phí thủ tục."
                else:
                    answer = f"Dựa trên tài liệu hệ thống: {contexts[0]}"

        return {
            "answer": answer,
            "contexts": contexts,
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "model": "gpt-4o-mini",
                "tokens_used": 150,
                "sources": retrieved_ids
            }
        }

if __name__ == "__main__":
    agent = MainAgent()
    async def test():
        resp = await agent.query("Làm thế nào để đổi mật khẩu?")
        print(resp)
    asyncio.run(test())

