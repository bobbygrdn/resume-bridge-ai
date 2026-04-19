from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.schema import MatchAnalysis, JobInquiry
from src.database import get_db
from src.services import analyze_job_match
from src.scraper import scrape_job_listing

router = APIRouter()

@router.post("/match", response_model=MatchAnalysis)
async def match_job(inquiry: JobInquiry, db: Session = Depends(get_db)):
    try:
        markdown_content = await scrape_job_listing(inquiry.target_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch job content: {e}")
    result = await analyze_job_match(
        markdown_content,
        inquiry.target_url,
        db,
        inquiry.user_id,
        "Resume to Job Req Match",
        save_to_db=False,
        log_to_queue=False
    )
    if result is None:
        raise HTTPException(status_code=404, detail="No valid match analysis could be performed.")
    return result