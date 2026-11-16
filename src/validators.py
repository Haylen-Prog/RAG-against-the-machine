"""Validation helpers for CLI arguments."""
from pathlib import Path
from typing import Any


def validate_k(k: Any) -> int:
    """Return k as a positive int or raise ValueError."""
    try:
        value = int(k)
    except (TypeError, ValueError):
        raise ValueError("'k' must be an int.") from None
    if value <= 0:
        raise ValueError("'k' must be greater than 0.")
    return value


def validate_path_exists(path: Any) -> str:
    """Return the path as a string or raise FileNotFoundError."""
    if not Path(str(path)).exists():
        raise FileNotFoundError(f"Path not found: {path}")
    return str(path)


def validate_save_directory(path: Any) -> str:
    """Create the directory if needed and return it."""
    directory = Path(str(path))
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory)


def validate_query(query: Any) -> str:
    """Return a non-empty query string or raise."""
    if not isinstance(query, str):
        raise TypeError("'query' must be a string.")
    if not query.strip():
        raise ValueError("'query' cannot be empty.")
    return query


def validate_max_chunk_size(max_chunk_size: Any) -> int:
    """Return a chunk size between 1 and 2000 or raise ValueError."""
    try:
        value = int(max_chunk_size)
    except (TypeError, ValueError):
        raise ValueError("'max_chunk_size' must be an int.") from None
    if not 0 < value <= 2000:
        raise ValueError("'max_chunk_size' must be within 1 and 2000.")
    return value
