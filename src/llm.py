"""Answer generation with a local LLM."""
import logging
from typing import Any

import ollama

from . import config

logger = logging.getLogger(__name__)


class LLManager:
    """Thin wrapper around the chat model."""

    def __init__(self, llm_name: str) -> None:
        """Store the model name and generation options."""
        self.model = llm_name
        self.options: dict[str, Any] = {
            "temperature": 0.1,
            "top_p": 0.8,
            "top_k": 20,
            "num_predict": 300,
            "repeat_penalty": 1.1,
            "num_ctx": 8192,
        }

    def build_context(self, chunks: list[dict[str, Any]]) -> str:
        """Concatenate chunks (best first) within the prompt budget."""
        parts: list[str] = []
        used = 0
        for i, chunk in enumerate(chunks, 1):
            passage = f"[Passage {i} - {chunk['file_path']}]\n{chunk['text']}"
            if used + len(passage) > config.MAX_PROMPT_CHARS:
                break
            parts.append(passage)
            used += len(passage)
        return "\n\n".join(parts)

    def generation(
        self, question: str, chunks: list[dict[str, Any]]
    ) -> str:
        """Answer the question using only the given chunks."""
        context = self.build_context(chunks)
        response = ollama.chat(
            model=self.model,
            think=False,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You answer questions about vLLM. Use only the "
                        "provided context. If the answer is not in it, "
                        "say so. Answer in the language of the question."
                    ),
                },
                {
                    "role": "user",
                    "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{question}",
                },
            ],
            options=self.options,
        )
        return response.message.content or ""
