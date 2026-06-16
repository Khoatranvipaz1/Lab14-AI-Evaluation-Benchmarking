import asyncio
import re
from typing import Dict, List

from data.synthetic_gen import SOURCE_DOCUMENTS


STOPWORDS = {
    "a", "ai", "anh", "bao", "bi", "bo", "ca", "can", "cau", "cho", "co",
    "cua", "de", "duoc", "gi", "hay", "he", "hoi", "khach", "khong", "la",
    "lam", "luu", "mot", "nay", "neu", "nguoi", "nhu", "o", "phai", "qua",
    "sao", "tai", "thi", "thong", "tin", "toi", "trong", "ve", "voi", "xu",
}


def tokenize(text: str) -> List[str]:
    return [
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) > 1 and token not in STOPWORDS
    ]

class MainAgent:
    """
    Đây là Agent mẫu sử dụng kiến trúc RAG đơn giản.
    Sinh viên nên thay thế phần này bằng Agent thực tế đã phát triển ở các buổi trước.
    """
    def __init__(self):
        self.name = "SupportAgent-v1"
        self.documents = SOURCE_DOCUMENTS

    def retrieve(self, question: str, top_k: int = 3) -> List[Dict]:
        query_terms = set(tokenize(question))
        scored_docs = []

        for doc in self.documents:
            searchable_text = " ".join([doc["doc_id"], doc["title"], doc["text"]])
            doc_terms = set(tokenize(searchable_text))
            overlap_score = len(query_terms & doc_terms)

            if overlap_score > 0:
                scored_docs.append((overlap_score, doc))

        scored_docs.sort(key=lambda item: (-item[0], item[1]["doc_id"]))
        return [doc for _, doc in scored_docs[:top_k]]

    async def query(self, question: str) -> Dict:
        """
        Mô phỏng quy trình RAG:
        1. Retrieval: Tìm kiếm context liên quan.
        2. Generation: Gọi LLM để sinh câu trả lời.
        """
        # Giả lập độ trễ mạng/LLM
        await asyncio.sleep(0.5) 
        
        retrieved_docs = self.retrieve(question, top_k=3)
        retrieved_ids = [doc["doc_id"] for doc in retrieved_docs]
        contexts = [doc["text"] for doc in retrieved_docs]

        return {
            "answer": f"Dựa trên tài liệu hệ thống, tôi xin trả lời câu hỏi '{question}' như sau: [Câu trả lời mẫu].",
            "retrieved_ids": retrieved_ids,
            "contexts": contexts,
            "metadata": {
                "model": "gpt-4o-mini",
                "tokens_used": 150,
                "sources": retrieved_ids,
            }
        }

if __name__ == "__main__":
    agent = MainAgent()
    async def test():
        resp = await agent.query("Làm thế nào để đổi mật khẩu?")
        print(resp)
    asyncio.run(test())
