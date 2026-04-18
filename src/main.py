from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from src.engine import client, process_resume_pdf, default_storage_context, models
from src.scraper import job_extraction_program
from src.schema import MatchAnalysis, JobInquiry
from src.database import get_db, MatchRecord
from src.search_provider import find_job_urls
from src.logging_utils import log_queue
from sqlalchemy.orm import Session
from llama_index.readers.file import PyMuPDFReader
import shutil
from pathlib import Path
import os
import asyncio
import re

crawler_instance = None
templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global crawler_instance
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler_instance = AsyncWebCrawler(config=browser_config)
    await crawler_instance.start()
    yield
    await crawler_instance.close()

app = FastAPI(title="AI Job Hunter", lifespan=lifespan)
reader = PyMuPDFReader()

def is_dead_link(markdown: str) -> bool:
    """Guarding: Detects 404s, expired jobs, and empty pages."""
    dead_signals = [
        "404", "page not found", "job no longer available",
        "this job has expired", "error 404", "site maintenance", "The job you are looing for is no longer open."
    ]

    content = markdown.lower()

    if any(signal in content for signal in dead_signals) or len(content) < 300:
        return True
    return False

def is_index_page(url: str, markdown: str) -> bool:
    """🛡️ Directory Guard: Detects job boards/list pages."""
    index_patterns = [
        r"\?location=",
        r"\?department=",
        r"\?team=",
        r"/jobs/?$",
        r"search\?",
        r"/open-positions/?$",
        r"/careers/?$",
        r"\?error=true",
        r"/apply/?$",
        r"/form/"
    ]

    if any(re.search(p, url, re.IGNORECASE) for p in index_patterns):
        return True

    content = markdown.lower()
    if content.count("apply") > 4 or content.count("view job") > 3:
        return True
    return False

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user_id: str = "robert_gordon", db: Session = Depends(get_db)):
    try:
        matches = db.query(MatchRecord).filter(
            MatchRecord.user_id == user_id,
            MatchRecord.match_score >= 50,
            MatchRecord.archived == False
        ).order_by(MatchRecord.created_at.desc()).all()

        identity_label = "Identity Not Yet Indexed"
        existing_collections = client.get_collections().collections
        exists = any(c.name == "resume_collection" for c in existing_collections)

        if exists:
            scroll_result = client.scroll(
                collection_name="resume_collection",
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
                ),
                limit=1,
                with_payload=True
            )

            points = scroll_result[0]
            if points:
                payload = points[0].payload
                metadata = payload.get("metadata", {})
                name = payload.get("full_name", "Anonymous")
                headline = payload.get("headline", "No Headline")
                identity_label = f"{name} | {headline}"

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"matches": matches, "identity_label": identity_label, "current_user": user_id}
        )
    except Exception as e:
        print(f"❌ Dashboard Error: {e}")
        return templates.TemplateResponse(request=request, name="index.html", context={"matches": [], "identity_label": "Error"})

@app.post("/upload_resume")
async def upload_resume(user_id: str, file: UploadFile = File(...)):
    temp_path = f"data/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        documents = reader.load_data(file_path=Path(temp_path))
        raw_text = "\n".join([doc.text for doc in documents])
        profile = await process_resume_pdf(raw_text, default_storage_context, user_id)
        return {"message": "Identity indexed", "profile": profile}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.post("/match-job", response_model=MatchAnalysis)
async def match_job(inquiry: JobInquiry, db: Session = Depends(get_db)):
    result = await crawler_instance.arun(url=inquiry.target_url, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS, wait_until="networkidle"))
    if not result.success:
        raise HTTPException(status_code=500, detail="Failed to fetch job posting content.")

    analysis = await perform_analysis_logic(
        result.markdown, inquiry.target_url, db, inquiry.user_id, "Resume to Job Req Match", save_to_db=False, log_to_queue=False
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="No valid match analysis could be performed.")
    return analysis

