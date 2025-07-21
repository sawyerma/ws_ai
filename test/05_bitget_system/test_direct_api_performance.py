#!/usr/bin/env python3
"""
DIRECT API PERFORMANCE TEST
Testet Backend API Performance ohne Frontend Browser
"""

import time
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor

def test_single_api_call(url, timeout=10):
    """Einzelner API Call mit Zeitmessung"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        latency = (time.time() - start_time) * 1000  # in ms
        return True, response.status_code, latency, len(response.text)
    except Exception as e:
        return False, 0, 0, str(e)

def test_concurrent_calls(url, num_calls=10):
    """Concurrent API Calls"""
    results = []
    
    def make_call():
        return test_single_api_call(url)
    
    with ThreadPoolExecutor(max_workers=num_calls) as executor:
        futures = [executor.submit(make_call) for _ in range(num_calls)]
        for future in futures:
            results.append(future.result())
    
    return results

def main():
    print("📡 Direct API Performance Test")
    print("="*60)
    
    backend_base = "http://localhost:8100"
    
    # API Endpoints to test
    endpoints = [
        ("/health", "Health Check"),
        ("/api/v1/symbols", "Symbols API"),
        ("/api/v1/ticker", "Ticker API"),
        ("/api/v1/trades", "Trades API"),
    ]
    
    print("🔄 Testing API Performance (Direct Backend Calls)...")
    
    for endpoint, name in endpoints:
        url = f"{backend_base}{endpoint}"
        print(f"\n📊 TESTING {name} ({endpoint})")
        
        # Single Call Test
        print(f"🎯 Single Call Test...")
        success, status_code, latency, response_size = test_single_api_call(url)
        
        if success:
            print(f"✅ Status: {status_code}, Latency: {latency:.1f}ms, Size: {response_size} bytes")
        else:
            print(f"❌ Failed: {response_size}")
            continue
        
        # Multiple Sequential Calls
        print(f"🔄 Sequential Calls Test (10 calls)...")
        latencies = []
        successful_calls = 0
        
        for i in range(10):
            success, status_code, latency, _ = test_single_api_call(url)
            if success:
                latencies.append(latency)
                successful_calls += 1
        
        if latencies:
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            median_latency = statistics.median(latencies)
            
            print(f"  Success Rate: {successful_calls}/10 calls")
            print(f"  Average:      {avg_latency:.1f}ms")
            print(f"  Median:       {median_latency:.1f}ms")  
            print(f"  Min/Max:      {min_latency:.1f}ms / {max_latency:.1f}ms")
            
            # Performance Classification
            if avg_latency < 50:
                perf_rating = "⚡ EXCELLENT"
            elif avg_latency < 200:
                perf_rating = "✅ GOOD"
            elif avg_latency < 1000:
                perf_rating = "⚠️ ACCEPTABLE"
            else:
                perf_rating = "❌ SLOW"
            
            print(f"  Performance:  {perf_rating}")
        
        # Concurrent Calls Test
        print(f"🔥 Concurrent Calls Test (10 concurrent)...")
        concurrent_results = test_concurrent_calls(url, 10)
        
        successful_concurrent = [r for r in concurrent_results if r[0]]
        if successful_concurrent:
            concurrent_latencies = [r[2] for r in successful_concurrent]
            avg_concurrent = statistics.mean(concurrent_latencies)
            
            print(f"  Concurrent Success: {len(successful_concurrent)}/10")
            print(f"  Avg Concurrent Latency: {avg_concurrent:.1f}ms")
            
            # Compare sequential vs concurrent
            if len(latencies) > 0:
                performance_under_load = avg_concurrent / avg_latency
                if performance_under_load < 1.5:
                    print(f"  Load Handling: ✅ GOOD ({performance_under_load:.1f}x slower)")
                elif performance_under_load < 3:
                    print(f"  Load Handling: ⚠️ MODERATE ({performance_under_load:.1f}x slower)")
                else:
                    print(f"  Load Handling: ❌ POOR ({performance_under_load:.1f}x slower)")
        else:
            print("  ❌ All concurrent calls failed!")
    
    # Overall Backend Performance Test
    print(f"\n🏆 OVERALL BACKEND PERFORMANCE ASSESSMENT:")
    
    # Test critical endpoint performance
    symbols_url = f"{backend_base}/api/v1/symbols"
    print(f"🎯 Critical Path Test (Symbols API - 5 rapid calls)...")
    
    critical_latencies = []
    for i in range(5):
        success, _, latency, _ = test_single_api_call(symbols_url)
        if success:
            critical_latencies.append(latency)
        time.sleep(0.1)  # Small delay between calls
    
    if critical_latencies:
        avg_critical = statistics.mean(critical_latencies)
        print(f"  Critical Path Average: {avg_critical:.1f}ms")
        
        if avg_critical < 100:
            final_rating = "⚡ EXCELLENT - Backend performing optimally"
        elif avg_critical < 500:
            final_rating = "✅ GOOD - Backend performance acceptable"
        elif avg_critical < 2000:
            final_rating = "⚠️ SLOW - Backend needs optimization"
        else:
            final_rating = "❌ CRITICAL - Backend severely underperforming"
        
        print(f"  Final Rating: {final_rating}")
        
        # Diagnosis
        if avg_critical > 1000:
            print(f"\n🚨 PERFORMANCE ISSUES DETECTED:")
            print(f"  - API calls taking {avg_critical:.1f}ms (should be <200ms)")
            print(f"  - This explains slow Frontend performance!")
            print(f"  - Check: Redis cache, Database connections, Backend load")
    else:
        print("❌ Critical path test FAILED - Backend may be down!")
    
    print(f"\n🎉 Direct API Performance Test COMPLETED!")

if __name__ == "__main__":
    main()
