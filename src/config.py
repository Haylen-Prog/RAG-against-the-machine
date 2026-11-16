"""Global configuration and default paths."""
from pathlib import Path

DEBUG_SETUP = False
RAW_ROOT = Path("data/raw/vllm-0.10.1")
CHUNKS_PATH = Path("data/processed/chunk.jsonl")
LLM_NAME = "qwen3:0.6b"
MAX_PROMPT_CHARS = 12000
