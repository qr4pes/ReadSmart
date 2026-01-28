# System Architecture

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Frontend (HTML/CSS/JS)                       │  │
│  │  • URL Input Form                                         │  │
│  │  • Loading States                                         │  │
│  │  • Results Display                                        │  │
│  │  • Error Handling                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API (FastAPI)                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   API Layer (routes.py)                   │  │
│  │  • POST /api/analyze                                      │  │
│  │  • GET /api/analysis/{id}                                 │  │
│  │  • GET /api/health                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Service Layer (services/)                    │  │
│  │                                                            │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐ │  │
│  │  │   Scraper   │→ │   Chunker    │→ │    Analyzer     │ │  │
│  │  │             │  │              │  │                 │ │  │
│  │  │ • Fetch URL │  │ • Split text │  │ • Analyze chunks│ │  │
│  │  │ • Clean HTML│  │ • Tokenize   │  │ • Aggregate     │ │  │
│  │  │ • Extract   │  │ • Overlap    │  │ • Score         │ │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘ │  │
│  │                                              │             │  │
│  └──────────────────────────────────────────────┼────────────┘  │
│                                                  │                │
│  ┌──────────────────────────────────────────────┼────────────┐  │
│  │              Data Layer (models.py)          │            │  │
│  │  • SQLAlchemy ORM                            │            │  │
│  │  • Database Sessions                         │            │  │
│  │  • Request Tracking                          │            │  │
│  └──────────────────────────────────────────────┼────────────┘  │
└───────────────────────────────────────────────┬─┼──────────────┘
                                                │ │
                  ┌─────────────────────────────┘ │
                  │                                │
                  ▼                                ▼
┌───────────────────────────────┐  ┌──────────────────────────────┐
│   PostgreSQL Database         │  │    OpenAI API (GPT-4)        │
│                               │  │                              │
│  • analysis_requests table    │  │  • Content analysis          │
│  • URL tracking               │  │  • JSON responses            │
│  • Results storage            │  │  • Credibility scoring       │
│  • User IP logging            │  │  • Propaganda detection      │
└───────────────────────────────┘  └──────────────────────────────┘
```

## Data Flow Diagram

```
┌──────┐       ┌─────────┐       ┌─────────┐       ┌─────────┐
│ User │──1──→ │ FastAPI │──2──→ │ Scraper │──3──→ │ Website │
└──────┘       └─────────┘       └─────────┘       └─────────┘
    ▲              │                   │
    │              │                   ▼
    │              │              ┌─────────┐
    │              │              │  HTML   │
    │              │              │ Content │
    │              │              └─────────┘
    │              │                   │
    │              │              4. Clean text
    │              │                   │
    │              │                   ▼
    │              │              ┌─────────┐       ┌──────────┐
    │              │              │ Chunker │──5──→ │  Chunks  │
    │              │              └─────────┘       │  [1,2,3] │
    │              │                                └──────────┘
    │              │                                     │
    │              │              6. Analyze each chunk │
    │              │                                     │
    │              │                   ┌─────────────────┘
    │              │                   ▼
    │              │              ┌──────────┐      ┌──────────┐
    │              │              │ Analyzer │─7──→ │  OpenAI  │
    │              │              │          │←─8─  │   API    │
    │              │              └──────────┘      └──────────┘
    │              │                   │
    │              │              9. Aggregate results
    │              │                   │
    │              │                   ▼
    │              │              ┌──────────┐
    │              │          ┌──→│PostgreSQL│
    │              │          │   │ Database │
    │              │          │   └──────────┘
    │              │      10. Store
    │              │          │
    │              ▼          │
    │         ┌────────────────┘
    │         │ 11. Return results
    │         │
    └────12───┘ Display
