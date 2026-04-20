# RAG Directory File Placement Guide

This document explains what kind of files should be stored in each directory inside `rag/`.
It is written as a working reference for future maintenance, so new files can be added without
guesswork or accidental mixing of responsibilities.

## Core Principle

Keep `lucent/` organized by responsibility:

- backend code goes into responsibility-based Python packages
- runtime artifacts stay outside backend code
- notebooks stay in `notebooks/`
- configuration stays in `config/`
- documentation stays in `docs/`
- compatibility code stays thin and temporary

Do not mix source code, generated data, experiments, and runtime state in the same folder.

## Directory Map

| Directory | Purpose | What files belong here | Common file types | Naming guidance | What should not go here | Example files |
|---|---|---|---|---|---|---|
| `rag/` | Root of the local backend workspace | High-level package entrypoints and top-level project files only | `.py`, `.md`, `.env`, `.ipynb` only if intentionally root-level | Keep root minimal; only files with repo-wide purpose | Feature-specific code, generated data, random scratch files | `__init__.py`, `AGENTS.md`, `.env` |
| `rag/config/` | Configuration and deployment/runtime settings | Model settings, environment templates, YAML/TOML/JSON config files, prompt/provider config, local run profiles | `.yaml`, `.yml`, `.json`, `.toml`, `.ini`, `.env.example`, `.txt` | Use names that describe the environment or subsystem | Business logic, notebooks, test data, generated output | `ollama.yaml`, `retrieval.yaml`, `Modelfile.txt`, `local.env.example` |
| `rag/dataset/` | Dataset-facing backend code | Python modules for schemas, ingestion, chunking, metadata parsing, validators, loaders, corpus preparation helpers | `.py` | Prefer names by function: `models.py`, `ingestion.py`, `chunking.py`, `parsers.py`, `validators.py` | Saved datasets, PDFs, notebooks, generated embeddings, one-off scripts | `models.py`, `ingestion.py`, `chunking.py`, `metadata_parser.py` |
| `rag/retriever/` | Retrieval backend code | Python modules for search, filtering, reranking, query analysis, vector store access, ranking helpers | `.py` | Name by retrieval responsibility, not by notebook name | Raw data files, configs, notebook experiments | `retrieval.py`, `reranker.py`, `filters.py`, `vector_store.py`, `query_expansion.py` |
| `rag/utils/` | Shared backend utilities | Cross-cutting helpers used by multiple modules, common setup, runtime helpers, path utilities, environment loading | `.py` | Use narrow utility names; avoid dumping unrelated code in one file | Domain-heavy logic that belongs in `dataset/` or `retriever/` | `common.py`, `paths.py`, `env.py`, `logging.py` |
| `rag/src/` | Temporary compatibility layer for old imports | Thin wrappers that re-export moved code so older notebooks or scripts do not break immediately | `.py` | Wrapper names should mirror old import paths | New business logic, large implementations, new features | `models.py`, `__init__.py` |
| `rag/utility/` | Temporary compatibility layer for old notebook imports | Thin wrappers for old `utility.*` imports only | `.py` | Keep file names aligned with prior notebook usage | New implementation code, feature work, refactors | `common.py`, `ingestion.py`, `retrieval.py` |
| `rag/notebooks/` | Interactive workflows and analysis notebooks | Jupyter notebooks for ingestion runs, retrieval experiments, debugging, demos, evaluation walkthroughs | `.ipynb`, optional small `.md` notes | Use descriptive workflow names; prefer stable names over vague names like `test.ipynb` | Reusable backend logic, large datasets, generated DB files | `data_ingestion.ipynb`, `retrieval_debug.ipynb`, `reranking_eval.ipynb` |
| `rag/docs/` | Human-readable documentation for yourself or collaborators | Maintenance guides, architecture notes, folder rules, setup notes, troubleshooting docs, runbooks | `.md` | Prefer explicit names such as `directory_file_placement_guide.md`, `architecture_notes.md` | Python modules, generated reports that belong in `results/` | `directory_file_placement_guide.md`, `setup_guide.md` |
| `rag/storage/` | Local runtime persistence | Local vector database storage, cache folders, serialized runtime artifacts, temporary persistent stores | database files, binary files, cache directories | Name subfolders by storage engine or environment | Source code, documentation, notebooks | `chroma_db/`, `faiss_index/`, `cache/` |
| `rag/storage/chroma_db/` | Persistent Chroma vector store data | Chroma SQLite files, binary index shards, collection metadata | `.sqlite3`, `.bin`, generated internal files | Usually let the storage engine decide names | Hand-authored files, notes, configs | `chroma.sqlite3`, shard folders, Chroma metadata files |
| `rag/models/` | Local model-related assets | Downloaded local models, model manifests, tokenizer files, adapter weights, prompt packs if treated as assets | model-specific files and directories | Group by model/provider/version | Python logic, notebooks, training outputs that belong elsewhere | `llama3.2/`, `nomic-embed-text/`, `adapters/` |
| `rag/results/` | Output artifacts from runs | Evaluation reports, retrieval outputs, experiment results, benchmark snapshots, exported CSV/JSON summaries | `.json`, `.jsonl`, `.csv`, `.md`, `.txt`, `.html` | Use dated or run-specific names; include experiment purpose | Source code, configs, long-term runtime DB storage | `retrieval_eval_2026-04-20.json`, `ranking_report.md`, `ablation.csv` |
| `rag/scripts/` | Operational scripts and entrypoints | Repeatable CLI scripts for ingestion, index building, evaluation, export, cleanup, smoke checks | `.py`, `.sh` | Name by operation and keep them runnable from CLI | Notebook-only exploratory code, shared library code that should be imported | `build_index.py`, `run_ingestion.py`, `evaluate_retrieval.py`, `smoke_test.sh` |
| `rag/tests/` | Automated test code | Unit tests, integration tests, fixtures, test helpers, sample test inputs | `.py`, `.json`, `.jsonl`, fixture files | Use `test_*.py` naming; fixtures should be small and deterministic | Production data, notebooks, generated DB state | `test_models.py`, `test_ingestion.py`, `fixtures/sample_chunks.json` |

