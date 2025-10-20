"""
Production-Ready HR Bot Crew
Single agent system with Hybrid RAG and API Deck integration
"""

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from hr_bot.tools.hybrid_rag_tool import HybridRAGTool
from hr_bot.tools.apideck_hr_tool import APIDeckhHRTool


@CrewBase
class HrBot():
    """
    Production-ready HR Bot with advanced capabilities:
    - Hybrid RAG search (BM25 + Vector) optimized for tables
    - API Deck integration for live HR system data
    - Gemini LLM for low-cost, high-performance responses
    - Intelligent caching for low latency
    """

    agents: List[BaseAgent]
    tasks: List[Task]
    
    def __init__(self):
        super().__init__()
        
        # Initialize Gemini LLM (using environment variables)
        # For Gemini via litellm, we need to set GEMINI_API_KEY environment variable
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if gemini_api_key:
            os.environ["GEMINI_API_KEY"] = gemini_api_key  # litellm expects GEMINI_API_KEY
        
        self.llm = LLM(
            model=os.getenv("GEMINI_MODEL", "gemini/gemini-2.0-flash-lite-001"),
            temperature=0.3,  # Lower temperature for more consistent, factual responses
        )
        
        # Initialize tools
        self.hybrid_rag_tool = HybridRAGTool(data_dir="data")
        self.apideck_tool = APIDeckhHRTool()
    
    @agent
    def hr_assistant(self) -> Agent:
        """
        Employee-focused HR assistant with access to organizational documents and HR systems
        Configuration is loaded from agents.yaml
        """
        return Agent(
            config=self.agents_config['hr_assistant'],
            tools=[self.hybrid_rag_tool, self.apideck_tool],
            llm=self.llm,
            verbose=True,
            max_iter=5,  # Limit iterations for faster responses
            memory=True,  # Enable conversation memory
        )
    
    @task
    def answer_hr_query(self) -> Task:
        """
        Main task: Answer employee HR queries using organizational documents and HR systems
        Configuration is loaded from tasks.yaml
        """
        return Task(
            config=self.tasks_config['answer_hr_query'],
            agent=self.hr_assistant(),
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the production-ready HR Bot crew"""
        crew = Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,  # Disable memory to avoid OpenAI dependency
            cache=True,   # Enable caching for faster repeated queries
        )
        hybrid_tool = self.hybrid_rag_tool

        class CrewWithSources:
            def __init__(self, inner):
                self._inner = inner

            def kickoff(self, *args, **kwargs):
                output = self._inner.kickoff(*args, **kwargs)
                try:
                    output_text = str(output)
                    if "Sources:" not in output_text:
                        sources = hybrid_tool.last_sources()
                        if sources:
                            sources_line = "Sources: " + ", ".join(sources)
                            separator = "\n" if output_text.endswith("\n") else "\n\n"
                            new_text = f"{output_text}{separator}{sources_line}"
                            if hasattr(output, "raw"):
                                output.raw = new_text
                            if hasattr(output, "final_output"):
                                output.final_output = new_text
                            if hasattr(output, "tasks_output") and isinstance(output.tasks_output, list):
                                for task in output.tasks_output:
                                    if isinstance(task, dict) and "output" in task:
                                        task["output"] = new_text
                except Exception:
                    pass
                return output

            def __getattr__(self, item):
                return getattr(self._inner, item)

        return CrewWithSources(crew)
