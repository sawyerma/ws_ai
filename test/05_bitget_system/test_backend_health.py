#!/usr/bin/env python3
"""
BACKEND HEALTH & LATENCY TEST
Testet Backend API Performance und Health Status
"""

import time
import requests
from datetime import datetime

def test_api_call(url, timeout=5):
    """Testet einen API Call und misst Latenz"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        latency = (time.time() - start_time) * 1000  # in ms
        return True, response.status_code, latency, response.text[:200]
    except requests.exceptions.RequestException as e:
        return False, 0, 0, str(e)

def main():
    print("🏥 Backend Health & Latency Test")
    print("="*60)
    
    backend_base = "http://localhost:8100"
    
    # Test Suite
    tests = [
        ("/health", "Health Endpoint"),
        ("/api/v1/symbols", "Symbols API"),
        ("/api/v1/ticker", "Ticker API"),
        ("/api/v1/trades", "Trades API"),
    ]
    
    results = []
    
    print("🔄 Testing Backend Endpoints...")
    for endpoint, name in tests:
        url = f"{backend_base}{endpoint}"
        print(f"\n📡 Testing {name} ({endpoint})...")
        
        success, status_code, latency, response_preview = test_api_call(url)
        
        if success:
            print(f"✅ {name}: {status_code} - {latency:.1f}ms")
            if latency > 1000:
                print(f"⚠️  WARNING: High latency ({latency:.1f}ms)")
        else:
            print(f"❌ {name}: FAILED - {response_preview}")
        
        results.append({
            'name': name,
            'success': success,
            'status_code': status_code,
            'latency': latency
        })
    
    # Performance Analysis
    print("\n📊 BACKEND PERFORMANCE ANALYSIS:")
    successful_tests = [r for r in results if r['success']]
    
    if successful_tests:
        avg_latency = sum(r['latency'] for r in successful_tests) / len(successful_tests)
        max_latency = max(r['latency'] for r in successful_tests)
        min_latency = min(r['latency'] for r in successful_tests)
        
        print(f"  Average Latency: {avg_latency:.1f}ms")
        print(f"  Fastest Call:    {min_latency:.1f}ms")
        print(f"  Slowest Call:    {max_latency:.1f}ms")
        print(f"  Success Rate:    {len(successful_tests)}/{len(tests)} ({len(successful_tests)/len(tests)*100:.1f}%)")
        
        # Performance Rating
        if avg_latency < 50:
            rating = "⚡ EXCELLENT"
        elif avg_latency < 200:
            rating = "✅ GOOD"
        elif avg_latency < 1000:
            rating = "⚠️ ACCEPTABLE"
        else:
            rating = "❌ SLOW"
        
        print(f"  Performance Rating: {rating}")
        
        # Specific Warnings
        if avg_latency > 500:
            print("\n🚨 PERFORMANCE ISSUES DETECTED:")
            print("  - Backend API calls are too slow")
            print("  - Check Redis cache configuration")
            print("  - Check database connections")
            print("  - Check backend resource usage")
    else:
        print("❌ ALL BACKEND TESTS FAILED!")
        print("🚨 Backend may be down or unreachable")
    
    # Load Test
    print("\n🔥 BACKEND LOAD TEST (10 concurrent calls):")
    start_time = time.time()
    health_url = f"{backend_base}/health"
    
    total_time = 0
    successful_calls = 0
    
    for i in range(10):
        success, status_code, latency, _ = test_api_call(health_url, timeout=10)
        if success:
            successful_calls += 1
            total_time += latency
    
    if successful_calls > 0:
        avg_load_latency = total_time / successful_calls
        print(f"  Load Test Results: {successful_calls}/10 successful")
        print(f"  Average Latency under load: {avg_load_latency:.1f}ms")
        
        if avg_load_latency > avg_latency * 2:
            print("⚠️  WARNING: Performance degrades significantly under load!")
    else:
        print("❌ Load test FAILED - Backend unresponsive")
    
    print(f"\n🎉 Backend Health Test COMPLETED!")

if __name__ == "__main__":
    main()
