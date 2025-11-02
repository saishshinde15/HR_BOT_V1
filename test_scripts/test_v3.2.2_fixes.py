#!/usr/bin/env python3
"""
Test v3.2.2 Fixes: Small Talk Sources & Master Actions Relevance
Tests the intelligent improvements for source attribution and action matching
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from hr_bot.crew import HrBot


def print_test_header(test_name: str):
    """Print formatted test header"""
    print("\n" + "="*80)
    print(f"🧪 TEST: {test_name}")
    print("="*80)


def print_response(query: str, response: str):
    """Print query and response in formatted way"""
    print(f"\n📝 Query: {query}")
    print(f"\n🤖 Response:\n{response}")
    print("\n" + "-"*80)


def test_small_talk_sources():
    """
    TEST #1: Small Talk Should NOT Show Document Sources
    
    Expected Behavior:
    - Greetings like "hi", "hello" should return friendly responses
    - NO document sources should be listed
    - NO "Sources:" line should appear
    
    This tests the intelligent source stripping for conversational queries.
    """
    print_test_header("Small Talk - No Document Sources")
    
    crew = HrBot()
    
    test_queries = [
        "hi",
        "hello",
        "hey there",
        "good morning",
        "thanks",
        "thank you",
        "bye",
        "goodbye",
    ]
    
    results = {"passed": 0, "failed": 0, "details": []}
    
    for query in test_queries:
        response = crew.query_with_cache(query)
        
        # Check for sources
        has_sources = "Sources:" in response or "sources:" in response.lower()
        has_document_evidence = "Document Evidence:" in response
        
        # Small talk should NOT have sources
        passed = not has_sources and not has_document_evidence
        
        if passed:
            results["passed"] += 1
            status = "✅ PASS"
        else:
            results["failed"] += 1
            status = "❌ FAIL"
            results["details"].append({
                "query": query,
                "reason": "Sources found in small talk response",
                "response": response
            })
        
        print(f"\n{status} - Query: '{query}'")
        print(f"Has Sources: {has_sources}")
        print(f"Has Document Evidence: {has_document_evidence}")
        if not passed:
            print(f"Response: {response[:200]}...")
    
    print(f"\n📊 Results: {results['passed']}/{len(test_queries)} passed")
    return results


def test_master_actions_relevance():
    """
    TEST #2: Master Actions Should Return Relevant Actions Only
    
    Expected Behavior:
    - "drug test" should NOT return "apply leave" action
    - "background check" should NOT return irrelevant actions
    - Only actions with meaningful keyword overlap should be returned
    - If no relevant action exists, should gracefully handle it
    
    This tests the intelligent keyword matching with stop word filtering.
    """
    print_test_header("Master Actions - Relevance Filtering")
    
    crew = HrBot()
    
    test_cases = [
        {
            "query": "how do i apply for leave",
            "should_contain": "Apply Leave",
            "should_not_contain": ["Payslip", "Training"],
            "description": "Leave query should match leave action"
        },
        {
            "query": "download my payslip",
            "should_contain": "Payslip",
            "should_not_contain": ["Leave", "Training"],
            "description": "Payslip query should match payslip action"
        },
        {
            "query": "drug test procedure",
            "should_contain": None,  # No drug test action exists
            "should_not_contain": ["Apply Leave", "Training", "Payslip"],
            "description": "Drug test should NOT return irrelevant actions"
        },
        {
            "query": "background check",
            "should_contain": None,  # No background check action exists
            "should_not_contain": ["Apply Leave", "Training", "Payslip"],
            "description": "Background check should NOT return irrelevant actions"
        },
        {
            "query": "enroll in training",
            "should_contain": "Training",
            "should_not_contain": ["Leave", "Payslip"],
            "description": "Training query should match training action"
        },
    ]
    
    results = {"passed": 0, "failed": 0, "details": []}
    
    for test_case in test_cases:
        query = test_case["query"]
        response = crew.query_with_cache(query)
        
        # Check conditions
        passed = True
        failure_reason = []
        
        # Check should_contain
        if test_case["should_contain"]:
            if test_case["should_contain"] not in response:
                passed = False
                failure_reason.append(f"Missing expected: {test_case['should_contain']}")
        
        # Check should_not_contain
        for forbidden in test_case["should_not_contain"]:
            if forbidden in response:
                passed = False
                failure_reason.append(f"Found forbidden: {forbidden}")
        
        if passed:
            results["passed"] += 1
            status = "✅ PASS"
        else:
            results["failed"] += 1
            status = "❌ FAIL"
            results["details"].append({
                "query": query,
                "description": test_case["description"],
                "reason": "; ".join(failure_reason),
                "response": response
            })
        
        print(f"\n{status} - {test_case['description']}")
        print(f"Query: '{query}'")
        if not passed:
            print(f"Reason: {'; '.join(failure_reason)}")
            print(f"Response: {response[:300]}...")
    
    print(f"\n📊 Results: {results['passed']}/{len(test_cases)} passed")
    return results


def test_edge_cases():
    """
    TEST #3: Edge Cases - Mixed Queries
    
    Tests queries that combine greetings with questions to ensure
    proper handling.
    """
    print_test_header("Edge Cases - Mixed Queries")
    
    crew = HrBot()
    
    test_cases = [
        {
            "query": "hi, how do i apply for leave?",
            "should_have_sources": True,
            "description": "Greeting + question should have sources"
        },
        {
            "query": "hello, can you help me?",
            "should_have_sources": True,
            "description": "Greeting + help request should have sources"
        },
        {
            "query": "thanks, that's helpful!",
            "should_have_sources": False,
            "description": "Pure gratitude should NOT have sources"
        },
    ]
    
    results = {"passed": 0, "failed": 0, "details": []}
    
    for test_case in test_cases:
        query = test_case["query"]
        response = crew.query_with_cache(query)
        
        has_sources = "Sources:" in response or "sources:" in response.lower()
        expected_sources = test_case["should_have_sources"]
        
        passed = (has_sources == expected_sources)
        
        if passed:
            results["passed"] += 1
            status = "✅ PASS"
        else:
            results["failed"] += 1
            status = "❌ FAIL"
            results["details"].append({
                "query": query,
                "description": test_case["description"],
                "reason": f"Expected sources: {expected_sources}, Got: {has_sources}",
                "response": response
            })
        
        print(f"\n{status} - {test_case['description']}")
        print(f"Query: '{query}'")
        print(f"Has Sources: {has_sources} (Expected: {expected_sources})")
        if not passed:
            print(f"Response: {response[:200]}...")
    
    print(f"\n📊 Results: {results['passed']}/{len(test_cases)} passed")
    return results


def main():
    """Run all v3.2.2 tests"""
    print("\n" + "="*80)
    print("🚀 STARTING v3.2.2 INTELLIGENT IMPROVEMENTS TEST SUITE")
    print("="*80)
    print("\nTesting:")
    print("1. ✨ Small Talk - Intelligent Source Stripping")
    print("2. ✨ Master Actions - Semantic Relevance Filtering")
    print("3. ✨ Edge Cases - Mixed Query Handling")
    print("\n" + "="*80)
    
    # Run all tests
    test_results = []
    
    try:
        # Test 1: Small Talk Sources
        result1 = test_small_talk_sources()
        test_results.append(("Small Talk Sources", result1))
        
        # Test 2: Master Actions Relevance
        result2 = test_master_actions_relevance()
        test_results.append(("Master Actions Relevance", result2))
        
        # Test 3: Edge Cases
        result3 = test_edge_cases()
        test_results.append(("Edge Cases", result3))
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    
    total_passed = 0
    total_tests = 0
    
    for test_name, result in test_results:
        total_passed += result["passed"]
        total_tests += result["passed"] + result["failed"]
        status = "✅" if result["failed"] == 0 else "❌"
        print(f"\n{status} {test_name}: {result['passed']}/{result['passed'] + result['failed']} passed")
        
        # Show failures
        if result["details"]:
            print(f"   ⚠️  Failures:")
            for detail in result["details"]:
                print(f"      - {detail['query']}: {detail.get('reason', 'Failed')}")
    
    print(f"\n{'='*80}")
    print(f"🎯 OVERALL: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("✅ ALL TESTS PASSED - v3.2.2 Intelligent Improvements Working!")
    else:
        print(f"❌ {total_tests - total_passed} tests failed - Review failures above")
    
    print("="*80 + "\n")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
