import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from src.schema import JobPosting
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.openai import OpenAI

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
        async for result in await crawler.arun(url=url, config=run_config):
            
            if result.success:
                structured_job = job_extraction_program(text=result.markdown)
                return structured_job
            else:
                print(f"⚠️ Partial failure or warning: {result.error_message}")
                
        raise Exception("Scraper completed without yielding a successful result.")

if __name__ == "__main__":
    test_url = "https://jobs.sevendaysvt.com/job/engineering-architecture/telecommunications-service-technician/"
    asyncio.run(scrape_job_listing(test_url))