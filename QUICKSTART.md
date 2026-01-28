# Quick Start Guide

Get the Website Content Analyzer running locally in 5 minutes!

## Prerequisites

- Docker Desktop (recommended) OR Python 3.11+ and PostgreSQL
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Setup (Docker - Recommended)

1. **Navigate to project directory**
   ```bash
   cd website-analyzer
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Add your OpenAI API key**

   Edit `.env` file:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**

   Open in browser: http://localhost:8000

That's it! The application is now running.

## Using the Application

1. Enter any website URL in the input field
2. Click "Analyze" button
3. Wait 30-60 seconds for analysis
4. Review the credibility report

### Example URLs to Test

- News articles
- Blog posts
- Opinion pieces
- Educational content
- Marketing pages

## Viewing Logs

```bash
docker-compose logs -f backend
```

## Stopping the Application

```bash
docker-compose down
```

## Troubleshooting

### "Docker is not running"
- Start Docker Desktop

### "Analysis failed"
- Check if OPENAI_API_KEY is set correctly in `.env`
- Verify you have OpenAI API credits

### "Database connection error"
- Run: `docker-compose down -v && docker-compose up -d`

## API Access

- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000/api

### Example API Request

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Read [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) for production deployment
- Customize the analysis prompts in `backend/app/services/analyzer.py`
- Adjust chunking parameters in `backend/app/services/chunker.py`

## Common Configuration Changes

### Change AI Model

Edit `backend/app/services/analyzer.py`:
```python
self.model = "gpt-4-turbo-preview"  # or "gpt-3.5-turbo" for cost savings
```

### Adjust Chunk Size

Edit `backend/app/services/chunker.py`:
```python
ContentChunker(max_tokens=3000, overlap=200)
```

### Change Port

Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Access on port 8080 instead
```

## Support

Issues? Check the [README.md](README.md) troubleshooting section.
