from src.utils import is_dead_link, is_index_page, clean_llm_json
from src.engine import client, models
from src.scraper import job_extraction_program
from src.schema import MatchAnalysis
from src.database import MatchRecord
from src.logging_utils import log_queue

async def perform_analysis_logic(markdown_content: str, url: str, db, user_id: str, search_query: str, save_to_db=True, log_to_queue=True):
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
