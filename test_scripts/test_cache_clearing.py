"""
Test script to verify cache clearing functionality
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hr_bot.crew import HrBot

def test_cache_clearing():
    """Test that cache clearing works correctly"""
    
    print("🧪 Testing Cache Clearing Functionality...")
    print("=" * 80)
    
    # Initialize bot
    bot = HrBot()
    
    # Test query
    test_query = "What is the sick leave policy?"
    
    print(f"\n1️⃣ First query (should be MISS - no cache): '{test_query}'")
    response1 = bot.run_crew(test_query)
    print(f"   Response length: {len(response1)} chars")
    
    # Check cache stats
    stats1 = bot.get_cache_stats()
    print(f"   Cache hits: {stats1['hits']}, misses: {stats1['misses']}")
    
    print(f"\n2️⃣ Second query (should be HIT - cached): '{test_query}'")
    response2 = bot.run_crew(test_query)
    print(f"   Response length: {len(response2)} chars")
    print(f"   Responses match: {response1 == response2}")
    
    # Check cache stats
    stats2 = bot.get_cache_stats()
    print(f"   Cache hits: {stats2['hits']}, misses: {stats2['misses']}")
    
    print(f"\n3️⃣ Clearing cache...")
    bot.crew_manager.response_cache.clear_all()
    print(f"   ✅ Cache cleared!")
    
    # Check cache stats after clearing
    stats3 = bot.get_cache_stats()
    print(f"   Cache hits: {stats3['hits']}, misses: {stats3['misses']}")
    
    print(f"\n4️⃣ Third query (should be MISS - cache cleared): '{test_query}'")
    response3 = bot.run_crew(test_query)
    print(f"   Response length: {len(response3)} chars")
    
    # Check cache stats
    stats4 = bot.get_cache_stats()
    print(f"   Cache hits: {stats4['hits']}, misses: {stats4['misses']}")
    
    print("\n" + "=" * 80)
    print("✅ TEST RESULTS:")
    print(f"   First query cached: {'✅' if stats2['hits'] > stats1['hits'] else '❌'}")
    print(f"   Cache cleared successfully: {'✅' if stats3['disk_cache_files'] == 0 else '❌'}")
    print(f"   Post-clear query required fresh execution: {'✅' if stats4['misses'] > stats3['misses'] else '❌'}")
    print("=" * 80)

if __name__ == "__main__":
    test_cache_clearing()
