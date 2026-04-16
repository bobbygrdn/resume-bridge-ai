from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from src.engine import client, process_resume_pdf, default_storage_context
from src.scraper import scrape_job_listing, job_extraction_program
from src.schema import MatchAnalysis, JobInquiry
from src.database import get_db, MatchRecord
from src.search_provider import find_job_urls
from sqlalchemy.orm import Session
from llama_index.core import VectorStoreIndex
from llama_index.readers.file import PyMuPDFReader
import shutil
from pathlib import Path
import os
import asyncio
import re

crawler_instance = None
log_queue = asyncio.Queue()
templates = Jinja2Templates(directory="templates")

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


app = FastAPI(title="Resume Matcher API", lifespan=lifespan)
reader = PyMuPDFReader()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """The Visual Dashboard: Pulls from SQLite Memory"""
    try:
        matches = db.query(MatchRecord)\
            .filter(MatchRecord.match_score >= 60)\
            .order_by(MatchRecord.match_score.desc())\
            .all()

        identity_label = "Identity Not Yet Indexed"
        collections = client.scroll(
            collection_name="resume_collection",
            limit=1,
            with_payload=True
        )

        if collections[0]:
            profile = collections[0][0].payload
            name = profile.get("full_name", "Anonymous Professional")
            headline = profile.get("headline", "Verified AI Scout")
            identity_label = f"{name} | {headline}"

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"matches": matches, "identity_label": identity_label}
        )
    except Exception as e:
        print(f"Dashboard Error: {e}")
        raise HTTPException(status_code=500, detail="Could not load dashboard")

@app.post("/delete-match/{match_id}")
async def delete_match(match_id: int, db: Session = Depends(get_db)):
    """Removes a match you're not interested in"""
    record = db.query(MatchRecord).filter(MatchRecord.id == match_id).first()
    if record:
        db.delete(record)
        db.commit()
    return RedirectResponse(url="/", status_code=303)

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

@app.get("/matches")
async def get_saved_matches(min_score: int = 0, db: Session = Depends(get_db)):
    """
    Retrieve all saved matches, optionally filtering by a minimum score.
    Useful for seeing which jobs are worth your time.
    """
    results = db.query(MatchRecord).filter(MatchRecord.match_score >= min_score).all()
    return results

async def log_broadcaster():
    """Generator that sends messages to the frontend."""
    while True:
        msg = await log_queue.get()
        yield f"data: {msg}\n\n"

@app.get("/stream-logs")
async def stream_logs():
    return StreamingResponse(log_broadcaster(), media_type="text/event-stream")

@app.post("/hunt-jobs")
async def hunt_jobs(search_query: str, db: Session = Depends(get_db)):
    """
    The Agentic Loop:
    1. Finds URLs -> 2. Filters existing -> 3. Matches -> 4. Saves
    """

    await log_queue.put(f"Starting hunt for: {search_query}")
    candidate_urls = find_job_urls(search_query, max_results=10)

    await log_queue.put(f"Scout found {len(candidate_urls)} URLs.")

    urls_to_process = [
        url for url in candidate_urls
        if not db.query(MatchRecord).filter(MatchRecord.url == url).first()
    ]

    dupes = len(candidate_urls) - len(urls_to_process)
    if dupes > 0:
        await log_queue.put(f"Skipping {dupes} jobs already in your memory.")

    if not urls_to_process:
        await log_queue.put("All found jobs have already been analyzed.")
        return {"status": "Complete", "message": "All found jobs already exist in DB."}

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until="networkidle",
        page_timeout=30000
    )

    await log_queue.put(f"Running concurrent scrape for {len(urls_to_process)} URLs...")
    results = await crawler_instance.arun_many(urls=urls_to_process, config=run_config)

    matches_found = []

    for result in results:
        if not result.success:
            await log_queue.put(f"Failed to scrape: {result.url}")
            continue

        try:
            analysis_obj = await perform_analysis_logic(result.markdown, result.url, db)

            if analysis_obj and analysis_obj.match_score >= 50:
                matches_found.append({
                    "job": f"{analysis_obj.match_score}% - {result.url[:30]}..."
                })
        except Exception as e:
            print(f"Error processing {result.url}: {e}")

    await log_queue.put("🏁 Hunt complete. Dashboard refreshing...")
    return {"status": "Hunt Complete"}

def sanitize_json_string(text: str) -> str:
    """Removes LLM chatter like triple backticks or trailing newlines."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else text

def clean_llm_json(raw_text: str) -> str:
    """Explicitly extracts only the content between the first and last curly braces."""
    start = raw_text.find('{')
    end = raw_text.rfind('}')
    if start != -1 and end != -1:
        return raw_text[start:end + 1]
    return raw_text

async def perform_analysis_logic(markdown_content: str, url: str, db: Session):
    """
    The shared 'Brain' of the application. 
    Processes raw markdown into a saved MatchRecord.
    """
    try:
        structured_job = job_extraction_program(text=markdown_content)
        
        if not structured_job.job_title or structured_job.job_title.lower() in ["not listed", "not found"]:
            await log_queue.put(f"⚠️ Skipping dead listing: {url[:40]}...")
            return None

    except Exception as e:
        await log_queue.put(f"❌ Could not parse job at {url[:30]}... (Likely a dead link)")
        return None

    await log_queue.put(f"Comparing '{structured_job.job_title}' at {structured_job.company_name} against your identity...")

    collections = client.scroll(
        collection_name="resume_collection",
        limit=1,
        with_payload=True
    )

    if not collections[0]:
        raise HTTPException(status_code=404, detail="No resume profile found in Qdrant.")
    my_profile = collections[0][0].payload

    from llama_index.llms.openai import OpenAI
    llm = OpenAI(model="gpt-4o")

    prompt = (
        f"ACT AS A SKEPTICAL TECHNICAL RECRUITER.\n"
        f"CANDIDATE DATA: {my_profile}\n\n"
        f"JOB DESCRIPTION: {structured_job.model_dump()}\n\n"
        "INSTRUCTIONS:\n"
        "1. Compare CANDIDATE DATA against the JOB DESCRIPTION.\n"
        "2. If a skill is NOT explicitly in the data, it is a GAP.\n"
        "3. DO NOT INFER. Provide a MatchAnalysis JSON response."
    )

    s_llm = llm.as_structured_llm(MatchAnalysis)
    analysis = await s_llm.acomplete(prompt)

    clean_json = clean_llm_json(analysis.text)
    try:
        analysis_obj = MatchAnalysis.model_validate_json(clean_json)
    except Exception as e:
        await log_queue.put(f"❌ Validation failed for {url[:30]}")
        return MatchAnalysis(match_score=0, key_alignments=[], skill_gaps=[], personalized_pitch="Parsing error.")

    await log_queue.put(f"Result: {analysis_obj.match_score}% Match for {structured_job.job_title}")

    if analysis_obj.match_score >= 60:
        new_record = MatchRecord(
            job_title=structured_job.job_title,
            company_name=structured_job.company_name,
            match_score=analysis_obj.match_score,
            key_alignments=analysis_obj.key_alignments,
            skill_gaps=analysis_obj.skill_gaps,
            personalized_pitch=analysis_obj.personalized_pitch,
            url=url
        )
        db.add(new_record)
        db.commit()
        await log_queue.put(f"✅ Saved high-value match: {analysis_obj.match_score}%")
    else:
        await log_queue.put(f"⏭️ Discarding low match: {analysis_obj.match_score}%")

    await log_queue.put(f"🎯 Analysis Complete: {analysis_obj.match_score}% Match.")
    return analysis_obj