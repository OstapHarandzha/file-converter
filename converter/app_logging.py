import logging
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "converter.log"


def setup_logging() -> None:
    """Write operations and errors to converter.log in the project folder."""
    logging.basicConfig(
        filename=LOG_FILE,
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
