"""Perplexity Sonar API integration for company research and news."""

import json
import os
from typing import Dict, List

import httpx

from .utils import async_retry, safe_get


@async_retry(max_attempts=3)
async def search(
    company: str, domain: str = "", verbose: bool = False
) -> Dict[str, any]:
    """
    Query Perplexity Sonar API for company information and recent news.

    Args:
        company: Company name to search for
        domain: Domain name (optional, for better context)
        verbose: Whether to show detailed logging

    Returns:
        Dictionary with answer and citations
    """
    api_key = os.getenv("SONAR_API_KEY", "")
    if not api_key:
        if verbose:
            print(
                "    ⚠️  No Perplexity Sonar API key found, skipping company insights..."
            )
        return {"answer": "", "citations": []}

    if not company or not company.strip():
        if verbose:
            print("    ⚠️  Empty company name provided to Sonar...")
        return {"answer": "", "citations": []}

    # Construct search prompt
    domain_context = f" ({domain})" if domain else " (unknown domain)"
    prompt = (
        f"What does {company.strip()}{domain_context} do, which sales channels do they use, "
        f"and any recent news about them? Provide citations."
    )

    if verbose:
        print(f"    📞 Calling Perplexity Sonar API for: {company}")
        print(f"    💬 Search prompt: {prompt}")

    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",  # Sonar model for web search
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_completion_tokens": 600,
                "return_citations": True,
                "search_domain_filter": ["perplexity.ai"] if not domain else None,
            }

            if verbose:
                print(f"    📦 Request payload: {json.dumps(payload, indent=2)}")

            response = await client.post(
                "https://api.perplexity.ai/chat/completions",  # Sonar endpoint
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

            if verbose:
                print(
                    f"    ✅ Perplexity Sonar API response received (status: {response.status_code})"
                )
                print(f"    📊 Raw response data: {json.dumps(data, indent=2)}")

            # Extract answer
            choices = safe_get(data, "choices", default=[])
            if not choices:
                if verbose:
                    print("    ⚠️  No choices found in Sonar response")
                return {"answer": "", "citations": []}

            answer = safe_get(choices[0], "message", "content", default="")
            if verbose:
                print(
                    f"    💡 Answer extracted: {answer[:200]}{'...' if len(answer) > 200 else ''}"
                )

            # Extract citations
            citations = []
            citations_data = safe_get(data, "citations", default=[])

            for i, citation in enumerate(citations_data, 1):
                url = safe_get(citation, "url", default="")
                if url:
                    citations.append({"url": url, "n": i})

            if verbose:
                print(f"    🔗 Citations found: {len(citations)} sources")
                for citation in citations:
                    print(f"        [{citation['n']}] {citation['url']}")

            result = {"answer": answer, "citations": citations}
            return result

    except Exception as e:
        # Never raise - return empty results on any failure
        if verbose:
            print(f"    ❌ Sonar search failed for '{company}': {e}")
        return {"answer": "", "citations": []}
