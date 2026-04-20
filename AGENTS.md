# Repository Guidelines

## Project Structure & Module Organization
This `rag/` workspace now follows a more backend-oriented layout similar to FlashRAG. Core backend code is organized by responsibility: schemas and ingestion helpers live in `dataset/`, retrieval and reranking helpers live in `retriever/`, and shared runtime setup lives in `utils/`. Notebook workflows remain under `notebooks/`. Compatibility wrappers are kept in `src/` and `utility/` so older notebook imports continue to work while the new layout settles in. Local Chroma persistence is stored under `storage/chroma_db/`; treat it as generated runtime data, not hand-edited source. Ollama model instructions live in `config/Modelfile.txt`. Reserved runtime or growth directories such as `models/`, `results/`, `scripts/`, and `tests/` sit at the top level, outside the backend package. Secrets and local settings remain in `.env`.

## Build, Test, and Development Commands
Use the shared environment one directory up when possible.

```bash
python -m venv ../.venv
source ../.venv/bin/activate
pip install -r ../requirements.txt
```

Run notebooks locally with `jupyter lab` from `rag/`. For a quick code sanity check, use `python3 -m compileall dataset retriever utils src utility`. When changing schemas, verify imports with `python3 -c "from rag.dataset.models import ChunkMetadata, RankingKeywords"`.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation and clear type hints. Keep module names lowercase with underscores inside `dataset/`, `retriever/`, and `utils/`; classes use `PascalCase`, enums use `UPPER_SNAKE_CASE` members only when required by the API, and notebook filenames should stay descriptive, such as `data_ingestion.ipynb`. Prefer reusable functions in the backend packages over redefining logic inside notebooks. Keep `src/` and `utility/` as thin compatibility layers only. Do not hardcode secrets, model endpoints, or API keys; read them from `.env`.

## Testing Guidelines
There is no dedicated `tests/` directory yet, so treat notebook reruns and import checks as the current baseline. For new Python modules, add `pytest` tests under `tests/` with names like `test_models.py`. Focus first on schema validation, metadata edge cases, and any code that reads or writes `storage/chroma_db/`.

## Commit & Pull Request Guidelines
Git history is not available in this workspace, so use short imperative commit messages such as `Add fiscal year validation` or `Refine retrieval reranking notebook`. Keep commits focused. Pull requests should include a brief summary, affected files, setup or data assumptions, and screenshots only when notebook outputs or UI views materially change.

## Security & Configuration Tips
Keep `.env` local and out of commits. Avoid committing generated vector data unless the change explicitly updates a checked-in sample database. If notebook cells download data or call external APIs, document the dependency and expected credentials in the PR.
