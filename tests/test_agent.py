import pytest
from src.agent.context_manager import ContextManager, AgentContext
from src.agent.actions import SocialMediaActions
from src.agent.f1_agent import F1Agent
from src.race_nlp.generator import TextGenerationProtocol
from typing import Dict, Any

# Mock TextGenerator for testing F1Agent
class MockTextGenerator(TextGenerationProtocol):
    def generate(self, template_name: str, context: dict) -> str:
        # Simple mock implementation
        if template_name == "win_message":
            return f"Great win! Context: {context.get('race_stage', 'unknown')}"
        elif template_name == "loss_message":
             return f"Tough race. Context: {context.get('recent_result', 'unknown')}"
        else:
            return f"Generated text for {template_name} with context {context}"

# Tests for ContextManager
def test_context_manager_initialization():
    manager = ContextManager()
    assert manager.get_context().race_stage == "pre_race"
    assert manager.get_context().recent_result is None

def test_context_manager_update_context():
    manager = ContextManager()
    new_data = {"race_stage": "race", "recent_result": "good"}
    manager.update_context(new_data)
    context = manager.get_context()
    assert context.race_stage == "race"
    assert context.recent_result == "good"
    assert context.team_dynamics is None # Ensure other fields are unchanged

def test_context_manager_get_context_dict():
    manager = ContextManager()
    new_data = {"race_stage": "qualifying", "team_dynamics": "positive"}
    manager.update_context(new_data)
    context_dict = manager.get_context_dict()
    assert isinstance(context_dict, dict)
    assert context_dict["race_stage"] == "qualifying"
    assert context_dict["team_dynamics"] == "positive"

# Tests for SocialMediaActions
def test_social_media_actions_reply_comment():
    actions = SocialMediaActions()
    comment = "Great drive!"
    response = "Thanks!"
    result = actions.reply_comment(comment, response)
    assert result["status"] == "success"
    assert result["action"] == "reply_comment"
    assert f"Replied to comment '{comment}' with: '{response}'" in result["details"]

def test_social_media_actions_post_status_update():
    actions = SocialMediaActions()
    status = "Ready for the race!"
    result = actions.post_status_update(status)
    assert result["status"] == "success"
    assert result["action"] == "post_status_update"
    assert f"Posted status update: '{status}'" in result["details"]

def test_social_media_actions_simulate_like():
    actions = SocialMediaActions()
    post_id = "post123"
    result = actions.simulate_like(post_id)
    assert result["status"] == "success"
    assert result["action"] == "simulate_like"
    assert f"Simulated liking post with ID: {post_id}" in result["details"]

def test_social_media_actions_mention():
    actions = SocialMediaActions()
    mention_text = "@teammate good job!"
    result = actions.mention_teammate_or_competitor(mention_text)
    assert result["status"] == "success"
    assert result["action"] == "mention"
    assert f"Simulated mention: {mention_text}" in result["details"]

# Tests for F1Agent
@pytest.fixture
def f1_agent_instance():
    mock_generator = MockTextGenerator()
    agent = F1Agent.create(text_generator=mock_generator)
    return agent

def test_f1_agent_initialization(f1_agent_instance):
    agent = f1_agent_instance
    assert isinstance(agent.context_manager, ContextManager)
    assert isinstance(agent.actions, SocialMediaActions)
    assert isinstance(agent.text_generator, MockTextGenerator)

def test_f1_agent_think(f1_agent_instance):
    agent = f1_agent_instance
    new_context = {"race_stage": "race", "recent_result": "good"}
    updated_context = agent.think(new_context)
    assert updated_context.race_stage == "race"
    assert updated_context.recent_result == "good"
    assert agent.context_manager.get_context().race_stage == "race"

def test_f1_agent_speak(f1_agent_instance):
    agent = f1_agent_instance
    # Update context first
    agent.think({"race_stage": "post_race"})
    generated_text = agent.speak("win_message")
    assert "Great win!" in generated_text
    assert "Context: post_race" in generated_text

    # Test with additional context
    generated_text_with_additional = agent.speak("loss_message", {"recent_result": "bad"})
    assert "Tough race." in generated_text_with_additional
    assert "Context: bad" in generated_text_with_additional # Additional context overrides current context for speak

def test_f1_agent_act_reply_comment(f1_agent_instance):
    agent = f1_agent_instance
    action_data = {"comment_text": "Nice!", "agent_response": "Thanks!"}
    result = agent.act("reply_comment", action_data)
    assert result["status"] == "success"
    assert result["action"] == "reply_comment"

def test_f1_agent_act_post_status_update(f1_agent_instance):
    agent = f1_agent_instance
    action_data = {"status_text": "Feeling good!"}
    result = agent.act("post_status_update", action_data)
    assert result["status"] == "success"
    assert result["action"] == "post_status_update"

def test_f1_agent_act_unknown_action(f1_agent_instance):
    agent = f1_agent_instance
    action_data = {"some_key": "some_value"}
    with pytest.raises(ValueError, match="Unknown action type: unknown_action"):
        agent.act("unknown_action", action_data)
