"""Local recall@k computation (for your own testing only)."""
from .io_utils import (
    AnsweredQuestion,
    MinimalSource,
    RagDataset,
    StudentSearchResults,
)

IOU_THRESHOLD = 0.05


def _iou(a: MinimalSource, b: MinimalSource) -> float:
    """Intersection over union of two character ranges."""
    inter = (min(a.last_character_index, b.last_character_index)
             - max(a.first_character_index, b.first_character_index))
    if inter <= 0:
        return 0.0
    union = ((a.last_character_index - a.first_character_index)
             + (b.last_character_index - b.first_character_index) - inter)
    return inter / union if union > 0 else 0.0


def _found(expected: MinimalSource, top: list[MinimalSource]) -> bool:
    """Check whether a retrieved source overlaps the expected one."""
    return any(
        r.file_path == expected.file_path
        and _iou(r, expected) >= IOU_THRESHOLD
        for r in top
    )


def recall_at_k(
    results: StudentSearchResults,
    truth: RagDataset,
    ks: tuple[int, ...] = (1, 3, 5, 10),
) -> dict[int, float]:
    """Calculate recall scores for all questions with ground truth."""
    expected = {
        q.question_id: q.sources
        for q in truth.rag_questions
        if isinstance(q, AnsweredQuestion)
    }
    scores: dict[int, list[float]] = {k: [] for k in ks}
    for result in results.search_results:
        sources = expected.get(result.question_id)
        if not sources:
            continue
        for k in ks:
            top = result.retrieved_sources[:k]
            found = sum(_found(s, top) for s in sources)
            scores[k].append(found / len(sources))
    return {k: sum(v) / len(v) if v else 0.0 for k, v in scores.items()}
