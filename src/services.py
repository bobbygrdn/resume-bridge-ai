"""
Service layer for orchestrating agent calls and business logic.
Each function here coordinates between routers, agents, and persistence.
"""
from agents.resume_agent import ResumeAgent
from agents.job_extraction_agent import JobExtractionAgent
from agents.match_scoring_agent import MatchScoringAgent
from src.engine import default_storage_context, client, models
from src.schema import MatchAnalysis
from src.database import MatchRecord
from src.utils import clean_llm_json
from src.logging_utils import log_queue
from pathlib import Path
import os

resume_agent = ResumeAgent()
job_extraction_agent = JobExtractionAgent()
match_scoring_agent = MatchScoringAgent()

async def process_resume_upload(file_path: str, user_id: str):
    # Use ResumeAgent to extract profile
    result = await resume_agent.run(file_path, user_id)
    # Persist to Qdrant (if needed, can be moved here)
    # ...existing code for persistence if needed...
    return result

async def extract_job_details(markdown_content: str):
    return await job_extraction_agent.run(markdown_content)

async def analyze_job_match(markdown_content: str, url: str, db, user_id: str, search_query: str, save_to_db=True, log_to_queue=True):
    from src.utils import is_dead_link, is_index_page
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
        structured_job = await extract_job_details(markdown_content)
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
    analysis_obj = await match_scoring_agent.run(my_profile, structured_job, search_query)
    if log_to_queue:
        await log_queue.put(f"📊 Result: {analysis_obj.match_score}% Match.")
    if analysis_obj.match_score >= 50 and save_to_db:
        new_record = MatchRecord(
            user_id=user_id,
            job_title=structured_job.job_title,
            company=structured_job.company_name,
            match_score=analysis_obj.match_score,
            key_alignments=analysis_obj.key_alignments,
            skill_gaps=analysis_obj.skill_gaps,
            personalized_pitch=analysis_obj.personalized_pitch,
            archived=False
        )
        db.add(new_record)
        db.commit()
    return analysis_obj
