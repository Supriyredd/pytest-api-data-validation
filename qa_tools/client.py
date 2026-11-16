"""Small API client with timeouts, retries on transient errors and request logging."""
import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger("api")


class PharmacyClient:
    def __init__(self, base_url: str, token: str | None, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        # Retry only idempotent GETs on 502/503/504, never on assertion-relevant 4xx.
        retry = Retry(total=2, backoff_factor=0.2, status_forcelist=[502, 503, 504], allowed_methods=["GET"])
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _req(self, method: str, path: str, **kw) -> requests.Response:
        resp = self.session.request(method, f"{self.base_url}{path}", timeout=self.timeout, **kw)
        log.info("%s %s -> %s (%.0f ms)", method, path, resp.status_code, resp.elapsed.total_seconds() * 1000)
        return resp

    def get(self, path: str, **kw) -> requests.Response:
        return self._req("GET", path, **kw)

    def post(self, path: str, **kw) -> requests.Response:
        return self._req("POST", path, **kw)

    def all_patients(self, size: int = 10) -> list[dict]:
        """Walks every page so reconciliation sees the full data set."""
        page, items = 1, []
        while True:
            body = self.get("/patients", params={"page": page, "size": size}).json()
            items.extend(body["items"])
            if page * size >= body["total"]:
                return items
            page += 1
