"""Reusable retrieval and reranking helpers."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from urllib.request import urlopen

from rank_bm25 import BM25Plus

try:
    from lucent.schemas.models import ChunkMetadata, RankingKeywords
    from lucent.utils.common import DEFAULT_BASE_URL, create_chat_llm
except ModuleNotFoundError:
    from schemas.models import ChunkMetadata, RankingKeywords
    from utils.common import DEFAULT_BASE_URL, create_chat_llm


COMPANY_PATTERN = re.compile(
    r"\b(amazon|amzn|google|alphabet|googl|goog|apple|aapl|microsoft|msft|tesla|tsla|nvidia|nvda|meta|facebook|fb)\b",
    re.IGNORECASE,
)
DOC_TYPE_PATTERN = re.compile(
    r"\b(annual report|quarterly report|current report|10-k|10-q|8-k)\b",
    re.IGNORECASE,
)
TIME_PATTERN = re.compile(
    r"\b(20\d{2}|q[1-4]|quarter\s*[1-4]|fiscal\s+year|fy\s*20\d{2})\b",
    re.IGNORECASE,
)
FINANCIAL_PATTERN = re.compile(
    r"\b(revenue|net income|profit|profitability|cash flow|assets|liabilities|equity|eps|earnings)\b",
    re.IGNORECASE,
)


def available_models(base_url: str) -> set[str]:
    """Return the Ollama model names available at the provided host."""
    try:
        with urlopen(f"{base_url}/api/tags", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {model.get("name", "") for model in payload.get("models", [])}
    except Exception:
        return set()


def initialize_llm(
    preferred_model: str,
    base_url: str,
    fallback_base_url: str = DEFAULT_BASE_URL,
    probe_prompt: str = "Hello",
) -> tuple[object, object, str]:
    """Create a working LLM client with model and base-url fallbacks."""
    model_candidates = [
        preferred_model,
        preferred_model.replace("llama.", "llama"),
        "llama3.2:latest",
        "llama3.2",
    ]
    model_candidates = list(dict.fromkeys(model_candidates))

    base_url_candidates = [base_url, fallback_base_url]
    base_url_candidates = list(dict.fromkeys(base_url_candidates))

    llm = None
    response = None
    last_error = None
    selected_model = preferred_model

    for candidate_base_url in base_url_candidates:
        known_models = available_models(candidate_base_url)
        for candidate_model in model_candidates:
            if known_models and candidate_model not in known_models:
                continue
            try:
                test_llm = create_chat_llm(
                    model_name=candidate_model,
                    base_url=candidate_base_url,
                )
                test_response = test_llm.invoke(probe_prompt)
                llm = test_llm
                response = test_response
                selected_model = candidate_model
                break
            except Exception as exc:
                last_error = exc
        if llm is not None:
            break

    if llm is None:
        raise RuntimeError(
            f"Failed to initialize LLM. Last error: {last_error}\n"
            "Install a valid model, e.g.: ollama pull llama3.2:latest"
        )

    return llm, response, selected_model


def has_required_signals(user_query: str) -> bool:
    """Return True when the query contains expected SEC/financial hints."""
    if not user_query or not user_query.strip():
        return False

    return any(
        pattern.search(user_query)
        for pattern in (
            COMPANY_PATTERN,
            DOC_TYPE_PATTERN,
            TIME_PATTERN,
            FINANCIAL_PATTERN,
        )
    )


def extract_filters(llm, user_query: str) -> dict:
    """Extract structured metadata filters from a user query."""
    if not has_required_signals(user_query):
        print("No relevant company/doc/time/financial signals found. Skipping extraction.")
        return {}

    prompt = f"""
Extract metadata filters from the query. Return None for fields not mentioned.

USER QUERY: {user_query}

COMPANY MAPPINGS:
- Amazon/AMZN -> amazon
- Google/Alphabet/GOOGL/GOOG -> google
- Apple/AAPL -> apple
- Microsoft/MSFT -> microsoft
- Tesla/TSLA -> tesla
- Nvidia/NVDA -> nvidia
- Meta/Facebook/FB -> meta

