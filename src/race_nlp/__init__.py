"""
Natural Language Processing components for the F1 AI Agent

Exports:
- TextGenerator: Main text generation class
- PromptTemplates: Template management system
- GenerationError: Custom exception class
"""

from .generator import (
    TextGenerator,
    TextGenerationProtocol,
    TemplateHandlerProtocol,
    GenerationError
)
from .prompts import (
    PromptTemplates,
    TemplateName,
    TemplateConfig
)

__all__ = [
    # Core components
    'TextGenerator',
    'PromptTemplates',
    
    # Protocols
    'TextGenerationProtocol',
    'TemplateHandlerProtocol',
    
    # Exceptions
    'GenerationError',
    
    # Template types
    'TemplateName',
    'TemplateConfig'
]

# Package version
__version__ = "1.0.0"

# Initialize package logger
from ..utils.logger import F1Logger 
logger = F1Logger(name="race_nlp")
logger.info(
    action="package_init",
    response={"message": "Race NLP package initialized"}  # Structured response
)