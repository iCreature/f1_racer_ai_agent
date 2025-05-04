import pytest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError
from transformers import Pipeline

from src.race_nlp.prompts import TemplateConfig, TemplateName
from src.race_nlp.generator import (
    TextGenerator,
    TemplateHandler,
    TemplateHandlerProtocol,
    GenerationError
)
from src.race_nlp import ( 
    TextGenerator,
    PromptTemplates,
    TemplateName,
    GenerationError,
    TextGenerationProtocol,
    TemplateHandlerProtocol
)

# Fixtures
@pytest.fixture
def mock_pipeline():
    mock = MagicMock(spec=Pipeline)
    mock.return_value = [{"generated_text": "Sample generated text"}]
    return mock

@pytest.fixture
def text_generator(mock_pipeline):
    return TextGenerator(
        model=mock_pipeline,
        template_handler=TemplateHandler(),
        max_length=128,
        num_return_sequences=1
    )

@pytest.fixture
def valid_context():
    return {
        "race_name": "Monaco GP",
        "team": "Mercedes",
        "result": "P1",
        "race_hashtag": "MonacoMagic",
        "team_hashtag": "TeamMercedes",
        "sentiment": "excited"
    }

# Test PromptTemplates
def test_get_valid_template():
    template = PromptTemplates.get_template_config(TemplateName.POST_RACE)
    assert isinstance(template, TemplateConfig)
    assert "race_name" in template.required_context

def test_generation_with_invalid_template(text_generator):
    with pytest.raises(GenerationError):
        text_generator.generate(
            TemplateName.RACE_STRATEGY,
            {"team": "Mercedes"}
        )

def test_missing_template_raises_error():
    with pytest.raises(ValueError):
        PromptTemplates.get_template_config("invalid_template")

def test_template_formatting(valid_context):
    prompt = PromptTemplates.format_template(
        TemplateName.POST_RACE,
        valid_context
    )
    assert "Monaco GP" in prompt
    assert "#MonacoMagic" in prompt

def test_missing_context_validation():
    with pytest.raises(ValueError):
        PromptTemplates.format_template(
            TemplateName.POST_RACE,
            {"team": "Mercedes"}  # Missing race_name
        )

def test_template_registration():
    new_template = (
        "New template with {required} and {optional}"
    )
    
    PromptTemplates.register_template(
        TemplateName.RACE_STRATEGY,
        template=new_template,
        required_context={"required"},
        default_values={"optional": "default"}
    )
    
    config = PromptTemplates.get_template_config(TemplateName.RACE_STRATEGY)
    assert config.template == new_template

# Test TextGenerator
def test_successful_generation(text_generator, mock_pipeline, valid_context):
    result = text_generator.generate(
        TemplateName.POST_RACE,
        valid_context
    )
    mock_pipeline.assert_called_once()
    assert result == "Sample generated text"

def test_generation_with_invalid_template(text_generator):
    with pytest.raises(GenerationError):
        text_generator.generate(
            "invalid_template_enum_member",
            {"team": "Mercedes"}
        )

def test_fallback_mechanism(text_generator, mock_pipeline, valid_context):
    mock_pipeline.side_effect = Exception("Model failed")
    text_generator.enable_fallback = True
    
    result = text_generator.generate(
        TemplateName.POST_RACE,
        valid_context
    )
    assert "Monaco GP" in result  # Fallback to template

def test_error_propagation(text_generator, mock_pipeline):
    text_generator.enable_fallback = False
    mock_pipeline.side_effect = Exception("Critical failure")
    
    with pytest.raises(GenerationError) as exc_info:
            text_generator.generate(
                TemplateName.POST_RACE,
                {
                    "race_name": "Test",
                    "team": "Mercedes",
                    "result": "P1",
                    "race_hashtag": "TestHash",
                    "sentiment": "neutral",
                    "team_hashtag": "TestTeamHash" # Added missing context key
                }
            )
    
    assert "Critical failure" in str(exc_info.value.original)

def test_context_validation_logging(text_generator, caplog):
    with pytest.raises(GenerationError):
        text_generator.generate(
            TemplateName.POST_RACE,
            {"team": "Mercedes"}
        )
    
        # The actual log message includes the specific missing key
        # The log message format includes the level, logger name, file, line, and the message
        assert "ERROR    F1RacerAI:logger.py" in caplog.text
        assert "Missing context key: 'sentiment'" in caplog.text

# Test Template Configuration
def test_template_registration():
    new_template = "New template with {required} and {optional}"
    
    # Register with correct enum member
    PromptTemplates.register_template(
        TemplateName.RACE_STRATEGY, 
        template=new_template,
        required_context={"required"},
        default_values={"optional": "default"}
    )
    
    config = PromptTemplates.get_template_config(TemplateName.RACE_STRATEGY)
    assert config.template == new_template

def test_auto_placeholder_detection():
    config = TemplateConfig(
        template="Test {a} and {b}",
        required_context={"a"}
    )
    assert config.allowed_placeholders == {"a", "b"}

def test_textgenerator_protocol_compliance(text_generator):
    assert isinstance(text_generator, TextGenerationProtocol)


def test_prompttemplates_protocol_compliance():
    handler = TemplateHandler()
    assert isinstance(handler, TemplateHandlerProtocol)
