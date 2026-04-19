# Resume Bridge AI

A FastAPI-based backend for resume/job matching using LLM-powered extraction and analysis, with Qdrant as the vector database and SQLite for match records.

## Features

- Upload resumes and extract structured profiles
- Store and search profiles using Qdrant vector DB
- Analyze job postings and match them to uploaded resumes
- Modular agent-based architecture
- Dockerized for easy deployment

## Quickstart (Docker Compose)

1. **Clone the repo:**
   ```bash
   git clone https://github.com/yourusername/resume-bridge-ai.git
   cd resume-bridge-ai
   ```
2. **Set your OpenAI API key:**
   - Copy `.env.example` to `.env` and fill in your OpenAI API key:
     ```bash
     cp .env.example .env
     # Edit .env and set OPENAI_API_KEY
     ```
3. **Build and start the stack:**
   ```bash
   docker-compose up --build
   ```
4. **Access the API:**
   - FastAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Qdrant UI: [http://localhost:6333](http://localhost:6333)

## Project Structure

- `src/` - FastAPI app and business logic
- `agents/` - Modular LLM agent classes
- `tempData/` - Temporary storage for uploaded files (not committed)
- `storage/` - LlamaIndex persistent storage
- `qdrant_data/` - Qdrant vector DB storage
- `job_hunter.db` - SQLite database (persisted via Docker volume)

## Environment Variables

- `OPENAI_API_KEY` (required): Your OpenAI API key for LLM-powered features

## Development

- For local development, you can run the app with `python run.py` (requires Python 3.12+ and dependencies from `requirements.txt`).
- Use Docker Compose for production or easy onboarding.

## License

MIT
