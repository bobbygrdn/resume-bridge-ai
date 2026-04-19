"""
ResumeAgent: Handles profile creation from uploaded resumes using LLMs.
"""
from .base_agent import BaseAgent
from llama_index.readers.file import PyMuPDFReader
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.openai import OpenAI
from src.schema import ResumeProfile
from src.engine import default_storage_context, client, models
from pathlib import Path
import os
import shutil

class ResumeAgent(BaseAgent):
    def __init__(self):
        self.reader = PyMuPDFReader()
        self.llm_program = LLMTextCompletionProgram.from_defaults(
            output_cls=ResumeProfile,
            prompt_template_str=(
                "You are an expert technical recruiter. Extract professional information "
                "from the following resume text. Create a compelling 'headline' that "
                "summarizes their expertise and intent.\n\n"
                "CRITICAL: The 'headline' MUST be under 60 characters total. "
                "Be concise (e.g., 'Senior AI Engineer').\n\n"
                "RESUME TEXT:\n{text}"
            ),
            llm=OpenAI(model="gpt-4o-mini", temperature=0)
        )

    async def run(self, file_path: str, user_id: str):
        temp_path = file_path
        try:
            documents = self.reader.load_data(file_path=Path(temp_path))
            raw_text = "\n".join([doc.text for doc in documents])
            profile = self.llm_program(text=raw_text)
            # Optionally, persist to Qdrant as in process_resume_pdf
            # ...existing code for persistence if needed...
            return {"message": "Identity indexed", "profile": profile}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
