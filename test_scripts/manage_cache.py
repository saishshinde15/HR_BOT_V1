"""
Cache Management Utility
Clear or inspect the response cache
"""

import sys
import os
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from hr_bot.crew import HrBot


def show_stats():
    """Display cache statistics"""
    bot = HrBot()
    stats = bot.get_cache_stats()
    
    print("=" * 60)
    print("📊 CACHE STATISTICS")
    print("=" * 60)
    print(f"Total Queries:        {stats['total_queries']}")
    print(f"Cache Hits:           {stats['hits']}")
    print(f"Cache Misses:         {stats['misses']}")
    print(f"Hit Rate:             {stats['hit_rate']}")
    print(f"Memory Cache Size:    {stats['memory_cache_size']} items")
    print(f"Disk Cache Files:     {stats['disk_cache_files']} files")
    print()
    print(f"Memory Hits:          {stats['memory_hits']}")
    print(f"Disk Hits:            {stats['disk_hits']}")
    print("=" * 60)


def clear_cache(cache_type: str = "all"):
    """Clear cache"""
    bot = HrBot()
    
    if cache_type == "expired":
        print("🧹 Clearing expired cache entries...")
        bot.response_cache.clear_expired()
        print("✅ Expired cache cleared!")
    elif cache_type == "all":
        print("⚠️  Clearing ALL cache entries...")
        response = input("Are you sure? (yes/no): ")
        if response.lower() == "yes":
            bot.response_cache.clear_all()
            print("✅ All cache cleared!")
        else:
            print("❌ Cancelled")
    else:
        print(f"❌ Unknown cache type: {cache_type}")


def main():
    parser = argparse.ArgumentParser(description="Manage HR Bot response cache")
    parser.add_argument(
        "action",
        choices=["stats", "clear", "clear-expired"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    if args.action == "stats":
        show_stats()
    elif args.action == "clear":
        clear_cache("all")
    elif args.action == "clear-expired":
        clear_cache("expired")


if __name__ == "__main__":
    main()
