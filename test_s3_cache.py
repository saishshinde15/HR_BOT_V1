#!/usr/bin/env python3
"""
Test script for ETag-based S3 caching
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from hr_bot.utils.s3_loader import S3DocumentLoader

def test_s3_cache():
    """Test ETag-based S3 caching"""
    print("=" * 80)
    print("Testing ETag-Based S3 Caching")
    print("=" * 80)
    
    # Test 1: First load (should download)
    print("\n📝 TEST 1: First Load (Cold Cache)")
    print("-" * 80)
    loader = S3DocumentLoader(user_role='employee', cache_ttl=86400)
    docs = loader.load_documents()
    print(f"✅ Loaded {len(docs)} documents")
    
    # Test 2: Second load (should use cache)
    print("\n📝 TEST 2: Second Load (Cache Should Be Valid)")
    print("-" * 80)
    loader2 = S3DocumentLoader(user_role='employee', cache_ttl=86400)
    docs2 = loader2.load_documents()
    print(f"✅ Loaded {len(docs2)} documents")
    
    # Test 3: Cache info
    print("\n📝 TEST 3: Cache Information")
    print("-" * 80)
    cache_info = loader2.get_cache_info()
    print(f"Cache directory: {cache_info['cache_dir']}")
    print(f"Cache valid: {cache_info['cache_valid']}")
    print(f"Cache age: {cache_info['cache_age_hours']:.2f} hours")
    print(f"Document count: {cache_info['document_count']}")
    
    # Test 4: Force refresh
    print("\n📝 TEST 4: Force Refresh")
    print("-" * 80)
    docs3 = loader2.load_documents(force_refresh=True)
    print(f"✅ Loaded {len(docs3)} documents")
    
    print("\n" + "=" * 80)
    print("✅ All tests completed successfully!")
    print("=" * 80)

if __name__ == '__main__':
    test_s3_cache()
