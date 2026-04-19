"""
Service layer for orchestrating agent calls and business logic.
Each function here coordinates between routers, agents, and persistence.
"""
from llama_index.core import Document
from agents.resume_agent import ResumeAgent
from agents.job_extraction_agent import JobExtractionAgent
from agents.match_scoring_agent import MatchScoringAgent
from src.engine import default_storage_context, client, models
from src.schema import MatchAnalysis
from src.database import MatchRecord
from src.utils import clean_llm_json, is_dead_link, is_index_page
from src.logging_utils import log_queue
from pathlib import Path
import os

resume_agent = ResumeAgent()
job_extraction_agent = JobExtractionAgent()
match_scoring_agent = MatchScoringAgent()

async def process_resume_upload(file_path: str, user_id: str):
    profile = await resume_agent.run(file_path, user_id)

    collections = client.get_collections().collections
    if any(c.name == "resume_collection" for c in collections):
        client.delete(
            collection_name="resume_collection",
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
                )
            )
        )

    doc = Document(
        text=profile['profile'].summary,
        metadata={
            "user_id": user_id,
            "full_name": profile['profile'].full_name,
            "headline": profile['profile'].headline,
            "email": profile['profile'].email,
            "github_url": str(profile['profile'].github_url) if profile['profile'].github_url else None,
            "portfolio_url": str(profile['profile'].portfolio_url) if profile['profile'].portfolio_url else None,
            "target_roles": profile['profile'].target_roles,
            "skills": profile['profile'].skills,
            "certifications": [c.model_dump() for c in profile['profile'].certifications],
            "experience": [e.model_dump() for e in profile['profile'].experience],
            "education": [e.model_dump() for e in profile['profile'].education],
        }
    )
    if default_storage_context is not None:
        from llama_index.core import VectorStoreIndex
        index = VectorStoreIndex.from_documents([doc], storage_context=default_storage_context)
        index.storage_context.persist()

    return profile

async def extract_job_details(markdown_content: str):
    return await job_extraction_agent.run(markdown_content)

async def analyze_job_match(markdown_content: str, url: str, db, user_id: str, search_query: str, save_to_db=True, log_to_queue=True):
    # Debug: Check for dead link
    if is_dead_link(markdown_content):
        print(f"[DEBUG] Dead link detected for URL: {url}")
        if log_to_queue:
            await log_queue.put(f"👻 Dead Link Detected: {url[:40]}...")
        return None

    # Debug: Check for index/directory page
    if is_index_page(url, markdown_content):
        print(f"[DEBUG] Skipped directory page for URL: {url}")
        if log_to_queue:
            await log_queue.put(f"👻 Skipped (Directory Page): {url[:40]}...")
        return None

    try:
        if log_to_queue:
            await log_queue.put(f"🧪 Extracting requirements from {url[:30]}...")
        print(f"[DEBUG] Extracting job details for URL: {url}")
        structured_job = await extract_job_details(markdown_content)
        print(f"[DEBUG] Extracted job: {structured_job}")
        if not structured_job.job_title or structured_job.job_title.lower() in ["not listed", "not found"]:
            print(f"[DEBUG] No job title found for URL: {url}")
            if log_to_queue:
                await log_queue.put(f"🚫 Content rejected: No job title found.")
            return None
        if log_to_queue:
            await log_queue.put(f"🔍 Found: {structured_job.job_title} at {structured_job.company_name}")
    except Exception as e:
        print(f"[DEBUG] Exception during job extraction for URL: {url} | Exception: {e}")
        return None

    # Debug: Qdrant profile lookup
    print(f"[DEBUG] Looking up user profile in Qdrant for user_id: {user_id}")
    scroll_result = client.scroll(
        collection_name="resume_collection",
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
        ),
        limit=1, with_payload=True
    )
    if not scroll_result[0]:
        print(f"[DEBUG] No profile found in Qdrant for user_id: {user_id}")
        if log_to_queue:
            await log_queue.put(f"⚠️ Error: No profile found for {user_id}. Please upload resume.")
        return None
    my_profile = scroll_result[0][0].payload
    print(f"[DEBUG] Found user profile: {my_profile}")

    if log_to_queue:
        await log_queue.put(f"🧠 Scoring match against {user_id}'s skills...")
    print(f"[DEBUG] Running match scoring agent for user_id: {user_id}, job_title: {structured_job.job_title}")
    analysis_obj = await match_scoring_agent.run(my_profile, structured_job, search_query)
    print(f"[DEBUG] MatchAnalysis: {analysis_obj}")

    if log_to_queue:
        await log_queue.put(f"📊 Result: {analysis_obj.match_score}% Match.")
    if analysis_obj.match_score >= 50 and save_to_db:
        print(f"[DEBUG] Saving match to DB for user_id: {user_id}, job_title: {structured_job.job_title}, score: {analysis_obj.match_score}")
        new_record = MatchRecord(
            user_id=user_id,
            job_title=structured_job.job_title,
            company_name=structured_job.company_name,
            match_score=analysis_obj.match_score,
            key_alignments=analysis_obj.key_alignments,
            skill_gaps=analysis_obj.skill_gaps,
            personalized_pitch=analysis_obj.personalized_pitch,
            archived=False
        )
        db.add(new_record)
        db.commit()
    else:
        print(f"[DEBUG] Not saving match (score < 50 or save_to_db=False) for user_id: {user_id}, job_title: {structured_job.job_title}, score: {analysis_obj.match_score}")
    return analysis_obj
