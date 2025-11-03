# Cache Clearing Feature Documentation

## Overview

The HR Bot now includes a **"Clear Cache"** button that allows users to clear cached responses when tool calls fail. This prevents failed responses from being served for 72 hours (the default cache TTL) and enables immediate retry of queries.

## Problem Solved

### Before v4.1:
- When a tool call failed (e.g., network timeout, API error), the failure message was cached
- Subsequent identical queries received the same cached error for 72 hours
- Users had no way to force a fresh retry
- Only solution was to wait 72 hours or manually delete cache files

### After v4.1:
- Failed tool calls are **NOT cached** (auto-detection)
- Users can manually clear cache via UI button
- Clear guidance provided in error messages
- Fresh retry possible immediately

## Features Implemented

### 1. Clear Cache Button (UI)
**Location:** Top right corner of Streamlit interface
**Appearance:** 🗑️ Clear Cache
**Tooltip:** "Clear cached responses. Use this if you get a technical error and want to retry your query."

**Code Location:** `src/hr_bot/ui/app.py` lines ~1196-1224

```python
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("🗑️ Clear Cache", help="..."):
        bot.crew_manager.response_cache.clear_all()
        st.success("✅ Cache cleared successfully! You can now retry your query.")
```

### 2. Enhanced Error Messages (UI)
**Location:** Error handler in `app.py`
**Code Location:** `src/hr_bot/ui/app.py` lines ~1242-1250

When an exception occurs:
```
⚠️ Technical Error: [error details]

💡 Tip: This error response has been cached. To retry your query successfully, 
please click the '🗑️ Clear Cache' button in the top right corner, 
then ask your question again.
```

### 3. Fallback Message Updates (Crew)
**Location:** Response cleaning logic in `crew.py`
**Code Location:** `src/hr_bot/crew.py` lines ~943-951

When tool calls produce no usable results:
```
I apologize, but I encountered a technical issue while processing your request.
This might be due to unclear search results or a tool failure.

💡 Tip: Click the '🗑️ Clear Cache' button in the top right corner, 
then try asking your question again. This will ensure a fresh search is performed.

Alternatively, you can try rephrasing your question, or contact your 
HR department directly for assistance.
```

### 4. Auto-Detection of Failed Responses (Crew)
**Location:** Caching logic in `crew.py`
**Code Location:** `src/hr_bot/crew.py` lines ~360-380

Failed responses are **automatically** excluded from cache:
```python
is_technical_failure = (
    "technical issue" in response_text.lower() or
    "tool failure" in response_text.lower() or
    "encountered an issue" in response_text.lower() or
    "Clear Cache" in response_text  # Our fallback message
)

if not is_technical_failure:
    self.response_cache.set(query, response_text, context)
else:
    print(f"⚠️  Skipping cache for technical failure response")
```

## User Journey

### Scenario: Tool Call Failure

1. **User asks:** "What is the paternity leave policy?"
2. **Tool fails** (network timeout, API error, etc.)
3. **Bot responds:**
   ```
   I apologize, but I encountered a technical issue...
   💡 Tip: Click the '🗑️ Clear Cache' button...
   ```
4. **User clicks** 🗑️ Clear Cache button
5. **System shows:** "✅ Cache cleared successfully! You can now retry your query."
6. **User re-asks** the same question
7. **Bot performs** fresh tool call (not cached)
8. **Success!** Correct answer returned

## Technical Details

### Cache Clearing Implementation

**Method:** `ResponseCache.clear_all()`
**Location:** `src/hr_bot/utils/cache.py` lines ~389-399

```python
def clear_all(self):
    """Clear all cached responses (memory + disk)"""
    # Clear memory
    self.memory_cache.clear()
    
    # Clear disk
    count = 0
    for cache_file in self.cache_dir.glob("*.json"):
        cache_file.unlink()
        count += 1
    
    logger.info(f"🗑️ Cleared all cache: {count} files deleted")
```

### What Gets Cleared:
- **Memory cache:** `self.memory_cache` dictionary (hot cache)
- **Disk cache:** All `.json` files in `storage/response_cache/` directory
- **Query index:** Automatically rebuilt on next load

### What Stays:
- **Cache statistics:** Preserved for analytics (hits/misses/rates)
- **Hybrid RAG indexes:** Vector and BM25 indexes remain untouched
- **Long-term memory:** Crew memory (short-term, long-term, entity) unchanged

## Testing

### Manual Test:
1. Start Streamlit: `uv run streamlit run src/hr_bot/ui/app.py`
2. Ask: "What is sick leave policy?"
3. Click "Clear Cache" button
4. Verify success message appears
5. Ask same question again
6. Verify fresh response (cache miss in logs)

### Automated Test:
```bash
cd hr_bot
uv run python test_scripts/test_cache_clearing.py
```

**Expected Output:**
```
✅ TEST RESULTS:
   First query cached: ✅
   Cache cleared successfully: ✅
   Post-clear query required fresh execution: ✅
```

## Performance Impact

### Cache Clear Operation:
- **Speed:** ~50-200ms (depends on cache size)
- **Memory:** Instant (just clear dictionary)
- **Disk:** O(n) where n = number of cache files
- **Typical:** 100-500 files = ~100ms

### Post-Clear Performance:
- **First query:** Cache MISS → Fresh execution (~8-15 seconds)
- **Subsequent queries:** Build up cache naturally
- **No degradation:** System returns to normal cache hit rate quickly

## Monitoring

### Check Cache Status:
```python
from hr_bot.crew import HrBot

bot = HrBot()
stats = bot.get_cache_stats()
print(stats)
# Output: {'hits': 42, 'misses': 18, 'hit_rate': '70.0%', ...}
```

### Logs to Monitor:
- `🗑️ Cleared all cache: X files deleted` - Cache cleared successfully
- `⚠️  Skipping cache for technical failure response` - Auto-exclusion triggered
- `❌ Cache MISS for query: ...` - Fresh execution required

## Future Enhancements

### Potential Improvements:
1. **Selective clearing:** Clear only failed responses, keep successful ones
2. **TTL override:** Temporary 5-minute TTL for suspected failures
3. **Auto-retry:** Automatically retry failed tool calls once before caching
4. **Analytics:** Track failed tool call frequency and patterns
5. **Cache health:** Visual indicator showing cache status in UI

## Related Files

| File | Purpose | Lines Modified |
|------|---------|----------------|
| `src/hr_bot/ui/app.py` | UI button + error messages | ~1196-1224, ~1242-1250 |
| `src/hr_bot/crew.py` | Auto-detection + fallback msg | ~360-380, ~943-951 |
| `src/hr_bot/utils/cache.py` | Cache clearing logic | ~389-399 (existing) |
| `test_scripts/test_cache_clearing.py` | Test script | New file |

## Version Information

- **Feature Version:** 4.1
- **Base Version:** 4.0 (Source deduplication fixes)
- **Previous Version:** 3.5 (Nova Lite critical bugs)
- **LLM:** Amazon Nova Lite (bedrock/amazon.nova-lite-v1:0)
- **Date:** November 3, 2024

## Support

If cache clearing doesn't resolve the issue:
1. Check Streamlit logs for error details
2. Verify tool configuration (API keys, endpoints)
3. Test tools individually with test scripts
4. Contact development team with error logs
