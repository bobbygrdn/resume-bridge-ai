"""
JobExtractionAgent: Extracts job details from markdown using LLMs.
"""
from .base_agent import BaseAgent
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.openai import OpenAI
from src.schema import JobPosting

class JobExtractionAgent(BaseAgent):
    def __init__(self):
        self.llm_program = LLMTextCompletionProgram.from_defaults(
            output_cls=JobPosting,
            prompt_template_str=(
                "You are an expert technical recruiter. Extract the job details "
                "from the following markdown text. If information is missing, use 'Not Listed'.\n\n"
                "JOB POSTING TEXT:\n{text}"
            ),
            llm=OpenAI(model="gpt-4o-mini", temperature=0)
        )

    async def run(self, markdown_content: str):
        return self.llm_program(text=markdown_content)
