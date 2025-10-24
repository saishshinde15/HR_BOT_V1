"""
Production-Grade Hierarchical HR Bot Crew
Manager Agent + Policy Specialist + HRMS Specialist

Architecture:
- Manager Agent: Routes queries and synthesizes responses
- Policy Specialist: Searches documents via RAG tool
- HRMS Specialist: Executes operations via Apideck tool
- Process: Hierarchical (manager delegates to specialists)
"""

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from hr_bot.tools.hybrid_rag_tool import HybridRAGTool
from hr_bot.tools.apideck_hr_tool import APIDeckhHRTool


@CrewBase
class HrBotHierarchical():
    """
    Production-grade Hierarchical HR Bot with specialized agents and a dedicated manager agent:

    1. HR Manager Agent (Gemini Pro powered):
        - Analyzes queries
        - Delegates to specialists
        - Synthesizes responses
        - Ensures quality

    2. Policy Specialist (RAG Expert):
        - Searches company documents
        - Extracts policy information
        - Provides comprehensive policy details

    3. HRMS Specialist (System Expert):
        - Executes HR system operations
        - Manages employee/company data
        - Handles CRUD operations safely

    Process: Hierarchical
    - CrewAI manager agent delegates dynamically
    - Specialists work independently
    - Manager synthesizes final response
    """

    agents_config = "config/agents_hierarchical.yaml"
    tasks_config = "config/tasks_hierarchical.yaml"
    
    def __init__(self):
        super().__init__()
        
        # Initialize Gemini LLM
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if gemini_api_key:
            os.environ["GEMINI_API_KEY"] = gemini_api_key
        
        # LLM for manager agent (Gemini Pro for orchestration)
        self.manager_llm = LLM(
            model=os.getenv("GEMINI_MANAGER_MODEL", "gemini/gemini-2.0-flash-lite-001"),
            temperature=0.4,
        )
        
        # LLM for specialists (lower temperature for accuracy)
        self.specialist_llm = LLM(
            model=os.getenv("GEMINI_MODEL", "gemini/gemini-2.0-flash-lite-001"),
            temperature=0.2,  # Lower for more precise, factual responses
        )
        
        # Initialize tools
        self.rag_tool = HybridRAGTool(data_dir="data")
        self.hrms_tool = APIDeckhHRTool()
    
    @agent
    def hr_manager(self) -> Agent:
        """
        Senior HR Manager - Routes queries and synthesizes responses
        Delegates all execution to specialists
        """
        return Agent(
            config=self.agents_config['hr_manager'],
            tools=[],  # Manager delegates instead of using tools
            llm=self.manager_llm,
            verbose=True,
            max_iter=10,
            memory=True,
            allow_delegation=True,
        )

    @agent
    def policy_specialist(self) -> Agent:
        """
        Policy Specialist - Expert in document search and policy extraction
        Uses ONLY RAG tool
        """
        return Agent(
            config=self.agents_config['policy_specialist'],
            tools=[self.rag_tool],  # Only RAG tool
            llm=self.specialist_llm,
            verbose=True,
            max_iter=5,
            memory=False,  # Specialists don't need memory
            allow_delegation=False,  # Specialists don't delegate
        )
    
    @agent
    def hrms_specialist(self) -> Agent:
        """
        HRMS Specialist - Expert in HR system operations
        Uses ONLY Apideck tool
        """
        return Agent(
            config=self.agents_config['hrms_specialist'],
            tools=[self.hrms_tool],  # Only HRMS tool
            llm=self.specialist_llm,
            verbose=True,
            max_iter=5,
            memory=False,
            allow_delegation=False,
        )
    
    @task
    def route_and_synthesize_task(self) -> Task:
        """
        Manager task - analyzes query and delegates to exactly one specialist
        """
        return Task(
            config=self.tasks_config['route_and_synthesize'],
        )

    @task
    def search_policy_task(self) -> Task:
        """
        Policy search task - Assigned to policy specialist
        Manager will delegate here for policy/document queries
        Contains ALL the detailed instructions for the policy specialist
        """
        return Task(
            config=self.tasks_config['search_policy_documents'],
            agent=self.policy_specialist(),  # ASSIGNED to policy specialist
        )
    
    @task
    def hrms_operations_task(self) -> Task:
        """
        HRMS operations task - Assigned to HRMS specialist
        Manager will delegate here for system operations
        Contains ALL the detailed instructions for the HRMS specialist
        """
        return Task(
            config=self.tasks_config['execute_hrms_operations'],
            agent=self.hrms_specialist(),  # ASSIGNED to HRMS specialist
        )
    
    @crew
    def crew(self) -> Crew:
        """
        Creates the hierarchical HR Bot crew
        
        HIERARCHICAL DELEGATION ARCHITECTURE:

          How it works:
          1. User asks: "What is sick leave policy?" (STATIC - from documents)
              → Manager agent analyzes query
              → Manager delegates to policy specialist via search_policy_task
              → Policy specialist executes search_policy_task using RAG tool
              → Manager synthesizes response for the employee

          2. User asks: "Update my department" (DYNAMIC - system changes)
              → Manager agent analyzes query
              → Manager delegates to HRMS specialist via hrms_operations_task
              → HRMS specialist executes hrms_operations_task using Apideck tool
              → Manager confirms action with the employee

          IMPORTANT HIERARCHICAL ARCHITECTURE:
          - Manager orchestration handled by CrewAI manager agent with Gemini Pro
          - search_policy_task: Policy specialist's detailed task (assigned to policy_agent)
          - hrms_operations_task: HRMS specialist's detailed task (assigned to hrms_agent)
          - Manager analyzes inputs, delegates, and synthesizes while specialists execute
        """
        
        # Create agent instances
        #manager_agent = self.hr_manager()
        policy_agent = self.policy_specialist()
        hrms_agent = self.hrms_specialist()

        # Manager orchestrates and delegates based on intent
        manager_task = self.route_and_synthesize_task()

        # Create crew with hierarchical process
        crew_instance = Crew(
            agents=[
                policy_agent,  # Has RAG tool - for static policy queries
                hrms_agent,    # Has Apideck tool - for dynamic system operations
            ],
            tasks=[
                manager_task,
                
            ],
            process=Process.sequential,
            manager_agent=manager_agent,
            verbose=True,
            memory=False,
            cache=True,
            max_rpm=30,
        )
        
        # Wrap crew to add source citations from RAG tool
        hybrid_tool = self.rag_tool
        
        class CrewWithSources:
            """Wrapper to automatically add source citations to responses"""
            
            def __init__(self, inner):
                self._inner = inner
            
            def kickoff(self, *args, **kwargs):
                """Execute crew and add source citations"""
                output = self._inner.kickoff(*args, **kwargs)
                
                # Try to add sources from RAG tool if not already present
                try:
                    # Determine the base text we will augment with sources
                    if hasattr(output, "final_output") and output.final_output:
                        output_text = str(output.final_output)
                    elif hasattr(output, "raw") and output.raw:
                        output_text = str(output.raw)
                    else:
                        output_text = str(output)

                    # Only add sources if RAG tool was used and sources not already in output
                    if "Sources:" not in output_text and "Source:" not in output_text:
                        sources = hybrid_tool.last_sources()
                        if sources:
                            sources_line = "\n\n**Sources:** " + ", ".join(sources)
                            
                            # Update output text in all relevant attributes
                            if hasattr(output, "raw"):
                                output.raw = output_text + sources_line
                            if hasattr(output, "final_output"):
                                output.final_output = output_text + sources_line
                            if hasattr(output, "tasks_output") and isinstance(output.tasks_output, list):
                                for task_output in output.tasks_output:
                                    if hasattr(task_output, "output"):
                                        task_output.output = str(task_output.output) + sources_line
                
                except Exception as e:
                    # Silently fail source addition - don't break the response
                    print(f"Note: Could not add sources: {e}")
                
                return output
            
            def __getattr__(self, item):
                """Delegate all other attributes to inner crew"""
                return getattr(self._inner, item)
        
        return CrewWithSources(crew_instance)


# Convenience function for importing
def create_hierarchical_crew():
    """Factory function to create hierarchical crew"""
    return HrBotHierarchical().crew()
