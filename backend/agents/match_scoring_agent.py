"""
MatchScoringAgent: Scores job matches using the SKEPTICAL RECRUITER LLM prompt.
"""
from .base_agent import BaseAgent
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.openai import OpenAI
from src.schema import MatchAnalysis
from src.utils import clean_llm_json

class MatchScoringAgent(BaseAgent):
    def __init__(self):
        self.llm_program = LLMTextCompletionProgram.from_defaults(
            output_cls=MatchAnalysis,
            prompt_template_str=(
                "ACT AS A SKEPTICAL RECRUITER.\n"
                "INTENT: {search_query}\n"
                "CANDIDATE: {my_profile}\n"
                "JOB: {job}\n\n"
                "RULES:\n1. If the job is in a different region than the INTENT, score is 0.\n"
                "2. Remote jobs are ALWAYS a match for location.\n"
                "3. Score strictly on skill fit. JSON ONLY."
            ),
            llm=OpenAI(model="gpt-4o", temperature=0)
        )

    async def run(self, my_profile, structured_job, search_query):
        # Use .model_dump() for job if needed
        result = self.llm_program(
            my_profile=my_profile,
            job=structured_job.model_dump(),
            search_query=search_query
        )
        return result
