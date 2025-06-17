"""Deep Dive Sales Assistant - Main CLI entry point."""

import asyncio
import sys
from typing import Optional

import typer
from dotenv import load_dotenv

from src import llm
from src.services import builtwith, resolver, sonar

# Load environment variables
load_dotenv()

app = typer.Typer(
    name="deepdive",
    help="AI-powered sales intelligence tool for company research and prospect analysis",
    no_args_is_help=True,
)


async def research_company(company_name: str) -> dict:
    """
    Research a company using all available data sources.

    Args:
        company_name: Name of the company to research

    Returns:
        Combined research data
    """
    print(f"🔍 Researching {company_name}...")
    print(f"🚀 Starting comprehensive company analysis...")

    # Step 1: Resolve company using Google Knowledge Graph
    print("  → Resolving company info...")
    company_info = await resolver.lookup(company_name)

    print(f"  ✅ Company resolution complete")
    domain = company_info.get("domain", "")
    if domain:
        print(f"  🌐 Found company domain: {domain}")
    else:
        print(f"  ⚠️  No domain found for company")

    # Step 2: Gather additional data in parallel (skip BuiltWith if no domain)
    async def empty_tech_stack():
        return []

    tasks = []

    if domain:
        print(f"  → Analyzing tech stack for {domain}...")
        tasks.append(builtwith.lookup(domain))
    else:
        print(f"  → Skipping tech stack analysis (no domain available)...")
        tasks.append(empty_tech_stack())

    print("  → Searching for company insights...")
    tasks.append(sonar.search(company_name, domain))

    # Execute tasks in parallel
    print("  🔄 Running parallel API calls...")
    tech_stack, sonar_results = await asyncio.gather(*tasks)

    print(f"  ✅ All API calls completed")
    print(
        f"  📊 Tech stack found: {len(tech_stack) if isinstance(tech_stack, list) else 0} technologies"
    )
    print(
        f"  📊 Sonar insights: {'✅ Found' if sonar_results.get('answer') else '❌ None'}"
    )

    # Step 3: Merge all data
    print("  → Merging research data...")
    raw_data = {
        "company": company_name,
        "resolver": company_info,
        "tech_stack": tech_stack,
        "sonar": sonar_results,
        "citations": sonar_results.get("citations", []),
    }

    print(f"  ✅ Data merge complete - ready for AI analysis")
    return raw_data


@app.command()
def main(
    company: str = typer.Argument(..., help="Company name to research"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """
    Research a company and generate sales insights.

    Example:
        poetry run deepdive "Flagship Amsterdam"
    """
    if verbose:
        print(f"🎯 Starting deep dive research for: {company}")
        print(f"📋 Verbose mode enabled - showing detailed process information")

    try:
        print(f"⏰ Beginning company research process...")

        # Run the async research
        raw_data = asyncio.run(research_company(company))

        print(f"🤖 Proceeding to AI-powered insight generation...")

        # Step 4: Generate insights using LLM
        insights = asyncio.run(llm.generate(raw_data))

        print(f"✅ AI analysis complete - preparing final report...")

        # Step 5: Print results
        print("\n" + "=" * 60)
        print(f"SALES INTELLIGENCE: {company.upper()}")
        print("=" * 60)
        print(insights.get("pretty", "No insights generated"))

        # Print citations if available
        citations = insights.get("citations", [])
        if citations:
            print("\n" + "-" * 40)
            print("SOURCES:")
            for citation in citations:
                n = citation.get("n", "?")
                url = citation.get("url", "")
                print(f"[{n}] {url}")

        print("\n" + "=" * 60)
        print(f"🎉 Deep dive research complete for {company}!")

        # Exit successfully
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n❌ Research interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during research: {e}")
        if verbose:
            import traceback

            print("\n📋 Detailed error traceback:")
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    app()
