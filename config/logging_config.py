import re
import sys
from collections import Counter
from pathlib import Path
from typing import List, Optional, Tuple, Union

from loguru import logger

from config.settings import LOGS_DIR

LOG_DIR = LOGS_DIR

# Daily log file names end with _YYYY-MM-DD.log (e.g. CSCN_portal_2026-06-15.log).
_LOG_DATE_RE = re.compile(r"_(\d{4}-\d{2}-\d{2})\.log$")

# A standard loguru file line: "TIME | LEVEL | name:func:line - message".
_LOG_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\|\s*"
    r"(?P<level>[A-Z]+)\s*\|\s*"
    r"(?P<loc>\S+)\s-\s"
    r"(?P<msg>.*)$"
)

def setup_logging():
    """
    Configures the application logging using loguru.
    Logs are written to both the console and rotating log files.
    """
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Remove the default logger to configure a new one
    logger.remove()

    # Define log format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Add console handler only if sys.stderr exists (PyInstaller windowed apps have None)
    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            format=log_format,
            level="INFO",
            colorize=True
        )

    # Add file handler for general application logs
    logger.add(
        LOG_DIR / "CSCN_portal_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="DEBUG",
        rotation="10 MB",  # Rotate when file reaches 10MB
        retention="30 days",  # Keep logs for 30 days
        compression="zip",  # Compress older logs
        encoding="utf-8"
    )

    # Add specific file handler for errors
    logger.add(
        LOG_DIR / "CSCN_portal_error.log",
        format=log_format,
        level="ERROR",
        rotation="10 MB",
        retention="60 days",
        encoding="utf-8"
    )

    logger.info("Logging configured successfully.")


def list_log_files() -> List[Tuple[str, Path]]:
    """Return the available application log files as (label, path), newest first.

    Every dated daily log is included regardless of name prefix, so files written
    under a previous app name (e.g. the old mhnsec_* logs) still show up in the
    history. The error-only logs are excluded — they are a subset, not the full
    logging. The label is the YYYY-MM-DD date parsed from the file name."""
    try:
        entries = []
        for p in LOG_DIR.glob("*.log"):
            if p.name.endswith("_error.log"):
                continue
            m = _LOG_DATE_RE.search(p.name)
            date = m.group(1) if m else ""
            prefix = p.name[: m.start()] if m else p.stem  # e.g. "CSCN_portal"
            entries.append((date, prefix, p))
        # Newest first: sort by the parsed date, then file name as a tiebreaker.
        entries.sort(key=lambda e: (e[0], e[2].name), reverse=True)
        # When the same date has more than one file (e.g. logs written under a
        # previous app name), append the name prefix so the labels stay distinct.
        dupes = {d for d, c in Counter(d for d, _, _ in entries if d).items() if c > 1}
        result = []
        for date, prefix, p in entries:
            if not date:
                result.append((prefix, p))
            elif date in dupes:
                result.append((f"{date} ({prefix})", p))
            else:
                result.append((date, p))
        return result
    except OSError:
        return []


def get_latest_log_file() -> Optional[Path]:
    """Return the most recent application log file, or None if none exists."""
    files = list_log_files()
    return files[0][1] if files else None


def read_log_tail(path: Optional[Union[Path, str]] = None, max_bytes: int = 1_000_000) -> str:
    """Read the full application log (logs.log) for a given file, or the most
    recent one when `path` is None. Returns at most `max_bytes` from the end of
    the file so the UI stays responsive even after the file has grown; the
    leading partial line is dropped when truncated."""
    if path is None:
        path = get_latest_log_file()
    if path is None:
        return ""
    path = Path(path)
    try:
        size = path.stat().st_size
        with path.open("r", encoding="utf-8", errors="replace") as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
                f.readline()  # discard the partial first line after seeking
            return f.read()
    except OSError as e:
        return f"تعذّر قراءة ملف السجل: {e}"


def parse_log_lines(text: str) -> List[List[str]]:
    """Split raw log text into [time, level, source, message] rows for tabular
    (Excel/PDF) export. Lines that don't match the standard format (tracebacks,
    wrapped output) are kept as a message-only row so nothing is lost."""
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        m = _LOG_LINE_RE.match(line)
        if m:
            rows.append([m.group("ts"), m.group("level"), m.group("loc"), m.group("msg")])
        else:
            rows.append(["", "", "", line])
    return rows


# Setup logging automatically when module is imported
setup_logging()
