"""Compatibility wrapper for older imports from `utility.retrieval`."""

try:
    from lucent.retriever.retrieval import *  # noqa: F403
except ModuleNotFoundError:
    from retriever.retrieval import *  # noqa: F403
