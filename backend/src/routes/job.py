from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.schema import MatchAnalysis, JobInquiry
from src.database import get_db, MatchRecord
from src.search_provider import find_job_urls
from src.logging_utils import log_queue
from crawl4ai import CrawlerRunConfig, CacheMode
from src.services import analyze_job_match

@router.post("/hunt-jobs")
async def hunt_jobs(search_query: str, user_id: str, db: Session = Depends(get_db)):

    print(f"[HUNT] Starting hunt for user: {user_id} | Query: {search_query}")
    
    candidate_urls = find_job_urls(search_query, max_results=10)
    
    print(f"[HUNT] Scout found {len(candidate_urls)} total leads: {candidate_urls}")
    
    await log_queue.put(f"\U0001f4e1 Scout found {len(candidate_urls)} total leads.")
    urls_to_process = []
    
    for url in candidate_urls:
        if db.query(MatchRecord).filter(MatchRecord.url == url).first():
            await log_queue.put(f"\u23ed\ufe0f Skipping (Already in DB): {url[:40]}...\n")
            print(f"[HUNT] Skipping (Already in DB): {url}")
        else:
            urls_to_process.append(url)
    
    print(f"[HUNT] Downloading content for {len(urls_to_process)} new leads...")
    
    await log_queue.put(f"\U0001f4e5 Downloading content for {len(urls_to_process)} new leads...")
    
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, wait_until="commit")
    results = await router.crawler_instance.arun_many(urls=urls_to_process, config=run_config)
    
    for result in results:
        if result.success:
            try:
                print(f"[HUNT] Processing result for URL: {result.url}")
                await analyze_job_match(result.markdown, result.url, db, user_id, search_query)
            except Exception as e:
                print(f"[HUNT] Error processing {result.url}: {e}")
        else:
            print(f"[HUNT] Failed to fetch content for URL: {result.url}")
    
    await log_queue.put("\U0001f3c1 Hunt Complete.")
    
    print(f"[HUNT] Hunt Complete for user: {user_id}")
    
    return {"status": "Hunt Complete"}