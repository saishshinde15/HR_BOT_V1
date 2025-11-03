#!/usr/bin/env python3
"""Test drug test query to verify master actions fix"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hr_bot.crew import HrBot

print("\n" + "="*80)
print("🧪 TESTING DRUG TEST QUERY - Master Actions Relevance Fix")
print("="*80)

crew = HrBot()

print("\n📝 Query: 'what is drug test'")
print("-" * 80)

response = crew.query_with_cache("what is drug test")

print("\n🤖 Response:")
print(response)
print("\n" + "-" * 80)

# Check for issues
has_apply_leave = "Apply Leave" in response or "apply leave" in response.lower()
has_master_actions = "Master Actions" in response
has_darwinbox_leave_link = "darwinbox.com/demo-company/leaves" in response

print("\n📊 Analysis:")
print(f"  ❌ Contains 'Apply Leave' action: {has_apply_leave}")
print(f"  ℹ️  Mentions 'Master Actions': {has_master_actions}")
print(f"  ❌ Contains leave application link: {has_darwinbox_leave_link}")

if has_apply_leave or has_darwinbox_leave_link:
    print("\n❌ FAIL: Still returning irrelevant 'Apply Leave' action for drug test query!")
    print("   This means the master actions tool is still matching incorrectly.")
else:
    print("\n✅ PASS: No longer returning irrelevant 'Apply Leave' action!")
    print("   The intelligent semantic matching is working correctly.")

print("="*80 + "\n")
