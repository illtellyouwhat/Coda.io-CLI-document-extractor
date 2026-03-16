"""HTTP client for interacting with the Coda API v1."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterator, Optional

import requests
from requests import Response, Session
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from .utils import LOGGER_NAME


class APIError(RuntimeError):
    """Raised when the Coda API returns an error response."""

    def __init__(self, message: str, status: Optional[int] = None, retryable: bool = False):
        super().__init__(message)
        self.status = status
        self.retryable = retryable


def _retry_filter(exc: BaseException) -> bool:
    """Return True if the exception is retryable."""
    if isinstance(exc, APIError):
        return exc.retryable
    if isinstance(exc, requests.RequestException):
        return True
    return False


class CodaAPI:
    """Simple wrapper around the Coda HTTP API with retry semantics."""

    BASE_URL = "https://coda.io/apis/v1"

    def __init__(
        self,
        token: str,
        timeout: float = 30.0,
        max_retries: int = 5,
        sleep_initial: float = 0.8,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._session: Session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
        )
        self.timeout = timeout
        self.logger = logger or logging.getLogger(LOGGER_NAME)
        self._retry = Retrying(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=sleep_initial, min=sleep_initial, max=60),
            retry=retry_if_exception(_retry_filter),
            reraise=True,
        )

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Any] = None,
    ) -> dict:
        """Perform an HTTP request and return the decoded JSON body."""
        return self._request(method, path, params=params, json=json)

    def request_with_response(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Any] = None,
    ) -> tuple[dict, Response]:
        """Perform an HTTP request and return both JSON body and raw response."""
        payload, response = self._request(
            method,
            path,
            params=params,
            json=json,
            return_response=True,
        )
        return payload, response

    def get(self, path: str, params: Optional[Dict[str, str]] = None) -> dict:
        """Perform a GET request and return the JSON body."""
        return self.request("GET", path, params=params)

    def paginate(self, path: str, params: Optional[Dict[str, str]] = None) -> Iterator[dict]:
        """
        Iterate over paginated responses for endpoints that return ``items``.
        """
        query: Dict[str, str] = dict(params or {})
        while True:
            response = self.get(path, query)
            items = response.get("items", [])
            for item in items:
                yield item
            token = response.get("nextPageToken")
            if not token:
                break
            query["pageToken"] = token

    def download(self, url: str, timeout: float = 60.0) -> bytes:
        """Download binary content using the API session with retry semantics."""

        def _send() -> bytes:
            response = requests.get(url, timeout=timeout, headers={"Accept": "*/*"})
            status = response.status_code
            retryable = status in (429,) or 500 <= status < 600
            if status >= 400:
                message = response.text or f"HTTP {status}"
                raise APIError(f"Coda download error {status}: {message}", status=status, retryable=retryable)
            return response.content

        return self._retry(_send)

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Any] = None,
        *,
        return_response: bool = False,
    ) -> dict | tuple[dict, Response]:
        url = f"{self.BASE_URL}{path}"

        def _send() -> dict | tuple[dict, Response]:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout,
            )
            data = self._process_response(response)
            if return_response:
                return data, response
            return data

        return self._retry(_send)

    def _process_response(self, response: Response) -> dict:
        """Validate HTTP status codes and decode JSON."""
        status = response.status_code
        retryable = status in (429,) or 500 <= status < 600
        if status >= 400:
            try:
                payload = response.json()
            except ValueError:
                payload = {"message": response.text}
            message = payload.get("message") or payload
            raise APIError(f"Coda API error {status}: {message}", status=status, retryable=retryable)
        try:
            return response.json()
        except ValueError as exc:
            raise APIError("Failed to decode JSON response from Coda.", retryable=retryable) from exc

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self) -> "CodaAPI":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
