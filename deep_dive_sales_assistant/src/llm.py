"""OpenAI LLM integration for generating sales insights."""

import json
import os
from typing import Dict

from openai import AsyncOpenAI

from .services.utils import compact_json


async def generate(raw_data: Dict, verbose: bool = False) -> Dict[str, any]:
    """
    Generate sales insights using OpenAI o3 model.

    Args:
        raw_data: Raw data collected from various APIs
        verbose: Whether to show detailed logging

    Returns:
        Dictionary with formatted insights and citations
    """
    if verbose:
        print("  → Generating AI insights...")

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        if verbose:
            print("    ❌ Error: OpenAI API key not configured")
        return {"pretty": "Error: OpenAI API key not configured", "citations": []}

    client = AsyncOpenAI(api_key=api_key)

    # Prepare the raw data JSON
    raw_json = compact_json(raw_data)

    if verbose:
        print(
            f"    📊 Raw data being sent to AI: {raw_json[:500]}{'...' if len(raw_json) > 500 else ''}"
        )

    # Construct the prompt
    system_prompt = "You are a senior FareHarbor AE. Summarise and tailor insights."

    user_prompt = f"""RAW:
{raw_json}

TASKS
1. 50-word company gist (include channel mix & tech if present).
2. 3 inferred pains (bullets).
3. 3 discovery questions addressing those pains.
4. 25-word FareHarbor pitch line.
5. Cite sources numerically [1]..[n] using raw.citations.

Return strict JSON:
{{
  "pretty": "<terminal block>",
  "citations": [ {{"url": "...", "n": 1}}, … ]
}}"""

    if verbose:
        print(f"    💬 System prompt: {system_prompt}")
        print(
            f"    💬 User prompt: {user_prompt[:300]}{'...' if len(user_prompt) > 300 else ''}"
        )

    try:
        # First try with O3 model
        try:
            if verbose:
                print("    📞 Calling OpenAI API with o3-mini model...")

            response = await client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "user",
                        "content": f"System: {system_prompt}\n\nUser: {user_prompt}",
                    }
                ],
                max_completion_tokens=800,
                # Note: o3-mini doesn't support temperature parameter
            )

            if verbose:
                print(f"    ✅ OpenAI o3-mini API response received")

        except Exception as o3_error:
            # Fallback to gpt-4-turbo (more reliable than o1-preview)
            if verbose:
                print(
                    f"    ⚠️  O3 model not available, falling back to gpt-4-turbo: {o3_error}"
                )
                print("    📞 Calling OpenAI API with gpt-4-turbo model...")

            response = await client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=800,
                temperature=0.7,
            )

            if verbose:
                print(f"    ✅ OpenAI gpt-4-turbo API response received")

        # Extract the response content
        content = response.choices[0].message.content

        # Check for empty response
        if not content or content.strip() == "":
            if verbose:
                print(f"    ⚠️  Empty response received from OpenAI")
                print("    📞 Retrying with gpt-4o model...")

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=800,
                temperature=0.7,
            )

            content = response.choices[0].message.content
            if verbose:
                print(f"    ✅ OpenAI gpt-4o API response received")

        if verbose:
            print(f"    🤖 Raw AI response: {content}")

        # Check again for empty content after retries
        if not content or content.strip() == "":
            if verbose:
                print(f"    ❌ Still received empty response after retries")
            return {
                "pretty": "Error: OpenAI returned empty response after multiple attempts",
                "citations": [],
            }

        # Clean up the content - remove markdown code blocks if present
        cleaned_content = content.strip()
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[7:]  # Remove ```json
        if cleaned_content.startswith("```"):
            cleaned_content = cleaned_content[3:]  # Remove ```
        if cleaned_content.endswith("```"):
            cleaned_content = cleaned_content[:-3]  # Remove closing ```

        cleaned_content = cleaned_content.strip()

        if cleaned_content != content and verbose:
            print(f"    🧹 Cleaned markdown from response")
            print(f"    🤖 Cleaned AI response: {cleaned_content}")

        # Try to parse as JSON
        try:
            result = json.loads(cleaned_content)

            if verbose:
                print(f"    ✅ Successfully parsed AI response as JSON")
                print(f"    📝 Parsed result: {json.dumps(result, indent=2)}")

            # Validate the structure
            if not isinstance(result, dict) or "pretty" not in result:
                raise ValueError("Invalid response structure")

            # Ensure citations is a list
            if "citations" not in result:
                result["citations"] = []
            elif not isinstance(result["citations"], list):
                result["citations"] = []

            return result

        except (json.JSONDecodeError, ValueError) as e:
            # If JSON parsing fails, wrap the content as plain text
            if verbose:
                print(f"    ⚠️  Failed to parse AI response as JSON: {e}")
                print(f"    📝 Returning content as plain text wrapper")
            return {"pretty": cleaned_content, "citations": []}

    except Exception as e:
        if verbose:
            print(f"    ❌ OpenAI generation failed: {e}")
        return {"pretty": f"Error generating insights: {str(e)}", "citations": []}