```

### Flow Steps:
1. User submits URL via web interface
2. API receives request, creates DB record
3. Scraper fetches website content
4. Content is cleaned and converted to text
5. Chunker splits large content into pieces
6. Each chunk is sent for analysis
7. Analyzer sends chunk to OpenAI API
8. OpenAI returns structured analysis
9. Multiple chunk results are aggregated
10. Complete analysis stored in database
11. Results returned to API
12. Frontend displays formatted results

## Component Architecture

### Frontend Components

```
frontend/
│
├── HTML Structure (index.html)
│   ├── Header Section
│   │   └── Title and description
│   ├── Input Section
│   │   ├── URL input field
│   │   └── Analyze button
│   ├── Loading Section
│   │   ├── Spinner
│   │   └── Progress message
│   ├── Error Section
│   │   ├── Error message
│   │   └── Retry button
│   └── Results Section
│       ├── Credibility Score Card
│       ├── Assessment Grid
│       │   ├── Context Status
│       │   └── Propaganda Status
│       ├── Content Overview
│       ├── Detailed Analysis
│       │   ├── Key Concerns
│       │   ├── Positive Indicators
│       │   └── Summary
│       └── Metadata
│
├── Styling (styles.css)
│   ├── Global styles
│   ├── Layout (Grid/Flexbox)
│   ├── Components
│   │   ├── Cards
│   │   ├── Buttons
│   │   ├── Badges
│   │   └── Forms
│   ├── Animations
│   └── Responsive breakpoints
│
└── Logic (app.js)
    ├── API integration
    ├── State management
    ├── Event handlers
    ├── DOM manipulation
    └── Error handling
```

### Backend Components

```
backend/app/
│
├── main.py (Application Entry)
│   ├── FastAPI app initialization
│   ├── CORS middleware
│   ├── Router inclusion
│   ├── Static file serving
│   └── Startup events
│
├── api/routes.py (API Endpoints)
│   ├── POST /api/analyze
│   │   ├── Validate input
│   │   ├── Create DB record
│   │   ├── Orchestrate services
│   │   └── Return results
│   ├── GET /api/analysis/{id}
│   │   ├── Query database
│   │   └── Return stored results
│   └── GET /api/health
│       └── Health check
│
├── services/
│   │
│   ├── scraper.py (Web Scraping)
│   │   ├── WebScraper class
│   │   │   ├── fetch_content()
│   │   │   │   ├── HTTP request
│   │   │   │   ├── HTML parsing
│   │   │   │   ├── Clean unwanted elements
│   │   │   │   └── Extract text
│   │   │   └── get_page_metadata()
│   │   │       └── Extract title/description
│   │   └── Error handling
│   │
│   ├── chunker.py (Content Processing)
│   │   ├── ContentChunker class
│   │   │   ├── count_tokens()
│   │   │   │   └── Tiktoken encoding
│   │   │   ├── chunk_content()
│   │   │   │   ├── Check if chunking needed
│   │   │   │   ├── Split by paragraphs
│   │   │   │   ├── Handle long paragraphs
│   │   │   │   └── Add overlap
│   │   │   └── _get_overlap_text()
│   │   │       └── Extract overlap portion
│   │   └── Token management
│   │
│   └── analyzer.py (AI Analysis)
│       ├── ContentAnalyzer class
│       │   ├── analyze_chunk()
│       │   │   ├── Build prompt
│       │   │   ├── Call OpenAI API
│       │   │   └── Parse JSON response
│       │   ├── aggregate_results()
│       │   │   ├── Collect chunk results
│       │   │   ├── Build aggregation prompt
│       │   │   └── Synthesize final result
│       │   ├── _build_analysis_prompt()
│       │   │   └── Structured analysis request
│       │   └── _build_aggregation_prompt()
│       │       └── Multi-chunk synthesis
│       └── OpenAI client management
│
├── models.py (Database Schema)
│   └── AnalysisRequest model
│       ├── id (PK)
│       ├── url
│       ├── user_ip
│       ├── requested_at
│       ├── is_out_of_context
│       ├── is_propaganda
│       ├── credibility_score
│       ├── content_context
│       ├── analysis_duration
│       ├── status
│       ├── error_message
│       └── detailed_results (JSON)
│
└── database.py (Database Management)
    ├── Database URL configuration
    ├── SQLAlchemy engine
    ├── Session management
    ├── get_db() dependency
    └── init_db() initialization
```

## Deployment Architecture (AWS)

```
                    ┌──────────────────┐
                    │   Route 53 DNS   │
                    │  analyzer.com    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Certificate     │
                    │  Manager (ACM)   │
                    │  HTTPS/TLS       │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │  Application Load Balancer   │
              │  • Health checks             │
              │  • SSL termination           │
              │  • Path routing              │
              └──────────────┬───────────────┘
                             │
          ┌──────────────────┴────────────────────┐
          │                                       │
          ▼                                       ▼
