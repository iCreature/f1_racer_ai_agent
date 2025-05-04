from __future__ import annotations
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from abc import ABC, abstractmethod
from functools import wraps

from transformers import Pipeline, pipeline
from pydantic import BaseModel, validate_arguments

from utils.logger import F1Logger
from .prompts import PromptTemplates

logger = F1Logger()

@runtime_checkable
class TextGenerationProtocol(Protocol):
    """Abstract text generation interface"""
    @abstractmethod
    def generate(self, template_name: str, context: dict) -> str:
        ...

class TemplateHandlerProtocol(Protocol):
    """Abstract template handling interface"""
    @abstractmethod
    def get_template(self, template_name: str) -> str:
        ...
    
    @abstractmethod
    def format_template(self, template_name: str, context: dict) -> str:
        ...

class TemplateHandler(TemplateHandlerProtocol):
    """Handles template resolution and formatting with validation"""
    @validate_arguments
    def get_template(self, template_name: str) -> str:
        if not hasattr(PromptTemplates, template_name):
            logger.error(
                action="template_resolution",
                response=f"Missing template: {template_name}"
            )
            raise ValueError(f"Template '{template_name}' not found")
        return getattr(PromptTemplates, template_name)

    @validate_arguments
    def format_template(self, template_name: str, context: dict) -> str:
        template = self.get_template(template_name)
        try:
            return template.format(**context)
        except KeyError as e:
            logger.error(
                action="template_formatting",
                response=f"Missing context key: {e}"
            )
            raise ValueError(f"Missing context key: {e}") from None

class TextGenerator(BaseModel, TextGenerationProtocol):
    """Main text generation component with fallback logic"""
    model: Pipeline
    template_handler: TemplateHandlerProtocol
    max_length: int = 128
    num_return_sequences: int = 1
    enable_fallback: bool = True

    class Config:
        arbitrary_types_allowed = True  # For Pipeline type

    @classmethod
    def from_pretrained(
        cls,
        model_name: str,
        template_handler: Optional[TemplateHandlerProtocol] = None,
        **kwargs
    ) -> TextGenerator:
        """Factory method with sensible defaults"""
        return cls(
            model=pipeline("text-generation", model=model_name),
            template_handler=template_handler or TemplateHandler(),
            **kwargs
        )

    def generate(self, template_name: str, context: dict) -> str:
        """Main generation workflow with error handling"""
        try:
            prompt = self.template_handler.format_template(template_name, context)
            return self._generate_with_llm(prompt)
        except Exception as e:
            if self.enable_fallback:
                return self._fallback_response(template_name, context)
            raise GenerationError("Text generation failed") from e

    def _generate_with_llm(self, prompt: str) -> str:
        """Core LLM invocation with instrumentation"""
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
        """Template-based fallback when LLM fails"""
        logger.warn(
            action="fallback_triggered",
            response={"template": template_name}
        )
        return self.template_handler.format_template(template_name, context)

class GenerationError(Exception):
    """Custom exception for generation failures"""
    def __init__(self, message: str, original: Optional[Exception] = None):
        super().__init__(message)
        self.original = original