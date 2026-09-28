"""A daily background check; HTTP probes only read its cached result."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

DAY_SECONDS = 24 * 60 * 60


class DatabaseMonitor:
    def __init__(self, check):
        self.check = check
        self.result = {"ok": None, "checkedAt": None, "nextCheckAt": None}

    async def check_once(self):
        checked_at = datetime.now(timezone.utc).isoformat()
        try:
            database = await asyncio.to_thread(self.check)
            result = {"ok": True, "database": database, "checkedAt": checked_at}
        except Exception:
            logging.getLogger(__name__).error("Daily database check failed")
            result = {"ok": False, "database": {"ok": False}, "checkedAt": checked_at}
        result["nextCheckAt"] = (
            datetime.now(timezone.utc) + timedelta(seconds=DAY_SECONDS)
        ).isoformat()
        self.result = result

    async def run(self):
        while True:
            await self.check_once()
            await asyncio.sleep(DAY_SECONDS)

    def snapshot(self):
        return dict(self.result)
