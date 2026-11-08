"""Day3 advanced: Google ADK implementation of the study agent."""

from google.adk.agents import Agent

from app.agent import INSTRUCTIONS
from app.config import MODEL
from app.tools import (
    search_glossary,
    get_lecture_summary,
    make_quiz,
)

root_agent = Agent(
    name="aie2026_study_agent",
    model=MODEL,
    description="AIE2026の講座内容を学ぶための学習支援エージェント",
    instruction=INSTRUCTIONS,
    tools=[
        search_glossary,
        get_lecture_summary,
        make_quiz,
    ],
)
