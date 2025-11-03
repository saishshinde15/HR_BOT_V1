#!/usr/bin/env python3
"""
Quick validation script for v3.2 critical fixes
Tests all 5 security fixes to ensure they work correctly
"""

import sys
import os
import sqlite3
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from hr_bot.utils.cache import ResponseCache

def test_1_sqlite_threading():
    """Test Fix #1: SQLite threading locks"""
    print("\n" + "="*60)
    print("TEST 1: SQLite Threading Locks")
    print("="*60)
    
    try:
        from hr_bot.crew import HrBot
        bot = HrBot()
        
        # Verify _db_lock exists
        if not hasattr(bot, '_db_lock'):
            print("❌ FAILED: _db_lock not found in HrBot")
            return False
        
        # Verify _get_db_connection exists
        if not hasattr(bot, '_get_db_connection'):
            print("❌ FAILED: _get_db_connection method not found")
            return False
        
        print("✅ PASSED: Threading lock initialized")
        print("✅ PASSED: Context manager created")
        
        # Test concurrent access
        def access_db(i):
            try:
                with bot._get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    return f"Thread {i}: Found {len(tables)} tables"
            except Exception as e:
                return f"Thread {i}: ERROR - {e}"
        
        print("\n🔄 Testing concurrent database access (10 threads)...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(access_db, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]
        
        errors = [r for r in results if "ERROR" in r]
        if errors:
            print(f"❌ FAILED: {len(errors)} concurrent access errors")
            for error in errors:
                print(f"   {error}")
            return False
        
        print(f"✅ PASSED: All 10 threads accessed database successfully")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_2_cache_validation():
    """Test Fix #2: Cache response validation"""
    print("\n" + "="*60)
    print("TEST 2: Cache Response Validation")
    print("="*60)
    
    try:
        # Create temp cache directory
        cache_dir = Path("storage/test_cache_validation")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache = ResponseCache(cache_dir=str(cache_dir), ttl_hours=1)
        
        # Test 1: Empty response should be rejected
        print("\n🔄 Testing empty response rejection...")
        cache.set("test query 1", "", "")
        cached = cache.get("test query 1", "")
        if cached is not None:
            print(f"❌ FAILED: Empty response was cached: '{cached}'")
            return False
        print("✅ PASSED: Empty response rejected")
        
        # Test 2: Short response (<20 chars) should be rejected
        print("\n🔄 Testing short response rejection...")
        cache.set("test query 2", "short", "")
        cached = cache.get("test query 2", "")
        if cached is not None:
            print(f"❌ FAILED: Short response was cached: '{cached}'")
            return False
        print("✅ PASSED: Short response rejected")
        
        # Test 3: Valid response should be cached
        print("\n🔄 Testing valid response caching...")
        valid_response = "This is a valid response with sufficient length for caching."
        cache.set("test query 3", valid_response, "")
        cached = cache.get("test query 3", "")
        if cached != valid_response:
            print(f"❌ FAILED: Valid response not cached properly")
            return False
        print("✅ PASSED: Valid response cached successfully")
        
        # Cleanup
        import shutil
        shutil.rmtree(cache_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_3_json_error_handling():
    """Test Fix #3: JSON error handling"""
    print("\n" + "="*60)
    print("TEST 3: JSON Error Handling")
    print("="*60)
    
    try:
        # Create temp cache directory
        cache_dir = Path("storage/test_json_handling")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create corrupted JSON file
        corrupted_file = cache_dir / "corrupted.json"
        with open(corrupted_file, 'w') as f:
            f.write("{invalid json content}")
        
        print("\n🔄 Creating cache with corrupted JSON file...")
        cache = ResponseCache(cache_dir=str(cache_dir), ttl_hours=1)
        
        # Verify corrupted file was deleted during index build
        if corrupted_file.exists():
            print(f"❌ FAILED: Corrupted file still exists: {corrupted_file}")
            return False
        
        print("✅ PASSED: Corrupted file automatically deleted")
        
        # Cleanup
        import shutil
        shutil.rmtree(cache_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_4_memory_limits():
    """Test Fix #4: Memory limits"""
    print("\n" + "="*60)
    print("TEST 4: Memory Limits (Query Index)")
    print("="*60)
    
    try:
        # Create temp cache directory with many files
        cache_dir = Path("storage/test_memory_limits")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create 100 cache files (will test limit)
        print("\n🔄 Creating 100 cache files...")
        for i in range(100):
            cache_file = cache_dir / f"cache_{i:03d}.json"
            with open(cache_file, 'w') as f:
                json.dump({
                    "query_preview": f"Test query {i}",
                    "response": f"Test response {i}",
                    "timestamp": "2024-01-01T00:00:00"
                }, f)
            # Sleep to ensure different modification times
            if i % 20 == 0:
                time.sleep(0.01)
        
        # Set low limit for testing
        os.environ['CACHE_MAX_INDEX_ENTRIES'] = '50'
        
        print("🔄 Building cache index with 50-entry limit...")
        cache = ResponseCache(cache_dir=str(cache_dir), ttl_hours=1)
        
        # Verify index is limited to 50 entries
        if len(cache.query_index) > 50:
            print(f"❌ FAILED: Index has {len(cache.query_index)} entries (expected max 50)")
            return False
        
        print(f"✅ PASSED: Index limited to {len(cache.query_index)} entries (max 50)")
        
        # Cleanup
        os.environ.pop('CACHE_MAX_INDEX_ENTRIES', None)
        import shutil
        shutil.rmtree(cache_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_5_aws_retry_logic():
    """Test Fix #5: AWS retry logic (code inspection only)"""
    print("\n" + "="*60)
    print("TEST 5: AWS Retry Logic")
    print("="*60)
    
    try:
        # Read crew.py and verify retry logic exists
        crew_file = Path(__file__).parent.parent / "src" / "hr_bot" / "crew.py"
        with open(crew_file, 'r') as f:
            content = f.read()
        
        # Check for key retry components
        checks = [
            ("max_retries = 3", "Retry count defined"),
            ("retry_delays = [1, 2, 4]", "Exponential backoff defined"),
            ("ThrottlingException", "Throttling exception handled"),
            ("TooManyRequestsException", "Rate limit exception handled"),
            ("for attempt in range(max_retries)", "Retry loop implemented"),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✅ PASSED: {description}")
            else:
                print(f"❌ FAILED: {description} not found")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def main():
    """Run all v3.2 fix validation tests"""
    print("\n" + "="*60)
    print("v3.2 CRITICAL FIXES - VALIDATION SUITE")
    print("="*60)
    print("Testing all 5 security and stability fixes")
    
    results = {
        "Fix #1: SQLite Threading Locks": test_1_sqlite_threading(),
        "Fix #2: Cache Response Validation": test_2_cache_validation(),
        "Fix #3: JSON Error Handling": test_3_json_error_handling(),
        "Fix #4: Memory Limits": test_4_memory_limits(),
        "Fix #5: AWS Retry Logic": test_5_aws_retry_logic(),
    }
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "-"*60)
    print(f"OVERALL: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 SUCCESS! All v3.2 fixes validated!")
        return 0
    else:
        print(f"\n⚠️  WARNING: {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
