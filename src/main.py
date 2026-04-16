from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from src.engine import client, process_resume_pdf, default_storage_context
from src.schema import MatchAnalysis, JobInquiry, ResumeProfile
from src.database import get_db, MatchRecord
from sqlalchemy.orm import Session
from llama_index.readers.file import PyMuPDFReader
from crawl4ai import AsyncWebCrawler, BrowserConfig
import shutil
import os
from pathlib import Path
import asyncio

crawler_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global crawler_instance
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler_instance = AsyncWebCrawler(config=browser_config)
    await crawler_instance.start()
    print("Scraper Engine Started")

    yield

    await crawler_instance.close()
    print("Scraper Engine Shutdown")

asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="Resume Matcher API", lifespan=lifespan)
reader = PyMuPDFReader()

@app.get("/health")
async def health_check():
    try:
        collections = client.get_collections()
        return {
            "status": "online",
            "db_reachable": True,
            "collection_count": len(collections.collections)}
    except Exception as e:
        return {"status": "error", "db_reachable": False, "detail": str(e)}

@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    temp_path = f"data/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        file_arg = Path(temp_path)

        documents = reader.load_data(file_path=file_arg)

        raw_text = "\n".join([doc.text for doc in documents])

        profile = await process_resume_pdf(raw_text, default_storage_context)

        return {
            "message": "Resume successfully indexed",
            "profile": profile
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/match-job", response_model=MatchAnalysis)
async def match_job(inquiry: JobInquiry, db: Session = Depends(get_db)):
    try:
        existing_match = db.query(MatchRecord).filter(MatchRecord.url == inquiry.target_url).first()
    
        if existing_match:
            print(f"Returning cached match for: {existing_match.job_title}")
            return MatchAnalysis(
                match_score=existing_match.match_score,
                key_alignments=existing_match.key_alignments,
                skill_gaps=existing_match.skill_gaps,
                personalized_pitch=existing_match.personalized_pitch
            )

        result = await crawler_instance.arun(url=inquiry.target_url)
        if not result.success:
            raise HTTPException(status_code=500, detail="Scrape failed")

        return await perform_analysis_logic(result.markdown, inquiry.target_url, db)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
