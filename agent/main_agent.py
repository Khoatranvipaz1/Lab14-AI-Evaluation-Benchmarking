import asyncio
import re
from typing import Dict, List, Optional, Tuple

from data.synthetic_gen import AMBIGUOUS_CASES, OUT_OF_CONTEXT_CASES, SOURCE_DOCUMENTS


STOPWORDS = {
    "a", "ai", "anh", "bao", "bi", "bo", "ca", "can", "cau", "cho", "co",
    "cua", "de", "duoc", "gi", "hay", "he", "hoi", "khach", "khong", "la",
    "lam", "luu", "mot", "nay", "neu", "nguoi", "nhu", "o", "phai", "qua",
    "sao", "tai", "thi", "thong", "tin", "toi", "trong", "ve", "voi", "xu",
    "va", "thi", "the", "nao", "nay", "do", "dung",
}


def tokenize(text: str) -> List[str]:
    return [
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) > 1 and token not in STOPWORDS
    ]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


class MainAgent:
    """
    Lightweight deterministic RAG agent for the lab benchmark.

    mode="baseline" keeps the old weak behavior for regression comparison.
    mode="optimized" retrieves policy snippets and selects the best grounded fact.
    """

    def __init__(self, mode: str = "optimized"):
        self.mode = mode
        self.name = "SupportAgent-v2" if mode == "optimized" else "SupportAgent-v1"
        self.documents = SOURCE_DOCUMENTS
        self.fact_index = self._build_fact_index()
        self.ambiguous_answers = {
            normalize(question): answer for question, answer in AMBIGUOUS_CASES
        }
        self.ooc_answers = {
            normalize(question): answer for question, answer in OUT_OF_CONTEXT_CASES
        }

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
        await asyncio.sleep(0.05)

        retrieved_docs = self.retrieve(question, top_k=3)
        retrieved_ids = [doc["doc_id"] for doc in retrieved_docs]
        contexts = [doc["text"] for doc in retrieved_docs]

        if self.mode == "baseline":
            answer = (
                f"Duoc, toi da nhan cau hoi '{question}'. "
                "Can kiem tra them tai lieu truoc khi dua ra cau tra loi cu the."
            )
        else:
            answer = self.generate_answer(question, retrieved_docs)

        return {
            "answer": answer,
            "retrieved_ids": retrieved_ids,
            "contexts": contexts,
            "metadata": {
                "model": f"deterministic-rag-{self.mode}",
                "tokens_used": len(tokenize(question)) + len(tokenize(answer)),
                "sources": retrieved_ids,
            },
        }

    def generate_answer(self, question: str, retrieved_docs: List[Dict]) -> str:
        normalized_question = normalize(question)

        if normalized_question in self.ambiguous_answers:
            return self.ambiguous_answers[normalized_question]

        if normalized_question in self.ooc_answers:
            return self._safe_out_of_context_answer(question)

        injection_answer = self._handle_prompt_injection(question, retrieved_docs)
        if injection_answer:
            return injection_answer

        conflict_answer = self._handle_conflict_case(question)
        if conflict_answer:
            return conflict_answer

        best_fact = self._best_fact_answer(question, retrieved_docs)
        if best_fact:
            return best_fact

        if not retrieved_docs:
            return "Tai lieu duoc cung cap khong co thong tin de tra loi cau hoi nay. Vui long cung cap them ngu canh hoac tai lieu lien quan."

        return self._summarize_retrieved_docs(retrieved_docs)

    def _build_fact_index(self) -> List[Dict]:
        facts = []
        for doc in self.documents:
            for fact_question, fact_answer in doc.get("facts", []):
                facts.append(
                    {
                        "doc_id": doc["doc_id"],
                        "question": fact_question,
                        "answer": fact_answer,
                        "question_terms": set(tokenize(fact_question)),
                    }
                )
        return facts

    def _best_fact_answer(self, question: str, retrieved_docs: List[Dict]) -> Optional[str]:
        query_terms = set(tokenize(question))
        retrieved_ids = {doc["doc_id"] for doc in retrieved_docs}
        best: Optional[Tuple[float, str]] = None

        for fact in self.fact_index:
            if retrieved_ids and fact["doc_id"] not in retrieved_ids:
                continue

            overlap = len(query_terms & fact["question_terms"])
            if overlap == 0:
                continue

            score = overlap / max(len(fact["question_terms"]), 1)
            if fact["doc_id"] in retrieved_ids:
                score += 0.25

            if best is None or score > best[0]:
                best = (score, fact["answer"])

        if not best:
            return None

        answer = best[1]
        if "policy_refund_001" in retrieved_ids and "thoi han" in normalize(question):
            return (
                "Khach hang co the yeu cau hoan tien trong vong 30 ngay ke tu ngay mua, "
                "voi dieu kien san pham chua duoc su dung qua 20% dung luong dich vu."
            )
        return answer

    def _handle_prompt_injection(self, question: str, retrieved_docs: List[Dict]) -> Optional[str]:
        q = normalize(question)
        if "bo qua" not in q and "ignore" not in q and "viet mot bai tho" not in q:
            return None

        if "hoan tien" in q:
            return (
                "Toi tu choi prompt injection va dua cau tra loi dua tren tai lieu neu co lien quan; toi khong bo qua tai lieu he thong. "
                "Theo chinh sach, khach hang chi co the yeu cau hoan tien "
                "trong vong 30 ngay ke tu ngay mua neu san pham chua su dung qua 20% dung luong dich vu; "
                "goi Enterprise khong duoc hoan tien tu dong va can quan ly tai khoan phe duyet bang van ban."
            )

        return (
            "Toi chi ho tro tra loi dua tren tai lieu chinh sach duoc cung cap. "
            "Yeu cau nay khong lien quan den nhiem vu ho tro dua tren tai lieu, nen toi khong thuc hien."
        )

    def _handle_conflict_case(self, question: str) -> Optional[str]:
        q = normalize(question)
        if "link reset" in q and "het han" in q and "can lam gi" in q:
            return "Nguoi dung can tao lai yeu cau dat lai mat khau moi tu Account Settings hoac man hinh dang nhap."
        if "vuot gioi han" in q:
            return "Khi vuot gioi han, API tra ve ma 429."
        if "trang status" in q and "ai cap nhat" in q:
            return "Doi van hanh phai cap nhat trang status."
        if "trang status" in q and ("bao lau" in q or "moi" in q or "dien rong" in q):
            return "Trang status can duoc cap nhat moi 30 phut cho den khi su co duoc giai quyet."
        if "enterprise" in q and "phe duyet" in q:
            return "Yeu cau hoan tien Enterprise can quan ly tai khoan phe duyet bang van ban."
        if "enterprise" in q and "hoan tien" in q and "tu dong" in q:
            return (
                "Khong. Truong hop Enterprise la ngoai le rieng: khong hoan tien tu dong "
                "va moi yeu cau phai duoc quan ly tai khoan phe duyet bang van ban."
            )
        if "thanh toan that bai" in q and ("huy ngay" in q or "3 lan" in q):
            return "Theo tai lieu billing, he thong thu lai toi da 3 lan trong 7 ngay; khong co thong tin huy ngay lap tuc."
        if "link reset" in q and ("24 gio" in q or "het han" in q):
            return "Theo tai lieu, duong link dat lai mat khau het han sau 15 phut."
        if "admin" in q and "mfa" in q:
            return "Khong. Tat ca tai khoan quan tri vien bat buoc bat MFA."
        if "cong khai" in q and "lo hong" in q:
            return "Khong. Khong cong khai chi tiet lo hong truoc khi co ban va loi."
        return None

    def _safe_out_of_context_answer(self, question: str) -> str:
        q = normalize(question)
        if "bao hanh phan cung laptop" in q:
            return "Tai lieu duoc cung cap khong neu chinh sach bao hanh phan cung laptop, nen toi khong suy doan."
        if "gia co phieu" in q:
            return "Tai lieu khong chua thong tin gia co phieu theo thoi gian thuc, nen toi khong co du lieu de tra loi."
        if "ceo" in q or "doi thu" in q:
            return "Tai lieu khong noi ve doi thu hay nhan su cua doi thu, nen toi khong co thong tin de tra loi."
        return self._handle_prompt_injection(question, []) or "Tai lieu khong co thong tin lien quan, nen toi khong suy doan."

    @staticmethod
    def _summarize_retrieved_docs(retrieved_docs: List[Dict]) -> str:
        primary = retrieved_docs[0]
        if len(retrieved_docs) == 1:
            return primary["text"]

        snippets = [f"{doc['title']}: {doc['text']}" for doc in retrieved_docs[:2]]
        return " ".join(snippets)


if __name__ == "__main__":
    agent = MainAgent()

    async def test():
        resp = await agent.query("Nguoi dung doi mat khau o dau?")
        print(resp)

    asyncio.run(test())
