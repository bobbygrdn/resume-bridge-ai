import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from src.schema import JobPosting
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.openai import OpenAI

# 1. Initialize the LLM Extraction "Brain"
job_extraction_program = LLMTextCompletionProgram.from_defaults(
    output_cls=JobPosting,
    prompt_template_str=(
        "You are an expert technical recruiter. Extract the job details "
        "from the following markdown text. If information is missing, use 'Not Listed'.\n\n"
        "JOB POSTING TEXT:\n{text}"
    ),
    llm=OpenAI(model="gpt-4o-mini", temperature=0)
)

async def scrape_job_listing(url: str):
    browser_config = BrowserConfig(headless=True, verbose=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # 1. Use 'async for' because arun() yields results in phases
        async for result in await crawler.arun(url=url, config=run_config):
            
            # 2. Now 'result' is the actual CrawlResult object
            if result.success:
                # Step B: LLM Extraction from the clean Markdown
                structured_job = job_extraction_program(text=result.markdown)
                return structured_job
            else:
                # Log the specific error from the result
                print(f"⚠️ Partial failure or warning: {result.error_message}")
                
        raise Exception("Scraper completed without yielding a successful result.")

# --- QUICK TEST BLOCK ---
if __name__ == "__main__":
    # Test with a known job board URL
    test_url = "https://jobs.sevendaysvt.com/job/engineering-architecture/telecommunications-service-technician/"
    asyncio.run(scrape_job_listing(test_url))