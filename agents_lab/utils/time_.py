from datetime import datetime
from zoneinfo import ZoneInfo


def get_current_utc_time() -> datetime:
    return datetime.now(tz=ZoneInfo("UTC"))
