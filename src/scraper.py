import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from src.schema import JobPosting

# LLM logic removed; now handled by agents and service layer

async def scrape_job_listing(url: str):
    browser_config = BrowserConfig(headless=True, verbose=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        async for result in await crawler.arun(url=url, config=run_config):
            if result.success:
                return result.markdown
            else:
                print(f"⚠️ Partial failure or warning: {result.error_message}")
        raise Exception("Scraper completed without yielding a successful result.")

if __name__ == "__main__":
    test_url = "https://jobs.sevendaysvt.com/job/engineering-architecture/telecommunications-service-technician/"
    asyncio.run(scrape_job_listing(test_url))