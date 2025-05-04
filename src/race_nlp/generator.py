from __future__ import annotations
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from abc import abstractmethod
from functools import wraps
from .prompts import TemplateName  
from string import Formatter

from transformers import Pipeline, pipeline
from pydantic import (
    BaseModel,
    validate_call,
    ConfigDict,
    field_validator,
    model_validator,
    ValidationError
)
from src.utils.logger import F1Logger
from .prompts import PromptTemplates, TemplateConfig

logger = F1Logger()

# ========================
# Protocol Definitions
# ========================
@runtime_checkable
class TextGenerationProtocol(Protocol):
    @abstractmethod
    def generate(self, template_name: str, context: dict) -> str:
        ...

@runtime_checkable
class TemplateHandlerProtocol(Protocol):
    @abstractmethod
    def get_template(self, template_name: str) -> str:
        ...
    
    @abstractmethod
    def format_template(self, template_name: str, context: dict) -> str:
        ...

# ========================
# Template Handler
# ========================
class TemplateHandler(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @validate_call
    def get_template(self, template_name: "TemplateName") -> str:
        """Retrieve and validate template"""
        try:
            return PromptTemplates.get_template_config(template_name).template
        except ValueError as e:
            logger.error(
                action="template_resolution",
                response=f"Missing template: {template_name}"
            )
            raise ValueError(f"Template '{template_name}' not found")
    
    @validate_call
    def format_template(self, template_name: str, context: dict) -> str:
        """Format template with validation"""
        template = self.get_template(template_name)
        try:
            return template.format(**context)
        except KeyError as e:
            logger.error(
                action="template_formatting",
                response=f"Missing context key: {e}"
            )
            raise ValueError(f"Missing context key: {e}") from None

# ========================
# Text Generator
# ========================
class TextGenerator(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_default=True
    )

    model: Pipeline
    template_handler: TemplateHandlerProtocol
    max_length: int = 128
    num_return_sequences: int = 1
    enable_fallback: bool = True

    @classmethod
    def from_pretrained(
        cls,
        model_name: str,
        template_handler: Optional[TemplateHandlerProtocol] = None,
        **kwargs
    ) -> TextGenerator:
        """Factory method with dependency injection"""
        return cls(
            model=pipeline("text-generation", model=model_name),
            template_handler=template_handler or TemplateHandler(),
            **kwargs
        )

    def generate(self, template_name: str, context: dict) -> str:
        """Main generation workflow"""
        try:
            prompt = self.template_handler.format_template(template_name, context)

            return self._generate_with_llm(prompt)

        except (ValueError, ValidationError) as e:
             raise GenerationError(f"Template or context validation failed: {e}", original=e) from e

        except Exception as e:
            if self.enable_fallback:
                return self._fallback_response(template_name, context)
            raise GenerationError("Text generation failed", original=e) from e

    def _fallback_response(self, template_name: str, context: dict) -> str:
        """Template-based fallback mechanism"""
        logger.warn(
            action="fallback_triggered",
            response={"template": template_name}
        )
        try:
            return self.template_handler.format_template(template_name, context)
        except (ValueError, ValidationError) as e:
            raise GenerationError(f"Fallback template formatting failed: {e}", original=e) from e

    def _generate_with_llm(self, prompt: str) -> str:
        """Execute LLM pipeline with instrumentation"""
        logger.info(
            action="llm_invocation_start",
            response={"prompt": prompt}
        )

        try:
            outputs = self.model(
                prompt,
                max_length=self.max_length,
                num_return_sequences=self.num_return_sequences
            )
            result = outputs[0]["generated_text"]
        except Exception as e:
            logger.error(
                action="llm_invocation_error",
                response=str(e)
            )
            raise

        logger.info(
            action="llm_invocation_success",
            response={"output": result}
        )
        return result

    def _fallback_response(self, template_name: str, context: dict) -> str:
        """Template-based fallback mechanism"""
        logger.warn(
            action="fallback_triggered",
            response={"template": template_name}
        )
        return self.template_handler.format_template(template_name, context)

# ========================
# Custom Exceptions
# ========================
class GenerationError(Exception):
    """Custom exception for generation failures"""
    def __init__(self, message: str, original: Optional[Exception] = None):
        super().__init__(message)
        self.original = original
        self.message = message

    def __str__(self) -> str:
        return f"{self.message}: {self.original}"
