import asyncio
import json
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI


class LLMJudge:
    """
    Multi-judge evaluator backed by two real models:
    - OpenAI gpt-4o-mini
    - Hugging Face Router Qwen/Qwen3.6-27B:featherless-ai

    Required environment variables:
    - OPENAI_API_KEY
    - HF_TOKEN
    """

    def __init__(
        self,
        openai_model: str = "gpt-4o-mini",
        hf_model: str = "Qwen/Qwen3.6-27B:featherless-ai",
        timeout_seconds: int = 120,
    ):
        load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=True)
        self.openai_model = os.getenv("OPENAI_JUDGE_MODEL", openai_model)
        self.hf_model = os.getenv("HF_JUDGE_MODEL", hf_model)
        self.hf_base_url = os.getenv("HF_BASE_URL", "https://router.huggingface.co/v1")
        self.timeout_seconds = timeout_seconds

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.hf_token = os.getenv("HF_TOKEN")

        self.openai_client: Optional[AsyncOpenAI] = (
            AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        )
        self.hf_client: Optional[AsyncOpenAI] = (
            AsyncOpenAI(base_url=self.hf_base_url, api_key=self.hf_token)
            if self.hf_token
            else None
        )

        self.rubric = (
            "Score the agent answer from 1 to 5.\n"
            "Use the expected answer / ground truth as the primary grading target.\n"
            "Use retrieved context only as supporting evidence for grounding.\n"
            "Do not penalize an answer for omitting context details that are not asked by the question "
            "and are not required by the expected answer.\n"
            "Do not penalize an answer for adding accurate context details unless they contradict the expected answer, "
            "change the decision, or make the answer unsafe.\n"
            "If the answer contains every required point from the expected answer and any extra details are grounded, "
            "score it 5.\n"
            "5 = fully correct, grounded in the provided context, complete, and safe.\n"
            "4 = mostly correct with minor omissions.\n"
            "3 = partially correct but missing important details.\n"
            "2 = mostly incorrect, unsupported, or incomplete.\n"
            "1 = wrong, hallucinated, unsafe, or ignores the question.\n"
            "Return only valid JSON with keys: score, reasoning, strengths, weaknesses."
        )

    async def evaluate_multi_judge(
        self,
        question: str,
        answer: str,
        ground_truth: str,
        contexts: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._validate_clients()
        prompt = self._build_prompt(question, answer, ground_truth, contexts or [], metadata or {})

        openai_result, hf_result = await asyncio.gather(
            self._judge_with_openai(prompt),
            self._judge_with_huggingface(prompt),
        )

        scores = {
            self.openai_model: openai_result["score"],
            self.hf_model: hf_result["score"],
        }
        score_gap = abs(openai_result["score"] - hf_result["score"])
        conflict = score_gap > 1.0
        final_score = self._resolve_final_score(openai_result["score"], hf_result["score"])

        return {
            "final_score": final_score,
            "agreement_rate": self._agreement_rate(score_gap),
            "conflict": conflict,
            "score_gap": score_gap,
            "individual_scores": scores,
            "judge_details": {
                self.openai_model: openai_result,
                self.hf_model: hf_result,
            },
            "reasoning": self._combine_reasoning(openai_result, hf_result, conflict),
        }

    async def _judge_with_openai(self, prompt: str) -> Dict[str, Any]:
        assert self.openai_client is not None
        try:
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a strict AI evaluation judge. Return only JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                ),
                timeout=self.timeout_seconds,
            )
            content = response.choices[0].message.content or "{}"
            return self._normalize_judge_result(content, provider=self.openai_model)
        except Exception as exc:
            raise RuntimeError(
                f"OpenAI judge failed for model {self.openai_model}: {type(exc).__name__}: {exc}"
            ) from exc

    async def _judge_with_huggingface(self, prompt: str) -> Dict[str, Any]:
        assert self.hf_client is not None
        try:
            response = await asyncio.wait_for(
                self.hf_client.chat.completions.create(
                    model=self.hf_model,
                    temperature=0,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a strict AI evaluation judge. Return only JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                ),
                timeout=self.timeout_seconds,
            )
            content = response.choices[0].message.content or "{}"
            return self._normalize_judge_result(content, provider=self.hf_model)
        except Exception as exc:
            raise RuntimeError(
                f"Hugging Face judge failed for model {self.hf_model}: {type(exc).__name__}: {exc}"
            ) from exc

    def _validate_clients(self) -> None:
        missing = []
        if self.openai_client is None:
            missing.append("OPENAI_API_KEY")
        if self.hf_client is None:
            missing.append("HF_TOKEN")

        if missing:
            raise RuntimeError(
                "Cannot run LLMJudge because these requirements are missing: "
                + ", ".join(missing)
            )

    def _build_prompt(
        self,
        question: str,
        answer: str,
        ground_truth: str,
        contexts: List[str],
        metadata: Dict[str, Any],
    ) -> str:
        compact_context = "\n\n".join(contexts[:5]) if contexts else "(no retrieved context)"
        return (
            f"{self.rubric}\n\n"
            f"Metadata:\n{json.dumps(metadata, ensure_ascii=False)}\n\n"
            f"Question:\n{question}\n\n"
            f"Agent answer:\n{answer}\n\n"
            f"Expected answer / ground truth:\n{ground_truth}\n\n"
            f"Retrieved context:\n{compact_context}\n"
        )

    def _normalize_judge_result(self, raw_content: str, provider: str) -> Dict[str, Any]:
        data = self._parse_json(raw_content)
        score = self._coerce_score(data.get("score"))

        return {
            "provider": provider,
            "score": score,
            "reasoning": str(data.get("reasoning", "")).strip(),
            "strengths": self._as_list(data.get("strengths")),
            "weaknesses": self._as_list(data.get("weaknesses")),
        }

    @staticmethod
    def _parse_json(raw_content: str) -> Dict[str, Any]:
        raw_content = raw_content.strip()
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError:
            start = raw_content.find("{")
            if start == -1:
                raise ValueError(f"Judge did not return JSON: {raw_content[:300]}")
            decoder = json.JSONDecoder()
            try:
                parsed, _ = decoder.raw_decode(raw_content[start:])
            except json.JSONDecodeError:
                match = re.search(r"\{.*?\}", raw_content, flags=re.DOTALL)
                if not match:
                    raise ValueError(f"Judge did not return JSON: {raw_content[:300]}")
                parsed = json.loads(match.group(0))

        if not isinstance(parsed, dict):
            raise ValueError("Judge JSON response must be an object.")
        return parsed

    @staticmethod
    def _coerce_score(value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Judge score must be numeric, got {value!r}") from exc
        return max(1.0, min(5.0, score))

    @staticmethod
    def _as_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        text = str(value).strip()
        return [text] if text else []

    @staticmethod
    def _agreement_rate(score_gap: float) -> float:
        return round(max(0.0, 1.0 - (score_gap / 4.0)), 3)

    @staticmethod
    def _resolve_final_score(openai_score: float, secondary_score: float) -> float:
        score_gap = abs(openai_score - secondary_score)
        if score_gap > 1.0:
            return round(min(openai_score, secondary_score), 2)
        return round((openai_score + secondary_score) / 2, 2)

    @staticmethod
    def _combine_reasoning(
        openai_result: Dict[str, Any],
        hf_result: Dict[str, Any],
        conflict: bool,
    ) -> str:
        prefix = "Conflict detected; final score uses the stricter judge." if conflict else "Judges broadly agree."
        return (
            f"{prefix} "
            f"OpenAI: {openai_result.get('reasoning', '')} "
            f"HuggingFace: {hf_result.get('reasoning', '')}"
        ).strip()

    async def check_position_bias(self, response_a: str, response_b: str) -> Dict[str, Any]:
        prompt_ab = (
            "Compare response A and response B for quality. Return JSON with keys score, reasoning, strengths, weaknesses.\n"
            f"A: {response_a}\nB: {response_b}"
        )
        prompt_ba = (
            "Compare response A and response B for quality. Return JSON with keys score, reasoning, strengths, weaknesses.\n"
            f"A: {response_b}\nB: {response_a}"
        )
        first, swapped = await asyncio.gather(
            self._judge_with_openai(prompt_ab),
            self._judge_with_openai(prompt_ba),
        )
        return {"first_order": first, "swapped_order": swapped}
