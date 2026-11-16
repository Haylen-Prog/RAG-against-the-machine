"""CLI entry point: every public method of Monitoring is a command."""
import json
import logging
from pathlib import Path
from typing import Any

import fire
from tqdm import tqdm

from . import config
from .bm25 import Retriever
from .evaluation import recall_at_k
from .indexation import Indexation
from .io_utils import (
    MinimalAnswer,
    MinimalSearchResults,
    MinimalSource,
    RagDataset,
    StudentSearchResults,
    StudentSearchResultsAndAnswer,
)
from .llm import LLManager
from .logger import Logger
from .validators import (
    validate_k,
    validate_max_chunk_size,
    validate_path_exists,
    validate_query,
    validate_save_directory,
)

logger = logging.getLogger(__name__)
SOURCE_KEYS = ("file_path", "first_character_index", "last_character_index")
ERRORS = (OSError, ValueError, TypeError, KeyError)


def _sources(hits: list[dict[str, Any]]) -> list[MinimalSource]:
    """Keep only the fields required by the output format."""
    return [MinimalSource(**{k: h[k] for k in SOURCE_KEYS}) for h in hits]


def _read_span(source: MinimalSource, cache: dict[str, str]) -> str:
    """Return the text covered by a source (empty if unreadable)."""
    if source.file_path not in cache:
        try:
            cache[source.file_path] = Path(
                source.file_path
            ).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            cache[source.file_path] = ""
    text = cache[source.file_path]
    return text[source.first_character_index:source.last_character_index]


def _generate(
    llm: LLManager, question: str, chunks: list[dict[str, Any]]
) -> str:
    """Generate an answer, returning '' if the LLM fails."""
    try:
        return llm.generation(question, chunks)
    except Exception as error:
        logger.error("[LLM_ERROR] %s", error)
        return ""


class Monitoring:
    """Each public method is exposed as a CLI command by Fire."""

    def index(self, max_chunk_size: int = 2000) -> None:
        """Chunk data/raw and build the index under data/processed."""
        try:
            size = validate_max_chunk_size(max_chunk_size)
            count = Indexation(size).run()
        except ERRORS as error:
            logger.error("[INDEX_ERROR] %s", error)
            return
        logger.info("%d chunks written", count)
        print(
            "Ingestion complete! Indices saved under "
            f"{config.CHUNKS_PATH.parent}/"
        )

    def search(self, query: str, k: int = 10) -> None:
        """Print the top-k sources for one query."""
        try:
            text = validate_query(query)
            top = validate_k(k)
            hits = Retriever(config.CHUNKS_PATH).search(text, top)
        except ERRORS as error:
            logger.error("[SEARCH_ERROR] %s", error)
            return
        print(json.dumps(
            [{key: h[key] for key in SOURCE_KEYS} for h in hits], indent=2
        ))

    def search_dataset(
        self, dataset_path: str, save_directory: str, k: int = 10
    ) -> None:
        """Run the search on a whole dataset."""
        try:
            path = Path(validate_path_exists(dataset_path))
            top = validate_k(k)
            out_dir = Path(validate_save_directory(save_directory))
            dataset = RagDataset.model_validate_json(
                path.read_text(encoding="utf-8")
            )
            retriever = Retriever(config.CHUNKS_PATH)
            results = [
                MinimalSearchResults(
                    question_id=q.question_id,
                    question=q.question,
                    retrieved_sources=_sources(
                        retriever.search(q.question, top)
                    ),
                )
                for q in tqdm(dataset.rag_questions, desc="Searching")
            ]
            output = StudentSearchResults(search_results=results, k=top)
            target = out_dir / path.name
            target.write_text(output.model_dump_json(indent=2),
                              encoding="utf-8")
        except ERRORS as error:
            logger.error("[SEARCH_DATASET_ERROR] %s", error)
            return
        print(f"Saved student_search_results to {target}")

    def answer(self, query: str, k: int = 5) -> None:
        """Answer one query using the retrieved context."""
        try:
            text = validate_query(query)
            top = validate_k(k)
            hits = Retriever(config.CHUNKS_PATH).search(text, top)
            reply = LLManager(config.LLM_NAME).generation(text, hits)
        except Exception as error:
            logger.error("[ANSWER_ERROR] %s", error)
            return
        print(reply)

    def answer_dataset(
        self, student_search_results_path: str, save_directory: str
    ) -> None:
        """Generate answers for a StudentSearchResults file."""
        try:
            path = Path(validate_path_exists(student_search_results_path))
            out_dir = Path(validate_save_directory(save_directory))
            data = StudentSearchResults.model_validate_json(
                path.read_text(encoding="utf-8")
            )
            llm = LLManager(config.LLM_NAME)
            cache: dict[str, str] = {}
            answers: list[MinimalAnswer] = []
            for res in tqdm(data.search_results, desc="Answering"):
                chunks = [
                    {"file_path": s.file_path,
                     "text": _read_span(s, cache)}
                    for s in res.retrieved_sources
                ]
                answers.append(MinimalAnswer(
                    **res.model_dump(),
                    answer=_generate(llm, res.question, chunks),
                ))
            output = StudentSearchResultsAndAnswer(
                search_results=answers, k=data.k
            )
            target = out_dir / path.name
            target.write_text(output.model_dump_json(indent=2),
                              encoding="utf-8")
        except ERRORS as error:
            logger.error("[ANSWER_DATASET_ERROR] %s", error)
            return
        print(f"Saved student_search_results_and_answer to {target}")

    def evaluate(
        self, student_search_results_path: str, dataset_path: str
    ) -> None:
        """Print our own recall@k against a ground-truth dataset."""
        try:
            results_path = Path(
                validate_path_exists(student_search_results_path)
            )
            truth_path = Path(validate_path_exists(dataset_path))
            results = StudentSearchResults.model_validate_json(
                results_path.read_text(encoding="utf-8")
            )
            truth = RagDataset.model_validate_json(
                truth_path.read_text(encoding="utf-8")
            )
            ks = tuple(k for k in (1, 3, 5, 10) if k <= results.k)
            scores = recall_at_k(results, truth, ks)
        except ERRORS as error:
            logger.error("[EVALUATE_ERROR] %s", error)
            return
        print("  ".join(f"Recall@{k}: {v:.3f}" for k, v in scores.items()))


def main() -> None:
    """Initialise logging and expose Monitoring as a Fire CLI."""
    Logger(config.DEBUG_SETUP).init_logger()
    fire.Fire(Monitoring)
