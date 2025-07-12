"""
Comprehensive test suite for Message Queue MCP Server

Tests all US-003 acceptance criteria:
- Basic pub/sub functionality works
- Messages are delivered with < 100ms latency
- Message delivery is reliable (no message loss)
- Simple test demonstrates agent-to-agent communication
- Performance metrics are logged
"""

import asyncio
import json
import pytest
import time
import uuid
from typing import Dict, Any
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from message_queue_server import MessageQueueServer, Message, Subscription, PerformanceMetrics


class TestBasicPubSubFunctionality:
    """Test basic pub/sub functionality acceptance criteria."""
    
    @pytest.fixture
    async def server(self):
        """Create a test server instance."""
        server = MessageQueueServer("test-queue", "1.0.0")
        await server.start()
        yield server
        await server.stop()
        
    @pytest.mark.asyncio
    async def test_publish_and_subscribe_basic(self, server):
        """Test basic publish and subscribe functionality."""
        # Subscribe to channel
        subscribe_request = {
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "test-channel",
                    "agent_id": "agent-1"
                }
            }
        }
        
        response = server.handle_request(subscribe_request)
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "test-1"
        assert "result" in response
        assert response["result"]["subscribed"] is True
        assert response["result"]["channel"] == "test-channel"
        
        # Publish message
        publish_request = {
            "jsonrpc": "2.0",
            "id": "test-2",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "test-channel",
                    "content": {"type": "greeting", "message": "Hello World"},
                    "sender": "agent-2"
                }
            }
        }
        
        response = server.handle_request(publish_request)
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "test-2"
        assert "result" in response
        assert "message_id" in response["result"]
        assert response["result"]["channel"] == "test-channel"
        
        # Get messages
        get_messages_request = {
            "jsonrpc": "2.0",
            "id": "test-3",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "agent-1",
                    "channel": "test-channel"
                }
            }
        }
        
        response = server.handle_request(get_messages_request)
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "test-3"
        assert "result" in response
        messages = response["result"]["messages"]
        assert len(messages) == 1
        assert messages[0]["content"]["message"] == "Hello World"
        assert messages[0]["sender"] == "agent-2"
        
    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_channel(self, server):
        """Test multiple agents can subscribe to the same channel."""
        # Subscribe multiple agents
        for agent_id in ["agent-1", "agent-2", "agent-3"]:
            request = {
                "jsonrpc": "2.0",
                "id": f"sub-{agent_id}",
                "method": "tools/call",
                "params": {
                    "name": "subscribe_channel",
                    "arguments": {
                        "channel": "broadcast",
                        "agent_id": agent_id
                    }
                }
            }
            response = server.handle_request(request)
            assert response["result"]["subscribed"] is True
            
        # Publish message
        publish_request = {
            "jsonrpc": "2.0",
            "id": "broadcast",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "broadcast",
                    "content": {"announcement": "Server maintenance scheduled"},
                    "sender": "system"
                }
            }
        }
        
        server.handle_request(publish_request)
        
        # All agents should receive the message
        for agent_id in ["agent-1", "agent-2", "agent-3"]:
            request = {
                "jsonrpc": "2.0",
                "id": f"get-{agent_id}",
                "method": "tools/call",
                "params": {
                    "name": "get_messages",
                    "arguments": {"agent_id": agent_id}
                }
            }
            response = server.handle_request(request)
            messages = response["result"]["messages"]
            assert len(messages) == 1
            assert messages[0]["content"]["announcement"] == "Server maintenance scheduled"
            
    @pytest.mark.asyncio
    async def test_unsubscribe_functionality(self, server):
        """Test unsubscribe functionality."""
        # Subscribe
        subscribe_request = {
            "jsonrpc": "2.0",
            "id": "sub",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "temp-channel",
                    "agent_id": "agent-temp"
                }
            }
        }
        server.handle_request(subscribe_request)
        
        # Unsubscribe
        unsubscribe_request = {
            "jsonrpc": "2.0",
            "id": "unsub",
            "method": "tools/call",
            "params": {
                "name": "unsubscribe_channel",
                "arguments": {
                    "channel": "temp-channel",
                    "agent_id": "agent-temp"
                }
            }
        }
        
        response = server.handle_request(unsubscribe_request)
        assert response["result"]["unsubscribed"] is True
        
        # Publish message after unsubscribe
        publish_request = {
            "jsonrpc": "2.0",
            "id": "pub",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "temp-channel",
                    "content": {"message": "Should not receive"},
                    "sender": "system"
                }
            }
        }
        server.handle_request(publish_request)
        
        # Agent should not receive message
        get_request = {
            "jsonrpc": "2.0",
            "id": "get",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {"agent_id": "agent-temp"}
            }
        }
        response = server.handle_request(get_request)
        assert len(response["result"]["messages"]) == 0


