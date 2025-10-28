"""
Test script to verify cache is working
Run this to see cache hit in action!
"""

import time
from src.hr_bot.crew import HrBot

def test_cache():
    print("🧪 Testing Response Cache...\n")
    
    bot = HrBot()
    test_query = "What is the sick leave policy?"
    
    # First query - should be CACHE MISS
    print("=" * 60)
    print("TEST 1: First query (should be CACHE MISS)")
    print("=" * 60)
    start = time.time()
    response1 = bot.query_with_cache(test_query)
    time1 = time.time() - start
    print(f"\n⏱️  Time taken: {time1:.2f}s")
    print(f"📊 Cache stats: {bot.get_cache_stats()}\n")
    
    # Second query - should be CACHE HIT (instant!)
    print("=" * 60)
    print("TEST 2: Same query again (should be CACHE HIT)")
    print("=" * 60)
    start = time.time()
    response2 = bot.query_with_cache(test_query)
    time2 = time.time() - start
    print(f"\n⏱️  Time taken: {time2:.2f}s")
    print(f"📊 Cache stats: {bot.get_cache_stats()}\n")
    
    # Third query - different question (CACHE MISS)
    test_query2 = "How do I request vacation time?"
    print("=" * 60)
    print("TEST 3: Different query (should be CACHE MISS)")
    print("=" * 60)
    start = time.time()
    response3 = bot.query_with_cache(test_query2)
    time3 = time.time() - start
    print(f"\n⏱️  Time taken: {time3:.2f}s")
    print(f"📊 Cache stats: {bot.get_cache_stats()}\n")
    
    # Fourth query - repeat second question (CACHE HIT)
    print("=" * 60)
    print("TEST 4: Repeat second query (should be CACHE HIT)")
    print("=" * 60)
    start = time.time()
    response4 = bot.query_with_cache(test_query2)
    time4 = time.time() - start
    print(f"\n⏱️  Time taken: {time4:.2f}s")
    print(f"📊 Cache stats: {bot.get_cache_stats()}\n")
    
    # Summary
    print("=" * 60)
    print("📈 PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"Query 1 (miss): {time1:.2f}s")
    print(f"Query 2 (HIT):  {time2:.2f}s  ⚡ {(time1/time2):.1f}x faster!")
    print(f"Query 3 (miss): {time3:.2f}s")
    print(f"Query 4 (HIT):  {time4:.2f}s  ⚡ {(time3/time4):.1f}x faster!")
    print(f"\n✅ Cache is working! Speedup: {((time1 + time3) / (time2 + time4)):.1f}x")

if __name__ == "__main__":
    test_cache()
