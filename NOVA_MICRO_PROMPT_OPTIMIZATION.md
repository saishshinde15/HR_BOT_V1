# Nova Micro Prompt Optimization Guide

## Problem Statement

After migrating from Google Gemini Flash to Amazon Bedrock Nova Micro, the model exhibited "dumb" behaviors:

1. **Unnecessary placeholders**: Adding `[Your Name]`, `[Employee Name]`, `[Job Title]` in responses
2. **Fake markdown links**: Creating URLs like `[Document.docx](https://example.com/...)` that don't exist
3. **Formal letter formatting**: Adding "Best regards, [Your Name]" signatures unnecessarily

### Example of Bad Output (Before):
```
Best regards,
[Your Name]
HR Department

**Sources:** [Sickness-And-Absence-Policy.docx](https://example.com/policy/Sickness-And-Absence-Policy.docx)
```

## Root Cause

Nova Micro is a smaller, less capable model compared to Gemini Flash. It:
- Takes instructions more literally
- Fills in "templates" it thinks it sees
- Struggles with nuanced, complex instructions
- Cannot infer context as well

## Solution: Stricter, More Directive Prompts

### Key Changes Made

#### 1. **Simplified Agent Backstory** (`agents.yaml`)

**Before**: Long, nuanced personality descriptions (104 lines)
**After**: Direct, rule-based instructions (89 lines)

Key improvements:
- Replaced personality descriptions with **CRITICAL FORMAT RULES**
- Added explicit "NEVER" and "ALWAYS" directives
- Removed metaphorical language
- Added clear examples of correct vs. wrong formats

**Critical Rules Added:**
```yaml
1. NEVER add placeholders like [Your Name], [Employee Name], [Job Title]
2. NEVER create markdown links - only write document names as plain text
3. NEVER add formal letter signatures
4. NEVER add "Dear [Name]" or formal greetings
5. ALWAYS start directly with empathetic acknowledgment
6. ALWAYS use hr_document_search tool BEFORE answering
7. ALWAYS cite sources as plain text: "Sources: Document1.docx, Document2.docx"
```

#### 2. **Restructured Task Instructions** (`tasks.yaml`)

**Before**: Flowing narrative style with examples embedded in text
**After**: Rigid, numbered step-by-step format with explicit rules

Key improvements:
- **CRITICAL FORMAT RULES** section at the top
- Clear DO NOT / DO lists
- Structured 6-step process (STEP 1, STEP 2, etc.)
- Explicit format templates for each section
- Multiple correct/wrong examples with ✅/❌ markers
- **QUALITY CHECKLIST** at the end

**Task Structure:**
```
STEP 1: EMPATHETIC OPENING (2-3 sentences)
STEP 2: USE HR_DOCUMENT_SEARCH TOOL (mandatory)
STEP 3: PROVIDE COMPLETE INFORMATION (5 subsections A-E)
STEP 4: PROVIDE CLEAR NEXT STEPS (numbered list)
STEP 5: SUPPORTIVE CLOSING (1-2 sentences)
STEP 6: SOURCE CITATION (exact format specified)
```

#### 3. **Explicit Examples**

Added clear examples with visual markers:

✅ **CORRECT** Source Citation:
```
Sources: Sickness-And-Absence-Policy.docx, Employee-Handbook.docx
```

❌ **WRONG** - Has markdown links:
```
Sources: [Sick-Leave-Policy.docx](https://example.com/policy/sick-leave)
```

❌ **WRONG** - Has placeholders:
```
Best regards,
[Your Name]
HR Department
```

#### 4. **Removed Ambiguity**

**Before**: "Use natural, warm language like a caring HR professional"
**After**: "Use natural, conversational language. Avoid corporate jargon. Be warm but professional. NEVER add formal signatures."

## Results

### Output Quality Improvement

**After optimization** (Test 1 - Phone usage):
```
I understand this is a challenging situation for you. Let me guide you 
through the company's policy regarding the use of company phones while on duty.

**Section A: Policy Overview**
The Company's telephone lines and mobile phones...

**Next Steps:**
1. Notify your immediate supervisor as soon as possible.
2. If requested, prepare a written explanation for your actions.
3. Be prepared for a discussion with your supervisor regarding this incident.

I hope this helps! Please reach out if you need anything else.

Sources: Communications-Email-Internet-and-Social-Media-Policy.docx
```

✅ **No placeholders**
✅ **No fake links**
✅ **No formal signatures**
✅ **Clear structure**
✅ **Plain text sources**

### Verified Fixes

| Issue | Status | Evidence |
|-------|--------|----------|
| `[Your Name]` placeholders | ✅ Fixed | No brackets in output |
| Fake markdown links | ✅ Fixed | Sources in plain text |
| Formal signatures | ✅ Fixed | Simple closing only |
| Structured responses | ✅ Working | Sections A-E present |
| Source citation | ✅ Working | Plain text format |

## Best Practices for Working with Smaller Models

### 1. **Be Extremely Explicit**
- Use "NEVER" and "ALWAYS" instead of "avoid" or "prefer"
- List specific forbidden patterns
- Provide exact format templates

### 2. **Use Visual Markers**
- ✅ for correct examples
- ❌ for wrong examples
- **CRITICAL**, **REQUIRED**, **MANDATORY** for important rules

### 3. **Structure Over Narrative**
- Numbered steps (STEP 1, STEP 2)
- Clear sections (Section A, Section B)
- Rigid format templates

### 4. **Show, Don't Tell**
- Multiple concrete examples
- Side-by-side correct/wrong comparisons
- Exact text to use/avoid

### 5. **Add Checkpoints**
- Quality checklist at the end
- Verification requirements
- Format validation rules

### 6. **Remove Ambiguity**
- No metaphorical language
- No "it's like..." explanations
- Direct, imperative instructions

### 7. **Front-Load Rules**
- Put CRITICAL rules at the top
- Repeat important rules
- Make violations obvious to detect

## Code Changes Summary

### Files Modified
- `src/hr_bot/config/agents.yaml` (89 lines, -15 lines)
- `src/hr_bot/config/tasks.yaml` (complete restructure)

### Verification
- ✅ Kluster code review passed (no issues)
- ✅ Manual testing with 2 different queries
- ✅ Format rules followed correctly
- ✅ No regression in empathy or accuracy

## Conclusion

Nova Micro can produce quality output comparable to Gemini Flash **IF** prompts are:
1. Extremely directive and explicit
2. Structured with clear steps and rules
3. Reinforced with multiple examples
4. Validated with checklists

The key is treating the model like a less experienced team member who needs very specific instructions rather than someone who can infer intent from context.

**Cost Savings**: Nova Micro is significantly cheaper than Gemini Flash while maintaining output quality with optimized prompts.

**Trade-off**: Initial prompt engineering effort vs. ongoing model cost savings.
