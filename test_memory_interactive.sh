#!/bin/bash
# Test long-term memory with three sequential queries

echo "========================================================================"
echo "Testing Long-Term Memory - Query 1"
echo "========================================================================"
echo ""
echo "Query: I have taken 5 sick days this year. Can you tell me about the sick leave policy?"
echo ""

cd /Users/saish/Downloads/PoC_HR_BoT/hr_bot
export QUERY_1="I have taken 5 sick days this year. Can you tell me about the sick leave policy?"

# Create a temporary Python script to run queries
cat > /tmp/test_mem.py << 'EOF'
import sys
sys.path.insert(0, 'src')
from hr_bot.crew import HrBot

bot = HrBot()
crew = bot.crew()

print("\n=== Query 1: Establishing context ===")
r1 = crew.kickoff(inputs={'query': 'I have taken 5 sick days this year. Can you tell me about the sick leave policy?', 'context': ''})
print(f"\nResponse 1:\n{r1}\n")

print("\n=== Query 2: Testing memory recall ===")
r2 = crew.kickoff(inputs={'query': 'How many sick days did I say I already used this year?', 'context': ''})
print(f"\nResponse 2:\n{r2}\n")

print("\n=== Query 3: Continue conversation ===")
r3 = crew.kickoff(inputs={'query': 'What if I need more sick days beyond what I mentioned?', 'context': ''})
print(f"\nResponse 3:\n{r3}\n")
EOF

uv run python /tmp/test_mem.py
