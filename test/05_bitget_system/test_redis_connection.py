#!/usr/bin/env python3
"""
REDIS CONNECTION & PERFORMANCE TEST
Testet direkt Redis Verbindung und Performance
"""

import time
import redis
from datetime import datetime

def main():
    print("🔴 Redis Connection & Performance Test")
    print("="*60)
    
    # Redis Connection Test
    try:
        print("🔄 Connecting to Redis (localhost:6380)...")
        r = redis.Redis(host='localhost', port=6380, db=0)
        
        # Connection Test
        pong = r.ping()
        if pong:
            print("✅ Redis Connection: SUCCESS")
        else:
            print("❌ Redis Connection: FAILED")
            return
            
        # Performance Test - Write
        print("\n📊 REDIS WRITE PERFORMANCE:")
        start_time = time.time()
        for i in range(1000):
            r.set(f"test_key_{i}", f"test_value_{i}")
        write_time = time.time() - start_time
        write_ops_per_sec = 1000 / write_time
        print(f"  1000 Writes: {write_time:.2f}s ({write_ops_per_sec:.0f} ops/sec)")
        
        # Performance Test - Read
        print("\n📊 REDIS READ PERFORMANCE:")
        start_time = time.time()
        for i in range(1000):
            r.get(f"test_key_{i}")
        read_time = time.time() - start_time
        read_ops_per_sec = 1000 / read_time
        print(f"  1000 Reads:  {read_time:.2f}s ({read_ops_per_sec:.0f} ops/sec)")
        
        # Redis Info
        print("\n📊 REDIS SERVER INFO:")
        info = r.info()
        print(f"  Redis Version: {info.get('redis_version', 'Unknown')}")
        print(f"  Connected Clients: {info.get('connected_clients', 0)}")
        print(f"  Used Memory: {info.get('used_memory_human', 'Unknown')}")
        print(f"  Total Keys: {r.dbsize()}")
        
        # Cache Hit Test
        print("\n🎯 CACHE HIT/MISS TEST:")
        # Set test data
        r.set("cache_test", "cached_value", ex=60)
        
        # Test cache hit
        cached_value = r.get("cache_test")
        if cached_value:
            print("✅ Cache Hit: SUCCESS")
        else:
            print("❌ Cache Hit: FAILED")
        
        # Cleanup test keys
        for i in range(1000):
            r.delete(f"test_key_{i}")
        r.delete("cache_test")
        
        print("\n🎉 Redis Performance Test COMPLETED!")
        print(f"📊 Summary: {write_ops_per_sec:.0f} writes/sec, {read_ops_per_sec:.0f} reads/sec")
        
        # Performance Rating
        if write_ops_per_sec > 10000 and read_ops_per_sec > 10000:
            print("⚡ Performance Rating: EXCELLENT")
        elif write_ops_per_sec > 5000 and read_ops_per_sec > 5000:
            print("✅ Performance Rating: GOOD")
        else:
            print("⚠️ Performance Rating: SLOW - Check Redis config!")
            
    except redis.ConnectionError as e:
        print(f"❌ Redis Connection ERROR: {e}")
    except Exception as e:
        print(f"❌ Redis Test ERROR: {e}")

if __name__ == "__main__":
    main()