DOC TYPE:
- Annual report -> 10-k
- Quarterly report -> 10-q
- Current report -> 8-k

EXAMPLES:
"Amazon Q3 2024 revenue" -> {{"company_name": "amazon", "doc_type": "10-q", "fiscal_year": 2024, "fiscal_quarter": "q3"}}
"Apple 2023 annual report" -> {{"company_name": "apple", "doc_type": "10-k", "fiscal_year": 2023}}
"Tesla profitability" -> {{"company_name": "tesla"}}

Extract metadata:
""".strip()

    try:
        metadata = llm.with_structured_output(ChunkMetadata).invoke(prompt)
        return metadata.model_dump(exclude_none=True)
    except Exception as exc:
        print(f"extract_filters failed: {exc}")
        return {}


def generate_ranking_keywords(llm, user_query: str) -> list[str]:
    """Generate exactly five ranking keywords using filing terminology."""
    if not has_required_signals(user_query):
        print("No relevant company/doc/time/financial signals found. Skipping extraction.")
        return []

    prompt = f"""Generate EXACTLY 5 financial keywords from SEC filings terminology.

USER QUERY: {user_query}

USE EXACT TERMS FROM 10-K/10-Q FILINGS:

STATEMENT HEADINGS:
"consolidated statements of operations", "consolidated balance sheets", "consolidated statements of cash flows", "consolidated statements of stockholders equity"

INCOME STATEMENT:
"revenue", "net revenue", "cost of revenue", "gross profit", "operating income", "net income", "earnings per share"

BALANCE SHEET:
"total assets", "cash and cash equivalents", "total liabilities", "stockholders equity", "working capital", "long-term debt"

CASH FLOWS:
"cash flows from operating activities", "net cash provided by operating activities", "cash flows from investing activities", "free cash flow", "capital expenditures"

RULES:
- Return EXACTLY 5 keywords
- Use exact phrases from SEC filings
- Match query topic (revenue -> revenue terms, cash -> cash flow terms)
- Use "cash flows" (plural), "stockholders equity"

EXAMPLES:
"revenue analysis" -> ["revenue", "net revenue", "total revenue", "consolidated statements of operations", "net sales"]
"cash flow performance" -> ["consolidated statements of cash flows", "cash flows from operating activities", "net cash provided by operating activities", "free cash flow", "operating activities"]
"balance sheet strength" -> ["consolidated balance sheets", "total assets", "stockholders equity", "cash and cash equivalents", "long-term debt"]

Generate EXACTLY 5 keywords:
""".strip()

    try:
        result = llm.with_structured_output(RankingKeywords).invoke(prompt)
        if hasattr(result, "keywords"):
            return result.keywords
        if hasattr(result, "ranked_keyword"):
            return [result.ranked_keyword]
        print(f"Unexpected schema: {result}")
        return []
    except Exception as exc:
        print(f"generate_ranking_keywords failed: {type(exc).__name__}: {exc}")
        return []


def build_search_keyword_args(
    filters: dict | None = None,
    ranking_keywords: Sequence[str] | None = None,
    k: int = 5,
) -> dict:
    """Build Chroma search kwargs from metadata filters and keyword hints."""
    if not isinstance(k, int) or k <= 0:
        raise ValueError(f"`k` must be a positive integer. Got: {k}")

    search_keyword_args: dict[str, object] = {
        "k": k,
        "fetch_k": k * 20,
    }

    if filters is not None:
        if not isinstance(filters, dict):
            raise TypeError(f"`filters` must be a dict or None. Got: {type(filters).__name__}")
        cleaned_filters = {
            key: value
            for key, value in filters.items()
            if value is not None and str(value).strip() != ""
        }
        if cleaned_filters:
            if len(cleaned_filters) == 1:
                search_keyword_args["filter"] = cleaned_filters
            else:
                search_keyword_args["filter"] = {
                    "$and": [{key: value} for key, value in cleaned_filters.items()]
                }

    if ranking_keywords is not None:
        if not isinstance(ranking_keywords, (list, tuple, set)):
            raise TypeError(
                "`ranking_keywords` must be a list/tuple/set or None. "
                f"Got: {type(ranking_keywords).__name__}"
            )

        normalized_keywords: list[str] = []
        seen: set[str] = set()
        for keyword in ranking_keywords:
            if not isinstance(keyword, str):
                continue
            cleaned_keyword = keyword.strip()
            if cleaned_keyword and cleaned_keyword not in seen:
                normalized_keywords.append(cleaned_keyword)
                seen.add(cleaned_keyword)

        if normalized_keywords:
            if len(normalized_keywords) == 1:
                search_keyword_args["where_document"] = {
                    "$contains": normalized_keywords[0]
                }
            else:
                search_keyword_args["where_document"] = {
                    "$or": [{"$contains": keyword} for keyword in normalized_keywords]
                }

    return search_keyword_args


def search_vector_database(
    vector_store,
    query: str,
    filters: dict | None = None,
    ranking_keywords: Sequence[str] | None = None,
    k: int = 3,
):
    """Search the vector store using metadata and content filters."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("`query` must be a non-empty string.")

    search_kwargs = build_search_keyword_args(
        filters=filters,
        ranking_keywords=ranking_keywords,
        k=k,
    )
    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs,
    )
    return retriever.invoke(query)


