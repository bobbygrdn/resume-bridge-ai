# AI Coding Agent Instructions for Resume Bridge AI

Welcome to the Resume Bridge AI codebase! This file provides essential instructions and conventions to help AI coding agents and contributors be immediately productive.

## Project Overview

Resume Bridge AI is a FastAPI-based web application that helps users match their resumes to job postings using LLM-powered extraction and analysis, with Qdrant as the vector database and SQLite for match records.

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
- **Vector DB:** Qdrant (via `qdrant_client`)
- **LLM/Extraction:** llama_index, OpenAI API
- **Database:** SQLite (`job_hunter.db`, via SQLAlchemy)
- **Frontend:** Jinja2 templates (`templates/index.html`)
- **Async:** All crawling, LLM, and DB operations are async where possible
- **User Identity:** Controlled by `user_id` (default: `robert_gordon`)
- **Resume Data:** Uploaded as PDF, parsed and indexed into Qdrant
- **Job Search:** Uses DuckDuckGo (ddgs) to find postings, then crawls and analyzes them

## Common Pitfalls

- **Windows Async:** Uvicorn reload must be `False` on Windows due to subprocess bug
- **Qdrant:** Must be running for app to function; check Docker status
- **API Keys:** Requires valid OpenAI API key in `.env`
- **File Paths:** Use forward slashes or `os.path` for cross-platform compatibility

## Useful Files & Directories

- `src/main.py`: FastAPI app, endpoints, and core logic
- `src/engine.py`: Qdrant/LLM integration, resume processing
- `src/scraper.py`: Job posting extraction logic
- `src/schema.py`: Pydantic models for resume, job, and match analysis
- `src/database.py`: SQLAlchemy models and DB session
- `templates/index.html`: Main dashboard UI
- `docker-compose.yaml`: Qdrant service config

## How to Extend

- Add new endpoints to `src/main.py`
- Add new data models to `src/schema.py`
- Add new job sources in `src/search_provider.py`

## Links

- [Qdrant Docs](https://qdrant.tech/documentation/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [llama_index Docs](https://docs.llamaindex.ai/)

---

For more details, see the code comments in each module. If you add new conventions or patterns, update this file to help future agents and contributors.
