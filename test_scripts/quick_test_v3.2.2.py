#!/usr/bin/env python3
"""Quick validation test for v3.2.2 fixes"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hr_bot.crew import HrBot

print("\n" + "="*80)
print("🧪 QUICK v3.2.2 VALIDATION TEST")
print("="*80)

crew = HrBot()

# Test 1: Small talk - no sources
print("\n1️⃣ Testing: 'hi' (should have NO sources)")
response1 = crew.query_with_cache("hi")
has_sources1 = "Sources:" in response1 or "sources:" in response1.lower()
print(f"Response: {response1[:150]}...")
print(f"Has sources: {has_sources1}")
print(f"Result: {'❌ FAIL' if has_sources1 else '✅ PASS'}")

# Test 2: Small talk - no sources
print("\n2️⃣ Testing: 'thanks' (should have NO sources)")
response2 = crew.query_with_cache("thanks")
has_sources2 = "Sources:" in response2 or "sources:" in response2.lower()
print(f"Response: {response2[:150]}...")
print(f"Has sources: {has_sources2}")
print(f"Result: {'❌ FAIL' if has_sources2 else '✅ PASS'}")

# Test 3: Action query - should have response
print("\n3️⃣ Testing: 'how do i apply for leave' (should work normally)")
response3 = crew.query_with_cache("how do i apply for leave")
has_leave = "Leave" in response3 or "leave" in response3.lower()
print(f"Response length: {len(response3)} chars")
print(f"Mentions leave: {has_leave}")
print(f"Result: {'✅ PASS' if has_leave else '❌ FAIL'}")

print("\n" + "="*80)
passed = not has_sources1 and not has_sources2 and has_leave
print(f"{'✅ ALL TESTS PASSED' if passed else '❌ SOME TESTS FAILED'}")
print("="*80 + "\n")
