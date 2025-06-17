````
#  ─────────────────────────────────────────────────────────────
#  Project: deep-dive-sales-assistant  (v0.1 – CLI, NO caching)
#  Goal   : Given a company name, use Google Knowledge Graph to
#           resolve domain & logo, enrich with BuiltWith + 
#           Perplexity Sonar, run one OpenAI o3 prompt, then
#           print a rep-ready summary in the terminal.
#  Stack  : Python 3.12, Typer CLI, asyncio + httpx.
#  ─────────────────────────────────────────────────────────────

## 0. Repo layout to generate
deep_dive_sales_assistant/
├ prospect.py                 # Typer entry-point
├ pyproject.toml              # Poetry deps + scripts
├ .env.example                # API-key placeholders
├ README.md                   # setup & usage
└ src/
    ├ __init__.py
    ├ llm.py                  # OpenAI wrapper + prompt
    └ services/
        ├ resolver.py         # Google KG only
        ├ builtwith.py
        ├ sonar.py
        └ utils.py            # retry, JSON helpers

## 1. Dependencies (pyproject.toml)
typer[all]           |  httpx[http2]
python-dotenv        |  openai>=1.14
tldextract           |  asyncio-retry
rapidfuzz            |  toolz
# (test) pytest  |  pytest-asyncio  |  respx

## 2. Environment variables (.env.example)
OPENAI_API_KEY=
GOOGLE_KG_API_KEY=      # https://developers.google.com/knowledge-graph
SONAR_API_KEY=

## 3. Behaviour specification

### prospect.py  – CLI
Usage:
$ poetry run deepdive "Flagship Amsterdam"

Flow:
1. `resolver.lookup(company)` →  
   { domain:str, logo:str, brief:str, source:"googlekg" }
2. Async-gather (_skip BuiltWith if domain == ""_):
      builtwith.lookup(domain)
      sonar.search(company, domain)
3. Merge into `raw` dict.
4. `llm.generate(raw)` → {"pretty": str, "citations": [...]}
5. Print `pretty` verbatim; exit 0.
6. Exit non-zero on unhandled exceptions.

_No persistent storage — every run hits live APIs._

### services/resolver.py  (Google KG only)

```python
async def lookup(company: str) -> dict:
    """
    Query Google Knowledge Graph Search API:
      GET https://kgsearch.googleapis.com/v1/entities:search
          params={query: company,
                  key: GOOGLE_KG_API_KEY,
                  limit: 1,
                  types: "Organization"}
    Extract:
      domain = registered_domain(item['url']) if 'url' in item
      logo   = item.get('image', {}).get('contentUrl', '')
      brief  = (item.get('description', '')
                or item.get('detailedDescription', {}).get('articleBody', ''))
    Return {"domain": domain, "logo": logo, "brief": brief,
            "source": "googlekg"}.
    On failure return empty strings; never raise.
    """
````

Wrap the HTTP call with `utils.async_retry(max_attempts=3)`.

### services/builtwith.py

• Call BuiltWith Mini REST (`/v14/api.json?KEY=…&LOOKUP={domain}`)
• Return list of major tech categories.
• If `domain` is empty, return empty list.

### services/sonar.py

POST to Perplexity Sonar “answer” endpoint with prompt

```text
What does {company} ({domain or 'unknown'}) do, which sales channels,
and any recent news? Provide citations.
```

Return `{answer:str, citations:list}`.

### llm.generate(raw: dict)  – OpenAI o3

Temperature 0.2, max\_tokens 800.
Prompt:

```
SYSTEM
You are a senior FareHarbor AE. Summarise and tailor insights.

USER
RAW:
{{raw_json}}

TASKS
1. 50-word company gist (include channel mix & tech if present).
2. 3 inferred pains (bullets).
3. 3 discovery questions addressing those pains.
4. 25-word FareHarbor pitch line.
5. Cite sources numerically [1]..[n] using raw.citations.

Return strict JSON:
{
  "pretty": "<terminal block>",
  "citations": [ {"url": "...", "n": 1}, … ]
}
```

### utils.py

• `async_retry` decorator: exponential back-off (0.4 → 1.2 → 3.6 s, jitter).
• `compact_json` helper.

## 4. Developer-experience helpers

\[tool.poetry.scripts] deepdive = "prospect\:app"
`make test` runs pytest (include one mocked test per service).

## 5. README.md  (generate)

* Prereqs: Python 3.12, Poetry.
* `cp .env.example .env` and add keys.
* `poetry install` then `poetry run deepdive "<Company>"`.
* Typical latency / cost (< \$0.08 per run).
* Troubleshooting FAQ.

## 6. TODO comments only  (do NOT implement now)

– Streamlit UI
– Contact enrichment (Apollo / Hunter)
– Dockerfile + CI pipeline

# ─────────────────────────────────────────────────────────────

# End of specification – generate all code & docs accordingly.

# ─────────────────────────────────────────────────────────────

```
```
