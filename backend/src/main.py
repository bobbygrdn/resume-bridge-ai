from contextlib import asynccontextmanager
from fastapi import FastAPI
import os
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig

from src.routes import resume, job, archive

crawler_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global crawler_instance
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler_instance = AsyncWebCrawler(config=browser_config)
    await crawler_instance.start()
    # Inject crawler_instance into routers if needed
    job.router.crawler_instance = crawler_instance
    yield
    await crawler_instance.close()

app = FastAPI(title="AI Job Hunter", lifespan=lifespan)

# Include routers
app.include_router(resume.router)
app.include_router(job.router)
app.include_router(archive.router)

@app.get("/")
async def root():
    return {"message": "Resume Bridge AI backend is running."}