import asyncio
import json
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from engine.runner import BenchmarkRunner

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class ExpertEvaluator:
    def __init__(self):
        self.retrieval_evaluator = RetrievalEvaluator()

    async def score(self, case: Dict, resp: Dict) -> Dict:
        retrieval_result = self.retrieval_evaluator.evaluate_case(
            expected_ids=case.get("expected_retrieval_ids", []),
            retrieved_ids=resp.get("retrieved_ids", []),
            top_k=3,
        )

        return {
            "faithfulness": 0.9,
            "relevancy": 0.8,
            "retrieval": retrieval_result,
        }


def load_dataset(path: str = "data/golden_set.jsonl") -> Optional[List[Dict]]:
    if not os.path.exists(path):
        print(f"Missing {path}. Run 'python data/synthetic_gen.py' first.")
        return None

    with open(path, "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print(f"{path} is empty. Generate at least 1 test case first.")
        return None

    eval_limit = os.getenv("EVAL_LIMIT")
    if eval_limit:
        try:
            limit = int(eval_limit)
        except ValueError:
            print(f"Ignoring invalid EVAL_LIMIT={eval_limit!r}; expected an integer.")
        else:
            dataset = dataset[:limit]
            print(f"EVAL_LIMIT={limit}; running first {len(dataset)} cases only.")
    return dataset


def build_summary(agent_version: str, results: List[Dict], judge: LLMJudge) -> Dict:
    total = len(results)
    scored_retrieval_results = [
        r["ragas"]["retrieval"]
        for r in results
        if r["ragas"]["retrieval"].get("is_scored")
    ]

    def avg_retrieval_metric(metric_name: str) -> float:
        values = [
            item[metric_name]
            for item in scored_retrieval_results
            if isinstance(item.get(metric_name), (int, float))
        ]
        return sum(values) / len(values) if values else 0.0

    return {
        "metadata": {
            "version": agent_version,
            "total": total,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "judge_models": [judge.openai_model, judge.hf_model],
        },
        "metrics": {
            "avg_score": sum(r["judge"]["final_score"] for r in results) / total,
            "hit_rate": avg_retrieval_metric("hit_rate"),
            "mrr": avg_retrieval_metric("mrr"),
            "retrieval_scored_cases": len(scored_retrieval_results),
            "agreement_rate": sum(r["judge"]["agreement_rate"] for r in results) / total,
            "conflict_rate": sum(1 for r in results if r["judge"].get("conflict")) / total,
            "avg_latency_seconds": sum(r["latency"] for r in results) / total,
        },
    }


async def run_benchmark_with_results(
    agent_version: str,
    dataset: List[Dict],
    judge: LLMJudge,
    agent: MainAgent,
) -> Tuple[List[Dict], Dict]:
    print(f"Starting benchmark for {agent_version}...")
    runner = BenchmarkRunner(agent, ExpertEvaluator(), judge)
    results = await runner.run_all(dataset)
    return results, build_summary(agent_version, results, judge)


async def run_benchmark(
    version: str,
    dataset: List[Dict],
    judge: LLMJudge,
    agent: MainAgent,
) -> Dict:
    _, summary = await run_benchmark_with_results(version, dataset, judge, agent)
    return summary


async def main():
    dataset = load_dataset()
    if not dataset:
        return

    judge = LLMJudge()

    try:
        v1_summary = await run_benchmark(
            "Agent_V1_Base",
            dataset,
            judge,
            MainAgent(mode="baseline"),
        )
        v2_results, v2_summary = await run_benchmark_with_results(
            "Agent_V2_Optimized",
            dataset,
            judge,
            MainAgent(mode="optimized"),
        )
    except RuntimeError as exc:
        print(f"Benchmark failed: {exc}")
        return

    print("\n--- REGRESSION COMPARISON ---")
    delta = v2_summary["metrics"]["avg_score"] - v1_summary["metrics"]["avg_score"]
    print(f"V1 Score: {v1_summary['metrics']['avg_score']:.2f}")
    print(f"V2 Score: {v2_summary['metrics']['avg_score']:.2f}")
    print(f"Delta: {'+' if delta >= 0 else ''}{delta:.2f}")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    if delta > 0:
        print("RELEASE GATE: APPROVE")
    else:
        print("RELEASE GATE: BLOCK RELEASE")


if __name__ == "__main__":
    asyncio.run(main())
