"""Compatibility wrapper for older imports from `src.models`."""

try:
    from lucent.dataset.models import ChunkMetadata, DocType, FiscalQuarter, RankingKeywords
except ModuleNotFoundError:
    from dataset.models import ChunkMetadata, DocType, FiscalQuarter, RankingKeywords

__all__ = ["ChunkMetadata", "DocType", "FiscalQuarter", "RankingKeywords"]
