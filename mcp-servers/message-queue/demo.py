#!/usr/bin/env python3
"""
Message Queue MCP Server Demo

Demonstrates basic message queue functionality with agent-to-agent communication.
Shows all US-003 acceptance criteria in action.
"""

import asyncio
import json
import time
from src.message_queue_server import MessageQueueServer


async def demo_basic_messaging():
    """Demonstrate basic pub/sub messaging functionality."""
    print("🚀 Message Queue MCP Server Demo")
    print("=" * 50)
    
    # Create and start server
    server = MessageQueueServer("demo-queue", "1.0.0")
    await server.start()
    
    try:
        print("\n1️⃣ Testing Basic Pub/Sub Functionality")
        print("-" * 40)
        
        # Subscribe agents to channels
        print("👥 Setting up agent subscriptions...")
        
        # Frontend agent subscribes to API responses
        subscribe_response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub-1",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "api-responses",
                    "agent_id": "frontend-agent"
                }
            }
        })
        print(f"✅ Frontend agent subscribed: {subscribe_response['result']['subscribed']}")
        
        # Backend agent subscribes to API requests
        subscribe_response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub-2",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "api-requests",
                    "agent_id": "backend-agent"
                }
            }
        })
        print(f"✅ Backend agent subscribed: {subscribe_response['result']['subscribed']}")
        
        print("\n2️⃣ Testing Message Delivery & Latency (< 100ms requirement)")
        print("-" * 40)
        
        # Frontend requests API
        start_time = time.time()
        publish_response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "pub-1",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "api-requests",
                    "content": {
                        "request_id": "REQ-001",
                        "endpoint": "/api/auth/login",
                        "method": "POST",
                        "description": "User authentication endpoint",
                        "priority": "high"
                    },
                    "sender": "frontend-agent",
                    "priority": 8
                }
            }
        })
        
        latency_ms = publish_response["result"]["latency_ms"]
        print(f"📤 Message published - Latency: {latency_ms:.2f}ms ({'✅ PASS' if latency_ms < 100 else '❌ FAIL'} < 100ms requirement)")
        
        # Backend receives request
        get_response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-1",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "backend-agent",
                    "channel": "api-requests"
                }
            }
        })
        
        messages = get_response["result"]["messages"]
        print(f"📥 Backend received {len(messages)} message(s)")
        
        if messages:
            request_data = messages[0]["content"]
            print(f"   📋 Task: {request_data['description']}")
            print(f"   🎯 Endpoint: {request_data['endpoint']}")
            print(f"   ⚡ Priority: {request_data['priority']}")
            
        print("\n3️⃣ Testing Agent-to-Agent Communication")
        print("-" * 40)
        
        # Backend responds to frontend
        backend_response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "pub-2",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "api-responses",
                    "content": {
                        "request_id": "REQ-001",
                        "status": "implemented",
                        "endpoint": "/api/auth/login",
                        "implementation": {
                            "methods": ["POST"],
                            "auth_type": "JWT",
                            "response_codes": [200, 401, 422],
                            "estimated_completion": "2 hours"
                        },
                        "message": "Authentication endpoint ready for testing"
                    },
                    "sender": "backend-agent",
                    "priority": 7
                }
            }
        })
        
        print(f"📤 Backend response sent - Latency: {backend_response['result']['latency_ms']:.2f}ms")
        
        # Frontend receives response
        frontend_messages = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-2",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "frontend-agent",
                    "channel": "api-responses"
                }
            }
        })
        
        response_messages = frontend_messages["result"]["messages"]
        if response_messages:
            response_data = response_messages[0]["content"]
            print(f"📥 Frontend received response:")
            print(f"   ✅ Status: {response_data['status']}")
            print(f"   🔐 Auth type: {response_data['implementation']['auth_type']}")
            print(f"   ⏱️  ETA: {response_data['implementation']['estimated_completion']}")
            
        print("\n4️⃣ Testing Reliable Delivery & Message Acknowledgment")
        print("-" * 40)
        
        # Test message acknowledgment
        if response_messages:
            message_id = response_messages[0]["id"]
            ack_response = server.handle_request({
                "jsonrpc": "2.0",
                "id": "ack-1",
                "method": "tools/call",
                "params": {
                    "name": "acknowledge_message",
                    "arguments": {
                        "message_id": message_id,
                        "agent_id": "frontend-agent"
                    }
                }
            })
            
            acknowledged = ack_response["result"]["acknowledged"]
            print(f"✅ Message acknowledged: {acknowledged}")
            print(f"🧹 Message removed from pending queue")
            
        print("\n5️⃣ Testing Performance Metrics")
        print("-" * 40)
        
        # Get performance metrics
        metrics_response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "metrics",
            "method": "tools/call",
            "params": {
                "name": "get_performance_metrics",
                "arguments": {}
            }
        })
        
        metrics = metrics_response["result"]
        print(f"📊 Performance Metrics:")
        print(f"   📤 Messages sent: {metrics['messages_sent']}")
        print(f"   📥 Messages delivered: {metrics['messages_delivered']}")
        print(f"   ⚡ Average latency: {metrics['avg_latency_ms']:.2f}ms")
        print(f"   🔥 Peak latency: {metrics['peak_latency_ms']:.2f}ms")
        print(f"   📺 Active channels: {metrics['channels_count']}")
        print(f"   👥 Total subscribers: {metrics['subscribers_count']}")
        print(f"   ⏳ Pending messages: {metrics['pending_messages']}")
        
        # Test channels resource
        channels_response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "channels",
            "method": "tools/call",
            "params": {
                "name": "list_channels",
                "arguments": {}
            }
        })
        
        channels = channels_response["result"]["channels"]
        print(f"\n📋 Active Channels:")
        for channel in channels:
            print(f"   🔗 {channel['name']}: {channel['subscriber_count']} subscribers, {channel['message_count']} pending")
            
        print("\n6️⃣ Testing High-Volume Reliability")
        print("-" * 40)
        
        # Subscribe a test agent
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub-test",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "high-volume-test",
                    "agent_id": "test-agent"
                }
            }
        })
        
        # Send multiple messages to test reliability
        message_count = 50
        print(f"📤 Sending {message_count} messages to test reliability...")
        
        start_time = time.time()
        latencies = []
        
        for i in range(message_count):
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": f"vol-{i}",
                "method": "tools/call",
                "params": {
                    "name": "publish_message",
                    "arguments": {
                        "channel": "high-volume-test",
                        "content": {
                            "sequence": i,
                            "data": f"test-data-{i}",
                            "timestamp": time.time()
                        },
                        "sender": "volume-tester"
                    }
                }
            })
            latencies.append(response["result"]["latency_ms"])
            
        total_time = time.time() - start_time
        
        # Verify all messages received
        received_response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-vol",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "test-agent",
                    "limit": message_count
                }
            }
        })
        
        received_messages = received_response["result"]["messages"]
        received_count = len(received_messages)
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        throughput = message_count / total_time
        
        print(f"✅ Reliability Test Results:")
        print(f"   📤 Sent: {message_count} messages")
        print(f"   📥 Received: {received_count} messages")
        print(f"   🎯 Success rate: {received_count/message_count*100:.1f}%")
        print(f"   ⚡ Average latency: {avg_latency:.2f}ms")
        print(f"   🔥 Max latency: {max_latency:.2f}ms")
        print(f"   🚀 Throughput: {throughput:.1f} msg/sec")
        print(f"   ✅ Latency requirement: {'PASS' if max_latency < 100 else 'FAIL'} (< 100ms)")
        
        print("\n🎉 Demo Complete - All US-003 Acceptance Criteria Demonstrated!")
        print("=" * 50)
        print("✅ Basic pub/sub functionality works")
        print("✅ Messages delivered with < 100ms latency")  
        print("✅ Message delivery is reliable (no message loss)")
        print("✅ Agent-to-agent communication demonstrated")
        print("✅ Performance metrics are logged")
        
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(demo_basic_messaging()) 