class TestLatencyRequirements:
    """Test latency requirements < 100ms acceptance criteria."""
    
    @pytest.fixture
    async def server(self):
        """Create a test server instance."""
        server = MessageQueueServer("latency-test", "1.0.0")
        await server.start()
        yield server
        await server.stop()
        
    @pytest.mark.asyncio
    async def test_publish_latency_under_100ms(self, server):
        """Test that message publish latency is under 100ms."""
        # Setup subscriber
        subscribe_request = {
            "jsonrpc": "2.0",
            "id": "sub",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "latency-test",
                    "agent_id": "latency-agent"
                }
            }
        }
        server.handle_request(subscribe_request)
        
        # Test multiple publish operations for latency
        latencies = []
        for i in range(10):
            start_time = time.time()
            
            publish_request = {
                "jsonrpc": "2.0",
                "id": f"pub-{i}",
                "method": "tools/call",
                "params": {
                    "name": "publish_message",
                    "arguments": {
                        "channel": "latency-test",
                        "content": {"test_id": i, "data": "x" * 100},  # Larger payload
                        "sender": "latency-tester"
                    }
                }
            }
            
            response = server.handle_request(publish_request)
            latency_ms = response["result"]["latency_ms"]
            latencies.append(latency_ms)
            
            # Verify latency is recorded and under 100ms
            assert latency_ms < 100.0, f"Latency {latency_ms}ms exceeds 100ms requirement"
            
        # Verify average latency
        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 50.0, f"Average latency {avg_latency}ms is too high"
        print(f"Average publish latency: {avg_latency:.2f}ms")
        
    @pytest.mark.asyncio
    async def test_end_to_end_latency_measurement(self, server):
        """Test end-to-end latency from publish to retrieval."""
        # Subscribe agent
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "e2e-test",
                    "agent_id": "e2e-agent"
                }
            }
        })
        
        # Measure end-to-end latency
        start_time = time.time()
        
        # Publish
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "pub",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "e2e-test",
                    "content": {"timestamp": start_time},
                    "sender": "e2e-sender"
                }
            }
        })
        
        # Retrieve
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {"agent_id": "e2e-agent"}
            }
        })
        
        end_time = time.time()
        e2e_latency_ms = (end_time - start_time) * 1000
        
        assert e2e_latency_ms < 100.0, f"End-to-end latency {e2e_latency_ms}ms exceeds 100ms"
        assert len(response["result"]["messages"]) == 1
        print(f"End-to-end latency: {e2e_latency_ms:.2f}ms")


