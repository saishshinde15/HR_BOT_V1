"""
Master Actions Tool - Procedural Actions with Links & Steps
Handles queries about HOW TO perform actions in HR systems (DarwinBox, SumTotal, etc.)
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import re


@dataclass
class ActionGuide:
    """Structured action with link and steps"""
    action_name: str
    link: str
    steps: List[str]
    keywords: List[str]  # For matching queries


class MasterActionsDatabase:
    """In-memory structured database of procedural actions"""
    
    def __init__(self):
        self.actions: List[ActionGuide] = [
            ActionGuide(
                action_name="Apply Leave",
                link="https://www.darwinbox.com/demo-company/leaves",
                steps=[
                    "Click on the mentioned link",
                    "Select 'Apply Leave'",
                    "Select leave type, enter reason (if any) and duration",
                    "Hit 'Apply' and note request ID"
                ],
                keywords=[
                    "apply leave", "request leave", "take leave", "book leave",
                    "submit leave", "leave application", "leave request",
                    "annual leave", "vacation", "time off"
                ]
            ),
            ActionGuide(
                action_name="View Leave Balance",
                link="https://www.darwinbox.com/demo-company/leave-balance",
                steps=[
                    "Click on the mentioned link",
                    "Sign in if prompted",
                    "Go to 'Leave Balance' or 'My Entitlements'",
                    "View available balances by leave type"
                ],
                keywords=[
                    "leave balance", "remaining leave", "leave entitlement",
                    "check leave", "how much leave", "leave quota",
                    "days left", "available leave"
                ]
            ),
            ActionGuide(
                action_name="Download Payslip",
                link="https://www.darwinbox.com/demo-company/payroll/payslips",
                steps=[
                    "Click on the mentioned link",
                    "Navigate to 'Payslips' or 'Salary Statements'",
                    "Select month and year required",
                    "Click 'Download' or 'View PDF'"
                ],
                keywords=[
                    "payslip", "salary slip", "pay statement", "download payslip",
                    "payroll", "salary statement", "wage slip", "payment proof"
                ]
            ),
            ActionGuide(
                action_name="Update Personal Details",
                link="https://www.darwinbox.com/demo-company/profile/edit",
                steps=[
                    "Click on the mentioned link",
                    "Open 'Personal Details' or 'Edit Profile'",
                    "Update fields (address, phone, emergency contact, bank details)",
                    "Save changes and confirm via verification prompt if any"
                ],
                keywords=[
                    "update details", "change address", "update phone", "personal information",
                    "edit profile", "update profile", "change details", "emergency contact",
                    "bank details", "update bank"
                ]
            ),
            ActionGuide(
                action_name="Enroll in Mandatory Training",
                link="https://sumtotal.demo-company.com/learning/my-learning",
                steps=[
                    "Click on the mentioned link",
                    "Sign in if required",
                    "Search or open the assigned course under 'Assigned' or 'Recommended'",
                    "Click 'Enroll' or 'Start' and follow module instructions"
                ],
                keywords=[
                    "training", "course", "enroll training", "mandatory training",
                    "learning", "certification", "compliance training", "elearning",
                    "online course", "module"
                ]
            )
        ]
    
    def search_actions(self, query: str) -> List[ActionGuide]:
        """
        Search for relevant actions based on query keywords
        Uses fuzzy matching for better recall
        """
        query_lower = query.lower()
        query_tokens = set(re.findall(r'\b\w+\b', query_lower))
        
        matches = []
        for action in self.actions:
            # Calculate match score based on keyword overlap
            score = 0
            for keyword in action.keywords:
                keyword_tokens = set(re.findall(r'\b\w+\b', keyword.lower()))
                overlap = len(query_tokens & keyword_tokens)
                if overlap > 0:
                    score += overlap
            
            if score > 0:
                matches.append((score, action))
        
        # Sort by score (descending) and return actions
        matches.sort(key=lambda x: x[0], reverse=True)
        return [action for _, action in matches]


class MasterActionsToolInput(BaseModel):
    """Input schema for Master Actions Tool"""
    query: str = Field(
        ...,
        description="The query about HOW TO perform an action (e.g., 'how to apply leave', 'download payslip')"
    )


class MasterActionsTool(BaseTool):
    """
    Master Actions Tool - Provides step-by-step procedural guidance with links
    
    Use this tool when users ask HOW TO perform specific actions like:
    - Applying for leave
    - Downloading payslips
    - Updating personal details
    - Enrolling in training
    - Checking leave balance
    
    This tool returns direct links and step-by-step instructions.
    """
    
    name: str = "master_actions_guide"
    description: str = (
        "Provides step-by-step instructions with direct links for performing HR system actions. "
        "Use this tool when the user asks HOW TO do something specific like: "
        "apply leave, download payslip, update profile, enroll in training, check leave balance. "
        "Returns actionable links and clear step-by-step procedures."
    )
    args_schema: type[BaseModel] = MasterActionsToolInput
    
    database: MasterActionsDatabase = Field(default=None, exclude=True)
    
    def __init__(self, **kwargs):
        database_instance = MasterActionsDatabase()
        kwargs['database'] = database_instance
        super().__init__(**kwargs)
        
        # Initialize _last_sources
        object.__setattr__(self, '_last_sources', [])
    
    def _run(self, query: str) -> str:
        """
        Execute search for procedural actions
        
        Args:
            query: User's query about HOW TO perform an action
            
        Returns:
            Formatted string with links and steps, or "NO_ACTION_FOUND"
        """
        try:
            # Search for matching actions
            matching_actions = self.database.search_actions(query)
            
            if not matching_actions:
                return "NO_ACTION_FOUND"
            
            # Format output
            output = f"Found {len(matching_actions)} relevant action(s):\n\n"
            
            sources = []
            for idx, action in enumerate(matching_actions, 1):
                output += f"**{idx}. {action.action_name}**\n"
                output += f"🔗 Link: {action.link}\n\n"
                output += "**Steps:**\n"
                for step_num, step in enumerate(action.steps, 1):
                    output += f"   {step_num}. {step}\n"
                output += "\n"
                
                sources.append(f"[{idx}] {action.action_name}")
            
            # Store sources
            object.__setattr__(self, '_last_sources', sources)
            output += "Sources: Master Actions Guide - " + ", ".join(sources) + "\n"
            
            return output
            
        except Exception as e:
            return f"Error searching actions: {str(e)}"
    
    def last_sources(self) -> List[str]:
        """Return the most recent set of sources emitted by the tool."""
        try:
            return list(object.__getattribute__(self, '_last_sources'))
        except AttributeError:
            return []
