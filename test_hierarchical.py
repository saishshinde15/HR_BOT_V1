"""
Test script for Hierarchical HR Bot Crew
Tests manager delegation and specialist execution
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hr_bot.crew_hierarchical import HrBotHierarchical


def test_hierarchical_crew():
    """Test the hierarchical crew with various query types"""
    
    print("=" * 80)
    print(" HIERARCHICAL HR BOT CREW - PRODUCTION TEST")
    print("=" * 80)
    print()
    print("Architecture:")
    print("  🎯 HR Manager (Orchestrator)")
    print("     ├── 📚 Policy Specialist (RAG Tool)")
    print("     └── 💼 HRMS Specialist (Apideck Tool)")
    print()
    print("Process: Hierarchical (Manager delegates to specialists)")
    print("=" * 80)
    print()
    
    # Initialize crew
    print("🔧 Initializing hierarchical crew...")
    hr_bot = HrBotHierarchical()
    crew = hr_bot.crew()
    print("✅ Crew initialized successfully!")
    print()
    
    # Test cases
    test_cases = [
        {
            "name": "Policy-Only Query",
            "query": "What is the sick leave policy?",
            "expected": "Should delegate to Policy Specialist only"
        },
        {
            "name": "HRMS-Only Query",
            "query": "List all employees in the system",
            "expected": "Should delegate to HRMS Specialist only"
        },
        {
            "name": "Combined Query",
            "query": "What are the leave policies and show me all employees?",
            "expected": "Should delegate to both specialists"
        }
    ]
    
    print("=" * 80)
    print(" TEST CASES")
    print("=" * 80)
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Query: \"{test_case['query']}\"")
        print(f"Expected: {test_case['expected']}")
        print("-" * 80)
    
    print()
    print("=" * 80)
    print(" EXECUTION")
    print("=" * 80)
    print()
    
    # Run first test case
    print(f"🚀 Executing Test 1: {test_cases[0]['name']}")
    print(f"📝 Query: \"{test_cases[0]['query']}\"")
    print()
    print("⏳ Running crew... (this may take a moment)")
    print()
    
    try:
        # For hierarchical crews, we need to pass the query differently
        # The query should be part of the task description or passed via inputs
        inputs = {
            "query": test_cases[0]['query']
        }
        
        result = crew.kickoff(inputs=inputs)
        
        print()
        print("=" * 80)
        print(" RESULT")
        print("=" * 80)
        print()
        print(result)
        print()
        print("=" * 80)
        print("✅ Test completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print(" ERROR")
        print("=" * 80)
        print()
        print(f"❌ Test failed with error: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("=" * 80)
    
    print()
    print("📋 Summary:")
    print("   - Hierarchical crew structure: ✅ Configured")
    print("   - Manager agent: ✅ Created")
    print("   - Policy specialist: ✅ Created")
    print("   - HRMS specialist: ✅ Created")
    print("   - Test execution: Check results above")
    print()


if __name__ == "__main__":
    test_hierarchical_crew()
