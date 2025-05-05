import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Optional
from src.api.main import app
from src.agent.context_manager import AgentContext
from src.api.schemas import AgentResponse

# Mock dependencies
class MockTextGenerator:
    def generate(self, template_name: str, context: dict) -> str:
        return f"Mock generated text for {template_name}"

class MockContextManager:
    def __init__(self):
        self._context = AgentContext()

    def update_context(self, new_context_data: Dict[str, Any]):
        updated_data = self._context.model_dump()
        updated_data.update(new_context_data)
        self._context = AgentContext(**updated_data)

    def get_context(self) -> AgentContext:
        return self._context

    def get_context_dict(self) -> Dict[str, Any]:
        return self._context.model_dump()

class MockSocialMediaActions:
    def reply_comment(self, comment_text: str, agent_response: str) -> Dict[str, Any]:
        return {"status": "mock_success", "action": "mock_reply", "details": "mock reply details"}

    def post_status_update(self, status_text: str) -> Dict[str, Any]:
        return {"status": "mock_success", "action": "mock_post", "details": "mock post details"}

    def simulate_like(self, post_id: str) -> Dict[str, Any]:
        return {"status": "mock_success", "action": "mock_like", "details": "mock like details"}

    def mention_teammate_or_competitor(self, mention_text: str) -> Dict[str, Any]:
        return {"status": "mock_success", "action": "mock_mention", "details": "mock mention details"}

class MockF1Agent:
    def __init__(self, text_generator, context_manager, actions):
        self.text_generator = text_generator
        self.context_manager = context_manager
        self.actions = actions

    def create(self, text_generator):
         # This mock create method is simplified; in a real test, you might mock the actual create
         # or directly instantiate MockF1Agent with mocked dependencies.
         # For now, we'll assume the patch below handles the agent instance used by the app.
         pass

    def think(self, new_context_data: Dict[str, Any]) -> AgentContext:
        self.context_manager.update_context(new_context_data)
        return self.context_manager.get_context()

    def speak(self, template_name: str, additional_context: Optional[Dict[str, Any]] = None) -> str:
        # Combine current context and additional context for speak
        current_context = self.context_manager.get_context_dict()
        if additional_context:
            current_context.update(additional_context)
        return self.text_generator.generate(template_name, current_context)

    def act(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        action_method = getattr(self.actions, action_type, None)
        if action_method and callable(action_method):
            return action_method(**action_data)
        else:
            raise ValueError(f"Unknown action type: {action_type}")


# Fixture for the test client with mocked dependencies
@pytest.fixture(scope="module")
def test_client():
    # Patch the F1Agent.create method to return our mock agent instance
    mock_text_generator = MockTextGenerator()
    mock_context_manager = MockContextManager()
    mock_actions = MockSocialMediaActions()
    mock_agent_instance = MockF1Agent(mock_text_generator, mock_context_manager, mock_actions)

    with patch('src.api.main.F1Agent.create', return_value=mock_agent_instance) as mock_create:
         # Also patch the global f1_agent instance in main.py if it's initialized directly
         with patch('src.api.main.f1_agent', new=mock_agent_instance):
            client = TestClient(app)
            yield client
            # Reset the mock context manager after tests if needed, or rely on fixture scope

# Test endpoints
def test_generate_post(test_client):
    response = test_client.post("/generate_post", json={"template_name": "win_message", "context_data": {"race_stage": "post_race"}})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "Mock generated text" in response.json()["data"]["post_text"]

def test_reply_comment(test_client):
    response = test_client.post("/reply_comment", json={"comment_text": "Great job!", "agent_response": "Thanks!"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["action"] == "mock_reply"

def test_simulate_like(test_client):
    response = test_client.post("/simulate_like", json={"post_id": "post456"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["action"] == "mock_like"

def test_simulate_action_post_status(test_client):
    response = test_client.post("/simulate", json={"action_type": "post_status_update", "action_data": {"status_text": "Feeling ready!"}})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["action"] == "mock_post"

def test_simulate_action_mention(test_client):
    response = test_client.post("/simulate", json={"action_type": "mention_teammate_or_competitor", "action_data": {"mention_text": "@competitor"}})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["action"] == "mock_mention"

def test_simulate_action_unknown(test_client):
    response = test_client.post("/simulate", json={"action_type": "unknown_action", "action_data": {}})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid action type or data: Unknown action type: unknown_action"

def test_update_context(test_client):
    response = test_client.post("/update_context", json={"context_data": {"race_stage": "qualifying", "recent_result": "bad"}})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["race_stage"] == "qualifying"
    assert response.json()["data"]["recent_result"] == "bad"

def test_get_context(test_client):
    # First update context
    test_client.post("/update_context", json={"context_data": {"race_stage": "race", "team_dynamics": "neutral"}})
    # Then get context
    response = test_client.get("/get_context")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["race_stage"] == "race"
    assert response.json()["data"]["team_dynamics"] == "neutral"
    # Ensure values from previous updates are still present if not overwritten
    assert response.json()["data"]["recent_result"] == "bad"
