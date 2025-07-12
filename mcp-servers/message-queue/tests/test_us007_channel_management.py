"""
US-007: Message Queue - Channel Management - TDD Implementation

Test suite for US-007 acceptance criteria:
- Agents can subscribe/unsubscribe to channels
- Channel-based message routing works correctly
- Broadcast messages reach all subscribers
- Direct messages reach only intended recipient
- Channel list is discoverable
"""

import pytest
import pytest_asyncio
import asyncio
import json
import sys
import os
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from message_queue_server import MessageQueueServer, Message, Subscription


class TestUS007ChannelManagement:
    """Test suite for US-007: Message Queue - Channel Management"""

    @pytest_asyncio.fixture
    async def server(self):
        """Create a clean server instance for each test"""
        server = MessageQueueServer("us007-test", "1.0.0")
        await server.start()
        yield server
        await server.stop()

    @pytest.mark.asyncio
    async def test_agent_can_subscribe_to_channel(self, server):
        """Test that agents can subscribe to specific channels"""
        # Given: A clean server
        # When: Agent subscribes to a channel
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub-1",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "backend-updates",
                    "agent_id": "backend-dev-1"
                }
            }
        })
        
        # Then: Subscription is successful
        assert response["result"]["subscribed"] is True
        assert response["result"]["channel"] == "backend-updates"
        assert response["result"]["agent_id"] == "backend-dev-1"
        
        # And: Agent is in the subscription list
        assert "backend-dev-1" in server.agent_subscriptions
        assert "backend-updates" in server.agent_subscriptions["backend-dev-1"]

    @pytest.mark.asyncio
    async def test_agent_can_unsubscribe_from_channel(self, server):
        """Test that agents can unsubscribe from channels"""
        # Given: Agent is subscribed to a channel
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub-1",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "frontend-updates",
                    "agent_id": "frontend-dev-1"
                }
            }
        })
        
        # When: Agent unsubscribes from the channel
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "unsub-1",
            "method": "tools/call",
            "params": {
                "name": "unsubscribe_channel",
                "arguments": {
                    "channel": "frontend-updates",
                    "agent_id": "frontend-dev-1"
                }
            }
        })
        
        # Then: Unsubscription is successful
        assert response["result"]["unsubscribed"] is True
        assert response["result"]["channel"] == "frontend-updates"
        assert response["result"]["agent_id"] == "frontend-dev-1"
        
        # And: Agent is no longer in the subscription list
        assert "frontend-updates" not in server.agent_subscriptions.get("frontend-dev-1", set())

    @pytest.mark.asyncio
    async def test_channel_based_message_routing_works_correctly(self, server):
        """Test that messages are routed correctly based on channel subscriptions"""
        # Given: Multiple agents subscribed to different channels
        # Agent 1 subscribes to channel A
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub-1",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "channel-a",
                    "agent_id": "agent-1"
                }
            }
        })
        
        # Agent 2 subscribes to channel B
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub-2",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "channel-b",
                    "agent_id": "agent-2"
                }
            }
        })
        
        # When: Message is published to channel A
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "pub-1",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "channel-a",
                    "content": {"message": "Hello channel A"},
                    "sender": "sender-1"
                }
            }
        })
        
        # Then: Agent 1 receives the message
        response_agent1 = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-1",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "agent-1"
                }
            }
        })
        
        # And: Agent 2 does not receive the message
        response_agent2 = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-2",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "agent-2"
                }
            }
        })
        
        # Verify routing worked correctly
        assert len(response_agent1["result"]["messages"]) == 1
        assert response_agent1["result"]["messages"][0]["content"]["message"] == "Hello channel A"
        assert len(response_agent2["result"]["messages"]) == 0

    @pytest.mark.asyncio
    async def test_broadcast_messages_reach_all_subscribers(self, server):
        """Test that broadcast messages reach all subscribers of a channel"""
        # Given: Multiple agents subscribed to the same channel
        agents = ["agent-1", "agent-2", "agent-3"]
        channel = "broadcast-channel"
        
        for agent in agents:
            server.handle_request({
                "jsonrpc": "2.0",
                "id": f"sub-{agent}",
                "method": "tools/call",
                "params": {
                    "name": "subscribe_channel",
                    "arguments": {
                        "channel": channel,
                        "agent_id": agent
                    }
                }
            })
        
        # When: A broadcast message is published to the channel
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "broadcast-pub",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": channel,
                    "content": {
                        "type": "broadcast",
                        "message": "This is a broadcast to all"
                    },
                    "sender": "broadcaster"
                }
            }
        })
        
        # Then: All subscribed agents receive the message
        for agent in agents:
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": f"get-{agent}",
                "method": "tools/call",
                "params": {
                    "name": "get_messages",
                    "arguments": {
                        "agent_id": agent
                    }
                }
            })
            
            assert len(response["result"]["messages"]) == 1
            message = response["result"]["messages"][0]
            assert message["content"]["type"] == "broadcast"
            assert message["content"]["message"] == "This is a broadcast to all"
            assert message["channel"] == channel

    @pytest.mark.asyncio
    async def test_direct_messages_reach_only_intended_recipient(self, server):
        """Test that direct messages reach only the intended recipient"""
        # Given: Multiple agents subscribed to a general channel
        agents = ["agent-1", "agent-2", "agent-3"]
        general_channel = "general"
        
        for agent in agents:
            server.handle_request({
                "jsonrpc": "2.0",
                "id": f"sub-{agent}",
                "method": "tools/call",
                "params": {
                    "name": "subscribe_channel",
                    "arguments": {
                        "channel": general_channel,
                        "agent_id": agent
                    }
                }
            })
        
        # When: A direct message is sent to a specific agent via direct message channel
        # This tests the ability to send messages to specific agents
        # We'll use a direct message channel pattern: "direct-to-{agent_id}"
        direct_channel = "direct-to-agent-2"
        
        # Subscribe target agent to their direct channel
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub-direct",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": direct_channel,
                    "agent_id": "agent-2"
                }
            }
        })
        
        # Send direct message
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "direct-msg",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": direct_channel,
                    "content": {
                        "type": "direct",
                        "message": "This is for agent-2 only",
                        "recipient": "agent-2"
                    },
                    "sender": "agent-1"
                }
            }
        })
        
        # Then: Only agent-2 receives the direct message
        response_agent2 = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-agent2",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "agent-2"
                }
            }
        })
        
        # And: Other agents don't receive the direct message
        response_agent1 = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-agent1",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "agent-1"
                }
            }
        })
        
        response_agent3 = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-agent3",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "agent-3"
                }
            }
        })
        
        # Verify direct message routing
        assert len(response_agent2["result"]["messages"]) == 1
        direct_msg = response_agent2["result"]["messages"][0]
        assert direct_msg["content"]["type"] == "direct"
        assert direct_msg["content"]["recipient"] == "agent-2"
        
        # Other agents should not receive the direct message
        assert len(response_agent1["result"]["messages"]) == 0
        assert len(response_agent3["result"]["messages"]) == 0

    @pytest.mark.asyncio
    async def test_channel_list_is_discoverable(self, server):
        """Test that channel list is discoverable"""
        # Given: Multiple channels with subscribers
        channels_data = [
            ("development", "dev-agent-1"),
            ("testing", "test-agent-1"),
            ("deployment", "devops-agent-1"),
            ("notifications", "pm-agent-1")
        ]
        
        for channel, agent in channels_data:
            server.handle_request({
                "jsonrpc": "2.0",
                "id": f"sub-{channel}",
                "method": "tools/call",
                "params": {
                    "name": "subscribe_channel",
                    "arguments": {
                        "channel": channel,
                        "agent_id": agent
                    }
                }
            })
        
        # When: Requesting channel list
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "list-channels",
            "method": "tools/call",
            "params": {
                "name": "list_channels",
                "arguments": {}
            }
        })
        
        # Then: All channels are discoverable
        assert "channels" in response["result"]
        assert "total_channels" in response["result"]
        assert response["result"]["total_channels"] == 4
        
        channel_names = [ch["name"] for ch in response["result"]["channels"]]
        for channel, _ in channels_data:
            assert channel in channel_names

    @pytest.mark.asyncio
    async def test_multiple_agents_can_subscribe_to_same_channel(self, server):
        """Test that multiple agents can subscribe to the same channel"""
        # Given: Multiple agents
        agents = ["backend-dev-1", "backend-dev-2", "backend-dev-3"]
        channel = "backend-coordination"
        
        # When: All agents subscribe to the same channel
        for agent in agents:
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": f"sub-{agent}",
                "method": "tools/call",
                "params": {
                    "name": "subscribe_channel",
                    "arguments": {
                        "channel": channel,
                        "agent_id": agent
                    }
                }
            })
            assert response["result"]["subscribed"] is True
        
        # Then: All agents are subscribed
        for agent in agents:
            assert channel in server.agent_subscriptions[agent]
        
        # And: Channel has all subscribers
        assert len(server.subscriptions[channel]) == 3

    @pytest.mark.asyncio
    async def test_agent_can_subscribe_to_multiple_channels(self, server):
        """Test that a single agent can subscribe to multiple channels"""
        # Given: Multiple channels
        channels = ["frontend-updates", "ui-discussions", "deployment-notifications"]
        agent = "frontend-dev-1"
        
        # When: Agent subscribes to multiple channels
        for channel in channels:
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": f"sub-{channel}",
                "method": "tools/call",
                "params": {
                    "name": "subscribe_channel",
                    "arguments": {
                        "channel": channel,
                        "agent_id": agent
                    }
                }
            })
            assert response["result"]["subscribed"] is True
        
        # Then: Agent is subscribed to all channels
        assert len(server.agent_subscriptions[agent]) == 3
        for channel in channels:
            assert channel in server.agent_subscriptions[agent]

    @pytest.mark.asyncio
    async def test_channel_subscription_with_filters(self, server):
        """Test that agents can subscribe to channels with message filters"""
        # Given: Agent with specific filter preferences
        agent = "filtered-agent"
        channel = "notifications"
        filters = {"priority": "high", "type": "alert"}
        
        # When: Agent subscribes with filters
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub-filtered",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": channel,
                    "agent_id": agent,
                    "filters": filters
                }
            }
        })
        
        # Then: Subscription is successful with filters
        assert response["result"]["subscribed"] is True
        assert response["result"]["filters"] == filters
        
        # And: Filters are stored in subscription
        subscriptions = server.subscriptions[channel]
        agent_subscription = next((sub for sub in subscriptions if sub.agent_id == agent), None)
        assert agent_subscription is not None
        assert agent_subscription.filters == filters

    @pytest.mark.asyncio
    async def test_unsubscribe_from_nonexistent_channel_gracefully(self, server):
        """Test that unsubscribing from a nonexistent channel is handled gracefully"""
        # When: Agent tries to unsubscribe from a channel they're not subscribed to
        response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "unsub-nonexistent",
            "method": "tools/call",
            "params": {
                "name": "unsubscribe_channel",
                "arguments": {
                    "channel": "nonexistent-channel",
                    "agent_id": "test-agent"
                }
            }
        })
        
        # Then: Operation completes without error
        assert response["result"]["unsubscribed"] is True
        assert response["result"]["channel"] == "nonexistent-channel"
        assert response["result"]["agent_id"] == "test-agent"

    @pytest.mark.asyncio
    async def test_channel_management_comprehensive_scenario(self, server):
        """Test a comprehensive scenario covering all US-007 acceptance criteria"""
        # This test combines all acceptance criteria in a realistic scenario
        
        # Setup: Create a development team with different roles
        agents = {
            "pm-agent": ["planning", "notifications"],
            "backend-dev": ["backend", "api-changes", "notifications"],
            "frontend-dev": ["frontend", "api-changes", "notifications"],
            "tester": ["testing", "notifications"]
        }
        
        # Step 1: All agents subscribe to their respective channels
        for agent, channels in agents.items():
            for channel in channels:
                response = server.handle_request({
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
                assert response["result"]["subscribed"] is True
        
        # Step 2: Verify channel discovery
        channels_response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "discover-channels",
            "method": "tools/call",
            "params": {
                "name": "list_channels",
                "arguments": {}
            }
        })
        
        expected_channels = {"planning", "notifications", "backend", "api-changes", "frontend", "testing"}
        actual_channels = {ch["name"] for ch in channels_response["result"]["channels"]}
        assert expected_channels == actual_channels
        
        # Step 3: Test broadcast to all via notifications channel
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "broadcast-notification",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "notifications",
                    "content": {
                        "type": "broadcast",
                        "message": "Sprint planning meeting in 30 minutes"
                    },
                    "sender": "pm-agent"
                }
            }
        })
        
        # Step 4: Test specific channel communication
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "api-change-notification",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "api-changes",
                    "content": {
                        "type": "api-change",
                        "message": "User API endpoint modified - please update tests"
                    },
                    "sender": "backend-dev"
                }
            }
        })
        
        # Step 5: Test direct message to specific agent
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "sub-direct-tester",
            "method": "tools/call",
            "params": {
                "name": "subscribe_channel",
                "arguments": {
                    "channel": "direct-to-tester",
                    "agent_id": "tester"
                }
            }
        })
        
        server.handle_request({
            "jsonrpc": "2.0",
            "id": "direct-to-tester",
            "method": "tools/call",
            "params": {
                "name": "publish_message",
                "arguments": {
                    "channel": "direct-to-tester",
                    "content": {
                        "type": "direct",
                        "message": "Can you prioritize testing the login feature?"
                    },
                    "sender": "pm-agent"
                }
            }
        })
        
        # Step 6: Verify message routing worked correctly
        
        # All agents should have received the broadcast notification
        for agent in agents.keys():
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": f"get-{agent}",
                "method": "tools/call",
                "params": {
                    "name": "get_messages",
                    "arguments": {
                        "agent_id": agent
                    }
                }
            })
            
            messages = response["result"]["messages"]
            broadcast_msg = next((msg for msg in messages if msg["content"]["type"] == "broadcast"), None)
            assert broadcast_msg is not None
            assert "Sprint planning meeting" in broadcast_msg["content"]["message"]
        
        # Only backend-dev and frontend-dev should have received API change notification
        api_change_agents = ["backend-dev", "frontend-dev"]
        for agent in api_change_agents:
            response = server.handle_request({
                "jsonrpc": "2.0",
                "id": f"get-api-{agent}",
                "method": "tools/call",
                "params": {
                    "name": "get_messages",
                    "arguments": {
                        "agent_id": agent,
                        "channel": "api-changes"
                    }
                }
            })
            
            messages = response["result"]["messages"]
            api_msg = next((msg for msg in messages if msg["content"]["type"] == "api-change"), None)
            assert api_msg is not None
        
        # Only tester should have received the direct message
        tester_response = server.handle_request({
            "jsonrpc": "2.0",
            "id": "get-tester-direct",
            "method": "tools/call",
            "params": {
                "name": "get_messages",
                "arguments": {
                    "agent_id": "tester",
                    "channel": "direct-to-tester"
                }
            }
        })
        
        direct_messages = tester_response["result"]["messages"]
        assert len(direct_messages) == 1
        assert direct_messages[0]["content"]["type"] == "direct"
        assert "prioritize testing" in direct_messages[0]["content"]["message"] 