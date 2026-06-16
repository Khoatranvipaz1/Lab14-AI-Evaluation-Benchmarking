import asyncio
import time
from typing import List, Dict
# Import other components...

import asyncio
import time
from typing import List, Dict

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    async def run_single_test(self, test_case: Dict, semaphore: asyncio.Semaphore) -> Dict:
        async with semaphore:
            start_time = time.perf_counter()
            
            # 1. Gọi Agent
            response = await self.agent.query(test_case["question"])
            latency = time.perf_counter() - start_time
            
            # Đồng bộ lại retrieved_ids từ response của Agent để Retrieval Evaluator tính toán
            # Nếu Agent không trả về, ta mặc định lấy từ metadata nguồn hoặc danh sách trống
            retrieved_ids = response.get("retrieved_ids", response.get("metadata", {}).get("sources", []))
            test_case_with_retrieved = {**test_case, "retrieved_ids": retrieved_ids}
            
            # 2. Chạy RAGAS / Retrieval Evaluation metrics
            ragas_scores = await self.evaluator.score(test_case_with_retrieved, response)
            
            # 3. Chạy Multi-Judge
            judge_result = await self.judge.evaluate_multi_judge(
                test_case["question"], 
                response["answer"], 
                test_case["expected_answer"]
            )
            
            # Tính toán Cost và Token Usage
            agent_tokens = response.get("metadata", {}).get("tokens_used", 0)
            # Giá sơ bộ cho gpt-4o-mini của Agent (ví dụ: $0.15/1M input, $0.6/1M output -> trung bình $0.3/1M)
            agent_cost = (agent_tokens * 0.3) / 1e6
            
            judge_meta = judge_result.get("metadata", {})
            judge_tokens = judge_meta.get("tokens_used", 0)
            judge_cost = judge_meta.get("cost_usd", 0.0)
            
            total_tokens = agent_tokens + judge_tokens
            total_cost = agent_cost + judge_cost
            
            return {
                "test_case": test_case["question"],
                "agent_response": response["answer"],
                "latency": latency,
                "ragas": ragas_scores,
                "judge": {
                    "final_score": judge_result["final_score"],
                    "agreement_rate": judge_result["agreement_rate"],
                    "reasoning": judge_result["reasoning"],
                    "individual_scores": judge_result.get("individual_scores", {})
                },
                "status": "fail" if judge_result["final_score"] < 3 else "pass",
                "performance": {
                    "tokens_used": total_tokens,
                    "cost_usd": total_cost,
                    "latency_sec": latency
                }
            }

    async def run_all(self, dataset: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Chạy song song sử dụng Semaphore để kiểm soát Rate Limit.
        """
        semaphore = asyncio.Semaphore(batch_size)
        tasks = [self.run_single_test(case, semaphore) for case in dataset]
        results = await asyncio.gather(*tasks)
        return results

