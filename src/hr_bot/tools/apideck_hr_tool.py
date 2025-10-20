"""
Production-Ready Apideck HR Tool with Full CRUD Operations
Supports all Okta HRMS endpoints via Apideck unified API
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import httpx
import diskcache as dc
import json


class APIDeckhHRToolInput(BaseModel):
    """Input schema for Apideck HR Tool"""
    action: str = Field(
        ...,
        description="""Action to perform. Available actions:
        
        **COMPANIES:**
        - list_companies: Get all companies
        - get_company: Get specific company (requires resource_id)
        - create_company: Create new company (requires data)
        - update_company: Update company (requires resource_id and data)
        - delete_company: Delete company (requires resource_id)
        
        **DEPARTMENTS:**
        - list_departments: Get all departments
        - get_department: Get specific department (requires resource_id)
        - create_department: Create new department (requires data)
        - update_department: Update department (requires resource_id and data)
        - delete_department: Delete department (requires resource_id)
        
        **EMPLOYEES:**
        - list_employees: Get all employees
        - get_employee: Get specific employee (requires resource_id)
        - create_employee: Create new employee (requires data)
        - update_employee: Update employee (requires resource_id and data)
        - delete_employee: Delete employee (requires resource_id)
        
        **PAYROLL:**
        - list_payroll: Get all payroll records
        - get_payroll: Get specific payroll (requires resource_id)
        - list_employee_payrolls: Get employee's payroll history (requires resource_id)
        - get_employee_payroll: Get specific employee payroll (requires resource_id and payroll_id in filters)
        
        **SCHEDULES:**
        - list_employee_schedules: Get employee schedules (requires resource_id)
        
        **TIME OFF:**
        - list_time_off_requests: Get all time-off requests
        - get_time_off_request: Get specific request (requires resource_id)
        - create_time_off_request: Submit new request (requires data)
        - update_time_off_request: Update request (requires resource_id and data)
        - delete_time_off_request: Cancel request (requires resource_id)
        """
    )
    resource_id: Optional[str] = Field(
        None,
        description="Resource ID (employee_id, department_id, company_id, payroll_id, request_id)"
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Data payload for create/update operations (JSON format)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Query parameters and filters (e.g., {'limit': 10, 'cursor': 'abc'})"
    )


class APIDeckhHRTool(BaseTool):
    """
    Full-featured HR system integration via Apideck unified API
    Provides complete CRUD operations for Okta HRMS
    """
    
    name: str = "HR System Operations"
    description: str = """Perform comprehensive HR operations via Apideck unified API connected to Okta HRMS.
    
    This tool provides full CRUD (Create, Read, Update, Delete) capabilities for:
    - Companies: List, get, create, update, delete
    - Departments: List, get, create, update, delete
    - Employees: List, get, create, update, delete
    - Payroll: List, get employee payrolls
    - Schedules: List employee schedules
    - Time Off: List, get, create, update, delete requests
    
    Use this for ANY HR-related operations like viewing employee data, applying for leave,
    updating records, managing departments, etc.
    """
    args_schema: type[BaseModel] = APIDeckhHRToolInput
    
    # Configuration
    api_key: str = Field(default="")
    app_id: str = Field(default="")
    service_id: str = Field(default="")
    consumer_id: str = Field(default="")
    base_url: str = Field(default="https://unify.apideck.com")
    
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
            data["service_id"] = os.getenv("APIDECK_SERVICE_ID", "okta")
        if not data.get("consumer_id"):
            data["consumer_id"] = os.getenv("APIDECK_CONSUMER_ID", "test-consumer")
        
        super().__init__(**data)
        self._initialize()
    
    def _initialize(self):
        """Initialize HTTP client and cache"""
        cache_dir = ".apideck_cache"
        os.makedirs(cache_dir, exist_ok=True)
        self._cache = dc.Cache(cache_dir)
        
        self._client = httpx.Client(
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
            cached_result = self._cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Make API request
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "x-apideck-app-id": self.app_id,
            "x-apideck-service-id": self.service_id,
            "x-apideck-consumer-id": self.consumer_id,
            "Content-Type": "application/json",
        }
        
        try:
            response = self._client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
            response.raise_for_status()
            result = response.json()
            
            # Cache successful GET requests
            if method == "GET":
                self._cache.set(cache_key, result, expire=1800)  # 30 minutes
            
            return result
            
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            return {
                "error": f"Request failed: {str(e)}"
            }
    
    # ========== COMPANY OPERATIONS ==========
    
    def _list_companies(self, filters: Optional[Dict] = None) -> str:
        """List all companies"""
        result = self._make_request("hris/companies", params=filters)
        if "error" in result:
            return f"❌ Error listing companies: {result['error']}"
        
        companies = result.get("data", [])
        output = f"🏢 **Companies ({len(companies)}):**\n\n"
        for company in companies:
            output += f"• **{company.get('legal_name', 'N/A')}**\n"
            output += f"  - ID: {company.get('id', 'N/A')}\n"
            output += f"  - Status: {company.get('status', 'N/A')}\n\n"
        return output
    
    def _get_company(self, company_id: str) -> str:
        """Get specific company details"""
        if not company_id:
            return "❌ Company ID required"
        result = self._make_request(f"hris/companies/{company_id}")
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        company = result.get("data", {})
        output = "🏢 **Company Details:**\n\n"
        output += f"**Name:** {company.get('legal_name', 'N/A')}\n"
        output += f"**ID:** {company.get('id', 'N/A')}\n"
        output += f"**Status:** {company.get('status', 'N/A')}\n"
        output += f"**Country:** {company.get('country', 'N/A')}\n"
        return output
    
    def _create_company(self, data: Dict) -> str:
        """Create new company"""
        if not data:
            return "❌ Company data required"
        result = self._make_request("hris/companies", method="POST", json_data=data)
        if "error" in result:
            return f"❌ Error creating company: {result['error']}"
        return f"✅ Company created successfully! ID: {result.get('data', {}).get('id', 'N/A')}"
    
    def _update_company(self, company_id: str, data: Dict) -> str:
        """Update company information"""
        if not company_id or not data:
            return "❌ Company ID and data required"
        result = self._make_request(f"hris/companies/{company_id}", method="PUT", json_data=data)
        if "error" in result:
            return f"❌ Error updating company: {result['error']}"
        return "✅ Company updated successfully!"
    
    def _delete_company(self, company_id: str) -> str:
        """Delete company"""
        if not company_id:
            return "❌ Company ID required"
        result = self._make_request(f"hris/companies/{company_id}", method="DELETE")
        if "error" in result:
            return f"❌ Error deleting company: {result['error']}"
        return "✅ Company deleted successfully!"
    
    # ========== DEPARTMENT OPERATIONS ==========
    
    def _list_departments(self, filters: Optional[Dict] = None) -> str:
        """List all departments"""
        result = self._make_request("hris/departments", params=filters)
        if "error" in result:
            return f"❌ Error listing departments: {result['error']}"
        
        departments = result.get("data", [])
        output = f"🏛️ **Departments ({len(departments)}):**\n\n"
        for dept in departments:
            output += f"• **{dept.get('name', 'N/A')}**\n"
            output += f"  - ID: {dept.get('id', 'N/A')}\n"
            output += f"  - Status: {dept.get('status', 'N/A')}\n\n"
        return output
    
    def _get_department(self, dept_id: str) -> str:
        """Get specific department details"""
        if not dept_id:
            return "❌ Department ID required"
        result = self._make_request(f"hris/departments/{dept_id}")
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        dept = result.get("data", {})
        output = "🏛️ **Department Details:**\n\n"
        output += f"**Name:** {dept.get('name', 'N/A')}\n"
        output += f"**ID:** {dept.get('id', 'N/A')}\n"
        output += f"**Status:** {dept.get('status', 'N/A')}\n"
        return output
    
    def _create_department(self, data: Dict) -> str:
        """Create new department"""
        if not data:
            return "❌ Department data required"
        result = self._make_request("hris/departments", method="POST", json_data=data)
        if "error" in result:
            return f"❌ Error creating department: {result['error']}"
        return f"✅ Department created successfully! ID: {result.get('data', {}).get('id', 'N/A')}"
    
    def _update_department(self, dept_id: str, data: Dict) -> str:
        """Update department information"""
        if not dept_id or not data:
            return "❌ Department ID and data required"
        result = self._make_request(f"hris/departments/{dept_id}", method="PUT", json_data=data)
        if "error" in result:
            return f"❌ Error updating department: {result['error']}"
        return "✅ Department updated successfully!"
    
    def _delete_department(self, dept_id: str) -> str:
        """Delete department"""
        if not dept_id:
            return "❌ Department ID required"
        result = self._make_request(f"hris/departments/{dept_id}", method="DELETE")
        if "error" in result:
            return f"❌ Error deleting department: {result['error']}"
        return "✅ Department deleted successfully!"
    
    # ========== EMPLOYEE OPERATIONS ==========
    
    def _list_employees(self, filters: Optional[Dict] = None) -> str:
        """List all employees"""
        result = self._make_request("hris/employees", params=filters)
        if "error" in result:
            return f"❌ Error listing employees: {result['error']}"
        
        employees = result.get("data", [])
        output = f"👥 **Employees ({len(employees)}):**\n\n"
        for emp in employees[:20]:  # Limit to 20 for readability
            output += f"• **{emp.get('first_name', '')} {emp.get('last_name', '')}**\n"
            output += f"  - ID: {emp.get('id', 'N/A')}\n"
            output += f"  - Email: {emp.get('email', 'N/A')}\n"
            output += f"  - Title: {emp.get('job_title', 'N/A')}\n\n"
        
        if len(employees) > 20:
            output += f"\n... and {len(employees) - 20} more employees"
        return output
    
    def _get_employee(self, emp_id: str) -> str:
        """Get specific employee details"""
        if not emp_id:
            return "❌ Employee ID required"
        result = self._make_request(f"hris/employees/{emp_id}")
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        emp = result.get("data", {})
        output = "👤 **Employee Details:**\n\n"
        output += f"**Name:** {emp.get('first_name', '')} {emp.get('last_name', '')}\n"
        output += f"**Email:** {emp.get('email', 'N/A')}\n"
        output += f"**ID:** {emp.get('id', 'N/A')}\n"
        output += f"**Job Title:** {emp.get('job_title', 'N/A')}\n"
        output += f"**Department:** {emp.get('department', 'N/A')}\n"
        output += f"**Employment Status:** {emp.get('employment_status', 'N/A')}\n"
        output += f"**Start Date:** {emp.get('start_date', 'N/A')}\n"
        return output
    
    def _create_employee(self, data: Dict) -> str:
        """Create new employee"""
        if not data:
            return "❌ Employee data required"
        result = self._make_request("hris/employees", method="POST", json_data=data)
        if "error" in result:
            return f"❌ Error creating employee: {result['error']}"
        return f"✅ Employee created successfully! ID: {result.get('data', {}).get('id', 'N/A')}"
    
    def _update_employee(self, emp_id: str, data: Dict) -> str:
        """Update employee information"""
        if not emp_id or not data:
            return "❌ Employee ID and data required"
        result = self._make_request(f"hris/employees/{emp_id}", method="PUT", json_data=data)
        if "error" in result:
            return f"❌ Error updating employee: {result['error']}"
        return "✅ Employee updated successfully!"
    
    def _delete_employee(self, emp_id: str) -> str:
        """Delete employee"""
        if not emp_id:
            return "❌ Employee ID required"
        result = self._make_request(f"hris/employees/{emp_id}", method="DELETE")
        if "error" in result:
            return f"❌ Error deleting employee: {result['error']}"
        return "✅ Employee deleted successfully!"
    
    # ========== PAYROLL OPERATIONS ==========
    
    def _list_payroll(self, filters: Optional[Dict] = None) -> str:
        """List all payroll records"""
        result = self._make_request("hris/payrolls", params=filters)
        if "error" in result:
            return f"❌ Error listing payroll: {result['error']}"
        
        payrolls = result.get("data", [])
        output = f"💰 **Payroll Records ({len(payrolls)}):**\n\n"
        for payroll in payrolls:
            output += f"• **Payroll ID:** {payroll.get('id', 'N/A')}\n"
            output += f"  - Period: {payroll.get('start_date', 'N/A')} to {payroll.get('end_date', 'N/A')}\n\n"
        return output
    
    def _get_payroll(self, payroll_id: str) -> str:
        """Get specific payroll details"""
        if not payroll_id:
            return "❌ Payroll ID required"
        result = self._make_request(f"hris/payrolls/{payroll_id}")
        if "error" in result:
            return f"❌ Error: {result['error']}"
        return f"💰 **Payroll Details:**\n\n```json\n{json.dumps(result.get('data', {}), indent=2)}\n```"
    
    def _list_employee_payrolls(self, emp_id: str, filters: Optional[Dict] = None) -> str:
        """Get employee's payroll history"""
        if not emp_id:
            return "❌ Employee ID required"
        result = self._make_request(f"hris/employees/{emp_id}/payrolls", params=filters)
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        payrolls = result.get("data", [])
        output = f"💰 **Employee Payroll History ({len(payrolls)}):**\n\n"
        for payroll in payrolls:
            output += f"• Period: {payroll.get('start_date', 'N/A')} to {payroll.get('end_date', 'N/A')}\n"
            output += f"  - Amount: {payroll.get('gross_pay', 'N/A')}\n\n"
        return output
    
    def _get_employee_payroll(self, emp_id: str, filters: Optional[Dict] = None) -> str:
        """Get specific employee payroll"""
        if not emp_id:
            return "❌ Employee ID required"
        payroll_id = filters.get("payroll_id") if filters else None
        if not payroll_id:
            return "❌ Payroll ID required in filters"
        result = self._make_request(f"hris/employees/{emp_id}/payrolls/{payroll_id}")
        if "error" in result:
            return f"❌ Error: {result['error']}"
        return f"💰 **Employee Payroll:**\n\n```json\n{json.dumps(result.get('data', {}), indent=2)}\n```"
    
    # ========== SCHEDULE OPERATIONS ==========
    
    def _list_employee_schedules(self, emp_id: str, filters: Optional[Dict] = None) -> str:
        """List employee schedules"""
        if not emp_id:
            return "❌ Employee ID required"
        result = self._make_request(f"hris/employees/{emp_id}/schedules", params=filters)
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        schedules = result.get("data", [])
        output = f"📅 **Employee Schedules ({len(schedules)}):**\n\n"
        for schedule in schedules:
            output += f"• **Date:** {schedule.get('date', 'N/A')}\n"
            output += f"  - Start: {schedule.get('start_time', 'N/A')}\n"
            output += f"  - End: {schedule.get('end_time', 'N/A')}\n\n"
        return output
    
    # ========== TIME-OFF OPERATIONS ==========
    
    def _list_time_off_requests(self, filters: Optional[Dict] = None) -> str:
        """List all time-off requests"""
        result = self._make_request("hris/time-off-requests", params=filters)
        if "error" in result:
            return f"❌ Error listing time-off requests: {result['error']}"
        
        requests = result.get("data", [])
        output = f"🏖️ **Time-Off Requests ({len(requests)}):**\n\n"
        for req in requests:
            output += f"• **Request ID:** {req.get('id', 'N/A')}\n"
            output += f"  - Employee: {req.get('employee_id', 'N/A')}\n"
            output += f"  - Type: {req.get('type', 'N/A')}\n"
            output += f"  - Dates: {req.get('start_date', 'N/A')} to {req.get('end_date', 'N/A')}\n"
            output += f"  - Status: {req.get('status', 'N/A')}\n\n"
        return output
    
    def _get_time_off_request(self, request_id: str) -> str:
        """Get specific time-off request"""
        if not request_id:
            return "❌ Request ID required"
        result = self._make_request(f"hris/time-off-requests/{request_id}")
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        req = result.get("data", {})
        output = "🏖️ **Time-Off Request Details:**\n\n"
        output += f"**Request ID:** {req.get('id', 'N/A')}\n"
        output += f"**Employee:** {req.get('employee_id', 'N/A')}\n"
        output += f"**Type:** {req.get('type', 'N/A')}\n"
        output += f"**Start Date:** {req.get('start_date', 'N/A')}\n"
        output += f"**End Date:** {req.get('end_date', 'N/A')}\n"
        output += f"**Status:** {req.get('status', 'N/A')}\n"
        output += f"**Days:** {req.get('days', 'N/A')}\n"
        return output
    
    def _create_time_off_request(self, data: Dict) -> str:
        """Create new time-off request"""
        if not data:
            return "❌ Time-off request data required"
        result = self._make_request("hris/time-off-requests", method="POST", json_data=data)
        if "error" in result:
            return f"❌ Error creating time-off request: {result['error']}"
        return f"✅ Time-off request submitted successfully! ID: {result.get('data', {}).get('id', 'N/A')}"
    
    def _update_time_off_request(self, request_id: str, data: Dict) -> str:
        """Update time-off request"""
        if not request_id or not data:
            return "❌ Request ID and data required"
        result = self._make_request(f"hris/time-off-requests/{request_id}", method="PUT", json_data=data)
        if "error" in result:
            return f"❌ Error updating time-off request: {result['error']}"
        return "✅ Time-off request updated successfully!"
    
    def _delete_time_off_request(self, request_id: str) -> str:
        """Delete/cancel time-off request"""
        if not request_id:
            return "❌ Request ID required"
        result = self._make_request(f"hris/time-off-requests/{request_id}", method="DELETE")
        if "error" in result:
            return f"❌ Error deleting time-off request: {result['error']}"
        return "✅ Time-off request cancelled successfully!"
    
    # ========== MAIN RUN METHOD ==========
    
    def _run(
        self,
        action: str,
        resource_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute HR operations via Apideck API"""
        
        # Validate configuration
        if not self.api_key or not self.app_id:
            return (
                "❌ Apideck not configured. Please set:\n"
                "- APIDECK_API_KEY\n"
                "- APIDECK_APP_ID\n"
                "- APIDECK_CONSUMER_ID\n"
                "- APIDECK_SERVICE_ID"
            )
        
        # Route to appropriate handler
        try:
            # Company operations
            if action == "list_companies":
                return self._list_companies(filters)
            elif action == "get_company":
                return self._get_company(resource_id)
            elif action == "create_company":
                return self._create_company(data)
            elif action == "update_company":
                return self._update_company(resource_id, data)
            elif action == "delete_company":
                return self._delete_company(resource_id)
            
            # Department operations
            elif action == "list_departments":
                return self._list_departments(filters)
            elif action == "get_department":
                return self._get_department(resource_id)
            elif action == "create_department":
                return self._create_department(data)
            elif action == "update_department":
                return self._update_department(resource_id, data)
            elif action == "delete_department":
                return self._delete_department(resource_id)
            
            # Employee operations
            elif action == "list_employees":
                return self._list_employees(filters)
            elif action == "get_employee":
                return self._get_employee(resource_id)
            elif action == "create_employee":
                return self._create_employee(data)
            elif action == "update_employee":
                return self._update_employee(resource_id, data)
            elif action == "delete_employee":
                return self._delete_employee(resource_id)
            
            # Payroll operations
            elif action == "list_payroll":
                return self._list_payroll(filters)
            elif action == "get_payroll":
                return self._get_payroll(resource_id)
            elif action == "list_employee_payrolls":
                return self._list_employee_payrolls(resource_id, filters)
            elif action == "get_employee_payroll":
                return self._get_employee_payroll(resource_id, filters)
            
            # Schedule operations
            elif action == "list_employee_schedules":
                return self._list_employee_schedules(resource_id, filters)
            
            # Time-off operations
            elif action == "list_time_off_requests":
                return self._list_time_off_requests(filters)
            elif action == "get_time_off_request":
                return self._get_time_off_request(resource_id)
            elif action == "create_time_off_request":
                return self._create_time_off_request(data)
            elif action == "update_time_off_request":
                return self._update_time_off_request(resource_id, data)
            elif action == "delete_time_off_request":
                return self._delete_time_off_request(resource_id)
            
            else:
                return f"❌ Unknown action: {action}. See tool description for available actions."
        
        except Exception as e:
            return f"❌ Error executing {action}: {str(e)}"
    
    def __del__(self):
        """Cleanup HTTP client"""
        if self._client:
            self._client.close()


def create_apideck_hr_tool(**kwargs) -> APIDeckhHRTool:
    """Factory function to create APIDeckhHRTool instance"""
    return APIDeckhHRTool(**kwargs)
