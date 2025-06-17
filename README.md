# Deep Dive Sales Assistant

AI-powered sales intelligence tool that provides comprehensive company research and tailored insights for sales professionals. Given a company name, it automatically gathers information from multiple sources and generates actionable sales intelligence.

## Features

- 🔍 **Company Resolution**: Uses Google Knowledge Graph to find company domain, logo, and basic info
- 🛠️ **Tech Stack Analysis**: Identifies technologies used by the company (via BuiltWith)
- 📰 **Real-time Research**: Gets latest company news and insights (via Perplexity Sonar)
- 🤖 **AI Insights**: Generates tailored sales insights using OpenAI o3/o1
- ⚡ **Fast & Async**: Parallel API calls for optimal performance
- 💰 **Cost Efficient**: Typically costs less than $0.08 per company research

## Prerequisites

- Python 3.12+
- Poetry (for dependency management)
- API keys for:
  - OpenAI (required)
  - Google Knowledge Graph (required)
  - Perplexity Sonar (required)
  - BuiltWith (optional)

## Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd deep_dive_sales_assistant
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Configure API keys**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Test installation**:
   ```bash
   poetry run deepdive --help
   ```

## API Keys Setup

### OpenAI API Key
1. Visit [OpenAI API](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env`: `OPENAI_API_KEY=your_key_here`

### Google Knowledge Graph API Key
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Knowledge Graph Search API
3. Create credentials → API Key
4. Add to `.env`: `GOOGLE_KG_API_KEY=your_key_here`

### Perplexity API Key
1. Visit [Perplexity API](https://www.perplexity.ai/settings/api)
2. Generate API key
3. Add to `.env`: `SONAR_API_KEY=your_key_here`

### BuiltWith API Key (Optional)
1. Visit [BuiltWith API](https://api.builtwith.com/)
2. Sign up for API access
3. Add to `.env`: `BUILTWITH_API_KEY=your_key_here`

## Usage

### Basic Usage
```bash
poetry run deepdive "Company Name"
```

### With Verbose Output
```bash
poetry run deepdive "Company Name" --verbose
```

### Examples
```bash
# Research a well-known company
poetry run deepdive "Shopify"

# Research a local business
poetry run deepdive "Flagship Amsterdam"

# Get detailed process information
poetry run deepdive "HubSpot" -v
```

## Output Format

The tool generates a comprehensive sales intelligence report including:

1. **Company Overview** (50 words): Business model, channels, and tech stack
2. **Inferred Pain Points** (3 bullets): Likely challenges the company faces
3. **Discovery Questions** (3 questions): Strategic questions to ask prospects
4. **FareHarbor Pitch** (25 words): Tailored value proposition
5. **Source Citations**: Links to all information sources

## Performance & Costs

- **Typical Latency**: 10-30 seconds per company
- **API Costs**: ~$0.05-0.08 per research (varies by company complexity)
- **Rate Limits**: Built-in retry logic with exponential backoff

## Architecture

```
deep_dive_sales_assistant/
├── prospect.py                 # CLI entry point
├── pyproject.toml              # Dependencies
├── .env.example                # API key template
└── src/
    ├── llm.py                  # OpenAI integration
    └── services/
        ├── resolver.py         # Google Knowledge Graph
        ├── builtwith.py        # Technology detection
        ├── sonar.py            # Perplexity research
        └── utils.py            # Retry logic & helpers
```

## Troubleshooting

### Common Issues

**"No insights generated"**
- Check OpenAI API key is valid and has credits
- Verify internet connection

**"Google KG lookup failed"**
- Ensure Google Knowledge Graph API is enabled
- Check API key permissions
- Company might not be in Knowledge Graph

**"Sonar search failed"**
- Verify Perplexity API key
- Check if you have API credits remaining

**"BuiltWith lookup failed"**
- This is optional - tool continues without tech stack info
- Check BuiltWith API key if tech analysis is important

### Debug Mode
```bash
poetry run deepdive "Company Name" --verbose
```

### Test API Keys
```bash
# Test individual services (coming soon)
poetry run python -c "from src.services import resolver; print(asyncio.run(resolver.lookup('Google')))"
```

## Development

### Running Tests
```bash
poetry run pytest
```

### Code Quality
```bash
# Format code
poetry run black .

# Type checking
poetry run mypy src/
```

## Roadmap

Future enhancements (TODO - not implemented):

- [ ] Streamlit web UI
- [ ] Contact enrichment (Apollo/Hunter integration)
- [ ] Persistent caching layer
- [ ] Dockerfile and CI pipeline
- [ ] Slack/Teams integration
- [ ] Batch processing mode

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Copyright (c) 2024. All rights reserved.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review API documentation for external services
- Open an issue in the repository 