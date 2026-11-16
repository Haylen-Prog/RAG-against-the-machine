*This activity has been created as part of the 42 curriculum by azinciry.*

# Common Core – RAG Against the Machine

## Description

This project implements a search-and-answer engine based on the RAG (Retrieval-Augmented Generation) paradigm, for a documentation corpus and a Python code corpus (vLLM 0.10.1). The goal is to retrieve the most relevant passages for a question, then pass them to a language model so that it produces an answer grounded in the real content of the repository.

Overview of the pipeline:

1. The corpus is split into chunks and stored in a JSONL index.
2. A BM25 retriever ranks the chunks for a given query.
3. The top chunks are assembled into a short context and sent to a local LLM (through Ollama).
4. An evaluation module compares retrieval results against a ground-truth dataset (recall@k).

## Instructions

The Makefile targets set up the Python environment in `goinfre` when it is available.

```bash
make help          # list all available commands
make install       # install dependencies
make setup-data    # prepare the data
make run           # index the corpus
```

The raw corpus must be placed in:

```text
data/raw/vllm-0.10.1/
```

and the index is produced in:

```text
data/processed/chunk.jsonl
```

Quality checks:

```bash
make lint          # flake8 + mypy
make review-tests  # re-index, evaluate public datasets, run smoke tests and edge cases
```

## System architecture

The system is organized in four main blocks:

- **Indexing**: read the source files and split them into chunks.
- **Retrieval**: compute the similarity between the query and the indexed chunks.
- **Generation**: build a short, usable context, then call the model.
- **Evaluation**: compare retrieval results with a ground-truth dataset.

The entry point is the `src` CLI module, exposed through Fire and used via the Makefile.

Modules:

- `src/indexation.py`: chunking and writing of the JSONL index.
- `src/bm25.py`: BM25 engine used to rank chunks.
- `src/llm.py`: wrapper around the Ollama model.
- `src/io_utils.py`: Pydantic data models.
- `src/evaluation.py`: recall@k measurement.
- `src/validators.py`: CLI argument validation.
- `src/main.py`: public commands exposed via Fire.

## Chunking strategy

Two strategies are used, depending on the file type.

### Python code

For `.py` files, the system uses Chonkie's `CodeChunker`. It tries to preserve the structure of the code (functions, classes, logical blocks), which avoids breaking the semantic context when searching for a specific symbol or behavior.

### Text documents

For Markdown and other text documents, the project uses `RecursiveChunker`. It splits the text into reasonably sized pieces while keeping more natural context boundaries, which suits documentation queries.

The default chunk size is 2000 characters and can be changed with:

```bash
uv run python -m src index --max_chunk_size 1000
```

### Why this choice?

- Chunks that are too small, although precise, fragment the information and reduce overall coherence.
- Chunks that are too large dilute relevance and increase the risk of retrieval errors, especially for narrow queries.
- The chosen trade-off keeps passages readable for the model while retaining enough context in each one.

Each chunk is stored with the following metadata: `file_path`, `text`, `first_character_index`, `last_character_index`.

## Retrieval method

Retrieval relies on BM25, a classic and robust ranking function that works well on technical documents.

The retriever:

1. reads the JSONL index created during indexing,
2. cleans the query text,
3. tokenizes the words after normalization,
4. applies BM25 to rank the chunks,
5. returns the best results in order of relevance.

`src/bm25.py` also handles technical identifiers:

- `snake_case` is split into words,
- `camelCase` is also split,
- the file path is indexed as an additional relevance signal.

The search returns a list of sources with their character bounds (`file_path`, `first_character_index`, `last_character_index`).

## Answer generation

Once the best chunks are retrieved, the system builds a concatenated context and sends it to the language model.

- Default model: `qwen3:0.6b` (Ollama alias for Qwen/Qwen3-0.6B).
- The wrapper in `src/llm.py` assembles passages within a reasonable context window and caps its size with `MAX_PROMPT_CHARS`.
- The model is instructed to answer only from the provided context, and in the language of the question.

Generation uses Ollama, which makes it easy to run a local model without depending on a remote service.

## Performance analysis

The public check was run with `make review-tests`, which calls the Moulinette evaluator through `make mouli`.