┌─────────────────────┐              ┌─────────────────────┐
│   ECS Service       │              │   ECS Service       │
│   (AZ-1)            │              │   (AZ-2)            │
│                     │              │                     │
│  ┌──────────────┐   │              │  ┌──────────────┐   │
│  │ Fargate Task │   │              │  │ Fargate Task │   │
│  │ (Container)  │   │              │  │ (Container)  │   │
│  │              │   │              │  │              │   │
│  │ • Backend    │   │              │  │ • Backend    │   │
│  │ • Frontend   │   │              │  │ • Frontend   │   │
│  └──────┬───────┘   │              │  └──────┬───────┘   │
└─────────┼───────────┘              └─────────┼───────────┘
          │                                    │
          └──────────────┬─────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  RDS PostgreSQL  │
              │  • Multi-AZ      │
              │  • Automated     │
              │    backups       │
              │  • Read replicas │
              └──────────────────┘

External Services:
    ┌──────────────────┐       ┌──────────────────┐
    │  OpenAI API      │       │  CloudWatch      │
    │  (GPT-4)         │       │  • Logs          │
    │                  │       │  • Metrics       │
    └──────────────────┘       │  • Alarms        │
                               └──────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Security Layers                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Layer 1: Network Security                              │
│  ├── VPC with public/private subnets                    │
│  ├── Security Groups (least privilege)                  │
│  ├── NACLs                                               │
│  └── NAT Gateway for outbound traffic                   │
│                                                          │
│  Layer 2: Application Security                          │
│  ├── CORS configuration                                 │
│  ├── Input validation                                   │
│  ├── SQL injection protection (ORM)                     │
│  └── Error message sanitization                         │
│                                                          │
│  Layer 3: Data Security                                 │
│  ├── Environment variables for secrets                  │
│  ├── AWS Secrets Manager                                │
│  ├── RDS encryption at rest                             │
│  └── TLS/SSL in transit                                 │
│                                                          │
│  Layer 4: Access Control                                │
│  ├── IAM roles (least privilege)                        │
│  ├── Private subnets for backend                        │
│  ├── Security group restrictions                        │
│  └── No hardcoded credentials                           │
│                                                          │
│  Layer 5: Monitoring & Logging                          │
│  ├── CloudWatch Logs                                    │
│  ├── Access logs on ALB                                 │
│  ├── Database audit logs                                │
│  └── Alert on suspicious activity                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Database Schema

```
┌────────────────────────────────────────────────────────────┐
│                    analysis_requests                        │
├────────────────────────────────────────────────────────────┤
│ id                  SERIAL PRIMARY KEY                      │
│ url                 VARCHAR(2048) NOT NULL                  │
│ user_ip             VARCHAR(45) NULL                        │
│ requested_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()  │
│ is_out_of_context   VARCHAR(50) NULL                        │
│ is_propaganda       VARCHAR(50) NULL                        │
│ credibility_score   FLOAT NULL                              │
│ content_context     TEXT NULL                               │
│ analysis_duration   FLOAT NULL                              │
│ status              VARCHAR(20) DEFAULT 'pending'           │
│ error_message       TEXT NULL                               │
│ detailed_results    JSONB NULL                              │
├────────────────────────────────────────────────────────────┤
│ Indexes:                                                    │
│ • id (PRIMARY KEY)                                          │
│ • created_at (for time-based queries)                       │
│                                                             │
│ Sample Query Patterns:                                      │
│ • Find all analyses for a URL                               │
│ • Get analyses by date range                                │
│ • Aggregate statistics (avg credibility score)              │
│ • Track user IP patterns                                    │
└────────────────────────────────────────────────────────────┘
```

## API Request/Response Flow

