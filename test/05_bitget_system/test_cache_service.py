#!/usr/bin/env python3
"""
CACHE SERVICE FUNCTION TEST
Testet ob Backend Cache Service korrekt funktioniert
"""

import time
import requests
import redis
from datetime import datetime

def main():
    print("🗄️  Cache Service Function Test")
    print("="*60)
    
    # Redis Connection
    try:
        print("🔄 Connecting to Redis...")
        r = redis.Redis(host='localhost', port=6380, db=0)
        r.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return
    
    backend_base = "http://localhost:8100"
    
    # Clear Redis cache for clean test
    print("\n🧹 Clearing Redis cache...")
    r.flushdb()
    print("✅ Cache cleared")
    
    # Test 1: Cache Miss (first call should be slow)
    print("\n🎯 TEST 1: Cache Miss (first API call)")
    url = f"{backend_base}/api/v1/symbols"
    
    start_time = time.time()
    try:
        response = requests.get(url, timeout=10)
        first_call_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            print(f"✅ First call: {first_call_time:.1f}ms (Cache MISS)")
        else:
            print(f"❌ First call failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ First call error: {e}")
        return
    
    # Check if data was cached
    time.sleep(0.5)  # Wait for cache write
    cache_keys = r.keys("*symbols*")
    if cache_keys:
        print(f"✅ Data cached: {len(cache_keys)} cache keys found")
    else:
        print("⚠️  No cache keys found - Cache may not be working")
    
    # Test 2: Cache Hit (second call should be fast)
    print("\n🎯 TEST 2: Cache Hit (second API call)")
    
    start_time = time.time()
    try:
        response = requests.get(url, timeout=10)
        second_call_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            print(f"✅ Second call: {second_call_time:.1f}ms (Cache HIT)")
        else:
            print(f"❌ Second call failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Second call error: {e}")
        return
    
    # Test 3: Cache Performance Analysis
    print("\n📊 CACHE PERFORMANCE ANALYSIS:")
    speed_improvement = first_call_time / second_call_time if second_call_time > 0 else 0
    
    print(f"  First Call (Miss):  {first_call_time:.1f}ms")
    print(f"  Second Call (Hit):  {second_call_time:.1f}ms")
    print(f"  Speed Improvement:  {speed_improvement:.1f}x faster")
    
    # Cache Effectiveness Rating
    if speed_improvement > 10:
        print("⚡ Cache Effectiveness: EXCELLENT")
    elif speed_improvement > 5:
        print("✅ Cache Effectiveness: GOOD")
    elif speed_improvement > 2:
        print("⚠️ Cache Effectiveness: MODERATE")
    else:
        print("❌ Cache Effectiveness: POOR - Cache may not be working!")
    
    # Test 4: Multiple Endpoints Cache Test
    print("\n🔥 TEST 4: Multiple Endpoints Cache Test")
    endpoints = [
        "/api/v1/ticker",
        "/api/v1/trades",
    ]
    
    for endpoint in endpoints:
        url = f"{backend_base}{endpoint}"
        print(f"\n📡 Testing {endpoint}...")
        
        # First call (should cache)
        start_time = time.time()
        try:
            response1 = requests.get(url, timeout=10)
            first_time = (time.time() - start_time) * 1000
            
            # Second call (should use cache)
            start_time = time.time()
            response2 = requests.get(url, timeout=10)
            second_time = (time.time() - start_time) * 1000
            
            if response1.status_code == 200 and response2.status_code == 200:
                improvement = first_time / second_time if second_time > 0 else 0
                print(f"  First:  {first_time:.1f}ms, Second: {second_time:.1f}ms ({improvement:.1f}x)")
                
                if improvement < 2:
                    print(f"  ⚠️  Cache may not be working for {endpoint}")
            else:
                print(f"  ❌ Endpoint failed: {response1.status_code}/{response2.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Test 5: Redis Cache Inspection
    print("\n🔍 REDIS CACHE INSPECTION:")
    all_keys = r.keys("*")
    print(f"  Total Cache Keys: {len(all_keys)}")
    
    if all_keys:
        print("  Sample Cache Keys:")
        for key in all_keys[:5]:  # Show first 5 keys
            key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
            ttl = r.ttl(key)
            print(f"    {key_str} (TTL: {ttl}s)")
    
    # Overall Assessment
    print(f"\n📊 CACHE SERVICE ASSESSMENT:")
    if len(all_keys) > 0 and speed_improvement > 3:
        print("✅ Cache Service is WORKING correctly")
    elif len(all_keys) > 0 and speed_improvement > 1.5:
        print("⚠️  Cache Service is working but SUBOPTIMAL")
    else:
        print("❌ Cache Service appears to be NOT WORKING")
        print("🚨 This explains why API calls are slow!")
        print("💡 Check backend cache configuration:")
        print("   - Redis connection in backend")
        print("   - Cache service implementation")
        print("   - Cache decorators on API endpoints")
    
    print(f"\n🎉 Cache Service Test COMPLETED!")

if __name__ == "__main__":
    main()
