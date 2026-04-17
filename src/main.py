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
from sqlalchemy.orm import Session
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
    yield
    await crawler_instance.close()

app = FastAPI(title="AI Job Hunter", lifespan=lifespan)
reader = PyMuPDFReader()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user_id: str = "robert_gordon", db: Session = Depends(get_db)):
    try:
        matches = db.query(MatchRecord).filter(
            MatchRecord.user_id == user_id,
            MatchRecord.match_score >= 60
        ).order_by(MatchRecord.match_score.desc()).all()

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

@app.post("/hunt-jobs")
async def hunt_jobs(search_query: str, user_id: str, db: Session = Depends(get_db)):
    await log_queue.put(f"Starting hunt for {user_id}: {search_query}")
    candidate_urls = find_job_urls(search_query, max_results=10)
    
    urls_to_process = [
        url for url in candidate_urls 
        if not db.query(MatchRecord).filter(MatchRecord.url == url).first()
    ]

    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, wait_until="networkidle")
    results = await crawler_instance.arun_many(urls=urls_to_process, config=run_config)

    for result in results:
        if result.success:
            try:
                await perform_analysis_logic(result.markdown, result.url, db, user_id)
            except Exception as e: print(f"Error: {e}")

    return {"status": "Hunt Complete"}

def clean_llm_json(raw_text: str) -> str:
    start = raw_text.find('{')
    end = raw_text.rfind('}')
    return raw_text[start:end + 1] if start != -1 and end != -1 else raw_text

async def perform_analysis_logic(markdown_content: str, url: str, db: Session, user_id: str):
    try:
        structured_job = job_extraction_program(text=markdown_content)
        if not structured_job.job_title or structured_job.job_title.lower() in ["not listed", "not found"]:
            return None
    except Exception: return None

    scroll_result = client.scroll(
        collection_name="resume_collection",
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key="metadata.user_id", match=models.MatchValue(value=user_id))]
        ),
        limit=1, with_payload=True
    )

    if not scroll_result[0]: return None
    my_profile = scroll_result[0][0].payload

    from llama_index.llms.openai import OpenAI
    llm = OpenAI(model="gpt-4o")
    prompt = (f"ACT AS A SKEPTICAL RECRUITER.\nCANDIDATE: {my_profile}\nJOB: {structured_job.model_dump()}\nJSON OUTPUT ONLY.")
    
    s_llm = llm.as_structured_llm(MatchAnalysis)
    analysis = await s_llm.acomplete(prompt)
    analysis_obj = MatchAnalysis.model_validate_json(clean_llm_json(analysis.text))

    if analysis_obj.match_score >= 60:
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
    return analysis_obj

@app.get("/stream-logs")
async def stream_logs():
    async def log_broadcaster():
        while True:
            msg = await log_queue.get()
            yield f"data: {msg}\n\n"
    return StreamingResponse(log_broadcaster(), media_type="text/event-stream")

@app.post("/delete-match/{match_id}")
async def delete_match(match_id: int, db: Session = Depends(get_db)):
    record = db.query(MatchRecord).filter(MatchRecord.id == match_id).first()
    if record:
        db.delete(record)
        db.commit()
    return RedirectResponse(url="/", status_code=303)