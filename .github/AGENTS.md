# AI Coding Agent Instructions for Resume Bridge AI

Welcome to the Resume Bridge AI codebase! This file provides essential instructions and conventions to help AI coding agents and contributors be immediately productive.

## Project Overview

Resume Bridge AI is a FastAPI-based backend for resume/job matching using LLM-powered extraction and analysis, with Qdrant as the vector database and SQLite for match records. The codebase is organized by separation of concerns using FastAPI routers.

## Key Build & Run Commands

- **Run the app (dev, Windows):**
  ```bash
  python run.py
  ```
- **Qdrant (vector DB):**
  - Launched via Docker Compose: `docker-compose up -d`
- **Dependencies:**
  - Install with: `pip install -r requirements.txt`

## Architecture & Conventions

- **Backend:** FastAPI (`src/main.py`)
- **Routers:** All API endpoints are organized in `src/routes/` (e.g., `resume.py`, `job.py`, `archive.py`)
- **Vector DB:** Qdrant (via `qdrant_client`)
- **LLM/Extraction:** llama_index, OpenAI API
- **Database:** SQLite (`job_hunter.db`, via SQLAlchemy)
- **Async:** All crawling, LLM, and DB operations are async where possible
- **User Identity:** Controlled by `user_id` (default: `robert_gordon`)
- **Resume Data:** Uploaded as PDF, parsed and indexed into Qdrant
- **Job Search:** Uses DuckDuckGo (ddgs) to find postings, then crawls and analyzes them
- **Utilities:** Common helpers in `src/utils.py`

## Common Pitfalls

- **Windows Async:** Uvicorn reload must be `False` on Windows due to subprocess bug
- **Qdrant:** Must be running for app to function; check Docker status
- **API Keys:** Requires valid OpenAI API key in `.env`
- **File Paths:** Use forward slashes or `os.path` for cross-platform compatibility

## Useful Files & Directories

- `src/main.py`: FastAPI app setup and router inclusion
- `src/routes/`: All API routers (resume, job, archive, etc.)
- `src/engine.py`: Qdrant/LLM integration, resume processing
- `src/scraper.py`: Job posting extraction logic
- `src/schema.py`: Pydantic models for resume, job, and match analysis
- `src/database.py`: SQLAlchemy models and DB session
- `src/utils.py`: Utility/helper functions
- `docker-compose.yaml`: Qdrant service config

## How to Extend

- Add new endpoints as routers in `src/routes/`
- Add new data models to `src/schema.py`
- Add new job sources in `src/search_provider.py`

## Links

- [Qdrant Docs](https://qdrant.tech/documentation/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [llama_index Docs](https://docs.llamaindex.ai/)
