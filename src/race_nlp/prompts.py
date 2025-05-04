from __future__ import annotations
from enum import Enum
from typing import Dict, Optional, Set
from pydantic import BaseModel, ValidationError, validator
from src.utils.logger import F1Logger

logger = F1Logger()

class TemplateConfig(BaseModel):
    """Pydantic model for template validation"""
    template: str
    required_context: Set[str]
    allowed_placeholders: Set[str]
    default_values: Dict[str, str] = {}

    @validator('allowed_placeholders', always=True)
    def validate_placeholders(cls, v, values):
        """Automatically detect placeholders from template"""
        template = values.get('template', '')
        detected = {name for _, name, _, _ in Formatter().parse(template) if name}
        return detected

class TemplateName(str, Enum):
    """Type-safe template identifiers"""
    POST_RACE = "post_race"
    REPLY_FAN = "reply_fan"
    PRACTICE_UPDATE = "practice_update"
    MENTION_TEAMMATE = "mention_teammate"
    RACE_STRATEGY = "race_strategy"

class PromptTemplates:
    """
    Centralized prompt template registry with validation and context management.
    Implements TemplateHandlerProtocol from generate.py
    """
    
    _registry: Dict[TemplateName, TemplateConfig] = {
        TemplateName.POST_RACE: TemplateConfig(
            template=(
                "Write a {sentiment} social media post about the {race_name} race. "
                "Mention {team} team. Result: {result}. "
                "Include hashtags: #{race_hashtag} #{team_hashtag}"
            ),
            required_context={'race_name', 'team', 'result'},
            default_values={'sentiment': 'neutral'}
        ),
        TemplateName.REPLY_FAN: TemplateConfig(
            template=(
                "Respond to a fan comment about {topic}. "
                "Tone: {tone}. Max length: 280 characters. "
                "Include emoji related to {topic}"
            ),
            required_context={'topic'},
            default_values={'tone': 'positive'}
        ),
        TemplateName.PRACTICE_UPDATE: TemplateConfig(
            template=(
                "Create practice session update for {session_type}. "
                "Car feeling: {car_feeling}. "
                "Focus area: {focus_area}. "
                "Include weather info: {weather}"
            ),
            required_context={'session_type', 'car_feeling'}
        )
    }

    @classmethod
    def get_template_config(cls, name: TemplateName) -> TemplateConfig:
        """Retrieve validated template configuration"""
        if name not in cls._registry:
            logger.error(
                action="missing_template",
                response=f"Template {name} not found in registry"
            )
            raise ValueError(f"Template {name} not registered")
        return cls._registry[name]

    @classmethod
    def validate_context(cls, name: TemplateName, context: Dict) -> None:
        """Validate context against template requirements"""
        config = cls.get_template_config(name)
        missing = config.required_context - context.keys()
        if missing:
            logger.error(
                action="invalid_context",
                response=f"Missing required context keys: {missing}"
            )
            raise ValueError(f"Missing context keys: {missing}")

        extra = context.keys() - (config.required_context | config.allowed_placeholders)
        if extra:
            logger.warn(
                action="extra_context",
                response=f"Extra context keys provided: {extra}"
            )

    @classmethod
    def format_template(cls, name: TemplateName, context: Dict) -> str:
        """Format template with validated context and defaults"""
        config = cls.get_template_config(name)
        full_context = {**config.default_values, **context}
        
        try:
            cls.validate_context(name, full_context)
            return config.template.format(**full_context)
        except (KeyError, ValueError) as e:
            logger.error(
                action="template_format_error",
                response=f"Error formatting {name}: {str(e)}"
            )
            raise

    @classmethod
    def register_template(
        cls,
        name: TemplateName,
        template: str,
        required_context: Set[str],
        **kwargs
    ) -> None:
        """Dynamically register new templates at runtime"""
        try:
            config = TemplateConfig(
                template=template,
                required_context=required_context,
                **kwargs
            )
            cls._registry[name] = config
            logger.info(
                action="template_registered",
                response=f"Added new template: {name}"
            )
        except ValidationError as e:
            logger.error(
                action="invalid_template_config",
                response=f"Failed to register {name}: {str(e)}"
            )
            raise