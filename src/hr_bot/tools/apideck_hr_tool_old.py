"""
Production-Ready API Deck HR Integration Tool
Unified access to multiple HR platforms (SAP, Zoho People, BambooHR, etc.)
"""

import os
from typing import Optional, Dict, Any, List
from enum import Enum
import httpx
from pydantic import BaseModel, Field
from crewai.tools import BaseTool  # Correct import from crewai, not crewai_tools
import diskcache as dc
from datetime import datetime
import json


class HRPlatform(str, Enum):
    """Supported HR platforms via API Deck"""
    SAP_SUCCESS_FACTORS = "sap-successfactors"
    ZOHO_PEOPLE = "zoho-people"
    BAMBOO_HR = "bamboohr"
    WORKDAY = "workday"
    NAMELY = "namely"
    RIPPLING = "rippling"
    GUSTO = "gusto"
    ADP = "adp-workforce-now"
    PERSONIO = "personio"
    HIBOB = "hibob"


class APIDeckhHRToolInput(BaseModel):
    """Input schema for API Deck HR Tool"""
    query_type: str = Field(
        ...,
        description=(
            "Type of query to perform. Options: "
            "'employee' (get employee details), "
            "'employees_list' (list all employees), "
            "'department' (get department info), "
            "'time_off' (get time off/leave requests), "
            "'payroll' (get payroll info), "
            "'benefits' (get benefits info)"
        )
    )
    employee_id: Optional[str] = Field(
        None,
        description="Employee ID (required for employee-specific queries)"
    )
    filters: Optional[str] = Field(
        None,
        description="Optional JSON string with filters like department, date range, status"
    )


