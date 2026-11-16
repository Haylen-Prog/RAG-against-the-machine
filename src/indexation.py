"""Chunk the vLLM sources and write them to a JSONL index."""
import json
import logging
from pathlib import Path
from typing import Any

from chonkie import CodeChunker, RecursiveChunker
from tqdm import tqdm

from . import config

logger = logging.getLogger(__name__)
EXTENSIONS = {".md", ".py"}
EXTRA_NAMES = {"CMakeLists.txt"}
EXCLUDED_DIRS = {
    "tests", "benchmarks", "examples", "csrc", "tools",
    ".buildkite", ".github",
}


class Indexation:
    """Split documentation and code into chunks."""

    def __init__(
        self,
        max_chunk: int,
        root: Path = config.RAW_ROOT,
        out: Path = config.CHUNKS_PATH,
    ) -> None:
        """Create the two chunkers (text and Python code)."""
        self.root = root
        nested = root / root.name
        self.scan_root = nested if nested.is_dir() else root
        self.out = out
        self.md_chunker = RecursiveChunker(chunk_size=max_chunk)
        self.code_chunker = CodeChunker(
            chunk_size=max_chunk, language="python"
        )

    def list_files(self) -> list[Path]:
        """Return the indexable files under the corpus root."""
        if not self.scan_root.is_dir():
            raise FileNotFoundError(f"Corpus not found: {self.root}")
        return sorted(
            p for p in self.scan_root.rglob("*")
            if p.is_file()
            and (p.suffix.lower() in EXTENSIONS or p.name in EXTRA_NAMES)
            and not EXCLUDED_DIRS & set(p.relative_to(self.scan_root).parts)
        )

    def chunk_file(self, path: Path, text: str) -> list[Any]:
        """Chunk one file with the strategy matching its type."""
        if path.suffix.lower() == ".py":
            try:
                return list(self.code_chunker(text))
            except Exception as error:
                logger.warning(
                    "Code chunker failed on %s (%s), using text chunker",
                    path, error,
                )
        return list(self.md_chunker(text))

    def run(self) -> int:
        """Write all chunks to the index file, return their count."""
        files = self.list_files()
        self.out.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with open(self.out, "w", encoding="utf-8") as file:
            for path in tqdm(files, desc="Chunking"):
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as error:
                    logger.warning("Skipped %s: %s", path, error)
                    continue
                if not text.strip():
                    continue
                for chunk in self.chunk_file(path, text):
                    record = {
                        "file_path": (
                            self.root / path.relative_to(self.scan_root)
                        ).as_posix(),
                        "text": chunk.text,
                        "first_character_index": chunk.start_index,
                        "last_character_index": chunk.end_index,
                    }
                    file.write(json.dumps(record) + "\n")
                    count += 1
        return count
