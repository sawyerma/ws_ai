#!/usr/bin/env python3
"""
DarkMa Trading System - WebSocket Latency Tests
==============================================

Kritische Latenz-Tests für WebSocket Performance (Sub-100ms Anforderung).
"""

import asyncio
import json
import time
import sys
import statistics
import websockets
from typing import Dict, List, Optional, Tuple
import logging

# Test Configuration
BACKEND_WS_URL = "ws://localhost:8100/ws"
BACKEND_HTTP_URL = "http://localhost:8100"
LATENCY_THRESHOLD = 100  # milliseconds - CRITICAL REQUIREMENT
LATENCY_TARGET = 50     # milliseconds - OPTIMAL TARGET
LATENCY_SAMPLES = 100   # number of latency measurements
CONCURRENT_CLIENTS = 10 # concurrent clients for load testing

class LatencyTest:
    """WebSocket Latency Test Suite"""
    
    def __init__(self):
        self.test_results = {}
        self.latency_measurements = {}
        self.active_connections = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def run_all_tests(self) -> bool:
        """Run all latency tests"""
        print("⚡ WebSocket Latency Test Suite")
        print("=" * 50)
        print(f"🎯 Target: <{LATENCY_TARGET}ms (Optimal), <{LATENCY_THRESHOLD}ms (Critical)")
        
        tests = [
            ("Single Client Ping Latency", self.test_ping_latency),
            ("Message Round-Trip Latency", self.test_message_latency),
            ("Burst Message Latency", self.test_burst_latency),
            ("Multiple Client Latency", self.test_concurrent_latency),
            ("Large Message Latency", self.test_large_message_latency),
            ("Sustained Load Latency", self.test_sustained_load_latency),
            ("Cold Start Latency", self.test_cold_start_latency),
            ("Network Jitter Analysis", self.test_network_jitter),
            ("Peak Hour Simulation", self.test_peak_hour_latency),
            ("Latency Under Stress", self.test_stress_latency)
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                start_time = time.time()
                result = await test_func()
                duration = time.time() - start_time
                
                self.test_results[test_name] = {
                    "status": "PASS" if result else "FAIL",
                    "duration": f"{duration:.2f}s"
                }
                
                if result:
                    print(f"✅ {test_name}: PASSED ({duration:.2f}s)")
                else:
                    print(f"❌ {test_name}: FAILED ({duration:.2f}s)")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                self.test_results[test_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }
                all_passed = False
        
        await self.cleanup_connections()
        self.print_latency_analysis()
        self.print_summary()
        return all_passed
    
    async def test_ping_latency(self) -> bool:
        """Test WebSocket ping/pong latency"""
        try:
            websocket = await websockets.connect(BACKEND_WS_URL)
            self.active_connections.append(websocket)
            
            latencies = []
            
            print(f"   Measuring ping latency over {LATENCY_SAMPLES} samples...")
            
            for i in range(LATENCY_SAMPLES):
                start_time = time.time()
                pong_waiter = await websocket.ping()
                await pong_waiter
                latency_ms = (time.time() - start_time) * 1000
                
                latencies.append(latency_ms)
                
                if i % 20 == 0:
                    print(f"   Sample {i + 1}: {latency_ms:.2f}ms")
                
                # Small delay between pings
                await asyncio.sleep(0.01)
            
            # Calculate statistics
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
            
            self.latency_measurements["ping"] = {
                "samples": latencies,
                "avg": avg_latency,
                "min": min_latency,
                "max": max_latency,
                "p95": p95_latency,
                "p99": p99_latency
            }
            
            print(f"   📊 Ping Latency Statistics:")
            print(f"      Average: {avg_latency:.2f}ms")
            print(f"      Min/Max: {min_latency:.2f}ms / {max_latency:.2f}ms")
            print(f"      95th percentile: {p95_latency:.2f}ms")
            print(f"      99th percentile: {p99_latency:.2f}ms")
            
            # Pass if 95th percentile is under threshold
            success = p95_latency < LATENCY_THRESHOLD
            if success:
                if avg_latency < LATENCY_TARGET:
                    print(f"   🎉 Excellent: Average latency under target ({LATENCY_TARGET}ms)")
                else:
                    print(f"   ✅ Good: 95th percentile under threshold ({LATENCY_THRESHOLD}ms)")
            else:
                print(f"   ❌ Critical: 95th percentile exceeds threshold!")
            
            return success
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_message_latency(self) -> bool:
        """Test message round-trip latency"""
        try:
            websocket = await websockets.connect(BACKEND_WS_URL)
            self.active_connections.append(websocket)
            
            latencies = []
            message_count = 50  # Fewer samples for round-trip tests
            
            print(f"   Measuring message round-trip latency over {message_count} samples...")
            
            for i in range(message_count):
                # Send message with timestamp
                message = {
                    "type": "latency_test",
                    "message_id": i,
                    "client_timestamp": time.time(),
                    "test_data": f"latency_test_message_{i}"
                }
                
                start_time = time.time()
                await websocket.send(json.dumps(message))
                
                # Wait for echo/response (if server implements echo)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    latency_ms = (time.time() - start_time) * 1000
                    latencies.append(latency_ms)
                    
                    if i % 10 == 0:
                        print(f"   Message {i + 1}: {latency_ms:.2f}ms")
                        
                except asyncio.TimeoutError:
                    # If no echo, just measure send time
                    latency_ms = (time.time() - start_time) * 1000
                    latencies.append(latency_ms)
                
                await asyncio.sleep(0.02)  # Slightly longer delay for message tests
            
            if latencies:
                avg_latency = statistics.mean(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                p95_latency = statistics.quantiles(latencies, n=20)[18]
                
                self.latency_measurements["message"] = {
                    "samples": latencies,
                    "avg": avg_latency,
                    "min": min_latency,
                    "max": max_latency,
                    "p95": p95_latency
                }
                
                print(f"   📊 Message Latency Statistics:")
                print(f"      Average: {avg_latency:.2f}ms")
                print(f"      Min/Max: {min_latency:.2f}ms / {max_latency:.2f}ms")
                print(f"      95th percentile: {p95_latency:.2f}ms")
                
                return p95_latency < LATENCY_THRESHOLD
            else:
                print("   Warning: No latency measurements collected")
                return False
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_burst_latency(self) -> bool:
        """Test latency during burst message sending"""
        try:
            websocket = await websockets.connect(BACKEND_WS_URL)
            self.active_connections.append(websocket)
            
            burst_size = 20
            latencies = []
            
            print(f"   Testing burst latency with {burst_size} rapid messages...")
            
            # Send burst of messages
            start_time = time.time()
            send_tasks = []
            
            for i in range(burst_size):
                message = {
                    "type": "burst_test",
                    "message_id": i,
                    "timestamp": time.time()
                }
                send_tasks.append(websocket.send(json.dumps(message)))
            
            # Measure burst send time
            await asyncio.gather(*send_tasks)
            burst_duration = (time.time() - start_time) * 1000
            
            avg_message_latency = burst_duration / burst_size
            
            print(f"   Burst of {burst_size} messages sent in {burst_duration:.2f}ms")
            print(f"   Average message latency in burst: {avg_message_latency:.2f}ms")
            
            self.latency_measurements["burst"] = {
                "burst_duration": burst_duration,
                "avg_message_latency": avg_message_latency,
                "message_count": burst_size
            }
            
            return avg_message_latency < LATENCY_THRESHOLD
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_concurrent_latency(self) -> bool:
        """Test latency with multiple concurrent clients"""
        try:
            connections = []
            all_latencies = []
            
            print(f"   Testing latency with {CONCURRENT_CLIENTS} concurrent clients...")
            
            # Create multiple connections
            async def create_connection_and_test(client_id):
                try:
                    ws = await websockets.connect(BACKEND_WS_URL)
                    connections.append(ws)
                    
                    # Measure latency for this client
                    client_latencies = []
                    for i in range(10):  # 10 measurements per client
                        start_time = time.time()
                        pong_waiter = await ws.ping()
                        await pong_waiter
                        latency_ms = (time.time() - start_time) * 1000
                        client_latencies.append(latency_ms)
                        await asyncio.sleep(0.01)
                    
                    avg_client_latency = statistics.mean(client_latencies)
                    print(f"   Client {client_id}: avg {avg_client_latency:.2f}ms")
                    
                    return client_latencies
                    
                except Exception as e:
                    print(f"   Client {client_id} error: {e}")
                    return []
            
            # Run concurrent tests
            tasks = [create_connection_and_test(i) for i in range(CONCURRENT_CLIENTS)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect all latencies
            for result in results:
                if isinstance(result, list):
                    all_latencies.extend(result)
            
            # Add connections to cleanup list
            self.active_connections.extend(connections)
            
            if all_latencies:
                avg_latency = statistics.mean(all_latencies)
                p95_latency = statistics.quantiles(all_latencies, n=20)[18]
                
                self.latency_measurements["concurrent"] = {
                    "client_count": CONCURRENT_CLIENTS,
                    "total_samples": len(all_latencies),
                    "avg": avg_latency,
                    "p95": p95_latency
                }
                
                print(f"   📊 Concurrent Client Latency:")
                print(f"      Clients: {CONCURRENT_CLIENTS}")
                print(f"      Total samples: {len(all_latencies)}")
                print(f"      Average: {avg_latency:.2f}ms")
                print(f"      95th percentile: {p95_latency:.2f}ms")
                
                return p95_latency < LATENCY_THRESHOLD
            else:
                print("   Error: No latency data collected")
                return False
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_large_message_latency(self) -> bool:
        """Test latency with large messages"""
        try:
            websocket = await websockets.connect(BACKEND_WS_URL)
            self.active_connections.append(websocket)
            
            message_sizes = [1024, 10240, 102400]  # 1KB, 10KB, 100KB
            size_latencies = {}
            
            for size in message_sizes:
                print(f"   Testing {size} byte messages...")
                
                latencies = []
                large_data = "x" * size
                
                for i in range(10):  # 10 samples per size
                    message = {
                        "type": "large_message_test",
                        "size": size,
                        "data": large_data
                    }
                    
                    start_time = time.time()
                    await websocket.send(json.dumps(message))
                    latency_ms = (time.time() - start_time) * 1000
                    latencies.append(latency_ms)
                    
                    await asyncio.sleep(0.05)  # Longer delay for large messages
                
                avg_latency = statistics.mean(latencies)
                max_latency = max(latencies)
                
                size_latencies[size] = {
                    "avg": avg_latency,
                    "max": max_latency,
                    "samples": latencies
                }
                
                print(f"      {size} bytes: avg {avg_latency:.2f}ms, max {max_latency:.2f}ms")
            
            self.latency_measurements["large_messages"] = size_latencies
            
            # Check if largest messages still meet threshold
            largest_avg = size_latencies[message_sizes[-1]]["avg"]
            return largest_avg < (LATENCY_THRESHOLD * 2)  # Allow 2x threshold for large messages
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_sustained_load_latency(self) -> bool:
        """Test latency degradation under sustained load"""
        try:
            websocket = await websockets.connect(BACKEND_WS_URL)
            self.active_connections.append(websocket)
            
            duration_seconds = 30  # 30 second sustained test
            latencies = []
            
            print(f"   Running sustained load test for {duration_seconds} seconds...")
            
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < duration_seconds:
                # Send message and measure latency
                ping_start = time.time()
                pong_waiter = await websocket.ping()
                await pong_waiter
                latency_ms = (time.time() - ping_start) * 1000
                
                latencies.append(latency_ms)
                message_count += 1
                
                if message_count % 100 == 0:
                    elapsed = time.time() - start_time
                    current_avg = statistics.mean(latencies[-10:])  # Last 10 measurements
                    print(f"      {elapsed:.1f}s: {message_count} messages, recent avg: {current_avg:.2f}ms")
                
                await asyncio.sleep(0.01)  # 100 messages per second
            
            # Analyze latency degradation
            first_half = latencies[:len(latencies)//2]
            second_half = latencies[len(latencies)//2:]
            
            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)
            degradation = ((second_avg - first_avg) / first_avg) * 100
            
            self.latency_measurements["sustained"] = {
                "duration": duration_seconds,
                "message_count": message_count,
                "first_half_avg": first_avg,
                "second_half_avg": second_avg,
                "degradation_percent": degradation,
                "overall_avg": statistics.mean(latencies)
            }
            
            print(f"   📊 Sustained Load Results:")
            print(f"      Messages sent: {message_count}")
            print(f"      First half avg: {first_avg:.2f}ms")
            print(f"      Second half avg: {second_avg:.2f}ms")
            print(f"      Degradation: {degradation:.1f}%")
            
            # Pass if degradation is less than 50% and final average under threshold
            return degradation < 50 and second_avg < LATENCY_THRESHOLD
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_cold_start_latency(self) -> bool:
        """Test latency immediately after connection establishment"""
        try:
            cold_start_latencies = []
            
            print(f"   Testing cold start latency over 5 fresh connections...")
            
            for i in range(5):
                # Create fresh connection
                websocket = await websockets.connect(BACKEND_WS_URL)
                
                # Immediately test latency
                start_time = time.time()
                pong_waiter = await websocket.ping()
                await pong_waiter
                cold_latency = (time.time() - start_time) * 1000
                
                cold_start_latencies.append(cold_latency)
                print(f"   Connection {i + 1}: {cold_latency:.2f}ms")
                
                await websocket.close()
                await asyncio.sleep(0.1)  # Brief pause between connections
            
            avg_cold_start = statistics.mean(cold_start_latencies)
            max_cold_start = max(cold_start_latencies)
            
            self.latency_measurements["cold_start"] = {
                "samples": cold_start_latencies,
                "avg": avg_cold_start,
                "max": max_cold_start
            }
            
            print(f"   📊 Cold Start Latency:")
            print(f"      Average: {avg_cold_start:.2f}ms")
            print(f"      Maximum: {max_cold_start:.2f}ms")
            
            return avg_cold_start < LATENCY_THRESHOLD
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_network_jitter(self) -> bool:
        """Test network jitter and latency consistency"""
        try:
            websocket = await websockets.connect(BACKEND_WS_URL)
            self.active_connections.append(websocket)
            
            latencies = []
            jitter_samples = 100
            
            print(f"   Measuring network jitter over {jitter_samples} samples...")
            
            for i in range(jitter_samples):
                start_time = time.time()
                pong_waiter = await websocket.ping()
                await pong_waiter
                latency_ms = (time.time() - start_time) * 1000
                latencies.append(latency_ms)
                
                await asyncio.sleep(0.01)
            
            # Calculate jitter statistics
            avg_latency = statistics.mean(latencies)
            std_deviation = statistics.stdev(latencies)
            
            # Calculate jitter as difference between consecutive measurements
            jitter_values = [abs(latencies[i] - latencies[i-1]) for i in range(1, len(latencies))]
            avg_jitter = statistics.mean(jitter_values)
            max_jitter = max(jitter_values)
            
            self.latency_measurements["jitter"] = {
                "avg_latency": avg_latency,
                "std_deviation": std_deviation,
                "avg_jitter": avg_jitter,
                "max_jitter": max_jitter,
                "jitter_samples": jitter_values
            }
            
            print(f"   📊 Network Jitter Analysis:")
            print(f"      Average latency: {avg_latency:.2f}ms")
            print(f"      Standard deviation: {std_deviation:.2f}ms")
            print(f"      Average jitter: {avg_jitter:.2f}ms")
            print(f"      Maximum jitter: {max_jitter:.2f}ms")
            
            # Good jitter: avg < 10ms, max < 50ms
            return avg_jitter < 10 and max_jitter < 50
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_peak_hour_simulation(self) -> bool:
        """Simulate peak trading hour conditions"""
        try:
            # Create multiple connections to simulate peak load
            connections = []
            peak_clients = min(20, MAX_CONNECTIONS)
            
            print(f"   Simulating peak hour with {peak_clients} active clients...")
            
            # Create connections
            for i in range(peak_clients):
                ws = await websockets.connect(BACKEND_WS_URL)
                connections.append(ws)
            
            self.active_connections.extend(connections)
            
            # Simulate high-frequency trading activity
            async def simulate_trading_client(client_ws, client_id):
                client_latencies = []
                
                for i in range(20):  # 20 "trades" per client
                    # Simulate market data request
                    start_time = time.time()
                    
                    market_request = {
                        "type": "market_data_request",
                        "symbol": "BTCUSDT",
                        "timestamp": time.time()
                    }
                    
                    await client_ws.send(json.dumps(market_request))
                    latency_ms = (time.time() - start_time) * 1000
                    client_latencies.append(latency_ms)
                    
                    # Random delay to simulate real trading patterns
                    await asyncio.sleep(0.1 + (0.05 * (i % 3)))
                
                return statistics.mean(client_latencies)
            
            # Run all clients concurrently
            tasks = [simulate_trading_client(ws, i) for i, ws in enumerate(connections)]
            avg_latencies = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            valid_latencies = [lat for lat in avg_latencies if isinstance(lat, (int, float))]
            
            if valid_latencies:
                overall_avg = statistics.mean(valid_latencies)
                worst_client = max(valid_latencies)
                
                self.latency_measurements["peak_hour"] = {
                    "client_count": peak_clients,
                    "overall_avg": overall_avg,
                    "worst_client": worst_client,
                    "client_averages": valid_latencies
                }
                
                print(f"   📊 Peak Hour Simulation:")
                print(f"      Active clients: {peak_clients}")
                print(f"      Overall average: {overall_avg:.2f}ms")
                print(f"      Worst client: {worst_client:.2f}ms")
                
                return overall_avg < LATENCY_THRESHOLD and worst_client < (LATENCY_THRESHOLD * 1.5)
            else:
                print("   Error: No valid latency data from peak hour simulation")
                return False
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_stress_latency(self) -> bool:
        """Test latency under extreme stress conditions"""
        try:
            websocket = await websockets.connect(BACKEND_WS_URL)
            self.active_connections.append(websocket)
            
            print(f"   Testing latency under stress (rapid-fire messages)...")
            
            # Send messages as fast as possible
            stress_duration = 5  # seconds
            messages_sent = 0
            latencies = []
            
            start_time = time.time()
            
            while time.time() - start_time < stress_duration:
                message_start = time.time()
                
                stress_message = {
                    "type": "stress_test",
                    "message_id": messages_sent,
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(stress_message))
                
                send_latency = (time.time() - message_start) * 1000
                latencies.append(send_latency)
                messages_sent += 1
            
            messages_per_second = messages_sent / stress_duration
            avg_stress_latency = statistics.mean(latencies)
            max_stress_latency = max(latencies)
            
            self.latency_measurements["stress"] = {
                "duration": stress_duration,
                "messages_sent": messages_sent,
                "messages_per_second": messages_per_second,
                "avg_latency": avg_stress_latency,
                "max_latency": max_stress_latency
            }
            
            print(f"   📊 Stress Test Results:")
            print(f"      Messages sent: {messages_sent} in {stress_duration}s")
            print(f"      Rate: {messages_per_second:.1f} messages/second")
            print(f"      Average latency: {avg_stress_latency:.2f}ms")
            print(f"      Maximum latency: {max_stress_latency:.2f}ms")
            
            # Pass if we can maintain reasonable latency under stress
            return avg_stress_latency < (LATENCY_THRESHOLD * 2) and messages_per_second > 100
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def cleanup_connections(self):
        """Clean up all active connections"""
        for websocket in self.active_connections:
            try:
                if websocket.open:
                    await websocket.close()
            except:
                pass  # Ignore cleanup errors
        
        self.active_connections.clear()
    
    def print_latency_analysis(self):
        """Print comprehensive latency analysis"""
        print("\n" + "=" * 50)
        print("📊 Comprehensive Latency Analysis")
        print("=" * 50)
        
        if not self.latency_measurements:
            print("❌ No latency measurements available")
            return
        
        # Overall performance assessment
        all_averages = []
        critical_tests = ["ping", "message", "concurrent"]
        
        for test_name in critical_tests:
            if test_name in self.latency_measurements:
                avg = self.latency_measurements[test_name].get("avg", 0)
                all_averages.append(avg)
        
        if all_averages:
            overall_avg = statistics.mean(all_averages)
            
            print(f"🎯 Overall Performance Assessment:")
            print(f"   Combined Average Latency: {overall_avg:.2f}ms")
            
            if overall_avg < LATENCY_TARGET:
                print(f"   🎉 EXCELLENT: Well under target ({LATENCY_TARGET}ms)")
            elif overall_avg < LATENCY_THRESHOLD:
                print(f"   ✅ GOOD: Under critical threshold ({LATENCY_THRESHOLD}ms)")
            else:
                print(f"   ❌ CRITICAL: Exceeds threshold ({LATENCY_THRESHOLD}ms)")
        
        # Detailed test results
        print(f"\n📈 Detailed Test Results:")
        for test_name, data in self.latency_measurements.items():
            if isinstance(data, dict) and "avg" in data:
                avg = data["avg"]
                status = "🎉" if avg < LATENCY_TARGET else "✅" if avg < LATENCY_THRESHOLD else "❌"
                print(f"   {status} {test_name}: {avg:.2f}ms")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 Latency Test Summary")
        print("=" * 50)
        
        passed = sum(1 for r in self.test_results.values() if r['status'] == 'PASS')
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            duration = result.get('duration', 'N/A')
            print(f"{status_icon} {test_name}: {result['status']} ({duration})")
        
        print(f"\nResult: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All latency tests PASSED!")
            print("⚡ System meets sub-100ms latency requirements!")
        else:
            print("⚠️  Some latency tests FAILED!")
            print("🚨 Critical performance requirements not met!")


async def main():
    """Main test execution"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python latency_tests.py")
        print("Tests WebSocket latency for DarkMa Trading System")
