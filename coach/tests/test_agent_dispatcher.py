import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from coach.agent import CoachAgent

class TestAgentDispatcher:
    @patch("coach.agent.CoachAgent._load_config")
    @patch("coach.agent.MemoryManager")
    def test_dispatch_tool_success(self, mock_memory_manager, mock_load_config):
        mock_load_config.return_value = {}
        agent = CoachAgent()
        
        # Mock call_model to return a valid structured response
        agent.call_model = MagicMock(return_value="TOOL: store_session\nARG: Python\nARG: 45\nARG: 8\nARG: refactoring agent\nREASON: completed session")
        
        tool_name, args, reason = agent.dispatch_tool("Session complete: Python, 45 mins, 8/10")
        
        assert tool_name == "store_session"
        assert args == ["Python", "45", "8", "refactoring agent"]
        assert reason == "completed session"
        agent.call_model.assert_called_once()

    @patch("coach.agent.CoachAgent._load_config")
    @patch("coach.agent.MemoryManager")
    def test_dispatch_tool_none(self, mock_memory_manager, mock_load_config):
        mock_load_config.return_value = {}
        agent = CoachAgent()
        
        # Mock call_model to return None for tool
        agent.call_model = MagicMock(return_value="TOOL: None\nREASON: general conversation")
        
        tool_name, args, reason = agent.dispatch_tool("hello coach")
        
        assert tool_name is None
        assert args == []
        assert reason == "general conversation"

    @patch("coach.agent.CoachAgent._load_config")
    @patch("coach.agent.MemoryManager")
    def test_dispatch_tool_exception(self, mock_memory_manager, mock_load_config):
        mock_load_config.return_value = {}
        agent = CoachAgent()
        
        # Mock call_model to raise exception
        agent.call_model = MagicMock(side_effect=RuntimeError("API error"))
        
        tool_name, args, reason = agent.dispatch_tool("error out")
        
        assert tool_name is None
        assert args == []
        assert "Dispatch failed" in reason

    @patch("coach.agent.CoachAgent._load_config")
    @patch("coach.agent.MemoryManager")
    @patch("coach.agent.execute_tool")
    def test_process_input_routes_tool(self, mock_exec, mock_memory_manager, mock_load_config):
        mock_load_config.return_value = {}
        agent = CoachAgent()
        mock_exec.return_value = "Tool output"

        agent.dispatch_tool = MagicMock(return_value=("store_session", ["Python", "45", "8"], "completed"))
        agent.memory.get_context_for_query = MagicMock(return_value="Some context")
        agent.call_model = MagicMock(return_value="Coach response")

        response = agent.process_input("Session complete...")

        agent.dispatch_tool.assert_called_once_with("Session complete...")
        mock_exec.assert_called_once_with("store_session", ["Python", "45", "8"])
        agent.memory.get_context_for_query.assert_called_once_with("Session complete...")

        agent.call_model.assert_called_once()
        assert response == "Coach response"