## File Placement Rules By Type

| File type | Where it should usually go | Notes |
|---|---|---|
| Pydantic schemas / enums / metadata models | `rag/dataset/` | These define input and chunk metadata contracts |
| PDF ingestion logic | `rag/dataset/` | Parsing, metadata extraction, chunking, page splitting belong here |
| Chroma or vector-store access code | `rag/retriever/` or `rag/utils/` | Put domain-specific search logic in `retriever/`; generic setup helpers can stay in `utils/` |
| Query parsing and metadata filter extraction | `rag/retriever/` | It is part of retrieval behavior |
| Reranking logic | `rag/retriever/` | Keep search and ranking concerns together unless a future `pipeline/` layer is added |
| Shared environment loading | `rag/utils/` | Example: `.env` loading and base path resolution |
| One-time migration helpers | `rag/scripts/` | Do not bury operational scripts inside package code |
| Jupyter exploration | `rag/notebooks/` | Notebook should call package code, not contain permanent business logic |
| Human instructions and notes | `rag/docs/` | Keep these out of code directories |
| Local vector DB files | `rag/storage/` | Never mix them into source folders |
| Evaluation exports | `rag/results/` | Prefer dated names or run IDs |
| Local model binaries or adapters | `rag/models/` | Keep heavy assets out of code directories |
| Temporary backward-compatibility imports | `rag/src/` and `rag/utility/` | These should shrink over time, not grow |

## Recommended Future Files

| If you add this capability | Recommended file | Recommended directory | Why |
|---|---|---|---|
| Better PDF chunking rules | `chunking.py` | `rag/dataset/` | Chunking is part of ingestion/data preparation |
| Filename metadata parsing improvements | `metadata_parser.py` | `rag/dataset/` | Keeps extraction logic isolated and testable |
| Query expansion | `query_expansion.py` | `rag/retriever/` | Query reformulation belongs to retrieval |
| Metadata filter builders | `filters.py` | `rag/retriever/` | Keeps query-to-filter logic centralized |
| Chroma access abstraction | `vector_store.py` | `rag/retriever/` | Useful when storage access becomes more complex |
| Central path helpers | `paths.py` | `rag/utils/` | Prevents hardcoded paths across modules |
| Structured logging helpers | `logging.py` | `rag/utils/` | Shared utility concern |
| CLI ingestion command | `run_ingestion.py` | `rag/scripts/` | Operational entrypoint, not package logic |
| Retrieval evaluation script | `evaluate_retrieval.py` | `rag/scripts/` | Repeatable experiment runner |
| Model config profiles | `retrieval.yaml` / `generation.yaml` | `rag/config/` | Environment/runtime configuration |
| Automated tests for schema validation | `test_models.py` | `rag/tests/` | Directly verifies contracts |
| Sample deterministic fixture docs | `sample_filings.jsonl` | `rag/tests/fixtures/` | Useful for testing ingestion and retrieval |

