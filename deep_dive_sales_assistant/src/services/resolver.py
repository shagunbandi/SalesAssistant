"""Google Knowledge Graph API integration for company resolution."""

import json
import os
from typing import Dict

import httpx

from .utils import async_retry, normalize_domain, safe_get


@async_retry(max_attempts=3)
async def lookup(company: str, verbose: bool = False) -> Dict[str, str]:
    """
    Query Google Knowledge Graph Search API to resolve company information.

    Args:
        company: Company name to search for
        verbose: Whether to show detailed logging

    Returns:
        Dictionary with domain, logo, brief, and source fields
    """
    api_key = os.getenv("GOOGLE_KG_API_KEY", "")
    if not api_key:
        if verbose:
            print("    ⚠️  No Google KG API key found, skipping company resolution...")
        return {"domain": "", "logo": "", "brief": "", "source": "googlekg"}

    if not company or not company.strip():
        if verbose:
            print("    ⚠️  Empty company name provided to resolver...")
        return {"domain": "", "logo": "", "brief": "", "source": "googlekg"}

    try:
        if verbose:
            print(f"    📞 Calling Google Knowledge Graph API for: {company}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://kgsearch.googleapis.com/v1/entities:search",
                params={
                    "query": company.strip(),
                    "key": api_key,
                    "limit": 1,
                    "types": "Organization",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            if verbose:
                print(
                    f"    ✅ Google KG API response received (status: {response.status_code})"
                )
                print(f"    📊 Raw response data: {json.dumps(data, indent=2)}")

            items = safe_get(data, "itemListElement", default=[])
            if not items:
                if verbose:
                    print("    ⚠️  No items found in Google KG response")
                return {"domain": "", "logo": "", "brief": "", "source": "googlekg"}

            item = safe_get(items[0], "result", default={})

            # Extract domain from URL
            url = safe_get(item, "url", default="")
            domain = normalize_domain(url)

            # Extract logo
            logo = safe_get(item, "image", "contentUrl", default="")

            # Extract brief description
            brief = safe_get(item, "description", default="") or safe_get(
                item, "detailedDescription", "articleBody", default=""
            )

            result = {
                "domain": domain,
                "logo": logo,
                "brief": brief,
                "source": "googlekg",
            }

            if verbose:
                print(f"    📝 Parsed result: {json.dumps(result, indent=2)}")
            return result

    except Exception as e:
        # Never raise - return empty results on any failure
        if verbose:
            print(f"    ❌ Google KG lookup failed for '{company}': {e}")
        return {"domain": "", "logo": "", "brief": "", "source": "googlekg"}