class TestReliableMessageDelivery:
    """Test reliable message delivery (no message loss) acceptance criteria."""
    
    @pytest.fixture
    async def server(self):
        """Create a test server instance."""
        server = MessageQueueServer("reliability-test", "1.0.0")
        await server.start()
        yield server
        await server.stop()
        
    @pytest.mark.asyncio
    async def test_no_message_loss_high_volume(self, server):
        """Test no message loss under high volume."""
        # Setup multiple subscribers
        agents = [f"agent-{i}" for i in range(3)]
        for agent_id in agents:
            server.handle_request({
                "jsonrpc": "2.0",
                "id": f"sub-{agent_id}",
                "method": "tools/call",
                "params": {
                    "name": "subscribe_channel",
                    "arguments": {
                        "channel": "high-volume",
                        "agent_id": agent_id
                    }
                }
            })
            
        # Send many messages
        message_count = 100
        sent_message_ids = []
        
        for i in range(message_count):
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": f"msg-{i}",
                "method": "tools/call",
                "params": {
                    "name": "publish_message",
                    "arguments": {
                        "channel": "high-volume",
                        "content": {"sequence": i, "payload": f"data-{i}"},
                        "sender": "volume-tester"
                    }
                }
            })
            sent_message_ids.append(response["result"]["message_id"])
            
        # Verify all agents receive all messages
        for agent_id in agents:
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": f"get-{agent_id}",
                "method": "tools/call",
                "params": {
                    "name": "get_messages",
                    "arguments": {
                        "agent_id": agent_id,
                        "limit": message_count
                    }
                }
            })
            
            messages = response["result"]["messages"]
            assert len(messages) == message_count, f"Agent {agent_id} lost messages: got {len(messages)}, expected {message_count}"
            
            # Verify message order and content
            received_sequences = [msg["content"]["sequence"] for msg in messages]
            expected_sequences = list(range(message_count))
            assert sorted(received_sequences) == expected_sequences, "Message sequences don't match"
            
    @pytest.mark.asyncio
    async def test_message_acknowledgment_and_cleanup(self, server):
        """Test message acknowledgment and cleanup."""
        # Subscribe and send message
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "ack-test",
                    "agent_id": "ack-agent"
                }
            }
        })
        
        # Publish message
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "pub",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "ack-test",
                    "content": {"data": "test-acknowledgment"},
                    "sender": "ack-sender"
                }
            }
        })
        
        message_id = response["result"]["message_id"]
        
        # Verify message is pending
        assert message_id in server.pending_messages
        
        # Acknowledge message
        ack_response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "ack",
            "method": "tools/call",
            "params": {
                "name": "acknowledge_message",
                "arguments": {
                    "message_id": message_id,
                    "agent_id": "ack-agent"
                }
            }
        })
        
        assert ack_response["result"]["acknowledged"] is True
        
        # Verify message is cleaned up
        assert message_id not in server.pending_messages
        
    @pytest.mark.asyncio
    async def test_message_priority_handling(self, server):
        """Test message priority handling."""
        # Subscribe agent
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "priority-test",
                    "agent_id": "priority-agent"
                }
            }
        })
        
        # Send messages with different priorities
        priorities = [1, 5, 3, 10, 2]  # Out of order
        for i, priority in enumerate(priorities):
            server.handle_request({
                "jsonrpc": "2.0",
                "id": f"pri-{i}",
                "method": "tools/call",
                "params": {
                    "name": "publish_message",
                    "arguments": {
                        "channel": "priority-test",
                        "content": {"order": i, "priority": priority},
                        "sender": "priority-sender",
                        "priority": priority
                    }
                }
            })
            
        # Get messages and verify priority order
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-pri",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {"agent_id": "priority-agent"}
            }
        })
        
        messages = response["result"]["messages"]
        assert len(messages) == 5
        
        # Should be ordered by priority (highest first)
        received_priorities = [msg["priority"] for msg in messages]
        expected_priorities = sorted(priorities, reverse=True)
        assert received_priorities == expected_priorities


