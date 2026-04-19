from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.schema import MatchAnalysis, JobInquiry
from src.database import get_db, MatchRecord
from src.search_provider import find_job_urls
from src.logging_utils import log_queue
from crawl4ai import CrawlerRunConfig, CacheMode
from src.services import analyze_job_match

router = APIRouter()

@router.post("/match-job", response_model=MatchAnalysis)
async def match_job(inquiry: JobInquiry, db: Session = Depends(get_db)):
    result = await router.crawler_instance.arun(url=inquiry.target_url, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS, wait_until="networkidle"))
    if not result.success:
        raise HTTPException(status_code=500, detail="Failed to fetch job posting content.")
    analysis = await analyze_job_match(
        result.markdown, inquiry.target_url, db, inquiry.user_id, "Resume to Job Req Match", save_to_db=False, log_to_queue=False
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="No valid match analysis could be performed.")
    return analysis

@router.post("/hunt-jobs")
async def hunt_jobs(search_query: str, user_id: str, db: Session = Depends(get_db)):
    await log_queue.put(f"Starting hunt for {user_id}: {search_query}")
    candidate_urls = find_job_urls(search_query, max_results=10)
    await log_queue.put(f"📡 Scout found {len(candidate_urls)} total leads.")
    urls_to_process = []
    for url in candidate_urls:
        if db.query(MatchRecord).filter(MatchRecord.url == url).first():
            await log_queue.put(f"⏭️ Skipping (Already in DB): {url[:40]}...\n")
        else:
            urls_to_process.append(url)
    await log_queue.put(f"📥 Downloading content for {len(urls_to_process)} new leads...")
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, wait_until="commit")
    results = await router.crawler_instance.arun_many(urls=urls_to_process, config=run_config)
    for result in results:
        if result.success:
            try:
                await analyze_job_match(result.markdown, result.url, db, user_id, search_query)
            except Exception as e:
                print(f"Error: {e}")
    await log_queue.put("🏁 Hunt Complete.")
    return {"status": "Hunt Complete"}
