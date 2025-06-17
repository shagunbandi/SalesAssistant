"""BuiltWith API integration for technology stack detection."""

import json
import os
from typing import List

import httpx

from .utils import async_retry, safe_get


@async_retry(max_attempts=3)
async def lookup(domain: str, verbose: bool = False) -> List[str]:
    """
    Query BuiltWith Mini REST API to get technology stack information.

    Args:
        domain: Domain to analyze
        verbose: Whether to show detailed logging

    Returns:
        List of major technology categories
    """
    if not domain or not domain.strip():
        if verbose:
            print(
                "    ⚠️  No domain provided to BuiltWith, skipping tech stack analysis..."
            )
        return []

    api_key = os.getenv("BUILTWITH_API_KEY", "")
    if not api_key:
        # Skip BuiltWith lookup if no API key is provided
        if verbose:
            print("    ⚠️  No BuiltWith API key found, skipping tech stack analysis...")
        return []

    try:
        if verbose:
            print(f"    📞 Calling BuiltWith API for domain: {domain}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.builtwith.com/v14/api.json",
                params={"KEY": api_key, "LOOKUP": domain.strip()},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            if verbose:
                print(
                    f"    ✅ BuiltWith API response received (status: {response.status_code})"
                )
                print(f"    📊 Raw response data: {json.dumps(data, indent=2)}")

            # Extract major technology categories
            technologies = []

            # Get results for the domain
            results = safe_get(data, "Results", default=[])
            if not results:
                if verbose:
                    print("    ⚠️  No results found in BuiltWith response")
                return []

            result = results[0]  # First result
            paths = safe_get(result, "Result", "Paths", default=[])

            if not paths:
                if verbose:
                    print("    ⚠️  No paths found in BuiltWith result")
                return []

            path = paths[0]  # First path (usually root)
            categories = safe_get(path, "Technologies", default=[])

            # Extract major categories and avoid duplicates
            seen_categories = set()
            for category in categories:
                category_name = safe_get(category, "Name", default="")
                if category_name and category_name not in seen_categories:
                    technologies.append(category_name)
                    seen_categories.add(category_name)

                    # Limit to avoid overwhelming output
                    if len(technologies) >= 10:
                        break

            if verbose:
                print(f"    📝 Extracted technologies: {technologies}")
            return technologies

    except Exception as e:
        # Never raise - return empty list on any failure
        if verbose:
            print(f"    ❌ BuiltWith lookup failed for '{domain}': {e}")
        return []