```
┌─────────────────────────────────────────────────────────┐
│  Request: POST /api/analyze                              │
├─────────────────────────────────────────────────────────┤
│  Headers:                                                │
│    Content-Type: application/json                        │
│  Body:                                                   │
│    {                                                     │
│      "url": "https://example.com/article"                │
│    }                                                     │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────┐
          │  1. Validate Request     │
          │  2. Create DB Record     │
          │  3. Scrape Content       │
          │  4. Chunk Content        │
          │  5. Analyze Chunks       │
          │  6. Aggregate Results    │
          │  7. Update DB            │
          └──────────────┬───────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Response: 200 OK                                        │
├─────────────────────────────────────────────────────────┤
│  Headers:                                                │
│    Content-Type: application/json                        │
│  Body:                                                   │
│    {                                                     │
│      "request_id": 123,                                  │
│      "url": "https://example.com/article",               │
│      "status": "completed",                              │
│      "is_out_of_context": "No",                          │
│      "is_propaganda": "Uncertain",                       │
│      "credibility_score": 75.5,                          │
│      "content_context": "Educational article...",        │
│      "detailed_results": {                               │
│        "out_of_context": {...},                          │
│        "propaganda": {...},                              │
│        "key_concerns": [...],                            │
│        "positive_indicators": [...]                      │
│      },                                                  │
│      "analysis_duration": 45.2                           │
│    }                                                     │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack Layers

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  HTML5 • CSS3 • Vanilla JavaScript • Fetch API          │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────┐
│                    Application Layer                     │
│  FastAPI • Pydantic • Uvicorn • Python 3.11             │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                     Service Layer                        │
│  BeautifulSoup • Requests • Tiktoken • OpenAI SDK       │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                      Data Layer                          │
│  SQLAlchemy • Psycopg2 • PostgreSQL 15                  │
└─────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                  Infrastructure Layer                    │
│  Docker • Docker Compose • AWS ECS • RDS                │
└─────────────────────────────────────────────────────────┘
```

## Scalability Considerations

```
Current Architecture:
  • Handles ~100 requests/day comfortably
  • Single region deployment
  • Vertical scaling (larger instances)

Improvements for Scale:
  ┌──────────────────────────────────────┐
  │ 1. Horizontal Scaling                │
  │    • Multiple ECS tasks              │
  │    • Auto-scaling groups             │
  │    • Load balancing                  │
  ├──────────────────────────────────────┤
  │ 2. Caching Layer                     │
  │    • Redis for repeated URLs         │
  │    • CloudFront CDN                  │
  │    • Result caching (24 hours)       │
  ├──────────────────────────────────────┤
  │ 3. Async Processing                  │
  │    • SQS queue for analysis jobs     │
  │    • Lambda workers                  │
  │    • WebSocket status updates        │
  ├──────────────────────────────────────┤
  │ 4. Database Optimization             │
  │    • Read replicas                   │
  │    • Connection pooling              │
  │    • Query optimization              │
  ├──────────────────────────────────────┤
  │ 5. Multi-Region                      │
  │    • Route 53 geo-routing            │
  │    • Regional deployments            │
  │    • Cross-region replication        │
  └──────────────────────────────────────┘
```

## Monitoring and Observability

```
┌──────────────────────────────────────────────────────┐
│                   Monitoring Stack                    │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Application Metrics:                                │
│  ├── Request rate                                    │
│  ├── Response time (p50, p95, p99)                   │
│  ├── Error rate                                      │
│  └── Analysis duration                               │
│                                                       │
│  Infrastructure Metrics:                             │
│  ├── CPU utilization                                 │
│  ├── Memory usage                                    │
│  ├── Network I/O                                     │
│  └── Disk usage                                      │
│                                                       │
│  Database Metrics:                                   │
│  ├── Connection count                                │
│  ├── Query performance                               │
│  ├── Replication lag                                 │
│  └── Storage usage                                   │
│                                                       │
│  External Service Metrics:                           │
│  ├── OpenAI API latency                              │
│  ├── OpenAI API errors                               │
│  └── API cost tracking                               │
│                                                       │
│  Logging:                                            │
│  ├── Application logs (CloudWatch)                   │
│  ├── Access logs (ALB)                               │
│  ├── Database logs (RDS)                             │
│  └── Audit logs (CloudTrail)                         │
│                                                       │
│  Alerting:                                           │
│  ├── High error rate → SNS → Email/Slack             │
│  ├── High latency → PagerDuty                        │
│  ├── Low credibility scores → Dashboard              │
│  └── Cost anomalies → Budget alerts                  │
│                                                       │
└──────────────────────────────────────────────────────┘
```

This architecture provides a solid foundation for a production-ready application with clear separation of concerns, scalability options, and comprehensive monitoring.
