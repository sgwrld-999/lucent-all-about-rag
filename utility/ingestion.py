"""Compatibility wrapper for older imports from `utility.ingestion`."""

try:
    from lucent.dataset.ingestion import *  # noqa: F403
except ModuleNotFoundError:
    from dataset.ingestion import *  # noqa: F403
