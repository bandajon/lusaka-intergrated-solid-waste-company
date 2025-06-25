#!/usr/bin/env python3
"""
Cache clearing utility for Lusaka waste management system.
Clears both in-memory caches and Redis caches to ensure fresh analysis results.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.analytics_cache import get_global_cache, init_global_cache
from app.utils.earth_engine_analysis import EarthEngineAnalyzer

def clear_all_caches():
    """Clear all caches in the system"""
    print("🧹 Clearing all caches...")
    
    # Clear Earth Engine analyzer cache
    print("   • Clearing Earth Engine analyzer cache...")
    try:
        analyzer = EarthEngineAnalyzer()
        if hasattr(analyzer, 'cache'):
            analyzer.cache.clear()
            print(f"     ✓ Cleared {len(analyzer.cache)} Earth Engine cache entries")
        else:
            print("     ✓ Earth Engine cache is empty")
    except Exception as e:
        print(f"     ⚠️  Error clearing Earth Engine cache: {e}")
    
    # Clear analytics cache
    print("   • Clearing analytics cache...")
    try:
        # Try to get existing global cache
        cache = get_global_cache()
        if not cache:
            # Initialize if doesn't exist
            cache = init_global_cache()
        
        # Clear different cache patterns
        patterns_to_clear = [
            'zone:*',
            'earth_engine:*', 
            'ai_prediction:*',
            'population:*',
            'building:*'
        ]
        
        total_cleared = 0
        for pattern in patterns_to_clear:
            cleared = cache.invalidate_pattern(pattern)
            total_cleared += cleared
            print(f"     ✓ Cleared {cleared} entries matching '{pattern}'")
        
        print(f"     ✓ Total analytics cache entries cleared: {total_cleared}")
        
        # Show cache stats
        stats = cache.get_stats()
        print(f"     ℹ️  Cache backend: {stats['backend']}")
        print(f"     ℹ️  Memory items: {stats['memory_items']}")
        if stats.get('redis_connected'):
            print(f"     ℹ️  Redis keys: {stats.get('redis_keys', 0)}")
            
    except Exception as e:
        print(f"     ⚠️  Error clearing analytics cache: {e}")
    
    print("\n✅ Cache clearing completed!")
    print("   Next zone analysis will use fresh GHSL population data")

if __name__ == "__main__":
    clear_all_caches()