## Naming Conventions

| Category | Recommended naming style | Examples |
|---|---|---|
| Python modules | lowercase with underscores | `query_expansion.py`, `metadata_parser.py` |
| Notebook files | descriptive workflow names | `data_ingestion.ipynb`, `retrieval_debug.ipynb` |
| Result files | include date or run label | `retrieval_eval_2026-04-20.json` |
| Config files | describe subsystem or environment | `local.yaml`, `ollama.yaml`, `retriever_dev.toml` |
| Tests | `test_*.py` | `test_ingestion.py`, `test_filters.py` |
| Docs | explicit purpose names | `directory_file_placement_guide.md`, `setup_notes.md` |

## Placement Checklist Before Adding A File

| Question | If yes | If no |
|---|---|---|
| Is this reusable backend logic? | Put it in `dataset/`, `retriever/`, or `utils/` | Keep checking below |
| Is this only for notebook exploration? | Put it in `notebooks/` | Keep checking below |
| Is this runtime-generated data? | Put it in `storage/` or `results/` | Keep checking below |
| Is this configuration? | Put it in `config/` | Keep checking below |
| Is this documentation for humans? | Put it in `docs/` | Keep checking below |
| Is this a repeatable command-line entrypoint? | Put it in `scripts/` | Keep checking below |
| Is this only preserving old imports? | Put it in `src/` or `utility/` as a thin wrapper | Re-evaluate the design |

## Anti-Patterns To Avoid

| Anti-pattern | Why it is bad | Correct placement |
|---|---|---|
| Putting reusable functions inside notebooks only | Logic becomes hard to test and reuse | Move the code into `dataset/`, `retriever/`, or `utils/` |
| Saving generated Chroma files inside `dataset/` or `retriever/` | Mixes code and runtime state | Store under `storage/` |
| Creating random files in root such as `test.py` or `new.ipynb` | Root becomes unmanageable very quickly | Put them in `scripts/` or `notebooks/` |
| Adding new real logic into `src/` or `utility/` | Those folders are for compatibility only | Add logic to the new backend packages |
| Storing secrets in Python files | Hard to rotate and unsafe | Keep secrets in `.env` |
| Putting large PDFs in code directories | Bloats source folders and confuses ownership | Use a dedicated data folder in future, or keep sample fixtures under tests only if small |
| Naming files by date only without meaning | Future lookup becomes painful | Use `purpose + date` naming |

## Current Structure Summary

| Current directory | Current intent |
|---|---|
| `rag/config/` | configuration and model/runtime settings |
| `rag/dataset/` | schemas and ingestion backend code |
| `rag/retriever/` | retrieval and reranking backend code |
| `rag/utils/` | shared helpers used by backend modules |
| `rag/src/` | old import compatibility |
| `rag/utility/` | old notebook import compatibility |
| `rag/notebooks/` | exploratory and workflow notebooks |
| `rag/docs/` | human-readable maintenance documents |
| `rag/storage/` | local runtime persistence |
| `rag/models/` | model assets |
| `rag/results/` | outputs and reports |
| `rag/scripts/` | repeatable operational commands |
| `rag/tests/` | automated tests and fixtures |

## Personal Rule Of Thumb

Before creating any new file, ask:

1. Is this code, config, notebook, result, runtime data, or documentation?
2. Will this be imported by other Python modules?
3. Is this generated by the system or written by me?
4. Will I want to test it later?
5. Is this temporary compatibility code or real new architecture?

If those answers are clear, the correct folder is usually obvious.
