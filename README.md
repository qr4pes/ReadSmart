# Website Content Analyzer

A user-facing web application that analyzes website content for credibility, propaganda detection, and context understanding using AI.

## Features

- **Credibility Scoring**: Rates website content credibility from 0-100
- **Propaganda Detection**: Identifies propaganda techniques and manipulation
- **Context Analysis**: Determines if content is out of context or misleading
- **Content Overview**: Provides general description and categorization
- **Detailed Reports**: Lists key concerns and positive indicators
- **Request Tracking**: PostgreSQL database logs all analysis requests

## Architecture

### Backend
- **Framework**: FastAPI (Python)
- **AI Service**: OpenAI GPT-4
- **Database**: PostgreSQL
- **Content Processing**:
  - Web scraping with BeautifulSoup
  - Content chunking for large pages
  - Async analysis with result aggregation

### Frontend
- **Technology**: HTML, CSS, JavaScript
- **Design**: Clean, responsive UI with gradient backgrounds
- **UX**: Simple workflow with loading states and detailed results

### Infrastructure
- **Local Development**: Docker Compose or native Python
- **Production**: AWS ECS/Fargate with RDS PostgreSQL
- **Containerization**: Docker for consistent environments

## Prerequisites

### For Docker Setup (Recommended)
- Docker Desktop installed
- Docker Compose installed
- OpenAI API key

### For Local Development
- Python 3.11+
- PostgreSQL 15+ installed and running
- OpenAI API key

## Local Setup

### Option 1: Docker Compose (Recommended)

1. **Clone or navigate to the project directory**
   ```bash
   cd website-analyzer
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Add your OpenAI API key to `.env`**
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   - Frontend: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - API: http://localhost:8000/api

6. **View logs**
   ```bash
   docker-compose logs -f backend
   ```

7. **Stop the application**
   ```bash
   docker-compose down
   ```

### Option 2: Local Python Development

1. **Set up PostgreSQL database**
   ```bash
   # Install PostgreSQL (macOS with Homebrew)
   brew install postgresql@15
   brew services start postgresql@15

   # Create database and user
   psql postgres
   ```
   ```sql
   CREATE USER analyzer_user WITH PASSWORD 'analyzer_pass';
   CREATE DATABASE website_analyzer OWNER analyzer_user;
   \q
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   # Create .env file in backend directory
   echo "OPENAI_API_KEY=sk-your-actual-key-here" > .env
   echo "DATABASE_URL=postgresql://analyzer_user:analyzer_pass@localhost:5432/website_analyzer" >> .env
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the application**
   - Frontend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Usage

1. **Open the web interface** at http://localhost:8000