| Metric | Result | Threshold |
|---|---|---|
| Recall@5, documentation (100 questions) | **86.0 %** | 80 % |
| Recall@5, public code (99 questions) | **78.8 %** | 50 % |
| Local indexing time | ~**6 s** | 300 s |
| Search over both public datasets (199 questions) | ~**2 s** | 90 s |

Limitations of this evaluation:

- The public datasets only contain 99 code questions.
- The official `exam_retrieval.sh` and `exam_answer.sh` scripts and the private dataset are not available in the local archive, so these measurements validate the public datasets only and do not replace the private evaluation.
- The local measure in `src/evaluation.py` is based on the overlap of text ranges.
- The answer smoke test checks the execution path but does not replace the grading of the three answers by `exam_answer.sh`.

## Data models and validation

Shared data structures are defined in `src/io_utils.py` with Pydantic v2:

- `MinimalSource`
- `UnansweredQuestion`
- `AnsweredQuestion`
- `RagDataset`
- `MinimalSearchResults`
- `MinimalAnswer`
- `StudentSearchResults`
- `StudentSearchResultsAndAnswer`

They are used to validate question datasets, serialize search results, produce consistent JSON outputs and prepare automatic evaluations.

CLI validation (`k`, `query`, `path`, `max_chunk_size`) is centralized in `src/validators.py` to avoid configuration errors and invalid paths.

## Design decisions

### BM25 rather than dense embeddings

BM25 was chosen for its simplicity, speed and robustness on technical corpora. It is particularly suited to code and documentation repositories, where exact term matching matters a lot.

### Hybrid chunking

The project combines a hierarchical chunker for documents and a code-oriented chunker for Python files. This reduces context loss for both file types without requiring heavier parsers such as `ast` or a full Tree-sitter setup.

### Possible improvements

- Hybrid retrieval (BM25 + embeddings).
- Finer filtering of passages by file or symbol.
- A better evaluation protocol on the private dataset.
- A more adaptive generation context depending on passage length.

## Challenges faced

- **Chunk size trade-off**: chunks need enough context to remain useful without diluting retrieval relevance. The implementation uses separate code and text chunkers and exposes `--max_chunk_size`.
- **Technical identifiers**: natural-language queries may refer to `snake_case` or `camelCase` symbols. The retriever splits these identifiers and includes file paths as an additional ranking signal.
- **Strict typing with untyped libraries**: project code is checked with strict mypy settings; missing-import checks are selectively ignored for third-party modules without type stubs (`bm25s`, `Stemmer` and `fire`).
- **Evaluation data availability**: the checked-in public code dataset contains 99 questions. Private datasets and the official exam scripts are not present in this local environment, so the recorded scores cover public datasets only.

## Example usage

Index the corpus:

```bash
make run
```

Search a single query:

```bash
make search-smoke
```

Generate an answer:

```bash
make answer-smoke
```

Search over a whole dataset:

```bash
make search-all
```

Evaluation and robustness:

```bash
make mouli
make edge-cases
```

Full validation (`make review-tests`) re-indexes the corpus, evaluates the public results, runs the search and answer examples, then checks the four edge cases without any traceback.

## Resources

References:

- Robertson, S. & Zaragoza, H., *The Probabilistic Relevance Framework: BM25 and Beyond*, Foundations and Trends in Information Retrieval, 2009.
- Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, NeurIPS 2020.
- [bm25s](https://github.com/xhluca/bm25s): fast BM25 implementation in Python.
- [Chonkie](https://docs.chonkie.ai/): `CodeChunker` and `RecursiveChunker` documentation.
- [Ollama](https://ollama.com/) and the Qwen3 model card.
- [Pydantic v2](https://docs.pydantic.dev/) and [Python Fire](https://github.com/google/python-fire) documentation.
- [vLLM](https://docs.vllm.ai/): the corpus used for this project.

### How AI was used
    To fill in honestly: state which tasks and which parts of the project AI helped with. Example structure:

    Task: debugging mypy --strict errors on untyped libraries → Part: src/bm25.py, src/main.py.
    Task: translating and structuring this README → Part: documentation.
