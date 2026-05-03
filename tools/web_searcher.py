"""DuckDuckGo web searcher tool implementation."""

from __future__ import annotations

import json
from urllib.parse import quote_plus
from urllib.request import urlopen

from lucent.config.settings import Settings, get_settings
from lucent.interfaces import WebSearchTool


class DuckDuckGoSearcher(WebSearchTool):
    """Web search using DuckDuckGo Instant Answer API."""

    def __init__(self, settings: Settings | None = None):
        """Initialize with settings."""
        self.settings = settings or get_settings()

    def invoke(self, query: str, num_results: int = 5) -> str:
        """Search using DuckDuckGo API."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return "No query provided."

        limit = max(1, int(num_results))
        encoded_query = quote_plus(cleaned_query)
        url = (
            "https://api.duckduckgo.com/"
            f"?q={encoded_query}&format=json&no_redirect=1&no_html=1"
        )

        print(f"\n[WEB_SEARCH] Query: {cleaned_query}")

        try:
            with urlopen(url, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            return f"Web search failed: {exc}"

        rows: list[str] = [f"Results for: '{cleaned_query}'"]

        heading = payload.get("Heading", "").strip()
        abstract = payload.get("AbstractText", "").strip()
        abstract_url = payload.get("AbstractURL", "").strip()
        if abstract:
            rows.append(f"1. **{heading or 'Top result'}**\n   {abstract}\n   {abstract_url}")

        related = self._extract_topics(payload, limit)
        start_idx = 2 if abstract else 1
        for offset, (title, snippet) in enumerate(related, start=start_idx):
            rows.append(f"{offset}. **{title}**\n   {snippet}")

        if len(rows) == 1:
            print(f"[WEB_SEARCH] No results found")
            return f"No web results for '{cleaned_query}'."

        output = "\n\n".join(rows)
        self._write_debug(output, cleaned_query)
        return output

    @staticmethod
    def _extract_topics(payload: dict, limit: int) -> list[tuple[str, str]]:
        """Extract topic title and snippet from payload."""
        rows: list[tuple[str, str]] = []
        for topic in payload.get("RelatedTopics", []):
            if isinstance(topic, dict) and "Topics" in topic:
                for nested in topic.get("Topics", []):
                    text = nested.get("Text", "") if isinstance(nested, dict) else ""
                    if text:
                        title, _, snippet = text.partition(" - ")
                        rows.append((title or "Related", snippet or text))
            elif isinstance(topic, dict):
                text = topic.get("Text", "")
                if text:
                    title, _, snippet = text.partition(" - ")
                    rows.append((title or "Result", snippet or text))
            if len(rows) >= limit:
                break
        return rows[:limit]

    def _write_debug(self, content: str, query: str) -> None:
        """Write debug output to file."""
        debug_dir = self.settings.ensure_debug_dir()
        debug_file = debug_dir / "web_search_results.md"
        debug_file.write_text(f"Query: {query}\n\n{content}", encoding="utf-8")
