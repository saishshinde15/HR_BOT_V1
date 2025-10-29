"""
Pre-warm the response cache with common HR queries
Run this script to populate cache before production deployment
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.hr_bot.crew import HrBot

# 25 MOST common HR queries based on real employee needs
# Prioritized by frequency and importance
COMMON_QUERIES = [
    # Top 5 - Most frequent
    "What is the sick leave policy?",
    "How do I request vacation time?",
    "What are my annual leave entitlements?",
    "How do I report an absence?",
    "What health benefits are available?",
    
    # Next 10 - High frequency
    "How do I request paternity leave?",
    "How do I request maternity leave?",
    "What is the remote work policy?",
    "How do I submit an expense claim?",
    "How do I access my payslip?",
    "What training opportunities are available?",
    "How do I refer a candidate?",
    "What is the bereavement leave policy?",
    "How do I update my personal information?",
    "What is the company dress code?",
    
    # Next 10 - Medium frequency
    "How do I request flexible working?",
    "What are the probation period terms?",
    "How do I raise a grievance?",
    "How do I book a meeting room?",
    "What wellness programs are offered?",
    "How do I access employee assistance?",
    "What is the work from home policy?",
    "How do I request parental leave?",
    "What equipment can I request?",
    "How do I change my emergency contact?",
]


def prewarm_cache(verbose: bool = True):
    """
    Pre-warm cache with common queries
    
    Args:
        verbose: If True, print progress. If False, silent mode.
    """
    if verbose:
        print("🔥 Starting cache pre-warming...")
        print(f"📝 Queries to cache: {len(COMMON_QUERIES)}\n")
    
    bot = HrBot()
    successful = 0
    failed = 0
    total_time = 0
    
    for idx, query in enumerate(COMMON_QUERIES, 1):
        if verbose:
            print(f"[{idx}/{len(COMMON_QUERIES)}] Processing: {query[:60]}...")
        
        start = time.time()
        
        try:
            response = bot.query_with_cache(query, skip_memory=True)  # Skip memory for faster pre-warming
            elapsed = time.time() - start
            total_time += elapsed
            successful += 1
            
            if verbose:
                print(f"    ✅ Cached in {elapsed:.1f}s\n")
        except Exception as e:
            failed += 1
            if verbose:
                print(f"    ❌ Error: {e}\n")
            continue
    
    # Show final stats
    stats = bot.get_cache_stats()
    
    if verbose:
        print("\n" + "="*70)
        print("🎉 PRE-WARMING COMPLETE!")
        print("="*70)
        print(f"✅ Successfully cached: {successful}/{len(COMMON_QUERIES)} queries")
        print(f"❌ Failed: {failed}/{len(COMMON_QUERIES)} queries")
        print(f"⏱️  Total time: {total_time:.1f}s (avg: {total_time/max(successful, 1):.1f}s per query)")
        print(f"\n📊 Cache Statistics:")
        print(f"   • Total queries: {stats['total_queries']}")
        print(f"   • Memory cache size: {stats['memory_cache_size']}")
        print(f"   • Disk cache size: {stats.get('disk_cache_size', 'N/A')}")
        print(f"   • Cache hit rate: {stats['hit_rate']}")
        print(f"\n⚡ Your app is now ready for INSTANT responses!")
        print("="*70)
    
    return successful, failed, stats


if __name__ == "__main__":
    prewarm_cache(verbose=True)

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from hr_bot.crew import HrBot

# Top 30 most common HR queries across different topics
COMMON_QUERIES = [
    # Leave & Time Off
    "What is the sick leave policy?",
    "How do I request paternity leave?",
    "What are my vacation entitlements?",
    "How do I report an absence?",
    "What is the bereavement leave policy?",
    "What is the annual leave policy?",
    "How do I request parental leave?",
    "How many days of sick leave do I get?",
    "Can I carry over unused vacation days?",
    "What is the maternity leave policy?",
    
    # Benefits & Compensation
    "What health benefits are available?",
    "How do I access my payslip?",
    "What wellness programs are offered?",
    "What are the company health insurance options?",
    "How does the pension scheme work?",
    
    # Expenses & Claims
    "How do I submit an expense claim?",
    "What expenses can I claim?",
    "How long does expense reimbursement take?",
    
    # Work Arrangements
    "What is the remote work policy?",
    "How do I request flexible working?",
    "What is the company dress code?",
    "Can I work from home?",
    
    # Professional Development
    "What training opportunities are available?",
    "How do I access learning resources?",
    "What is the performance review process?",
    
    # Administrative
    "How do I update my personal information?",
    "How do I refer a candidate?",
    "How do I book a meeting room?",
    "How do I raise a grievance?",
    "What are the probation period terms?",
    "How do I access employee assistance?"
]


def prewarm_cache(verbose: bool = True):
    """
    Pre-generate and cache responses for common queries.
    
    This significantly speeds up the first-time user experience by
    ensuring popular questions have instant responses.
    """
    print("=" * 70)
    print("🔥 CACHE PRE-WARMING STARTED")
    print("=" * 70)
    print(f"📋 Caching {len(COMMON_QUERIES)} common HR queries...")
    print()
    
    # Initialize bot
    bot = HrBot()
    
    # Track statistics
    success_count = 0
    error_count = 0
    
    for i, query in enumerate(COMMON_QUERIES, 1):
        if verbose:
            print(f"[{i:2d}/{len(COMMON_QUERIES)}] {query}")
        
        try:
            # Query with cache - this will generate and cache the response
            response = bot.query_with_cache(query)
            
            if response:
                success_count += 1
                if verbose:
                    print(f"      ✅ Cached ({len(response)} chars)")
            else:
                error_count += 1
                if verbose:
                    print(f"      ⚠️  Empty response")
        
        except Exception as e:
            error_count += 1
            if verbose:
                print(f"      ❌ Error: {str(e)[:60]}")
        
        if verbose:
            print()
    
    # Display final statistics
    print("=" * 70)
    print("📊 CACHE PRE-WARMING COMPLETE")
    print("=" * 70)
    print(f"✅ Successfully cached: {success_count}/{len(COMMON_QUERIES)}")
    print(f"❌ Errors: {error_count}/{len(COMMON_QUERIES)}")
    
    # Get cache stats
    try:
        stats = bot.get_cache_stats()
        print()
        print("📈 Cache Statistics:")
        print(f"   - Total queries processed: {stats['total_queries']}")
        print(f"   - Cache hit rate: {stats['hit_rate']}")
        print(f"   - Memory cache size: {stats['memory_cache_size']} items")
        print(f"   - Disk cache files: {stats['disk_cache_files']} files")
    except Exception as e:
        print(f"⚠️  Could not retrieve cache stats: {e}")
    
    print("=" * 70)
    print()
    print("🚀 Your HR Bot is now pre-warmed for maximum performance!")
    print("💡 Common queries will now return instant responses (<0.5s)")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pre-warm HR Bot response cache")
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress detailed output"
    )
    
    args = parser.parse_args()
    
    prewarm_cache(verbose=not args.quiet)