class APIDeckhHRTool(BaseTool):
    """
    Unified HR platform integration via API Deck
    Provides access to employee data, time off, payroll, and more across multiple HR systems
    """
    
    name: str = "HR System Data Access"
    description: str = (
        "Access live HR system data from connected HR platforms (SAP SuccessFactors, "
        "Zoho People, BambooHR, Workday, etc.). Use this tool to retrieve real-time "
        "employee information, time-off requests, department details, payroll data, "
        "and benefits information. Requires proper API configuration with your HR platform."
    )
    args_schema: type[BaseModel] = APIDeckhHRToolInput
    
    # Configuration
    api_key: str = Field(default="")
    app_id: str = Field(default="")
    service_id: str = Field(default="")
    consumer_id: str = Field(default="")
    base_url: str = Field(default="https://unify.apideck.com")
    cache_ttl: int = Field(default=1800)  # 30 minutes cache for HR data
    
    # Internal state
    _cache: Optional[dc.Cache] = None
    _client: Optional[httpx.Client] = None
    
    def __init__(self, **data):
        # Load from environment if not provided
        if not data.get("api_key"):
            data["api_key"] = os.getenv("APIDECK_API_KEY", "")
        if not data.get("app_id"):
            data["app_id"] = os.getenv("APIDECK_APP_ID", "")
        if not data.get("service_id"):
            data["service_id"] = os.getenv("APIDECK_SERVICE_ID", "")
        if not data.get("consumer_id"):
            data["consumer_id"] = os.getenv("APIDECK_CONSUMER_ID", "test-consumer")
        
        super().__init__(**data)
        self._initialize()
    
    def _initialize(self):
        """Initialize HTTP client and cache"""
        # Setup cache
        cache_dir = ".apideck_cache"
        os.makedirs(cache_dir, exist_ok=True)
        self._cache = dc.Cache(cache_dir)
        
        # Setup HTTP client with proper headers
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "X-APIDECK-APP-ID": self.app_id,
                "X-APIDECK-SERVICE-ID": self.service_id,
                "X-APIDECK-CONSUMER-ID": self.consumer_id,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
    
    def _make_request(
        self, 
        endpoint: str, 
        method: str = "GET", 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Apideck API with caching"""
        
        # Create cache key (only for GET requests)
        if method == "GET":
            cache_key = f"{method}:{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Make API request
        url = f"{self.base_url}/{endpoint}"
        
        try:
            with httpx.Client() as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=json_data,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                # Cache successful GET requests
                if method == "GET":
                    cache.set(cache_key, result, expire=1800)  # 30 minutes
                
                return result
                
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            return {
                "error": f"Request failed: {str(e)}"
            }
    
    def _get_employee(self, employee_id: str) -> Dict[str, Any]:
        """Get employee details by ID"""
        endpoint = f"/hris/employees/{employee_id}"
        return self._make_request("GET", endpoint)
    
    def _list_employees(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """List all employees with optional filters"""
        endpoint = "/hris/employees"
        params = filters or {}
        return self._make_request("GET", endpoint, params)
    
    def _get_department(self, department_id: str) -> Dict[str, Any]:
        """Get department details"""
        endpoint = f"/hris/departments/{department_id}"
        return self._make_request("GET", endpoint)
    
    def _get_time_off_requests(self, employee_id: Optional[str] = None) -> Dict[str, Any]:
        """Get time off requests"""
        endpoint = "/hris/time-off-requests"
        params = {}
        if employee_id:
            params["employee_id"] = employee_id
        return self._make_request("GET", endpoint, params)
    
    def _get_payroll(self, employee_id: Optional[str] = None) -> Dict[str, Any]:
        """Get payroll information"""
        endpoint = "/hris/payrolls"
        params = {}
        if employee_id:
            params["employee_id"] = employee_id
        return self._make_request("GET", endpoint, params)
    
    def _get_benefits(self, employee_id: Optional[str] = None) -> Dict[str, Any]:
        """Get benefits information"""
        endpoint = "/hris/employee-benefits"
        params = {}
        if employee_id:
            params["employee_id"] = employee_id
        return self._make_request("GET", endpoint, params)
    
    def _format_employee_data(self, data: Dict[str, Any]) -> str:
        """Format employee data for display"""
        if "error" in data:
            return f"❌ Error: {data['error']}"
        
        if "data" not in data:
            return "No employee data found"
        
        employee = data["data"]
        
        result = "👤 **Employee Information:**\n\n"
        result += f"**Name:** {employee.get('first_name', '')} {employee.get('last_name', '')}\n"
        result += f"**Email:** {employee.get('email', 'N/A')}\n"
        result += f"**Employee ID:** {employee.get('id', 'N/A')}\n"
        result += f"**Department:** {employee.get('department', 'N/A')}\n"
        result += f"**Job Title:** {employee.get('job_title', 'N/A')}\n"
        result += f"**Employment Type:** {employee.get('employment_type', 'N/A')}\n"
        result += f"**Status:** {employee.get('employment_status', 'N/A')}\n"
        result += f"**Start Date:** {employee.get('start_date', 'N/A')}\n"
        
        if employee.get('manager'):
            result += f"**Manager:** {employee['manager'].get('name', 'N/A')}\n"
        
        return result
    
    def _format_employees_list(self, data: Dict[str, Any]) -> str:
        """Format list of employees"""
        if "error" in data:
            return f"❌ Error: {data['error']}"
        
        if "data" not in data:
            return "No employees found"
        
        employees = data["data"]
        
        result = f"📋 **Employee List ({len(employees)} employees):**\n\n"
        
        for emp in employees[:20]:  # Limit to first 20 for readability
            result += f"• **{emp.get('first_name', '')} {emp.get('last_name', '')}**\n"
            result += f"  - ID: {emp.get('id', 'N/A')}\n"
            result += f"  - Title: {emp.get('job_title', 'N/A')}\n"
            result += f"  - Department: {emp.get('department', 'N/A')}\n"
            result += f"  - Email: {emp.get('email', 'N/A')}\n\n"
        
        if len(employees) > 20:
            result += f"\n... and {len(employees) - 20} more employees"
        
        return result
    
    def _format_time_off(self, data: Dict[str, Any]) -> str:
        """Format time off requests"""
        if "error" in data:
            return f"❌ Error: {data['error']}"
        
        if "data" not in data or not data["data"]:
            return "No time-off requests found"
        
        requests = data["data"]
        
        result = f"🏖️ **Time-Off Requests ({len(requests)} requests):**\n\n"
        
        for req in requests:
            result += f"**Request ID:** {req.get('id', 'N/A')}\n"
            result += f"**Employee:** {req.get('employee_id', 'N/A')}\n"
            result += f"**Type:** {req.get('type', 'N/A')}\n"
            result += f"**Start Date:** {req.get('start_date', 'N/A')}\n"
            result += f"**End Date:** {req.get('end_date', 'N/A')}\n"
            result += f"**Status:** {req.get('status', 'N/A')}\n"
            result += f"**Days:** {req.get('days', 'N/A')}\n\n"
            result += "---\n\n"
        
        return result
    
    def _format_generic_data(self, data: Dict[str, Any], title: str) -> str:
        """Format generic data response"""
        if "error" in data:
            return f"❌ Error: {data['error']}"
        
        if "data" not in data:
            return f"No {title.lower()} data found"
        
        return f"**{title}:**\n\n```json\n{json.dumps(data['data'], indent=2)}\n```"
    
    def _run(
        self,
        query_type: str,
        employee_id: Optional[str] = None,
        filters: Optional[str] = None
    ) -> str:
        """
        Execute HR system query
        
        Args:
            query_type: Type of query (employee, employees_list, department, etc.)
            employee_id: Employee ID for specific queries
            filters: JSON string with additional filters
            
        Returns:
            Formatted string with query results
        """
        # Validate configuration
        if not self.api_key or not self.app_id:
            return (
                "❌ API Deck not configured. Please set the following environment variables:\n"
                "- APIDECK_API_KEY: Your API Deck API key\n"
                "- APIDECK_APP_ID: Your API Deck application ID\n"
                "- APIDECK_SERVICE_ID: Your HR platform service ID\n\n"
                "Visit https://developers.apideck.com to get your credentials and connect your HR platform."
            )
        
        # Parse filters if provided
        filter_dict = {}
        if filters:
            try:
                filter_dict = json.loads(filters)
            except json.JSONDecodeError:
                return f"❌ Invalid filters JSON: {filters}"
        
        # Route to appropriate handler
        try:
            if query_type == "employee":
                if not employee_id:
                    return "❌ Employee ID required for employee query"
                data = self._get_employee(employee_id)
                return self._format_employee_data(data)
            
            elif query_type == "employees_list":
                data = self._list_employees(filter_dict)
                return self._format_employees_list(data)
            
            elif query_type == "department":
                dept_id = filter_dict.get("department_id")
                if not dept_id:
                    return "❌ Department ID required in filters"
                data = self._get_department(dept_id)
                return self._format_generic_data(data, "Department Information")
            
            elif query_type == "time_off":
                data = self._get_time_off_requests(employee_id)
                return self._format_time_off(data)
            
            elif query_type == "payroll":
                data = self._get_payroll(employee_id)
                return self._format_generic_data(data, "Payroll Information")
            
            elif query_type == "benefits":
                data = self._get_benefits(employee_id)
                return self._format_generic_data(data, "Benefits Information")
            
            else:
                return (
                    f"❌ Unknown query type: {query_type}\n"
                    "Supported types: employee, employees_list, department, time_off, payroll, benefits"
                )
        
        except Exception as e:
            return f"❌ Error executing query: {str(e)}"
    
    def __del__(self):
        """Cleanup HTTP client"""
        if self._client:
            self._client.close()


# Factory function
def create_apideck_hr_tool(**kwargs) -> APIDeckhHRTool:
    """Factory function to create APIDeckhHRTool instance"""
    return APIDeckhHRTool(**kwargs)
