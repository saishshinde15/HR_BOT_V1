#!/usr/bin/env python3
"""Test long-term memory functionality"""

from hr_bot.crew import HrBot

def test_memory():
    print("\n" + "="*70)
    print("Testing Long-Term Memory")
    print("="*70 + "\n")
    
    bot = HrBot()
    crew = bot.crew()
    
    # First query - establish context
    print("Query 1: Establishing context about sick days used...")
    result1 = crew.kickoff(inputs={
        'query': 'I have taken 5 sick days this year. Can you tell me more about the sick leave policy?',
        'context': ''
    })
    print("\n--- Response 1 ---")
    print(result1)
    print("\n" + "-"*70 + "\n")
    
    # Second query - reference previous context
    print("Query 2: Asking to recall previous information...")
    result2 = crew.kickoff(inputs={
        'query': 'How many sick days did I mention I had already used?',
        'context': ''
    })
    print("\n--- Response 2 ---")
    print(result2)
    print("\n" + "-"*70 + "\n")
    
    # Third query - continue conversation
    print("Query 3: Following up on the policy...")
    result3 = crew.kickoff(inputs={
        'query': 'What happens if I need to take more sick days?',
        'context': ''
    })
    print("\n--- Response 3 ---")
    print(result3)
    print("\n" + "="*70)

if __name__ == "__main__":
    test_memory()
