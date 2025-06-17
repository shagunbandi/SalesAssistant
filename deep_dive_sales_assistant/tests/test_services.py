"""Tests for the services modules."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import respx
import httpx

from src.services import builtwith, resolver, sonar
from src.services.utils import async_retry, compact_json, normalize_domain


class TestResolver:
    """Tests for the Google Knowledge Graph resolver service."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_lookup_success(self):
        """Test successful company lookup."""
        # Mock the Google KG API response
        respx.get("https://kgsearch.googleapis.com/v1/entities:search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "itemListElement": [
                        {
                            "result": {
                                "url": "https://shopify.com",
                                "image": {"contentUrl": "https://example.com/logo.png"},
                                "description": "E-commerce platform",
                            }
                        }
                    ]
                },
            )
        )

        with patch.dict("os.environ", {"GOOGLE_KG_API_KEY": "test_key"}):
            result = await resolver.lookup("Shopify")

        assert result["domain"] == "shopify.com"
        assert result["logo"] == "https://example.com/logo.png"
        assert result["brief"] == "E-commerce platform"
        assert result["source"] == "googlekg"

    @pytest.mark.asyncio
    async def test_lookup_no_api_key(self):
        """Test lookup without API key."""
        with patch.dict("os.environ", {}, clear=True):
            result = await resolver.lookup("Test Company")

        assert result["domain"] == ""
        assert result["logo"] == ""
        assert result["brief"] == ""
        assert result["source"] == "googlekg"


class TestBuiltWith:
    """Tests for the BuiltWith API service."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_lookup_success(self):
        """Test successful tech stack lookup."""
        # Mock the BuiltWith API response
        respx.get("https://api.builtwith.com/v14/api.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "Results": [
                        {
                            "Result": {
                                "Paths": [
                                    {
                                        "Technologies": [
                                            {"Name": "React"},
                                            {"Name": "Shopify"},
                                            {"Name": "Google Analytics"},
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                },
            )
        )

        with patch.dict("os.environ", {"BUILTWITH_API_KEY": "test_key"}):
            result = await builtwith.lookup("shopify.com")

        assert "React" in result
        assert "Shopify" in result
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_lookup_empty_domain(self):
        """Test lookup with empty domain."""
        result = await builtwith.lookup("")
        assert result == []

    @pytest.mark.asyncio
    async def test_lookup_no_api_key(self):
        """Test lookup without API key."""
        with patch.dict("os.environ", {}, clear=True):
            result = await builtwith.lookup("example.com")
        assert result == []


class TestSonar:
    """Tests for the Perplexity Sonar service."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful company search."""
        # Mock the Perplexity API response
        respx.post("https://api.perplexity.ai/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [
                        {"message": {"content": "Shopify is an e-commerce platform..."}}
                    ],
                    "citations": [
                        {"url": "https://shopify.com/about"},
                        {"url": "https://news.example.com/shopify"},
                    ],
                },
            )
        )

        with patch.dict("os.environ", {"SONAR_API_KEY": "test_key"}):
            result = await sonar.search("Shopify", "shopify.com")

        assert "Shopify is an e-commerce platform" in result["answer"]
        assert len(result["citations"]) == 2
        assert result["citations"][0]["url"] == "https://shopify.com/about"
        assert result["citations"][0]["n"] == 1

    @pytest.mark.asyncio
    async def test_search_no_api_key(self):
        """Test search without API key."""
        with patch.dict("os.environ", {}, clear=True):
            result = await sonar.search("Test Company")

        assert result["answer"] == ""
        assert result["citations"] == []


class TestUtils:
    """Tests for utility functions."""

    @pytest.mark.asyncio
    async def test_async_retry_success(self):
        """Test async retry decorator with successful call."""

        @async_retry(max_attempts=3)
        async def mock_function():
            return "success"

        result = await mock_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_retry_with_retries(self):
        """Test async retry decorator with eventual success."""
        call_count = 0

        @async_retry(max_attempts=3, base_delay=0.01)  # Fast retry for testing
        async def mock_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.RequestError("Network error")
            return "success"

        result = await mock_function()
        assert result == "success"
        assert call_count == 3

    def test_compact_json(self):
        """Test JSON compaction."""
        data = {"key": "value", "list": [1, 2, 3]}
        result = compact_json(data)
        assert result == '{"key":"value","list":[1,2,3]}'

    def test_normalize_domain(self):
        """Test domain normalization."""
        assert normalize_domain("https://example.com/path") == "example.com"
        assert normalize_domain("http://subdomain.example.co.uk") == "example.co.uk"
        assert normalize_domain("") == ""
        assert normalize_domain("invalid") == ""