class TestAgentToAgentCommunication:
    """Test agent-to-agent communication acceptance criteria."""
    
    @pytest.fixture
    async def server(self):
        """Create a test server instance."""
        server = MessageQueueServer("agent-comm-test", "1.0.0")
        await server.start()
        yield server
        await server.stop()
        
    @pytest.mark.asyncio
    async def test_simple_agent_conversation(self, server):
        """Test simple agent-to-agent conversation."""
        # Setup two agents
        agents = ["frontend-agent", "backend-agent"]
        
        for agent in agents:
            for channel in ["api-requests", "api-responses"]:
                server.handle_request({
                    "jsonrpc": "2.0",
                    "id": f"sub-{agent}-{channel}",
                    "method": "tools/call",
                    "params": {
                        "name": "subscribe_channel",
                        "arguments": {
                            "channel": channel,
                            "agent_id": agent
                        }
                    }
                })
                
        # Frontend requests API endpoint
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "api-req",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "api-requests",
                    "content": {
                        "request_id": "req-123",
                        "endpoint": "/api/users",
                        "method": "GET",
                        "requester": "frontend-agent"
                    },
                    "sender": "frontend-agent"
                }
            }
        })
        
        # Backend receives request
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-req",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "backend-agent",
                    "channel": "api-requests"
                }
            }
        })
        
        requests = response["result"]["messages"]
        assert len(requests) == 1
        request_data = requests[0]["content"]
        assert request_data["endpoint"] == "/api/users"
        
        # Backend responds
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "api-resp",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "api-responses",
                    "content": {
                        "request_id": "req-123",
                        "status": "implemented",
                        "endpoint": "/api/users",
                        "response_code": 200,
                        "responder": "backend-agent"
                    },
                    "sender": "backend-agent"
                }
            }
        })
        
        # Frontend receives response
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-resp",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "frontend-agent",
                    "channel": "api-responses"
                }
            }
        })
        
        responses = response["result"]["messages"]
        assert len(responses) == 1
        response_data = responses[0]["content"]
        assert response_data["request_id"] == "req-123"
        assert response_data["status"] == "implemented"
        
    @pytest.mark.asyncio
    async def test_multi_agent_coordination_scenario(self, server):
        """Test complex multi-agent coordination scenario."""
        # Simulate development team coordination
        agents = ["pm-agent", "frontend-agent", "backend-agent", "tester-agent"]
        channels = ["tasks", "blockers", "updates", "reviews"]
        
        # Setup subscriptions
        for agent in agents:
            for channel in channels:
                server.handle_request({
                    "jsonrpc": "2.0",
                    "id": f"sub-{agent}-{channel}",
                    "method": "tools/call",
                    "params": {
                        "name": "subscribe_channel",
                        "arguments": {
                            "channel": channel,
                            "agent_id": agent
                        }
                    }
                })
                
        # PM creates task
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "create-task",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "tasks",
                    "content": {
                        "task_id": "TASK-001",
                        "title": "Implement user login",
                        "assigned_to": ["frontend-agent", "backend-agent"],
                        "priority": "high"
                    },
                    "sender": "pm-agent",
                    "priority": 8
                }
            }
        })
        
        # Backend reports blocker
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "report-blocker",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "blockers",
                    "content": {
                        "task_id": "TASK-001",
                        "blocker": "Need API authentication design",
                        "blocked_agent": "backend-agent",
                        "requires_input_from": "pm-agent"
                    },
                    "sender": "backend-agent",
                    "priority": 10  # High priority blocker
                }
            }
        })
        
        # Frontend provides status update
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "status-update",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "updates",
                    "content": {
                        "task_id": "TASK-001",
                        "status": "ui_mockup_ready",
                        "progress": 40,
                        "next_step": "waiting_for_api"
                    },
                    "sender": "frontend-agent",
                    "priority": 5
                }
            }
        })
        
        # Verify PM receives high-priority blocker first
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "pm-check",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {"agent_id": "pm-agent"}
            }
        })
        
        messages = response["result"]["messages"]
        assert len(messages) >= 2
        
        # First message should be the high-priority blocker
        first_message = messages[0]
        assert first_message["priority"] == 10
        assert "blocker" in first_message["content"]
        
        # Verify agents receive relevant messages
        for agent in ["frontend-agent", "backend-agent"]:
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": f"check-{agent}",
                "method": "tools/call",
                "params": {
                    "name": "get_messages",
                    "arguments": {"agent_id": agent}
                }
            })
            
            agent_messages = response["result"]["messages"]
            task_messages = [msg for msg in agent_messages if "task_id" in msg.get("content", {})]
            assert len(task_messages) >= 1, f"Agent {agent} should receive task messages"


