import os
from pathlib import Path

def pick_test_pdf(data_directory: str | Path, env_var: str = "ATTACHED_PDF_PATH") -> Path:
    """Pick a test PDF from the environment or the configured data directory."""
    attached = os.getenv(env_var, "").strip()
    if attached:
        path = Path(attached)
        if path.is_file() and path.suffix.lower() == ".pdf":
            return path
        raise FileNotFoundError(f"{env_var} is invalid: {attached}")

    pdfs = sorted(Path(data_directory).rglob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF found under DATA_DIRECTORY: {data_directory}")
    return pdfs[0]