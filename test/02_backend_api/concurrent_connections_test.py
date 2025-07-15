#!/usr/bin/env python3
"""
DarkMa Trading System - Concurrent WebSocket Connections Test
===========================================================

Test für Multiple WebSocket Clients und Skalierbarkeit (50+ Connections).
"""

import asyncio
import json
import time
import sys
import statistics
import websockets
from typing import Dict, List, Optional, Tuple
import logging
import gc
import psutil
import os

# Test Configuration
BACKEND_WS_URL = "ws://localhost:8100/ws"
MAX_CONCURRENT_CONNECTIONS = 100
TARGET_CONNECTIONS = 50
CONNECTION_TIMEOUT = 30
MESSAGE_TIMEOUT = 10
MESSAGES_PER_CLIENT = 10

class ConcurrentConnectionsTest:
    """Concurrent WebSocket Connections Test Suite"""
    
    def __init__(self):
        self.test_results = {}
        self.connection_stats = {}
        self.active_connections = []
        self.process = psutil.Process(os.getpid())
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def run_all_tests(self) -> bool:
        """Run all concurrent connection tests"""
        print("🔗 Concurrent WebSocket Connections Test Suite")
        print("=" * 60)
        print(f"🎯 Target: {TARGET_CONNECTIONS}+ concurrent connections")
        print(f"🏁 Maximum test limit: {MAX_CONCURRENT_CONNECTIONS} connections")
        
        tests = [
            ("Sequential Connection Test", self.test_sequential_connections),
            ("Concurrent Connection Burst", self.test_concurrent_burst),
            ("50+ Client Load Test", self.test_target_load),
            ("Maximum Capacity Test", self.test_maximum_capacity),
            ("Connection Stability Test", self.test_connection_stability),
            ("Message Broadcasting Load", self.test_broadcast_load),
            ("Memory Usage Under Load", self.test_memory_usage),
            ("Connection Recovery Test", self.test_connection_recovery),
            ("Graceful Degradation", self.test_graceful_degradation),
            ("Resource Cleanup Test", self.test_resource_cleanup)
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
            
            # Cleanup between tests
            await self.cleanup_connections()
            await asyncio.sleep(1)  # Brief pause between tests
            gc.collect()  # Force garbage collection
        
        self.print_performance_analysis()
        self.print_summary()
        return all_passed
    
    async def test_sequential_connections(self) -> bool:
        """Test creating connections sequentially"""
        try:
            connection_count = 20
            connections = []
            connection_times = []
            
            print(f"   Creating {connection_count} connections sequentially...")
            
            for i in range(connection_count):
                start_time = time.time()
                
                try:
                    websocket = await asyncio.wait_for(
                        websockets.connect(BACKEND_WS_URL),
                        timeout=CONNECTION_TIMEOUT
                    )
                    
                    connection_time = time.time() - start_time
                    connection_times.append(connection_time)
                    connections.append(websocket)
                    
                    if (i + 1) % 5 == 0:
                        avg_time = statistics.mean(connection_times[-5:])
                        print(f"      Connection {i + 1}: {connection_time:.3f}s (avg: {avg_time:.3f}s)")
                    
                except Exception as e:
                    print(f"      Connection {i + 1} failed: {e}")
                    break
            
            self.active_connections.extend(connections)
            
            # Test all connections are alive
            alive_count = 0
            for ws in connections:
                if ws.open:
                    try:
                        await asyncio.wait_for(ws.ping(), timeout=5)
                        alive_count += 1
                    except:
                        pass
            
            self.connection_stats["sequential"] = {
                "attempted": connection_count,
                "successful": len(connections),
                "alive": alive_count,
                "avg_connection_time": statistics.mean(connection_times) if connection_times else 0,
                "max_connection_time": max(connection_times) if connection_times else 0
            }
            
            success_rate = len(connections) / connection_count
            print(f"   📊 Sequential Connection Results:")
            print(f"      Successful: {len(connections)}/{connection_count} ({success_rate:.1%})")
            print(f"      Alive: {alive_count}/{len(connections)}")
            print(f"      Avg connection time: {statistics.mean(connection_times):.3f}s")
            
            return success_rate >= 0.9  # 90% success rate
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_concurrent_burst(self) -> bool:
        """Test creating many connections simultaneously"""
        try:
            connection_count = 25
            
            print(f"   Creating {connection_count} connections concurrently...")
            
            async def create_connection(client_id):
                try:
                    start_time = time.time()
                    websocket = await asyncio.wait_for(
                        websockets.connect(BACKEND_WS_URL),
                        timeout=CONNECTION_TIMEOUT
                    )
                    connection_time = time.time() - start_time
                    return websocket, connection_time, None
                    
                except Exception as e:
                    return None, 0, str(e)
            
            # Create all connections concurrently
            start_time = time.time()
            tasks = [create_connection(i) for i in range(connection_count)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Process results
            successful_connections = []
            connection_times = []
            errors = []
            
            for result in results:
                if isinstance(result, tuple):
                    ws, conn_time, error = result
                    if ws and not error:
                        successful_connections.append(ws)
                        connection_times.append(conn_time)
                    elif error:
                        errors.append(error)
                else:
                    errors.append(str(result))
            
            self.active_connections.extend(successful_connections)
            
            # Test connection health
            healthy_connections = 0
            for ws in successful_connections:
                if ws.open:
                    try:
                        await asyncio.wait_for(ws.ping(), timeout=2)
                        healthy_connections += 1
                    except:
                        pass
            
            self.connection_stats["concurrent_burst"] = {
                "attempted": connection_count,
                "successful": len(successful_connections),
                "healthy": healthy_connections,
                "total_time": total_time,
                "avg_connection_time": statistics.mean(connection_times) if connection_times else 0,
                "errors": len(errors)
            }
            
            success_rate = len(successful_connections) / connection_count
            health_rate = healthy_connections / len(successful_connections) if successful_connections else 0
            
            print(f"   📊 Concurrent Burst Results:")
            print(f"      Total time: {total_time:.3f}s")
            print(f"      Successful: {len(successful_connections)}/{connection_count} ({success_rate:.1%})")
            print(f"      Healthy: {healthy_connections}/{len(successful_connections)} ({health_rate:.1%})")
            print(f"      Errors: {len(errors)}")
            
            return success_rate >= 0.8 and health_rate >= 0.9  # 80% success, 90% health
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_target_load(self) -> bool:
        """Test target load of 50+ concurrent connections"""
        try:
            target_connections = TARGET_CONNECTIONS
            
            print(f"   Testing target load: {target_connections} concurrent connections...")
            
            # Create connections in batches to avoid overwhelming
            batch_size = 10
            all_connections = []
            
            for batch in range(0, target_connections, batch_size):
                batch_end = min(batch + batch_size, target_connections)
                batch_count = batch_end - batch
                
                print(f"      Creating batch {batch//batch_size + 1}: connections {batch + 1}-{batch_end}")
                
                # Create batch concurrently
                async def create_connection(client_id):
                    try:
                        ws = await asyncio.wait_for(
                            websockets.connect(BACKEND_WS_URL),
                            timeout=CONNECTION_TIMEOUT
                        )
                        return ws
                    except Exception as e:
                        print(f"         Connection {client_id} failed: {e}")
                        return None
                
                batch_tasks = [create_connection(batch + i) for i in range(batch_count)]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Filter successful connections
                batch_connections = [ws for ws in batch_results if ws and hasattr(ws, 'open')]
                all_connections.extend(batch_connections)
                
                print(f"         Batch success: {len(batch_connections)}/{batch_count}")
                
                # Brief pause between batches
                await asyncio.sleep(0.5)
            
            self.active_connections.extend(all_connections)
            
            # Test connection health and performance
            print(f"   Testing {len(all_connections)} active connections...")
            
            healthy_count = 0
            ping_times = []
            
            # Test a sample of connections for performance
            sample_size = min(20, len(all_connections))
            sample_connections = all_connections[:sample_size]
            
            for i, ws in enumerate(sample_connections):
                if ws.open:
                    try:
                        start_time = time.time()
                        await asyncio.wait_for(ws.ping(), timeout=5)
                        ping_time = (time.time() - start_time) * 1000
                        ping_times.append(ping_time)
                        healthy_count += 1
                        
                        if i % 5 == 0:
                            print(f"      Connection {i + 1}: {ping_time:.2f}ms")
                            
                    except Exception as e:
                        print(f"      Connection {i + 1} unhealthy: {e}")
            
            # Send test messages to verify functionality
            message_success = 0
            test_message = {"type": "load_test", "timestamp": time.time()}
            
            for ws in sample_connections[:10]:  # Test first 10 connections
                if ws.open:
                    try:
                        await ws.send(json.dumps(test_message))
                        message_success += 1
                    except:
                        pass
            
            self.connection_stats["target_load"] = {
                "target": target_connections,
                "achieved": len(all_connections),
                "healthy_sample": healthy_count,
                "sample_size": sample_size,
                "avg_ping_time": statistics.mean(ping_times) if ping_times else 0,
                "message_success": message_success
            }
            
            achievement_rate = len(all_connections) / target_connections
            health_rate = healthy_count / sample_size if sample_size > 0 else 0
            avg_ping = statistics.mean(ping_times) if ping_times else 0
            
            print(f"   📊 Target Load Results:")
            print(f"      Achieved: {len(all_connections)}/{target_connections} ({achievement_rate:.1%})")
            print(f"      Health rate: {healthy_count}/{sample_size} ({health_rate:.1%})")
            print(f"      Average ping: {avg_ping:.2f}ms")
            print(f"      Message success: {message_success}/10")
            
            # Success if we achieve target with good health and performance
            return (achievement_rate >= 1.0 and health_rate >= 0.8 and 
                   avg_ping < 200 and message_success >= 8)
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_maximum_capacity(self) -> bool:
        """Test maximum connection capacity"""
        try:
            print(f"   Testing maximum capacity up to {MAX_CONCURRENT_CONNECTIONS} connections...")
            
            connections = []
            connection_count = 0
            failure_count = 0
            max_consecutive_failures = 5
            
            # Keep creating connections until we hit failures
            while (connection_count < MAX_CONCURRENT_CONNECTIONS and 
                   failure_count < max_consecutive_failures):
                
                try:
                    ws = await asyncio.wait_for(
                        websockets.connect(BACKEND_WS_URL),
                        timeout=CONNECTION_TIMEOUT
                    )
                    
                    connections.append(ws)
                    connection_count += 1
                    failure_count = 0  # Reset failure count on success
                    
                    if connection_count % 10 == 0:
                        print(f"      Created {connection_count} connections...")
                    
                except Exception as e:
                    failure_count += 1
                    print(f"      Connection {connection_count + 1} failed: {e}")
                
                # Brief pause to avoid overwhelming
                if connection_count % 20 == 0:
                    await asyncio.sleep(0.1)
            
            self.active_connections.extend(connections)
            
            # Test a sample for health
            sample_size = min(20, len(connections))
            healthy_sample = 0
            
            for ws in connections[:sample_size]:
                if ws.open:
                    try:
                        await asyncio.wait_for(ws.ping(), timeout=3)
                        healthy_sample += 1
                    except:
                        pass
            
            self.connection_stats["maximum_capacity"] = {
                "max_connections": len(connections),
                "target_limit": MAX_CONCURRENT_CONNECTIONS,
                "healthy_sample": healthy_sample,
                "sample_size": sample_size,
                "failure_count": failure_count
            }
            
            print(f"   📊 Maximum Capacity Results:")
            print(f"      Maximum achieved: {len(connections)} connections")
            print(f"      Health sample: {healthy_sample}/{sample_size}")
            print(f"      Final failure count: {failure_count}")
            
            # Success if we achieve a reasonable maximum
            return len(connections) >= TARGET_CONNECTIONS
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_connection_stability(self) -> bool:
        """Test connection stability over time"""
        try:
            connection_count = 30
            test_duration = 60  # seconds
            
            print(f"   Testing {connection_count} connections for {test_duration} seconds...")
            
            # Create connections
            connections = []
            for i in range(connection_count):
                try:
                    ws = await websockets.connect(BACKEND_WS_URL)
                    connections.append(ws)
                except Exception as e:
                    print(f"      Connection {i + 1} failed: {e}")
            
            self.active_connections.extend(connections)
            initial_count = len(connections)
            
            print(f"      Created {initial_count} connections, monitoring stability...")
            
            # Monitor connections over time
            stable_connections = initial_count
            stability_checks = []
            
            check_interval = 10  # seconds
            checks = test_duration // check_interval
            
            for check in range(checks):
                await asyncio.sleep(check_interval)
                
                # Check how many connections are still alive
                alive_count = 0
                for ws in connections:
                    if ws.open:
                        try:
                            await asyncio.wait_for(ws.ping(), timeout=2)
                            alive_count += 1
                        except:
                            pass
                
                stability_percentage = (alive_count / initial_count) * 100
                stability_checks.append(stability_percentage)
                
                elapsed = (check + 1) * check_interval
                print(f"      {elapsed}s: {alive_count}/{initial_count} alive ({stability_percentage:.1f}%)")
            
            avg_stability = statistics.mean(stability_checks) if stability_checks else 0
            min_stability = min(stability_checks) if stability_checks else 0
            
            self.connection_stats["stability"] = {
                "initial_connections": initial_count,
                "test_duration": test_duration,
                "avg_stability": avg_stability,
                "min_stability": min_stability,
                "stability_checks": stability_checks
            }
            
            print(f"   📊 Stability Results:")
            print(f"      Average stability: {avg_stability:.1f}%")
            print(f"      Minimum stability: {min_stability:.1f}%")
            
            # Success if average stability > 90% and minimum > 80%
            return avg_stability > 90 and min_stability > 80
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_broadcast_load(self) -> bool:
        """Test message broadcasting to many clients"""
        try:
            connection_count = 40
            messages_per_broadcast = 5
            
            print(f"   Testing broadcast to {connection_count} clients...")
            
            # Create connections
            connections = []
            for i in range(connection_count):
                try:
                    ws = await websockets.connect(BACKEND_WS_URL)
                    connections.append(ws)
                except:
                    pass
            
            self.active_connections.extend(connections)
            
            print(f"      Created {len(connections)} connections for broadcast test")
            
            # Send subscription messages (simulate broadcast scenario)
            subscription_message = {
                "type": "subscribe",
                "channel": "market_data",
                "symbol": "BTCUSDT"
            }
            
            subscription_success = 0
            for ws in connections:
                try:
                    await ws.send(json.dumps(subscription_message))
                    subscription_success += 1
                except:
                    pass
            
            # Test sending rapid messages to all connections
            send_success = 0
            send_failures = 0
            
            for i in range(messages_per_broadcast):
                test_message = {
                    "type": "broadcast_test",
                    "message_id": i,
                    "timestamp": time.time()
                }
                
                batch_success = 0
                for ws in connections:
                    if ws.open:
                        try:
                            await ws.send(json.dumps(test_message))
                            batch_success += 1
                        except:
                            send_failures += 1
                
                send_success += batch_success
                print(f"      Broadcast {i + 1}: {batch_success}/{len(connections)} successful")
                
                await asyncio.sleep(0.1)  # Brief pause between broadcasts
            
            total_attempts = len(connections) * messages_per_broadcast
            success_rate = send_success / total_attempts if total_attempts > 0 else 0
            
            self.connection_stats["broadcast_load"] = {
                "connection_count": len(connections),
                "subscription_success": subscription_success,
                "total_send_attempts": total_attempts,
                "send_success": send_success,
                "send_failures": send_failures,
                "success_rate": success_rate
            }
            
            print(f"   📊 Broadcast Load Results:")
            print(f"      Connections: {len(connections)}")
            print(f"      Subscriptions: {subscription_success}/{len(connections)}")
            print(f"      Send success rate: {success_rate:.1%}")
            print(f"      Total messages sent: {send_success}")
            
            return success_rate > 0.85  # 85% success rate for broadcasts
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_memory_usage(self) -> bool:
        """Test memory usage under connection load"""
        try:
            print(f"   Monitoring memory usage during connection load...")
            
            # Get initial memory usage
            initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            print(f"      Initial memory usage: {initial_memory:.1f} MB")
            
            connection_count = 50
            connections = []
            memory_samples = [initial_memory]
            
            # Create connections and monitor memory
            for i in range(connection_count):
                try:
                    ws = await websockets.connect(BACKEND_WS_URL)
                    connections.append(ws)
                    
                    if (i + 1) % 10 == 0:
                        current_memory = self.process.memory_info().rss / 1024 / 1024
                        memory_samples.append(current_memory)
                        memory_increase = current_memory - initial_memory
                        print(f"      {i + 1} connections: {current_memory:.1f} MB (+{memory_increase:.1f} MB)")
                        
                except:
                    pass
            
            self.active_connections.extend(connections)
            
            # Final memory check
            final_memory = self.process.memory_info().rss / 1024 / 1024
            memory_samples.append(final_memory)
            
            total_increase = final_memory - initial_memory
            memory_per_connection = total_increase / len(connections) if connections else 0
            
            # Test memory after some activity
            for ws in connections[:20]:  # Test first 20
                if ws.open:
                    try:
                        test_message = {"type": "memory_test", "data": "x" * 1000}
                        await ws.send(json.dumps(test_message))
                    except:
                        pass
            
            await asyncio.sleep(2)
            activity_memory = self.process.memory_info().rss / 1024 / 1024
            
            self.connection_stats["memory_usage"] = {
                "initial_memory": initial_memory,
                "final_memory": final_memory,
                "activity_memory": activity_memory,
                "total_increase": total_increase,
                "memory_per_connection": memory_per_connection,
                "connection_count": len(connections),
                "memory_samples": memory_samples
            }
            
            print(f"   📊 Memory Usage Results:")
            print(f"      Initial: {initial_memory:.1f} MB")
            print(f"      Final: {final_memory:.1f} MB")
            print(f"      Increase: {total_increase:.1f} MB")
            print(f"      Per connection: {memory_per_connection:.2f} MB")
            print(f"      After activity: {activity_memory:.1f} MB")
            
            # Success if memory increase is reasonable (< 5MB per connection)
            return memory_per_connection < 5.0 and total_increase < 250
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_connection_recovery(self) -> bool:
        """Test connection recovery after failures"""
        try:
            print(f"   Testing connection recovery after simulated failures...")
            
            # Create initial connections
            initial_count = 30
            connections = []
            
            for i in range(initial_count):
                try:
                    ws = await websockets.connect(BACKEND_WS_URL)
                    connections.append(ws)
                except:
                    pass
            
            print(f"      Created {len(connections)} initial connections")
            
            # Forcefully close some connections
            close_count = len(connections) // 3  # Close 1/3 of connections
            for i in range(close_count):
                try:
                    await connections[i].close()
                    print(f"      Closed connection {i + 1}")
                except:
                    pass
            
            # Attempt to recreate connections
            recovered_connections = []
            for i in range(close_count):
                try:
                    ws = await asyncio.wait_for(
                        websockets.connect(BACKEND_WS_URL),
                        timeout=CONNECTION_TIMEOUT
                    )
                    recovered_connections.append(ws)
                except Exception as e:
                    print(f"      Recovery {i + 1} failed: {e}")
            
            # Add all connections to cleanup list
            self.active_connections.extend(connections[close_count:])  # Remaining original
            self.active_connections.extend(recovered_connections)      # Recovered
            
            recovery_rate = len(recovered_connections) / close_count if close_count > 0 else 0
            total_healthy = len(connections) - close_count + len(recovered_connections)
            
            self.connection_stats["recovery"] = {
                "initial_connections": len(connections),
                "closed_connections": close_count,
                "recovered_connections": len(recovered_connections),
                "recovery_rate": recovery_rate,
                "total_healthy": total_healthy
            }
            
            print(f"   📊 Recovery Results:")
            print(f"      Initial: {len(connections)}")
            print(f"      Closed: {close_count}")
            print(f"      Recovered: {len(recovered_connections)}")
            print(f"      Recovery rate: {recovery_rate:.1%}")
            
            return recovery_rate > 0.8  # 80% recovery rate
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_graceful_degradation(self) -> bool:
        """Test graceful degradation under extreme load"""
        try:
            print(f"   Testing graceful degradation under extreme load...")
            
            # Try to create more connections than reasonable
            extreme_count = min(150, MAX_CONCURRENT_CONNECTIONS)
            connections = []
            failure_threshold = 0
            
            print(f"      Attempting {extreme_count} connections...")
            
            for i in range(extreme_count):
                try:
                    ws = await asyncio.wait_for(
                        websockets.connect(BACKEND_WS_URL),
                        timeout=5  # Shorter timeout for extreme test
                    )
                    connections.append(ws)
                    
                    if (i + 1) % 25 == 0:
                        print(f"      Created {i + 1} connections...")
                        
                except Exception as e:
                    failure_threshold += 1
                    if failure_threshold > 20:  # Stop after too many failures
                        print(f"      Stopping at {i + 1} attempts due to excessive failures")
                        break
            
            self.active_connections.extend(connections)
            
            # Test if system is still responsive
            responsive_connections = 0
            sample_size = min(20, len(connections))
            
            for ws in connections[:sample_size]:
                if ws.open:
                    try:
                        await asyncio.wait_for(ws.ping(), timeout=3)
                        responsive_connections += 1
                    except:
                        pass
            
            responsiveness = responsive_connections / sample_size if sample_size > 0 else 0
            achievement_rate = len(connections) / extreme_count
            
            self.connection_stats["graceful_degradation"] = {
                "attempted": extreme_count,
                "achieved": len(connections),
                "achievement_rate": achievement_rate,
                "responsive_sample": responsive_connections,
                "sample_size": sample_size,
                "responsiveness": responsiveness
            }
            
            print(f"   📊 Graceful Degradation Results:")
            print(f"      Achieved: {len(connections)}/{extreme_count} ({achievement_rate:.1%})")
            print(f"      Responsive: {responsive_connections}/{sample_size} ({responsiveness:.1%})")
            
            # Success if we achieve reasonable performance even under extreme load
            return len(connections) >= TARGET_CONNECTIONS and responsiveness > 0.7
            
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def test_resource_cleanup(self) -> bool:
        """Test proper resource cleanup"""
        try:
            print(f"   Testing resource cleanup after connection cycles...")
            
            initial_memory = self.process.memory_info().rss / 1024 / 1024
            
            # Create and destroy connections multiple times
            cycles = 5
            connections_per_cycle = 20
            
            for cycle in range(cycles):
                print(f"      Cycle {cycle + 1}: Creating {connections_per_cycle} connections...")
                
                cycle_connections = []
                for i in range(connections_per_cycle):
                    try:
                        ws = await websockets.connect(BACKEND_WS_URL)
                        cycle_connections.append(ws)
                    except:
                        pass
                
                # Use connections briefly
                for ws in cycle_connections:
                    if ws.open:
                        try:
                            test_message = {"type": "cleanup_test", "cycle": cycle}
                            await ws.send(json.dumps(test_message))
                        except:
                            pass
                
                # Close all connections
                for ws in cycle_connections:
                    try:
                        await ws.close()
                    except:
                        pass
                
                # Force garbage collection
                gc.collect()
                await asyncio.sleep(1)
                
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_diff = current_memory - initial_memory
                print(f"         Memory after cycle {cycle + 1}: {current_memory:.1f} MB (+{memory_diff:.1f} MB)")
            
            final_memory = self.process.memory_info().rss / 1024 / 1024
            total_memory_increase = final_memory - initial_memory
            
            self.connection_stats["resource_cleanup"] = {
                "cycles": cycles,
                "connections_per_cycle": connections_per_cycle,
                "initial_memory": initial_memory,
                "final_memory": final_memory,
                "total_memory_increase": total_memory_increase
            }
            
            print(f"   📊 Resource Cleanup Results:")
            print(f"      Initial memory: {initial_memory:.1f} MB")
            print(f"      Final memory: {final_memory:.1f} MB")
            print(f"      Total increase: {total_memory_increase:.1f} MB")
            
            # Success if memory increase is minimal (< 50MB after all cycles)
            return total_memory_increase < 50
            
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
        gc.collect()  # Force garbage collection after cleanup
    
    def print_performance_analysis(self):
        """Print comprehensive performance analysis"""
        print("\n" + "=" * 60)
        print("📊 Concurrent Connections Performance Analysis")
        print("=" * 60)
        
        if not self.connection_stats:
            print("❌ No performance data available")
            return
        
        # Overall assessment
        key_metrics = {}
        
        if "target_load" in self.connection_stats:
            target_data = self.connection_stats["target_load"]
            key_metrics["target_achievement"] = target_data.get("achieved", 0)
            key_metrics["target_health"] = target_data.get("healthy_sample", 0) / target_data.get("sample_size", 1)
            key_metrics["target_ping"] = target_data.get("avg_ping_time", 0)
        
        if "maximum_capacity" in self.connection_stats:
            max_data = self.connection_stats["maximum_capacity"]
            key_metrics["max_connections"] = max_data.get("max_connections", 0)
        
        if "stability" in self.connection_stats:
            stability_data = self.connection_stats["stability"]
            key_metrics["avg_stability"] = stability_data.get("avg_stability", 0)
        
        if "memory_usage" in self.connection_stats:
            memory_data = self.connection_stats["memory_usage"]
            key_metrics["memory_per_connection"] = memory_data.get("memory_per_connection", 0)
        
        print(f"🎯 Key Performance Metrics:")
        
        if "target_achievement" in key_metrics:
            target_achieved = key_metrics["target_achievement"]
            target_status = "🎉" if target_achieved >= TARGET_CONNECTIONS else "❌"
            print(f"   {target_status} Target Load: {target_achieved}/{TARGET_CONNECTIONS} connections")
        
        if "target_health" in key_metrics:
            health_rate = key_metrics["target_health"]
            health_status = "🎉" if health_rate > 0.9 else "✅" if health_rate > 0.8 else "❌"
            print(f"   {health_status} Health Rate: {health_rate:.1%}")
        
        if "target_ping" in key_metrics:
            ping_time = key_metrics["target_ping"]
            ping_status = "🎉" if ping_time < 100 else "✅" if ping_time < 200 else "❌"
            print(f"   {ping_status} Average Ping: {ping_time:.2f}ms")
        
        if "max_connections" in key_metrics:
            max_conn = key_metrics["max_connections"]
            max_status = "🎉" if max_conn >= TARGET_CONNECTIONS * 2 else "✅" if max_conn >= TARGET_CONNECTIONS else "❌"
            print(f"   {max_status} Maximum Capacity: {max_conn} connections")
        
        if "avg_stability" in key_metrics:
            stability = key_metrics["avg_stability"]
            stability_status = "🎉" if stability > 95 else "✅" if stability > 90 else "❌"
            print(f"   {stability_status} Average Stability: {stability:.1f}%")
        
        if "memory_per_connection" in key_metrics:
            memory_per = key_metrics["memory_per_connection"]
            memory_status = "🎉" if memory_per < 2 else "✅" if memory_per < 5 else "❌"
            print(f"   {memory_status} Memory Per Connection: {memory_per:.2f} MB")
        
        # Detailed breakdown
        print(f"\n📈 Detailed Performance Breakdown:")
        for test_name, data in self.connection_stats.items():
            if isinstance(data, dict):
                print(f"\n   {test_name.replace('_', ' ').title()}:")
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        if "time" in key.lower():
                            if value < 1:
                                print(f"      {key}: {value*1000:.0f}ms")
                            else:
                                print(f"      {key}: {value:.2f}s")
                        elif "rate" in key.lower() or "percentage" in key.lower():
                            print(f"      {key}: {value:.1%}")
                        elif "memory" in key.lower():
                            print(f"      {key}: {value:.1f} MB")
                        else:
                            print(f"      {key}: {value}")
        
        # Performance recommendations
        print(f"\n💡 Performance Recommendations:")
        
        if key_metrics.get("memory_per_connection", 0) > 3:
            print("   • Consider optimizing memory usage per connection")
        
        if key_metrics.get("target_ping", 0) > 150:
            print("   • Network latency may need optimization")
        
        if key_metrics.get("avg_stability", 100) < 95:
            print("   • Connection stability could be improved")
        
        if key_metrics.get("max_connections", 0) < TARGET_CONNECTIONS * 1.5:
            print("   • Maximum capacity may be limiting scalability")
        
        if all(metric > threshold for metric, threshold in [
            (key_metrics.get("target_achievement", 0), TARGET_CONNECTIONS),
            (key_metrics.get("target_health", 0), 0.9),
            (key_metrics.get("avg_stability", 0), 95)
        ]):
            print("   🎉 Excellent! System meets all scalability requirements")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 Concurrent Connections Test Summary")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results.values() if r['status'] == 'PASS')
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            duration = result.get('duration', 'N/A')
            print(f"{status_icon} {test_name}: {result['status']} ({duration})")
        
        print(f"\nResult: {passed}/{total} tests passed")
        
        # Overall system assessment
        if passed == total:
            print("🎉 All concurrent connection tests PASSED!")
            print(f"⚡ System successfully handles {TARGET_CONNECTIONS}+ concurrent connections!")
        else:
            print("⚠️  Some concurrent connection tests FAILED!")
            print("🚨 Scalability requirements not fully met!")
        
        # Quick stats if available
        if "target_load" in self.connection_stats:
            target_data = self.connection_stats["target_load"]
            achieved = target_data.get("achieved", 0)
            print(f"📈 Maximum concurrent connections achieved: {achieved}")


async def main():
    """Main test execution"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python concurrent_connections_test.py")
        print("Tests concurrent WebSocket connections for DarkMa Trading System")
        print(f"Target: {TARGET_CONNECTIONS}+ concurrent connections")
        print(f"Maximum test limit: {MAX_CONCURRENT_CONNECTIONS} connections")
        return
    
    test_suite = ConcurrentConnectionsTest()
    success = await test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
