# Test Scripts and Utilities

This folder contains all test scripts, utilities, and helper files for the HR Bot project.

## 📋 Test Scripts

### Production Test Suite
- **`test_bot.py`** - Main production test suite with 10 comprehensive tests
  - Master Actions queries
  - HR Document searches
  - Hybrid queries (both tools)
  - Validation system tests
  - Content safety (profanity + NSFW)
  - Conversational AI tests
  - **Result**: 10/10 tests passed (100% success rate)

### Component Tests
- **`test_hierarchical.py`** - Tests hierarchical crew structure
- **`test_memory.py`** - Tests conversation memory system
- **`test_memory_interactive.sh`** - Interactive memory testing shell script
- **`test_cache.py`** - Tests caching functionality
- **`test_semantic_cache.py`** - Tests semantic similarity caching
- **`test_semantic_simple.py`** - Simplified semantic cache tests
- **`test_final_semantic.py`** - Final semantic cache implementation tests

### API/Integration Tests
- **`test_apideck.py`** - Basic API Deck HR integration tests
- **`test_apideck_full.py`** - Comprehensive API Deck integration tests

## 🛠️ Utility Scripts

### Cache Management
- **`manage_cache.py`** - Cache management utility
  - View cache statistics
  - Clear expired entries
  - Clear all cache
  - Usage: `uv run python test_scripts/manage_cache.py stats`

- **`prewarm_cache.py`** - Pre-warm cache with common queries
  - Generates responses for 30 most common HR questions
  - Ensures instant responses for first-time users
  - Usage: `uv run python test_scripts/prewarm_cache.py`

### Analysis & Monitoring
- **`analyze_similarity.py`** - Analyzes semantic similarity in cache
- **`run_cost_estimate.py`** - Estimates cost per query
- **`validate_token_usage.py`** - Validates token usage and costs

### Quick Testing
- **`run_crew.py`** - Quick crew kickoff for testing
  - Usage: `uv run python test_scripts/run_crew.py`

## 🚀 Quick Start

### Run Production Tests
```bash
# Run the main test suite (10 tests)
uv run python test_scripts/test_bot.py
```

### Manage Cache
```bash
# View cache stats
uv run python test_scripts/manage_cache.py stats

# Pre-warm cache
uv run python test_scripts/prewarm_cache.py

# Clear all cache
uv run python test_scripts/manage_cache.py clear
```

### Analyze Performance
```bash
# Estimate query costs
uv run python test_scripts/run_cost_estimate.py

# Validate token usage
uv run python test_scripts/validate_token_usage.py

# Analyze cache similarity
uv run python test_scripts/analyze_similarity.py
```

## 📊 Test Results Summary

| Category | Tests | Status |
|----------|-------|--------|
| Master Actions Only | 2 | ✅ 100% |
| HR Documents Only | 1 | ✅ 100% |
| Hybrid (Both Tools) | 2 | ✅ 100% |
| Validation System | 1 | ✅ 100% |
| Content Safety | 2 | ✅ 100% |
| Conversational AI | 2 | ✅ 100% |
| **TOTAL** | **10** | **✅ 100%** |

## 🔍 Notes

- All test scripts use UV for dependency management
- Cache utilities work with the semantic cache in `storage/response_cache/`
- Production tests validate the dual-tool intelligence system
- Cost estimates based on Amazon Bedrock Nova Pro pricing
