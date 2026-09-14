from pathlib import Path


class CLI:
    def index(
            self,
            max_chunk_size: int = 2000) -> None:
        max_chunk_size = validate_max_chunk_size(max_chunk_size)

    def search(
            self,
            query: str,
            k: int) -> None:
        query = validate_query(query)
        k = validate_k(k)

    def search_dataset(
            self,
            dataset_path: str,
            k: int,
            save_directory: str) -> None:
        dataset_path = validate_path_exists(dataset_path)
        k = validate_k(k)
        save_directory = validate_save_directory(save_directory)

    def answer(
            self,
            query: str,
            k: int) -> None:
        query = validate_query(query)
        k = validate_k(k)

    def answer_dataset(
            self,
            student_search_results_path: str,
            save_directory: str) -> None:
        student_search_results_path = validate_path_exists(
            student_search_results_path
            )
        save_directory = validate_save_directory(save_directory)

    def evaluate(
        self,
        student_search_results_path: str,
        dataset_path: str,
    ) -> None:
        student_search_results_path = validate_path_exists(
            student_search_results_path
            )
        dataset_path = validate_path_exists(dataset_path)


def validate_k(k: int) -> int:
    try:
        k = int(k)
    except (TypeError, ValueError):
        raise ValueError("'k' must be an int.")
    if k <= 0:
        raise ValueError("'k' must be greater than 0.")
    return k


def validate_path_exists(
        path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    return path


def validate_save_directory(path: str) -> str:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


def validate_query(query: str) -> str:
    if not isinstance(query, str):
        raise TypeError("'query' must be a string.")
    if not query.strip():
        raise ValueError("'query' cannot be empty.")
    return query


def validate_max_chunk_size(max_chunk_size: int) -> int:
    try:
        max_chunk_size = int(max_chunk_size)
    except (TypeError, ValueError):
        raise ValueError("'max_chunk_size' must be an int.")

    if not 0 < max_chunk_size <= 2000:
        raise ValueError("'max_chunk_size' must be within 1 and 2000.")
    return max_chunk_size
