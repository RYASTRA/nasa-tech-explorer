"""Throttled, retrying HTTP client for the T2 API."""

import time
from typing import Callable

import httpx

from .config import API_BASE, REQUEST_RPS, REQUEST_TIMEOUT, RETRIES, USER_AGENT


class QueryError(Exception):
    """A query failed after all retries, or returned a malformed body."""


class T2Client:
    """Small wrapper around httpx with politeness throttling and retries."""

    def __init__(
        self,
        client: httpx.Client | None = None,
        rps: float = REQUEST_RPS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client or httpx.Client(
            timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT}
        )
        self._min_interval = 1.0 / rps
        self._sleep = sleep
        self._last_request = 0.0

    def _throttle(self) -> None:
        wait = self._min_interval - (time.monotonic() - self._last_request)
        if wait > 0:
            self._sleep(wait)
        self._last_request = time.monotonic()

    def fetch(self, dataset: str, term: str) -> list[list]:
        """Return all result rows for one keyword query (the API does not paginate)."""
        url = f"{API_BASE}/{dataset}/{term}"
        last_error: Exception | None = None
        for attempt in range(RETRIES):
            self._throttle()
            try:
                response = self._client.get(url)
                if response.status_code == 200:
                    body = response.json()
                    results = body.get("results")
                    if isinstance(results, list):
                        return results
                    raise QueryError(f"malformed body from {url}")
                last_error = QueryError(f"HTTP {response.status_code} from {url}")
            except (httpx.HTTPError, ValueError) as exc:  # ValueError covers bad JSON
                last_error = exc
            self._sleep(2**attempt)
        raise QueryError(f"query failed after {RETRIES} tries: {url}") from last_error

    def close(self) -> None:
        """Release the underlying HTTP connection pool."""
        self._client.close()
