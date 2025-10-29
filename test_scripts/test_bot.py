#!/usr/bin/env python
"""
Quick test script for HR Bot
"""
from hr_bot.crew import HrBot

def test_sick_leave_query():
    print("="*60)
    print("Testing HR Bot with sick leave policy query")
    print("="*60)
    
    # Initialize bot
    print("\n1. Initializing HR Bot...")
    bot = HrBot()
    print("✓ Bot initialized successfully!")
    
    # Run query
    print("\n2. Running query: 'What is the sick leave policy?'")
    print("-"*60)
    
    result = bot.crew().kickoff(inputs={
        'query': 'What is the sick leave policy?',
        'context': ''
    })
    
    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    print(result.raw)
    print("="*60)

if __name__ == "__main__":
    test_sick_leave_query()
