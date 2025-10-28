#!/usr/bin/env python3
"""
Simple standalone test for semantic cache - no dependencies required.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from hr_bot.utils.cache import ResponseCache

def test_semantic_cache():
    """Test semantic cache matching"""
    
    print("\n" + "="*80)
    print("🧪 SEMANTIC CACHE SIMPLE TEST")
    print("="*80)
    
    # Initialize cache with 75% similarity threshold
    cache = ResponseCache(
        cache_dir="storage/response_cache",
        ttl_hours=72,
        similarity_threshold=0.75
    )
    
    print(f"\n✅ Cache initialized:")
    print(f"   Similarity threshold: {cache.similarity_threshold}")
    print(f"   Query index size: {len(cache.query_index)} cached queries")
    print(f"   Cache files on disk: {len(list(cache.cache_dir.glob('*.json')))}")
    
    # Test cases: variations of cached questions
    test_cases = [
        {
            "name": "Sick Leave Variations",
            "variations": [
                "What is the sick leave policy?",  # Exact match (should be cached)
                "Tell me about sick leave",
                "How does sick leave work?",
                "What's the sick day policy?",
                "Sick leave policy?",
                "How many sick days do I get?",
                "What are the rules for sick leave?"
            ]
        },
        {
            "name": "Vacation Request Variations",
            "variations": [
                "How do I request vacation time?",  # Exact match (should be cached)
                "How to request vacation?",
                "How can I ask for time off?",
                "What's the process for vacation requests?",
                "How do I take vacation?",
                "Requesting vacation time",
                "What's the vacation request procedure?"
            ]
        },
        {
            "name": "Paternity Leave Variations",
            "variations": [
                "How do I request paternity leave?",  # Exact match (should be cached)
                "Tell me about paternity leave",
                "What's the paternity leave policy?",
                "How to apply for paternity leave?",
                "Paternity leave process"
            ]
        }
    ]
    
    total_queries = 0
    total_hits = 0
    exact_hits = 0
    semantic_hits = 0
    
    for test_case in test_cases:
        print(f"\n{'='*80}")
        print(f"📝 {test_case['name']}")
        print('='*80)
        
        case_hits = 0
        for i, query in enumerate(test_case['variations'], 1):
            print(f"\n{i}. Testing: '{query}'")
            
            result = cache.get(query)
            total_queries += 1
            
            if result:
                total_hits += 1
                case_hits += 1
                
                # Check if it was exact or semantic match
                if cache.stats["exact_hits"] > exact_hits:
                    print(f"   ✅ EXACT MATCH - Retrieved from cache")
                    exact_hits = cache.stats["exact_hits"]
                elif cache.stats["semantic_hits"] > semantic_hits:
                    print(f"   🎯 SEMANTIC MATCH - Retrieved from cache")
                    semantic_hits = cache.stats["semantic_hits"]
                
                print(f"   Preview: {result[:80]}...")
            else:
                print(f"   ❌ NO MATCH - Would query LLM")
        
        hit_rate = (case_hits / len(test_case['variations'])) * 100 if test_case['variations'] else 0
        print(f"\n📊 Hit Rate: {hit_rate:.1f}% ({case_hits}/{len(test_case['variations'])})")
    
    # Final statistics
    print("\n" + "="*80)
    print("📊 FINAL STATISTICS")
    print("="*80)
    
    overall_hit_rate = (total_hits / total_queries * 100) if total_queries > 0 else 0
    exact_rate = (exact_hits / total_queries * 100) if total_queries > 0 else 0
    semantic_rate = (semantic_hits / total_queries * 100) if total_queries > 0 else 0
    
    print(f"Total Queries Tested: {total_queries}")
    print(f"Total Hits: {total_hits} ({overall_hit_rate:.1f}%)")
    print(f"  - Exact matches: {exact_hits} ({exact_rate:.1f}%)")
    print(f"  - Semantic matches: {semantic_hits} ({semantic_rate:.1f}%)")
    print(f"Cache Misses: {total_queries - total_hits}")
    print(f"\nQuery Index Size: {len(cache.query_index)}")
    print(f"Disk Cache Files: {len(list(cache.cache_dir.glob('*.json')))}")
    
    # Show improvement
    if semantic_hits > 0:
        print(f"\n🎉 SEMANTIC MATCHING WORKING!")
        print(f"   Without semantic: {exact_rate:.1f}% hit rate")
        print(f"   With semantic: {overall_hit_rate:.1f}% hit rate")
        print(f"   Improvement: +{overall_hit_rate - exact_rate:.1f}%")
    
    print("\n" + "="*80)
    print("✅ Test completed!")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_semantic_cache()
