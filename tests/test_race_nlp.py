import pytest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError
from transformers import Pipeline

from src.race_nlp import ( 
    TextGenerator,
    PromptTemplates,
    TemplateName,
    GenerationError
)

# Fixtures
@pytest.fixture
def mock_pipeline():
    mock = MagicMock(spec=Pipeline)
    mock.__call__.return_value = [{"generated_text": "Sample text"}]
    return mock

@pytest.fixture
def text_generator(mock_pipeline):
    return TextGenerator.from_pretrained(
        "test-model",
        model=mock_pipeline,
        template_handler=PromptTemplates
    )

@pytest.fixture
def valid_context():
    return {
        "race_name": "Monaco GP",
        "team": "Mercedes",
        "result": "P1",
        "race_hashtag": "MonacoMagic"
    }

# Test PromptTemplates
def test_get_valid_template():
    template = PromptTemplates.get_template_config(TemplateName.POST_RACE)
    assert isinstance(template, TemplateConfig)
    assert "race_name" in template.required_context

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
            "invalid_template",
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
            {"race_name": "Test"}
        )
    
    assert "Critical failure" in str(exc_info.value.original)

def test_context_validation_logging(text_generator, caplog):
    with pytest.raises(GenerationError):
        text_generator.generate(
            TemplateName.POST_RACE,
            {"invalid": "context"}
        )
    
    assert "Missing required context keys" in caplog.text

# Test Template Configuration
def test_template_config_validation():
    with pytest.raises(ValidationError):
        TemplateConfig(
            template="Invalid template with {missing}",
            required_context={"present"}
        )

def test_auto_placeholder_detection():
    config = TemplateConfig(
        template="Test {a} and {b}",
        required_context={"a"}
    )
    assert config.allowed_placeholders == {"a", "b"}

# Test Protocol Compliance
def test_textgenerator_protocol_compliance():
    generator = TextGenerator(model=MagicMock())
    assert isinstance(generator, TextGenerationProtocol)

def test_prompttemplates_protocol_compliance():
    assert isinstance(PromptTemplates, TemplateHandlerProtocol)