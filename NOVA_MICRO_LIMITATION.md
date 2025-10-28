# Amazon Nova Micro Limitation with CrewAI

## Problem Summary

Amazon Bedrock Nova Micro (`us.amazon.nova-micro-v1:0`) is **incompatible** with CrewAI's tool execution framework. The model generates tool planning text in ReAct format but does not complete responses after tool calls.

## Symptoms

- Agent outputs contain planning text like:
  ```
  Thought: I will use hr_document_search to gather information...
  Action: [hr_document_search]
  Argument: {'query': 'paternity benefits policy', 'top_k': 12}
  Observation:
  ```
- Output terminates at "Observation:" without generating the final answer
- Occurs even with `max_tokens=2000` and memory disabled
- Simple test agents with minimal prompts show same behavior

## Root Cause

Nova Micro appears to be trained on ReAct-style prompting format, where it generates planning text that **looks like** tool invocation but doesn't trigger CrewAI's actual tool execution mechanism. The model is outputting this as literal text rather than using CrewAI's expected tool invocation protocol.

## Attempted Fixes (All Failed)

1. ✗ Setting `max_tokens=2000` - No effect
2. ✗ Disabling crew-level memory - No effect  
3. ✗ Disabling crew cache - No effect
4. ✗ Simplifying agent prompts - No effect
5. ✗ Testing with minimal agent configuration - Same issue

## Recommended Solutions

### Option 1: Switch to Compatible Model (RECOMMENDED)

Use a model known to work well with CrewAI:
- **Claude 3.5 Sonnet** (`anthropic.claude-3-5-sonnet-20241022-v2:0`) - Excellent with tools
- **Claude 3 Haiku** (`anthropic.claude-3-haiku-20240307-v1:0`) - Fast and cost-effective
- **GPT-4** - Proven compatibility with CrewAI

Update in `.env`:
```bash
BEDROCK_MODEL=bedrock/anthropic.claude-3-haiku-20240307-v1:0
```

### Option 2: Post-Process Responses (WORKAROUND)

If Nova Micro must be used, implement response filtering to detect incomplete outputs and either:
1. Strip the planning text and return "Unable to complete request"
2. Re-run with different parameters
3. Fall back to cached responses only

### Option 3: Use Direct API Calls

Bypass CrewAI's agent framework and call Nova Micro directly with custom prompt engineering to avoid the ReAct format conflict.

## Testing Results

### Successful Test (Non-CrewAI)
Direct tool invocation works fine:
```python
bot.hybrid_rag_tool._run('paternity leave policy', top_k=3)
# Returns: "Found 3 relevant results..." with complete content
```

### Failed Test (CrewAI Agent)
```python
crew.kickoff(inputs={'query': 'What are paternity benefits?', 'context': ''})
# Returns: Planning text ending with "Observation:" and no answer
```

## Status

**BLOCKING ISSUE** for production deployment with Nova Micro. Must either:
1. Switch models (recommended)
2. Implement comprehensive workaround
3. Accept incomplete responses

Last updated: 2025-01-28