2. **Enter a website URL** (e.g., https://example.com/article)

3. **Click "Analyze"** and wait for the analysis (30-60 seconds)

4. **Review the results**:
   - Credibility score (0-100)
   - Out-of-context assessment
   - Propaganda detection
   - Content overview
   - Key concerns and positive indicators

5. **Analyze another URL** or review previous analyses

## API Endpoints

### POST /api/analyze
Analyze a website URL

**Request:**
```json
{
  "url": "https://example.com/article"
}
```

**Response:**
```json
{
  "request_id": 1,
  "url": "https://example.com/article",
  "status": "completed",
  "is_out_of_context": "No",
  "is_propaganda": "Uncertain",
  "credibility_score": 75.5,
  "content_context": "Educational article about technology...",
  "detailed_results": { ... },
  "analysis_duration": 45.2
}
```

### GET /api/analysis/{request_id}
Retrieve a previous analysis

### GET /api/health
Health check endpoint

## Database Schema

### analysis_requests table
- `id`: Primary key
- `url`: Website URL analyzed
- `user_ip`: Client IP address
- `requested_at`: Timestamp
- `is_out_of_context`: Yes/No/Uncertain
- `is_propaganda`: Yes/No/Uncertain
- `credibility_score`: Float (0-100)
- `content_context`: Text description
- `analysis_duration`: Processing time in seconds
- `status`: pending/completed/failed
- `error_message`: Error details if failed
- `detailed_results`: JSON with full analysis

## How It Works

1. **Content Extraction**: Scrapes the target URL and extracts text content
2. **Chunking**: Splits large content into manageable chunks (≤3000 tokens each)
3. **AI Analysis**: Each chunk is analyzed by GPT-4 for:
   - Out-of-context information
   - Propaganda techniques
   - Credibility indicators
   - Content categorization
4. **Aggregation**: Results from all chunks are synthesized into final analysis
5. **Storage**: Analysis is saved to PostgreSQL for tracking
6. **Display**: Results are presented in user-friendly format

## AWS Deployment

### Architecture Overview
- **Frontend & API**: ECS Fargate containers
- **Database**: RDS PostgreSQL
- **Load Balancer**: Application Load Balancer (ALB)
- **Container Registry**: ECR for Docker images
- **Networking**: VPC with public/private subnets

### Deployment Steps

1. **Build and push Docker image to ECR**
   ```bash
   aws ecr create-repository --repository-name website-analyzer
   docker build -t website-analyzer ./backend
   docker tag website-analyzer:latest <account-id>.dkr.ecr.<region>.amazonaws.com/website-analyzer:latest
   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/website-analyzer:latest
   ```

2. **Create RDS PostgreSQL instance**
   - Engine: PostgreSQL 15
   - Instance class: db.t3.micro (or larger for production)
   - Storage: 20 GB SSD
   - Multi-AZ: Enabled for production

3. **Create ECS Cluster and Task Definition**
   - Task CPU: 512 (.5 vCPU)
   - Task Memory: 1024 MB
   - Environment variables: DATABASE_URL, OPENAI_API_KEY

4. **Configure Application Load Balancer**
   - Target group for ECS service
   - Health check: /api/health
   - SSL certificate for HTTPS

5. **Create ECS Service**
   - Desired count: 2+ for high availability
   - Auto-scaling based on CPU/memory

### Environment Variables for Production
```
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/dbname
OPENAI_API_KEY=sk-your-production-key
APP_ENV=production
```

## Configuration

### Adjusting Content Chunking
Edit `backend/app/services/chunker.py`:
```python
# Change max tokens per chunk
ContentChunker(max_tokens=3000, overlap=200)
```

### Changing AI Model
Edit `backend/app/services/analyzer.py`:
```python
# Use different OpenAI model
self.model = "gpt-4-turbo-preview"  # or "gpt-3.5-turbo"
```

### Database Connection
Set `DATABASE_URL` environment variable:
```
postgresql://user:password@host:port/database
```

## Troubleshooting

### Docker Issues
```bash
# Reset containers and volumes
docker-compose down -v
docker-compose up --build

# Check logs
docker-compose logs backend
docker-compose logs postgres
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U analyzer_user -d website_analyzer

# Reset database
docker-compose down -v
docker-compose up postgres -d
```

### OpenAI API Issues
- Verify API key is correct in `.env`
- Check API quota and billing
- Review error logs for specific API errors

## Development

### Running Tests (TODO)
```bash
cd backend
pytest tests/
```

### Code Structure
```
backend/
├── app/
│   ├── main.py           # FastAPI application
│   ├── models.py         # Database models
│   ├── database.py       # Database connection
│   ├── api/
│   │   └── routes.py     # API endpoints
│   └── services/
│       ├── scraper.py    # Web scraping
│       ├── chunker.py    # Content chunking
│       └── analyzer.py   # AI analysis
frontend/
├── index.html            # Main HTML
├── styles.css            # Styling
└── app.js                # Frontend logic
```

## Security Considerations

- API keys stored in environment variables, not in code
- Database credentials not committed to version control
- Input validation on URLs
- Rate limiting recommended for production
- CORS configured for security
- SQL injection protected by SQLAlchemy ORM

## Performance

- Analysis time: 30-60 seconds per URL
- Depends on content length and OpenAI API response time
- Chunking optimizes large pages
- Async processing for better throughput

## Limitations

- Requires valid OpenAI API key and quota
- Analysis quality depends on AI model performance
- Large websites may take longer to process
- Rate limited by OpenAI API constraints
- Some websites may block scraping

## Future Enhancements

- Add user authentication
- Implement analysis history per user
- Add comparison between multiple URLs
- Include source citation verification
- Batch analysis support
- Export results to PDF
- Real-time analysis status updates via WebSockets
- Cache repeated URL analyses

## License

This project is for educational purposes.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at http://localhost:8000/docs
3. Check application logs
# ReadSmart
