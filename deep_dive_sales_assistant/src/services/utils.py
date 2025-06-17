"""Utility functions for the sales assistant."""

import asyncio
import json
import random
from functools import wraps
from typing import Any, Callable, TypeVar, Union

import httpx

T = TypeVar("T")


def async_retry(max_attempts: int = 3, base_delay: float = 0.4) -> Callable:
    """
    Async retry decorator with exponential backoff and jitter.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds (0.4 → 1.2 → 3.6)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        break

                    # Exponential backoff with jitter: 0.4 → 1.2 → 3.6 seconds
                    delay = base_delay * (3**attempt)
                    jitter = random.uniform(0, delay * 0.1)  # 10% jitter
                    await asyncio.sleep(delay + jitter)
                except Exception as e:
                    # Don't retry for non-network errors
                    last_exception = e
                    break

            if last_exception:
                raise last_exception

            # This should never be reached, but just in case
            raise RuntimeError("Unexpected error in retry logic")

        return wrapper

    return decorator


def compact_json(data: Any) -> str:
    """
    Convert data to compact JSON string.

    Args:
        data: Data to serialize

    Returns:
        Compact JSON string
    """
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def safe_get(data: dict, *keys: str, default: Any = "") -> Any:
    """
    Safely get nested dictionary value.

    Args:
        data: Dictionary to traverse
        *keys: Keys to traverse (e.g., 'a', 'b', 'c' for data['a']['b']['c'])
        default: Default value if key path doesn't exist

    Returns:
        Value at key path or default
    """
    try:
        result = data
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError, IndexError):
        return default


def normalize_domain(url: str) -> str:
    """
    Extract domain from URL or return empty string if invalid.

    Args:
        url: URL to normalize

    Returns:
        Domain string or empty string
    """
    if not url or not isinstance(url, str):
        return ""

    try:
        import tldextract

        extracted = tldextract.extract(url)
        if extracted.domain and extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}"
        return ""
    except Exception:
        return ""
