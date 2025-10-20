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
    Production-grade Hierarchical HR Bot with specialized agents:
    
    1. HR Manager (Orchestrator):
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
    - Manager delegates tasks to specialists
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
        
        # LLM for manager (higher temperature for better delegation)
        self.manager_llm = LLM(
            model=os.getenv("GEMINI_MODEL", "gemini/gemini-2.0-flash-lite-001"),
            temperature=0.4,  # Slightly higher for better reasoning
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
        No tools - delegates all work to specialists
        """
        return Agent(
            config=self.agents_config['hr_manager'],
            tools=[],  # Manager doesn't use tools directly - only delegates
            llm=self.manager_llm,
            verbose=True,
            max_iter=10,  # More iterations for complex delegation
            memory=True,
            allow_delegation=True,  # CRITICAL: Enables delegation to other agents
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
    def analyze_and_respond_task(self) -> Task:
        """
        Main manager task - analyzes query and coordinates specialists
        Manager will use delegation to work with specialists
        """
        return Task(
            description="""
            Employee Query: {query}
            
            Analyze this employee's query carefully and understand what they truly need.
            
            **Step 1: Understand Query Intent**
            
            Ask yourself: What does the employee really want?
            
            A) INFORMATION REQUEST (Policy/Procedure Question)
               - "What is the sick leave policy?"
               - "How much parental leave do I get?"
               - "What are the benefits for..."
               - "Am I eligible for..."
               - "How do I apply for..."
               → Employee wants to KNOW/UNDERSTAND something
               → Delegate ONLY to "HR Policy Expert and Document Specialist"
            
            B) ACTION REQUEST (System Operation)
               - "Update my email"
               - "Apply for leave"
               - "Change my department"
               - "Create/delete/modify..."
               → Employee wants to DO/CHANGE something in the system
               → Delegate ONLY to "HRMS Operations Expert and System Administrator"
            
            C) EXPLORATORY QUESTION (Information First, Action Maybe Later)
               - "Can I take leave next week?"
               - "I'm having a baby, what do I do?"
               → Employee is EXPLORING options, not ready to take action yet
               → Delegate ONLY to "HR Policy Expert and Document Specialist"
               → Let them get the information they need FIRST
               → If they come back asking to actually apply/take action, THEN involve HRMS
            
            **Step 2: Delegate to ONE Specialist**
            
            CRITICAL: Do NOT delegate to both specialists unless the employee explicitly asks for BOTH information AND action in the same request.
            
            **For Policy Questions:**
            Ask coworker="HR Policy Expert and Document Specialist" with the full context of what the employee wants to know.
            
            **For System Operations:**
            Ask coworker="HRMS Operations Expert and System Administrator" with specific details about what operation to perform.
            
            **Step 3: Present Response**
            
            When you receive the specialist's answer:
            - Present it warmly and clearly to the employee
            - Add any helpful context if needed
            - If the employee's situation requires follow-up action, suggest it naturally
            - Maintain the caring, human tone from the specialist
            
            **Examples:**
            
            Query: "What is sick leave policy?"
            → ONLY delegate to HR Policy Expert
            → Present their detailed, caring response
            
            Query: "Update my email to john@example.com"
            → ONLY delegate to HRMS Specialist
            → Confirm the update was successful
            
            Query: "Can I take parental leave?"
            → ONLY delegate to HR Policy Expert (they're exploring options)
            → Present policy details
            → Suggest: "Once you're ready to apply, I can help you submit the request!"
            
            Query: "I want to apply for parental leave AND update my contact info"
            → NOW delegate to BOTH (explicit request for both)
            → Get policy from HR Policy Expert
            → Execute update with HRMS Specialist
            """,
            expected_output="""
            A warm, comprehensive response that:
            - Directly answers the employee's question
            - Maintains a caring, human tone
            - Provides complete information with sources (for policy questions)
            - Confirms actions taken (for system operations)
            - Suggests helpful next steps when appropriate
            - Makes the employee feel supported and informed
            """,
            # NO agent assignment - this task goes to manager by default in hierarchical mode
        )
    
    @task
    def search_policy_task(self) -> Task:
        """
        Policy search task - for policy specialist
        Not directly invoked - manager delegates here
        """
        return Task(
            config=self.tasks_config['search_policy_documents'],
        )
    
    @task
    def hrms_operations_task(self) -> Task:
        """
        HRMS operations task - for HRMS specialist  
        Not directly invoked - manager delegates here
        """
        return Task(
            config=self.tasks_config['execute_hrms_operations'],
        )
    
    @crew
    def crew(self) -> Crew:
        """
        Creates the hierarchical HR Bot crew
        
        HIERARCHICAL DELEGATION ARCHITECTURE:
        
        How it works:
        1. User asks: "What is sick leave policy?" (STATIC - from documents)
           → Manager receives query in analyze_and_respond_task
           → Manager delegates to "HR Policy Expert and Document Specialist"
           → Policy specialist uses RAG tool to search documents
           → Manager synthesizes response
        
        2. User asks: "Update my department" (DYNAMIC - system changes)
           → Manager receives query in analyze_and_respond_task
           → Manager delegates to "HRMS Operations Expert and System Administrator"
           → HRMS specialist uses Apideck tool to modify system
           → Manager confirms operation
        
        IMPORTANT: Only ONE task in hierarchical mode - the manager's task.
        Manager uses delegation (coworker=) to work with specialists.
        """
        
        # Create agent instances
        manager_agent = self.hr_manager()
        policy_agent = self.policy_specialist()
        hrms_agent = self.hrms_specialist()

        # Create ONLY the manager's task
        manager_task = self.analyze_and_respond_task()

        # Create crew with hierarchical process
        crew_instance = Crew(
            agents=[
                policy_agent,  # Has RAG tool - for static policy queries
                hrms_agent,    # Has Apideck tool - for dynamic system operations
            ],
            tasks=[
                manager_task,  # Manager's task - will delegate to specialists as needed
            ],
            process=Process.hierarchical,
            manager_agent=manager_agent,  # Analyzes query and delegates to right specialist
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