@app.post("/hunt-jobs")
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
    results = await crawler_instance.arun_many(urls=urls_to_process, config=run_config)

    for result in results:
        if result.success:
            try:
                await perform_analysis_logic(result.markdown, result.url, db, user_id, search_query)
            except Exception as e: print(f"Error: {e}")

    await log_queue.put("🏁 Hunt Complete.")
    return {"status": "Hunt Complete"}

def clean_llm_json(raw_text: str) -> str:
    start = raw_text.find('{')
    end = raw_text.rfind('}')
    return raw_text[start:end + 1] if start != -1 and end != -1 else raw_text

async def perform_analysis_logic(markdown_content: str, url: str, db: Session, user_id: str, search_query: str, save_to_db=True, log_to_queue=True):
    if is_dead_link(markdown_content):
        if log_to_queue:
            await log_queue.put(f"👻 Dead Link Detected: {url[:40]}...")
        return None
    if is_index_page(url, markdown_content):
        if log_to_queue:
            await log_queue.put(f"👻 Skipped (Directory Page): {url[:40]}...")
        return None

    try:
        if log_to_queue:
            await log_queue.put(f"🧪 Extracting requirements from {url[:30]}...")
        structured_job = job_extraction_program(text=markdown_content)

        if not structured_job.job_title or structured_job.job_title.lower() in ["not listed", "not found"]:
            if log_to_queue:
                await log_queue.put(f"🚫 Content rejected: No job title found.")
            return None

        if log_to_queue:
            await log_queue.put(f"🔍 Found: {structured_job.job_title} at {structured_job.company_name}")
    except Exception:
        return None

    scroll_result = client.scroll(
        collection_name="resume_collection",
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
        ),
        limit=1, with_payload=True
    )

    if not scroll_result[0]:
        if log_to_queue:
            await log_queue.put(f"⚠️ Error: No profile found for {user_id}. Please upload resume.")
        return None

    my_profile = scroll_result[0][0].payload
    if log_to_queue:
        await log_queue.put(f"🧠 Scoring match against {user_id}'s skills...")

    from llama_index.llms.openai import OpenAI
    llm = OpenAI(model="gpt-4o")
    prompt = (
        f"ACT AS A SKEPTICAL RECRUITER.\n"
        f"INTENT: {search_query}\n"
        f"CANDIDATE: {my_profile}\n"
        f"JOB: {structured_job.model_dump()}\n\n"
        "RULES:\n1. If the job is in a different region than the INTENT, score is 0.\n"
        "2. Remote jobs are ALWAYS a match for location.\n"
        "3. Score strictly on skill fit. JSON ONLY."
    )

    s_llm = llm.as_structured_llm(MatchAnalysis)
    analysis = await s_llm.acomplete(prompt)
    analysis_obj = MatchAnalysis.model_validate_json(clean_llm_json(analysis.text))

    if log_to_queue:
        await log_queue.put(f"📊 Result: {analysis_obj.match_score}% Match.")

    if analysis_obj.match_score >= 50 and save_to_db:
        new_record = MatchRecord(
            user_id=user_id,
            job_title=structured_job.job_title,
            company_name=structured_job.company_name,
            match_score=analysis_obj.match_score,
            personalized_pitch=analysis_obj.personalized_pitch,
            url=url
        )
        db.add(new_record)
        db.commit()
        if log_to_queue:
            await log_queue.put(f"✅ High match saved to dashboard!")
    return analysis_obj

@app.get("/stream-logs")
async def stream_logs():
    async def log_broadcaster():
        while True:
            msg = await log_queue.get()
            yield f"data: {msg}\n\n"
    return StreamingResponse(log_broadcaster(), media_type="text/event-stream")

@app.post("/archive-match/{match_id}")
async def archive_match(match_id: int, db: Session = Depends(get_db)):
    record = db.query(MatchRecord).filter(MatchRecord.id == match_id).first()
    if record:
        record.archived = True
        db.commit()
    return RedirectResponse(url="localhost:8000", status_code=303)