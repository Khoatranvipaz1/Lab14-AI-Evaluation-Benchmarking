from typing import Dict, List

class RetrievalEvaluator:
    def __init__(self):
        pass

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        """
        TODO: Tính toán xem ít nhất 1 trong expected_ids có nằm trong top_k của retrieved_ids không.
        """
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        TODO: Tính Mean Reciprocal Rank.
        Tìm vị trí đầu tiên của một expected_id trong retrieved_ids.
        MRR = 1 / position (vị trí 1-indexed). Nếu không thấy thì là 0.
        """
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    def evaluate_case(
        self,
        expected_ids: List[str],
        retrieved_ids: List[str],
        top_k: int = 3,
    ) -> Dict[str, object]:
        """
        Tính retrieval metrics cho 1 case.

        Các case không có expected_retrieval_ids như out-of-context hoặc ambiguous
        được đánh dấu is_scored=False để không kéo tụt điểm Hit Rate/MRR trung bình.
        """
        expected_ids = expected_ids or []
        retrieved_ids = retrieved_ids or []

        if not expected_ids:
            return {
                "hit_rate": None,
                "mrr": None,
                "is_scored": False,
                "top_k": top_k,
                "expected_ids": expected_ids,
                "retrieved_ids": retrieved_ids[:top_k],
                "note": "No ground-truth retrieval IDs for this case.",
            }

        return {
            "hit_rate": self.calculate_hit_rate(expected_ids, retrieved_ids, top_k),
            "mrr": self.calculate_mrr(expected_ids, retrieved_ids),
            "is_scored": True,
            "top_k": top_k,
            "expected_ids": expected_ids,
            "retrieved_ids": retrieved_ids[:top_k],
        }

    async def evaluate_batch(self, dataset: List[Dict]) -> Dict:
        """
        Chạy eval cho toàn bộ bộ dữ liệu đã có expected_retrieval_ids và retrieved_ids.
        """
        details = [
            self.evaluate_case(
                expected_ids=case.get("expected_retrieval_ids", []),
                retrieved_ids=case.get("retrieved_ids", []),
            )
            for case in dataset
        ]
        scored_details = [item for item in details if item["is_scored"]]

        return {
            "avg_hit_rate": self.average_metric(scored_details, "hit_rate"),
            "avg_mrr": self.average_metric(scored_details, "mrr"),
            "scored_cases": len(scored_details),
            "total_cases": len(details),
            "details": details,
        }

    @staticmethod
    def average_metric(results: List[Dict[str, object]], metric_name: str) -> float:
        values = [
            result[metric_name]
            for result in results
            if isinstance(result.get(metric_name), (int, float))
        ]
        return sum(values) / len(values) if values else 0.0
