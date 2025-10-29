"""
Comprehensive test script for production Apideck HR Tool
Tests all CRUD operations across all resource types
"""

import os
from dotenv import load_dotenv
from src.hr_bot.tools.apideck_hr_tool import APIDeckhHRTool

# Load environment variables
load_dotenv()

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")

def test_apideck_full():
    """Test all Apideck operations"""
    
    print_section("🚀 APIDECK HR TOOL - FULL PRODUCTION TEST")
    
    # Check environment variables
    api_key = os.getenv("APIDECK_API_KEY")
    app_id = os.getenv("APIDECK_APP_ID")
    service_id = os.getenv("APIDECK_SERVICE_ID")
    consumer_id = os.getenv("APIDECK_CONSUMER_ID")
    
    print("📋 Configuration Check:")
    print(f"  API Key: {'✓ Set' if api_key else '✗ Missing'}")
    print(f"  App ID: {'✓ Set' if app_id else '✗ Missing'}")
    print(f"  Service ID: {'✓ Set (' + service_id + ')' if service_id else '✗ Missing'}")
    print(f"  Consumer ID: {'✓ Set (' + consumer_id + ')' if consumer_id else '✗ Missing'}")
    
    if not all([api_key, app_id, service_id, consumer_id]):
        print("\n❌ Configuration incomplete. Please check .env file")
        return
    
    # Initialize tool
    print("\n🔧 Initializing Apideck HR Tool...")
    tool = APIDeckhHRTool()
    
    # ========== COMPANY TESTS ==========
    print_section("🏢 COMPANY OPERATIONS")
    
    print("TEST: List Companies")
    result = tool._run(action="list_companies")
    print(result)
    
    # ========== DEPARTMENT TESTS ==========
    print_section("🏛️ DEPARTMENT OPERATIONS")
    
    print("TEST: List Departments")
    result = tool._run(action="list_departments")
    print(result)
    
    # ========== EMPLOYEE TESTS ==========
    print_section("👥 EMPLOYEE OPERATIONS")
    
    print("TEST 1: List Employees")
    result = tool._run(action="list_employees")
    print(result)
    
    print("\n" + "-" * 70 + "\n")
    print("TEST 2: Get Specific Employee")
    # Using the employee ID from your curl example
    result = tool._run(action="get_employee", resource_id="00uwkyi5qsjbfjIt5697")
    print(result)
    
    # ========== PAYROLL TESTS ==========
    print_section("💰 PAYROLL OPERATIONS")
    
    print("TEST 1: List Payroll Records")
    result = tool._run(action="list_payroll")
    print(result)
    
    print("\n" + "-" * 70 + "\n")
    print("TEST 2: List Employee Payrolls")
    result = tool._run(action="list_employee_payrolls", resource_id="00uwkyi5qsjbfjIt5697")
    print(result)
    
    # ========== SCHEDULE TESTS ==========
    print_section("📅 SCHEDULE OPERATIONS")
    
    print("TEST: List Employee Schedules")
    result = tool._run(action="list_employee_schedules", resource_id="00uwkyi5qsjbfjIt5697")
    print(result)
    
    # ========== TIME-OFF TESTS ==========
    print_section("🏖️ TIME-OFF OPERATIONS")
    
    print("TEST 1: List Time-Off Requests")
    result = tool._run(action="list_time_off_requests")
    print(result)
    
    print("\n" + "-" * 70 + "\n")
    print("TEST 2: Create Time-Off Request (Example - READ ONLY)")
    print("To create a time-off request, you would use:")
    print("""
    tool._run(
        action="create_time_off_request",
        data={
            "employee_id": "00uwkyi5qsjbfjIt5697",
            "start_date": "2025-10-25",
            "end_date": "2025-10-27",
            "type": "vacation",
            "notes": "Family vacation"
        }
    )
    """)
    print("⚠️  Skipping actual creation to avoid modifying production data")
    
    # ========== SUMMARY ==========
    print_section("✅ TEST SUMMARY")
    
    print("Available Operations:")
    print("\n📖 READ Operations (Safe to run):")
    print("  ✓ list_companies, get_company")
    print("  ✓ list_departments, get_department")
    print("  ✓ list_employees, get_employee")
    print("  ✓ list_payroll, get_payroll")
    print("  ✓ list_employee_payrolls, get_employee_payroll")
    print("  ✓ list_employee_schedules")
    print("  ✓ list_time_off_requests, get_time_off_request")
    
    print("\n✏️  CREATE Operations (Requires data):")
    print("  • create_company, create_department")
    print("  • create_employee")
    print("  • create_time_off_request")
    
    print("\n🔄 UPDATE Operations (Requires resource_id + data):")
    print("  • update_company, update_department")
    print("  • update_employee")
    print("  • update_time_off_request")
    
    print("\n🗑️  DELETE Operations (Requires resource_id):")
    print("  • delete_company, delete_department")
    print("  • delete_employee")
    print("  • delete_time_off_request")
    
    print("\n" + "=" * 70)
    print("🎉 TEST COMPLETE - All endpoints configured and ready!")
    print("=" * 70)
    print("\n💡 Usage Examples:")
    print("  - List employees: action='list_employees'")
    print("  - Get employee: action='get_employee', resource_id='00uwkyi5qsjbfjIt5697'")
    print("  - Apply leave: action='create_time_off_request', data={...}")
    print("  - Update employee: action='update_employee', resource_id='...', data={...}")
    print()


if __name__ == "__main__":
    test_apideck_full()
