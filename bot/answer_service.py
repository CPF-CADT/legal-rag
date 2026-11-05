"""Grounded answer service shared by Telegram and future clients."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from pathlib import Path
from typing import Any

from dense_retrieval.retriever import DenseRetriever


INSUFFICIENT_EVIDENCE_MESSAGE = (
    "🔎 ខ្ញុំមិនអាចរកឃើញព័ត៌មានច្បាប់ដែលពាក់ព័ន្ធគ្រប់គ្រាន់សម្រាប់សំណួរនេះទេ។\n\n"
    "សូមសរសេរសំណួរឡើងវិញជាភាសាខ្មែរ ឬបន្ថែមព័ត៌មានលម្អិត ដូចជា៖\n"
    "- ឈ្មោះច្បាប់\n"
    "- លេខមាត្រា\n"
    "- ប្រធានបទច្បាប់"
)

INSUFFICIENT_ANSWER_MARKER = "មិនអាចរកឃើញព័ត៌មានគ្រប់គ្រាន់សម្រាប់សំណួរនេះទេ"


@dataclass
class AnswerResult:
    answer: str
    sources: list[dict[str, Any]]
    has_sufficient_evidence: bool
    usage: dict[str, int]


DEFAULT_TEMPLATE_PATH = (
    Path(__file__).resolve().parent / "prompts" / "khmer_legal_answer.txt"
)


def load_prompt_template(path: Path | None = None) -> str:
    template_path = Path(
        os.environ.get(
            "ANSWER_PROMPT_TEMPLATE_PATH",
            os.environ.get(
                "PROMPT_TEMPLATE_PATH",
                os.environ.get("TEMPLATE", str(path or DEFAULT_TEMPLATE_PATH)),
            ),
        )
    )
    if not template_path.is_file():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def build_prompt(question: str, context: str, template: str | None = None) -> str:
    prompt_template = template or load_prompt_template()
    return prompt_template.format(question=question, context=context)


def remove_inline_references(answer: str) -> str:
    """Remove model-added source citations; sources are rendered separately."""
    return re.sub(r"\s*\([^()\n]*ប្រភព[^()\n]*\)", "", answer).strip()


class AnswerService:
    def __init__(
        self,
        retriever: DenseRetriever,
        generator: Any,
        *,
        candidate_count: int = 100,
        top_k: int = 5,
        min_similarity: float = 0.35,
        prompt_template_path: Path | None = None,
    ) -> None:
        self.retriever = retriever
        self.generator = generator
        self.candidate_count = candidate_count
        self.top_k = top_k
        self.min_similarity = min_similarity
        self.prompt_template = load_prompt_template(prompt_template_path)

    def answer(self, question: str) -> AnswerResult:
        results = self.retriever.search(
            question,
            candidate_count=self.candidate_count,
            top_k=self.top_k,
        )
        if not results or results[0]["best_similarity"] < self.min_similarity:
            return AnswerResult(INSUFFICIENT_EVIDENCE_MESSAGE, [], False, {})

        context = self.retriever.format_context(results)
        answer = remove_inline_references(self.generator.generate(
            build_prompt(question, context, self.prompt_template)
        ))
        if not answer:
            return AnswerResult(INSUFFICIENT_EVIDENCE_MESSAGE, [], False, {})

        # The model can determine that retrieved passages do not answer the
        # question even when the similarity threshold was met. Do not expose
        # those merely related passages as references in that case.
        if INSUFFICIENT_ANSWER_MARKER in answer:
            return AnswerResult(answer, [], False, {})

        return AnswerResult(
            answer,
            results,
            True,
            dict(getattr(self.generator, "last_usage", {}) or {}),
        )
