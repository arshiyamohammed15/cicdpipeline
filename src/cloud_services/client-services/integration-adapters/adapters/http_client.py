"""
Common HTTP client for adapters with retries, idempotency, and rate limit awareness.

What: Shared HTTP client with retry logic, idempotency, rate limit handling per FR-14
Why: Centralize HTTP concerns (retries, backoff, rate limits) for all adapters
Reads/Writes: External provider APIs via HTTP
Contracts: PRD FR-8 (Error Handling, Retries & Circuit Breaking)
Risks: Rate limit violations, unbounded retries, circuit breaker failures
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Dict, Optional
from enum import Enum

import httpx


class ErrorType(str, Enum):
    """Error classification per FR-8."""
    CLIENT = "client"  # 4xx (except 429/408)
    SERVER = "server"  # 5xx
    NETWORK = "network"  # Connection errors, timeouts
    RATE_LIMIT = "rate_limit"  # 429


class HTTPClient:
    """
    HTTP client with retry logic, idempotency, and rate limit awareness.
    
    Features:
    - Exponential backoff with jitter
    - Idempotency key injection
    - Rate limit header parsing (429, Retry-After)
    - Circuit breaker integration
    - Error classification
    """

    def __init__(
        self,
        base_url: str,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        jitter: bool = True,
        timeout: float = 30.0,
    ):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL for API requests
            max_retries: Maximum number of retries
            initial_backoff: Initial backoff time in seconds
            max_backoff: Maximum backoff time in seconds
            jitter: Whether to add jitter to backoff
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.jitter = jitter
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method
            path: Request path
            headers: HTTP headers
            json: JSON body
            params: Query parameters
            idempotency_key: Optional idempotency key
            
        Returns:
            HTTP response
            
        Raises:
            httpx.HTTPError: If request fails after retries
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        request_headers = headers or {}
        
        # Add idempotency key if provided
        if idempotency_key:
            request_headers["Idempotency-Key"] = idempotency_key
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=json,
                    params=params,
                )
                
                # Check for rate limit (429)
                if response.status_code == 429:
                    retry_after = self._parse_retry_after(response.headers)
                    if retry_after and attempt < self.max_retries:
                        time.sleep(retry_after)
                        continue
                    return response
                
                # Check for retryable errors
                error_type = self._classify_error(response.status_code)
                if error_type in [ErrorType.SERVER, ErrorType.NETWORK] and attempt < self.max_retries:
                    backoff = self._calculate_backoff(attempt)
                    time.sleep(backoff)
                    continue
                
                # Non-retryable or success
                return response
                
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                error_type = ErrorType.NETWORK
                if attempt < self.max_retries:
                    backoff = self._calculate_backoff(attempt)
                    time.sleep(backoff)
                    continue
                raise
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise httpx.HTTPError(f"Request failed after {self.max_retries} retries")

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff with jitter.
        
        Args:
            attempt: Retry attempt number (0-indexed)
            
        Returns:
            Backoff time in seconds
        """
        backoff = min(
            self.initial_backoff * (2 ** attempt),
            self.max_backoff
        )
        
        if self.jitter:
            # Add random jitter (0-25% of backoff time)
            jitter_amount = backoff * 0.25 * random.random()
            backoff += jitter_amount
        
        return backoff

    def _parse_retry_after(self, headers: Dict[str, str]) -> Optional[float]:
        """
        Parse Retry-After header.
        
        Args:
            headers: HTTP response headers
            
        Returns:
            Retry-After value in seconds, or None
        """
        retry_after = headers.get("Retry-After")
        if not retry_after:
            return None
        
        try:
            # Retry-After can be seconds (integer) or HTTP date
            return float(retry_after)
        except ValueError:
            # Try parsing as HTTP date (not implemented for simplicity)
            return None

    def _classify_error(self, status_code: int) -> ErrorType:
        """
        Classify HTTP error per FR-8.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            Error type
        """
        if status_code == 429:
            return ErrorType.RATE_LIMIT
        elif 400 <= status_code < 500:
            if status_code in [408, 429]:
                return ErrorType.RATE_LIMIT
            return ErrorType.CLIENT
        elif 500 <= status_code < 600:
            return ErrorType.SERVER
        else:
            return ErrorType.CLIENT

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