def extract_headings_with_content(text: str) -> list[str]:
    """Extract markdown headings with the paragraph that follows them."""
    try:
        if not isinstance(text, str):
            raise TypeError(f"`text` must be a string. Got: {type(text).__name__}")

        stripped_text = text.strip()
        if not stripped_text:
            return []

        extracted_chunks: list[str] = []
        sections = [
            section.strip() for section in stripped_text.split("\n\n") if section.strip()
        ]
        heading_pattern = re.compile(r"^#+\s+")

        index = 0
        while index < len(sections):
            current_section = sections[index]
            if heading_pattern.match(current_section):
                if index + 1 < len(sections):
                    extracted_chunks.append(
                        f"{current_section}\n\n{sections[index + 1]}"
                    )
                    index += 2
                else:
                    extracted_chunks.append(current_section)
                    index += 1
            else:
                index += 1

        return extracted_chunks
    except Exception as exc:
        print(f"extract_headings_with_content failed: {type(exc).__name__}: {exc}")
        return []


def rank_documents_by_keywords(docs, keywords, k: int = 5):
    """Rank documents with BM25Plus using headings and adjacent content."""
    if not docs or not keywords:
        print("No documents or keywords found.")
        return []

    if not isinstance(k, int) or k <= 0:
        raise ValueError(f"`k` must be a positive integer. Got: {k}")

    def tokenize(text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    query_tokens = tokenize(" ".join(str(keyword) for keyword in keywords if keyword))
    if not query_tokens:
        print("No valid query tokens found.")
        return []

    doc_tokens = []
    for doc in docs:
        chunks = extract_headings_with_content(getattr(doc, "page_content", "") or "")
        combined_text = " ".join(chunks) if chunks else getattr(doc, "page_content", "") or ""
        doc_tokens.append(tokenize(combined_text))

    if not any(doc_tokens):
        print("No valid document content found.")
        return []

    bm25 = BM25Plus(doc_tokens)
    scores = bm25.get_scores(query_tokens)
    ranked_indices = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)

    for rank, index in enumerate(ranked_indices[:k], start=1):
        print(f"[{rank}] Doc {index}: score={scores[index]:.4f}")

    return [docs[index] for index in ranked_indices[:k]]


def initialize_retrieval_runtime(
    *,
    preferred_model: str,
    base_url: str,
    vector_store,
    fallback_base_url: str = DEFAULT_BASE_URL,
    probe_prompt: str = "Hello",
) -> dict[str, object]:
    """Initialize the LLM used by retrieval workflows and return runtime objects."""
    llm, response, selected_model = initialize_llm(
        preferred_model=preferred_model,
        base_url=base_url,
        fallback_base_url=fallback_base_url,
        probe_prompt=probe_prompt,
    )
    return {
        "llm": llm,
        "response": response,
        "selected_model": selected_model,
        "vector_store": vector_store,
        "base_url": base_url,
    }