class TestPerformanceMetrics:
    """Test performance metrics logging acceptance criteria."""
    
    @pytest.fixture
    async def server(self):
        """Create a test server instance."""
        server = MessageQueueServer("metrics-test", "1.0.0")
        await server.start()
        yield server
        await server.stop()
        
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, server):
        """Test that performance metrics are properly collected and logged."""
        # Initial metrics should be empty
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "metrics-0",
            "method": "tools/call",
            "params": {
                "name": "get_performance_metrics",
                "arguments": {}
            }
        })
        
        initial_metrics = response["result"]
        assert initial_metrics["messages_sent"] == 0
        assert initial_metrics["messages_delivered"] == 0
        assert initial_metrics["avg_latency_ms"] == 0.0
        
        # Setup and send messages
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub-metrics",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "metrics-channel",
                    "agent_id": "metrics-agent"
                }
            }
        })
        
        # Send multiple messages
        message_count = 10
        for i in range(message_count):
            server.handle_request({
                "jsonrpc": "2.0",
                "id": f"msg-{i}",
                "method": "tools/call",
                "params": {
                    "name": "publish_message",
                    "arguments": {
                        "channel": "metrics-channel",
                        "content": {"seq": i},
                        "sender": "metrics-sender"
                    }
                }
            })
            
        # Check updated metrics
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "metrics-1",
            "method": "tools/call",
            "params": {
                "name": "get_performance_metrics",
                "arguments": {}
            }
        })
        
        metrics = response["result"]
        assert metrics["messages_sent"] == message_count
        assert metrics["channels_count"] == 1
        assert metrics["subscribers_count"] == 1
        assert metrics["avg_latency_ms"] > 0.0
        assert metrics["peak_latency_ms"] > 0.0
        assert metrics["pending_messages"] == message_count
        
        # Acknowledge messages and verify delivery metrics
        get_messages_request = {
            "jsonrpc": "2.0",
            "id": "get-for-ack",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {"agent_id": "metrics-agent"}
            }
        }
        response = server.handle_request(get_messages_request)
        messages = response["result"]["messages"]
        
        # Acknowledge first message
        if messages:
            server.handle_request({
                "jsonrpc": "2.0",
                "id": "ack-msg",
                "method": "tools/call",
                "params": {
                    "name": "acknowledge_message",
                    "arguments": {
                        "message_id": messages[0]["id"],
                        "agent_id": "metrics-agent"
                    }
                }
            })
            
        # Check delivery metrics
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "metrics-2",
            "method": "tools/call",
            "params": {
                "name": "get_performance_metrics",
                "arguments": {}
            }
        })
        
        final_metrics = response["result"]
        assert final_metrics["messages_delivered"] == 1
        assert final_metrics["pending_messages"] == message_count - 1
        
    @pytest.mark.asyncio
    async def test_metrics_resource_access(self, server):
        """Test metrics access via MCP resources."""
        # Test metrics resource
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "resource-metrics",
            "method": "resources/read",
            "params": {
                "uri": "queue://metrics"
            }
        })
        
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        contents = response["result"]["contents"]
        assert len(contents) == 1
        assert contents[0]["mimeType"] == "application/json"
        
        # Parse metrics JSON
        metrics_data = json.loads(contents[0]["text"])
        assert "messages_sent" in metrics_data
        assert "avg_latency_ms" in metrics_data
        assert "timestamp" in metrics_data
        
        # Test channels resource
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "setup-channel",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "resource-test",
                    "agent_id": "resource-agent"
                }
            }
        })
        
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "resource-channels",
            "method": "resources/read",
            "params": {
                "uri": "queue://channels"
            }
        })
        
        channels_data = json.loads(response["result"]["contents"][0]["text"])
        assert "resource-test" in channels_data
        assert channels_data["resource-test"]["subscribers"] == ["resource-agent"]


