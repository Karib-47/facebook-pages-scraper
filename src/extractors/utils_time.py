thonimport logging
from datetime import datetime
from typing import Optional

from dateutil import parser, tz

logger = logging.getLogger(__name__)

def parse_datetime_to_unix_ms(value: str, default_tz: str = "UTC") -> Optional[int]:
    """
    Parse a human-readable datetime into a UNIX timestamp in milliseconds.

    Returns None if parsing fails.
    """
    if not value:
        return None

    try:
        dt = parser.parse(value)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=tz.gettz(default_tz))
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError, OverflowError) as exc:
        logger.warning("Failed to parse datetime '%s': %s", value, exc)
        return None

def unix_ms_to_iso(ts: Optional[int]) -> Optional[str]:
    """
    Convert a UNIX timestamp in milliseconds to an ISO 8601 string in UTC.
    """
    if ts is None:
        return None
    dt = datetime.fromtimestamp(ts / 1000.0, tz=tz.UTC)
    return dt.isoformat()

def now_unix_ms() -> int:
    """
    Get the current UNIX timestamp in milliseconds (UTC).
    """
    return int(datetime.now(tz.UTC).timestamp() * 1000)