"""
LMS API Client for fetching data from the backend.

Uses httpx for HTTP requests with Bearer token authentication.
"""

import httpx
from typing import Optional


class LmsApiError(Exception):
    """Custom exception for LMS API errors with user-friendly messages."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class LmsApiClient:
    """Client for the LMS backend API."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create an HTTP client with proper headers."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
        return self._client

    def get_items(self) -> list[dict]:
        """
        Fetch all items (labs and tasks) from the backend.

        Returns:
            List of item dictionaries with 'id', 'title', 'type', etc.

        Raises:
            LmsApiError: If the API request fails.
        """
        try:
            client = self._get_client()
            response = client.get("/items/")
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            raise LmsApiError(
                f"connection refused ({self.base_url}). Check that the services are running."
            ) from e
        except httpx.HTTPStatusError as e:
            raise LmsApiError(
                f"HTTP {e.response.status_code} {e.response.reason_phrase}. "
                "The backend service may be unavailable."
            ) from e
        except httpx.HTTPError as e:
            raise LmsApiError(f"HTTP error: {type(e).__name__}: {e}") from e
        except Exception as e:
            raise LmsApiError(f"unexpected error: {type(e).__name__}: {e}") from e

    def get_pass_rates(self, lab: str) -> list[dict]:
        """
        Fetch pass rates for a specific lab.

        Args:
            lab: The lab identifier (e.g., "lab-04").

        Returns:
            List of task pass rates with 'task', 'avg_score', 'attempts'.

        Raises:
            LmsApiError: If the API request fails.
        """
        try:
            client = self._get_client()
            response = client.get("/analytics/pass-rates", params={"lab": lab})
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            raise LmsApiError(
                f"connection refused ({self.base_url}). Check that the services are running."
            ) from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise LmsApiError(f"lab '{lab}' not found.") from e
            raise LmsApiError(
                f"HTTP {e.response.status_code} {e.response.reason_phrase}. "
                "The backend service may be unavailable."
            ) from e
        except httpx.HTTPError as e:
            raise LmsApiError(f"HTTP error: {type(e).__name__}: {e}") from e
        except Exception as e:
            raise LmsApiError(f"unexpected error: {type(e).__name__}: {e}") from e

    def health_check(self) -> dict:
        """
        Perform a health check by fetching items count.

        Returns:
            Dict with 'healthy' bool and 'item_count' int.

        Raises:
            LmsApiError: If the API request fails.
        """
        try:
            items = self.get_items()
            return {"healthy": True, "item_count": len(items)}
        except LmsApiError:
            raise

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None
