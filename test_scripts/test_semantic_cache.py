#!/usr/bin/env python3
"""
Test semantic cache matching with various query variations.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from hr_bot.crew import HrBot

def test_semantic_cache():
    """Test semantic cache with query variations"""
    
    print("\n" + "="*80)
    print("🧪 SEMANTIC CACHE TEST")
    print("="*80)
    
    # Initialize bot with cache
    bot = HrBot(use_cache=True)
    
    # Test cases: variations of the same question
    test_cases = [
        {
            "base_query": "What is the sick leave policy?",
            "variations": [
                "Tell me about sick leave",
                "How does sick leave work?",
                "What's the sick day policy?",
                "Sick leave policy?",
                "How many sick days do I get?",
                "What are the rules for sick leave?"
            ]
        },
        {
            "base_query": "How do I request vacation time?",
            "variations": [
                "How to request vacation?",
                "How can I ask for time off?",
                "What's the process for vacation requests?",
                "How do I take vacation?",
                "Requesting vacation time"
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST CASE {i}: {test_case['base_query']}")
        print('='*80)
        
        # Check if base query is already cached
        print(f"\n1️⃣ Checking if base query is cached...")
        result = bot.response_cache.get(test_case['base_query'])
        
        if result:
            print(f"   ✅ Base query IS cached (from pre-warming)")
            print(f"   Preview: {result[:100]}...")
        else:
            print(f"   ⚠️ Base query NOT cached - skipping this test case")
            continue
        
        # Test each variation
        print(f"\n2️⃣ Testing {len(test_case['variations'])} variations:")
        print("-" * 80)
        
        hits = 0
        for j, variation in enumerate(test_case['variations'], 1):
            print(f"\nVariation {j}: '{variation}'")
            result = bot.response_cache.get(variation)
            
            if result:
                print(f"   ✅ SEMANTIC MATCH - Retrieved from cache!")
                print(f"   Response preview: {result[:80]}...")
                hits += 1
            else:
                print(f"   ❌ NO MATCH - Would need to query LLM")
        
        hit_rate = (hits / len(test_case['variations'])) * 100
        print(f"\n📊 Hit Rate for this test: {hit_rate:.1f}% ({hits}/{len(test_case['variations'])})")
    
    # Print final statistics
    print("\n" + "="*80)
    print("📊 FINAL CACHE STATISTICS")
    print("="*80)
    stats = bot.get_cache_stats()
    print(f"Total Queries: {stats['total_queries']}")
    print(f"Cache Hits: {stats['hits']} ({stats['hit_rate']})")
    print(f"  - Exact matches: {stats['exact_hits']} ({stats['exact_hit_rate']})")
    print(f"  - Semantic matches: {stats['semantic_hits']} ({stats['semantic_hit_rate']})")
    print(f"Cache Misses: {stats['misses']}")
    print(f"Memory Cache Size: {stats['memory_cache_size']}")
    print(f"Disk Cache Files: {stats['disk_cache_files']}")
    print(f"Query Index Size: {stats['query_index_size']}")
    
    print("\n" + "="*80)
    print("✅ Semantic cache test completed!")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_semantic_cache()
