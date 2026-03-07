"""
Logging configuration for the Lexra backend.
"""
import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = Path("logs") / "lexra_api.log"


def setup_logging() -> None:
    """Configure application-wide logging."""
    LOG_FILE.parent.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE),
        ],
    )

    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
