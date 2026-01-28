from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import Optional
import time

from ..database import get_db
from ..models import AnalysisRequest
from ..services.scraper import WebScraper
from ..services.chunker import ContentChunker
from ..services.analyzer import ContentAnalyzer

router = APIRouter()

class AnalyzeURLRequest(BaseModel):
    url: str

class AnalysisResponse(BaseModel):
    request_id: int
    url: str
    status: str
    is_out_of_context: Optional[str] = None
    is_propaganda: Optional[str] = None
    credibility_score: Optional[float] = None
    content_context: Optional[str] = None
    detailed_results: Optional[dict] = None
    analysis_duration: Optional[float] = None
    error_message: Optional[str] = None

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_url(
    request_data: AnalyzeURLRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Analyze a website URL for content credibility, propaganda, and context
    """
    start_time = time.time()

    # Get client IP
    client_ip = request.client.host if request.client else None

    # Create database record
    analysis_request = AnalysisRequest(
        url=request_data.url,
        user_ip=client_ip,
        status="pending"
    )
    db.add(analysis_request)
    db.commit()
    db.refresh(analysis_request)

    try:
        # Step 1: Scrape website content
        scraper = WebScraper()
        content = scraper.fetch_content(request_data.url)

        if not content or len(content.strip()) < 100:
            raise Exception("Insufficient content extracted from URL")

        # Step 2: Chunk the content
        chunker = ContentChunker()
        chunks = chunker.chunk_content(content)

        # Step 3: Analyze each chunk
        analyzer = ContentAnalyzer()
        chunk_results = []

        for i, chunk in enumerate(chunks):
            chunk_result = analyzer.analyze_chunk(chunk, i, len(chunks))
            chunk_results.append(chunk_result)

        # Step 4: Aggregate results
        final_result = analyzer.aggregate_results(chunk_results)

        # Step 5: Update database with results
        analysis_duration = time.time() - start_time

        analysis_request.status = "completed"
        analysis_request.is_out_of_context = final_result.get("out_of_context", {}).get("assessment", "Uncertain")
        analysis_request.is_propaganda = final_result.get("propaganda", {}).get("assessment", "Uncertain")
        analysis_request.credibility_score = final_result.get("credibility_score", 0)
        analysis_request.content_context = final_result.get("content_context", "")
        analysis_request.detailed_results = final_result
        analysis_request.analysis_duration = analysis_duration

        db.commit()
        db.refresh(analysis_request)

        return AnalysisResponse(
            request_id=analysis_request.id,
            url=analysis_request.url,
            status=analysis_request.status,
            is_out_of_context=analysis_request.is_out_of_context,
            is_propaganda=analysis_request.is_propaganda,
            credibility_score=analysis_request.credibility_score,
            content_context=analysis_request.content_context,
            detailed_results=analysis_request.detailed_results,
            analysis_duration=analysis_request.analysis_duration
        )

    except Exception as e:
        # Update database with error
        analysis_request.status = "failed"
        analysis_request.error_message = str(e)
        analysis_request.analysis_duration = time.time() - start_time
        db.commit()

        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{request_id}", response_model=AnalysisResponse)
async def get_analysis(request_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a previous analysis by request ID
    """
    analysis_request = db.query(AnalysisRequest).filter(AnalysisRequest.id == request_id).first()

    if not analysis_request:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return AnalysisResponse(
        request_id=analysis_request.id,
        url=analysis_request.url,
        status=analysis_request.status,
        is_out_of_context=analysis_request.is_out_of_context,
        is_propaganda=analysis_request.is_propaganda,
        credibility_score=analysis_request.credibility_score,
        content_context=analysis_request.content_context,
        detailed_results=analysis_request.detailed_results,
        analysis_duration=analysis_request.analysis_duration,
        error_message=analysis_request.error_message
    )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
