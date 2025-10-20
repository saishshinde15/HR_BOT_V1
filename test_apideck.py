"""
Test script for Apideck HR integration
Tests connection and basic functionality
"""

import os
from dotenv import load_dotenv
from src.hr_bot.tools.apideck_hr_tool import APIDeckhHRTool

# Load environment variables
load_dotenv()

def test_apideck_connection():
    """Test Apideck connection and configuration"""
    
    print("=" * 60)
    print("APIDECK HR INTEGRATION TEST")
    print("=" * 60)
    
    # Check environment variables
    api_key = os.getenv("APIDECK_API_KEY")
    app_id = os.getenv("APIDECK_APP_ID")
    service_id = os.getenv("APIDECK_SERVICE_ID")
    consumer_id = os.getenv("APIDECK_CONSUMER_ID")
    
    print("\n📋 Configuration Check:")
    print(f"  API Key: {'✓ Set' if api_key else '✗ Missing'}")
    print(f"  App ID: {'✓ Set' if app_id else '✗ Missing'}")
    print(f"  Service ID: {'✓ Set' if service_id else '✗ Missing'} ({service_id if service_id else 'N/A'})")
    print(f"  Consumer ID: {'✓ Set' if consumer_id else '✗ Missing'} ({consumer_id if consumer_id else 'N/A'})")
    
    if not all([api_key, app_id, service_id]):
        print("\n❌ Configuration incomplete. Please check .env file")
        return
    
    # Initialize tool
    print("\n🔧 Initializing Apideck HR Tool...")
    tool = APIDeckhHRTool()
    
    # Test 1: List employees
    print("\n" + "=" * 60)
    print("TEST 1: List Employees")
    print("=" * 60)
    
    try:
        result = tool._run(
            query_type="employees_list",
            employee_id=None,
            filters=None
        )
        print(result)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get specific employee (if you have an employee ID)
    print("\n" + "=" * 60)
    print("TEST 2: Get Employee Details")
    print("=" * 60)
    
    try:
        result = tool._run(
            query_type="employee",
            employee_id="00uwkyi5qsjbfjIt5697",  # Aryan P's ID
            filters=None
        )
        print(result)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get time-off requests
    print("\n" + "=" * 60)
    print("TEST 3: Get Time-Off Requests")
    print("=" * 60)
    
    try:
        result = tool._run(
            query_type="time_off",
            employee_id=None,
            filters=None
        )
        print(result)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\n💡 Tips:")
    print("  - If you see authentication errors, verify your API credentials")
    print("  - Make sure your Apideck account is connected to an HR system")
    print("  - Visit https://app.apideck.com to manage connections")
    print()


if __name__ == "__main__":
    test_apideck_connection()