# Integration test demonstrating all acceptance criteria together
class TestUS003Integration:
    """Integration test demonstrating all US-003 acceptance criteria."""
    
    @pytest.mark.asyncio
    async def test_complete_us003_acceptance_criteria(self):
        """
        Comprehensive test that validates all US-003 acceptance criteria:
        - Basic pub/sub functionality works ✓
        - Messages are delivered with < 100ms latency ✓
        - Message delivery is reliable (no message loss) ✓
        - Simple test demonstrates agent-to-agent communication ✓
        - Performance metrics are logged ✓
        """
        server = MessageQueueServer("us003-integration", "1.0.0")
        await server.start()
        
        try:
            # ✓ Test 1: Basic pub/sub functionality
            print("Testing basic pub/sub functionality...")
            
            # Subscribe agents
            agents = ["frontend", "backend", "pm"]
            for agent in agents:
                server.handle_request({
                    "jsonrpc": "2.0",
                    "id": f"sub-{agent}",
                    "method": "tools/call",
                    "params": {
                        "name": "subscribe_channel",
                        "arguments": {
                            "channel": "team-updates",
                            "agent_id": agent
                        }
                    }
                })
                
            # Publish team update
            start_time = time.time()
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": "team-update",
                "method": "tools/call",
                "params": {
                    "name": "publish_message",
                    "arguments": {
                        "channel": "team-updates",
                        "content": {
                            "type": "sprint_update",
                            "message": "Sprint planning completed",
                            "timestamp": start_time
                        },
                        "sender": "pm"
                    }
                }
            })
            
            # ✓ Test 2: Latency under 100ms
            latency_ms = response["result"]["latency_ms"]
            assert latency_ms < 100.0, f"Latency {latency_ms}ms exceeds 100ms requirement"
            print(f"✓ Publish latency: {latency_ms:.2f}ms (< 100ms requirement)")
            
            # ✓ Test 3: Reliable delivery (no message loss)
            for agent in agents:
                response = server.handle_request({
                    "jsonrpc": "2.0",
                    "id": f"get-{agent}",
                    "method": "tools/call",
                    "params": {
                        "name": "get_messages",
                        "arguments": {"agent_id": agent}
                    }
                })
                
                messages = response["result"]["messages"]
                assert len(messages) == 1, f"Agent {agent} should receive exactly 1 message"
                assert messages[0]["content"]["type"] == "sprint_update"
                
            print("✓ Reliable delivery: All agents received messages")
            
            # ✓ Test 4: Agent-to-agent communication
            print("Testing agent-to-agent communication...")
            
            # Setup dedicated channels for agent communication
            for agent in ["frontend", "backend"]:
                for channel in ["task-requests", "task-responses"]:
                    server.handle_request({
                        "jsonrpc": "2.0",
                        "id": f"sub-{agent}-{channel}",
                        "method": "tools/call",
                        "params": {
                            "name": "subscribe_channel",
                            "arguments": {
                                "channel": channel,
                                "agent_id": agent
                            }
                        }
                    })
                    
            # Frontend requests backend task
            server.handle_request({
                "jsonrpc": "2.0",
                "id": "task-req",
                "method": "tools/call",
                "params": {
                    "name": "publish_message",
                    "arguments": {
                        "channel": "task-requests",
                        "content": {
                            "request_id": "REQ-001",
                            "task": "Create user authentication API",
                            "priority": "high",
                            "requester": "frontend"
                        },
                        "sender": "frontend"
                    }
                }
            })
            
            # Backend receives and responds
            backend_messages = server.handle_request({
                "jsonrpc": "2.0",
                "id": "backend-get",
                "method": "tools/call",
                "params": {
                    "name": "get_messages",
                    "arguments": {
                        "agent_id": "backend",
                        "channel": "task-requests"
                    }
                }
            })
            
            assert len(backend_messages["result"]["messages"]) == 1
            request = backend_messages["result"]["messages"][0]
            
            # Backend responds
            server.handle_request({
                "jsonrpc": "2.0",
                "id": "task-resp",
                "method": "tools/call",
                "params": {
                    "name": "publish_message",
                    "arguments": {
                        "channel": "task-responses",
                        "content": {
                            "request_id": request["content"]["request_id"],
                            "status": "accepted",
                            "estimated_completion": "2 days",
                            "responder": "backend"
                        },
                        "sender": "backend"
                    }
                }
            })
            
            # Frontend receives response
            frontend_messages = server.handle_request({
                "jsonrpc": "2.0",
                "id": "frontend-get",
                "method": "tools/call",
                "params": {
                    "name": "get_messages",
                    "arguments": {
                        "agent_id": "frontend",
                        "channel": "task-responses"
                    }
                }
            })
            
            assert len(frontend_messages["result"]["messages"]) == 1
            response_msg = frontend_messages["result"]["messages"][0]
            assert response_msg["content"]["request_id"] == "REQ-001"
            assert response_msg["content"]["status"] == "accepted"
            
            print("✓ Agent-to-agent communication: Request-response cycle completed")
            
            # ✓ Test 5: Performance metrics logging
            metrics_response = server.handle_request({
                "jsonrpc": "2.0",
                "id": "final-metrics",
                "method": "tools/call",
                "params": {
                    "name": "get_performance_metrics",
                    "arguments": {}
                }
            })
            
            metrics = metrics_response["result"]
            assert metrics["messages_sent"] >= 3  # Team update + request + response
            assert metrics["avg_latency_ms"] > 0.0
            assert metrics["channels_count"] >= 3
            assert metrics["subscribers_count"] >= 6
            
            print(f"✓ Performance metrics logged:")
            print(f"  - Messages sent: {metrics['messages_sent']}")
            print(f"  - Average latency: {metrics['avg_latency_ms']:.2f}ms")
            print(f"  - Peak latency: {metrics['peak_latency_ms']:.2f}ms")
            print(f"  - Active channels: {metrics['channels_count']}")
            print(f"  - Total subscribers: {metrics['subscribers_count']}")
            
            print("\n🎉 ALL US-003 ACCEPTANCE CRITERIA VALIDATED SUCCESSFULLY!")
            
        finally:
            await server.stop()


if __name__ == "__main__":
    # Run the integration test
    asyncio.run(TestUS003Integration().test_complete_us003_acceptance_criteria()) 