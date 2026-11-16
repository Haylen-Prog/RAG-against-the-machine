"""BM25 retriever over the chunk index."""
import json
import logging
import re
from pathlib import Path
from typing import Any

import bm25s
import Stemmer

logger = logging.getLogger(__name__)
_STEMMER = Stemmer.Stemmer("english")


def _prepare(text: str) -> str:
    """Split camelCase and snake_case identifiers into words."""
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return text.replace("_", " ")


def _index_text(chunk: dict[str, Any]) -> str:
    """Text indexed by BM25: file path (twice) + chunk text."""
    path = chunk["file_path"].removeprefix("data/raw/vllm-0.10.1/")
    words = re.sub(r"[/.\-]", " ", path)
    return _prepare(f"{words} {words} {chunk['text']}")


def _tokenize(texts: str | list[str]) -> Any:
    """Tokenize with stop words removal and stemming."""
    return bm25s.tokenize(
        texts, stopwords="en", stemmer=_STEMMER, show_progress=False
    )


class Retriever:
    """Rank chunks against a query with BM25."""

    def __init__(
        self, chunks_path: Path, k1: float = 2.0, b: float = 0.75
    ) -> None:
        """Load the chunks and build the BM25 index."""
        self.chunks = self._load_chunks(chunks_path)
        if not self.chunks:
            raise ValueError(f"No chunks found in {chunks_path}")
        self.bm25 = bm25s.BM25(k1=k1, b=b)
        self.bm25.index(
            _tokenize([_index_text(c) for c in self.chunks]),
            show_progress=False,
        )

    @staticmethod
    def _load_chunks(path: Path) -> list[dict[str, Any]]:
        """Read the JSONL index, skipping malformed lines."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Index not found: {path}. Run 'index' first."
            )
        chunks: list[dict[str, Any]] = []
        with open(path, encoding="utf-8") as file:
            for number, line in enumerate(file, 1):
                if not line.strip():
                    continue
                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("Skipping malformed line %d", number)
        return chunks

    def search(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        """Return the top-k chunks for the query (best first)."""
        if not query.strip() or k <= 0:
            return []
        k = min(k, len(self.chunks))
        try:
            ids, _ = self.bm25.retrieve(
                _tokenize(_prepare(query)), k=k, show_progress=False
            )
        except (ValueError, IndexError, KeyError):
            return []
        return [self.chunks[int(i)] for i in ids[0]]
