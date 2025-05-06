from string import Formatter
from enum import Enum
from pydantic import (
    BaseModel, 
    computed_field, 
    field_validator,
    ConfigDict
)
from typing import Dict, Set
from src.utils.logger import F1Logger

logger = F1Logger()

class TemplateConfig(BaseModel):
    """Pydantic v2 template configuration with computed fields"""
    model_config = ConfigDict(validate_assignment=True)

    template: str
    required_context: Set[str]
    default_values: Dict[str, str] = {}

    @computed_field
    @property
    def allowed_placeholders(self) -> Set[str]:
        """Automatically detect placeholders from template"""
        return {
            name 
            for _, name, _, _ in Formatter().parse(self.template) 
            if name
        }

class TemplateName(str, Enum):
    POST_RACE = "post_race"
    REPLY_FAN = "reply_fan"
    PRACTICE_UPDATE = "practice_update"
    MENTION_TEAMMATE = "mention_teammate"
    RACE_STRATEGY = "race_strategy"

class PromptTemplates:
    _registry: Dict[TemplateName, TemplateConfig] = {
        TemplateName.POST_RACE: TemplateConfig(
            template=(
                "Reflecting on the {race_name} race weekend from inside the cockpit. It was a {sentiment} one for us at {team}. "
                "Finished P{result}. The car felt {car_feeling} out there, especially with the {weather} conditions making things tricky. "
                "Not the easiest race, but we fought hard and gathered crucial data. Now, it's straight into the debrief with the engineers to understand everything and find those areas to improve for the next round. "
                "Massive thanks to every single person in the team, both here at the track and back at the factory. We're all pushing together! "
                "#{race_hashtag} #{team_hashtag}"
            ),
            required_context={"race_name", "team", "result", "car_feeling", "weather", "race_hashtag", "team_hashtag"},
            default_values={"sentiment": "challenging"}
        ),
        TemplateName.REPLY_FAN: TemplateConfig(
            template=(
                "Hey! Thanks for the message, really appreciate you reaching out. Your comment about \"{fan_comment}\" is a great point. "
                "Thinking about {topic}, it's definitely something we're always working on in F1, constantly looking for that edge. "
                "Given the context of {race_context}, my perspective on it is... [Generate a natural, authentic response as an F1 driver. Adopt a {tone} tone based on the context provided, integrating the {race_context} naturally into the response. Use language appropriate for social media, potentially including F1 terms where natural. Focus on generating a unique response based on the specific context provided, avoiding generic phrases. Keep it concise, max 280 characters. Include a relevant emoji related to {topic} or the fan comment.]"
            ),
            required_context={"fan_comment", "topic", "race_context", "tone"},
            default_values={}
        ),
        TemplateName.RACE_STRATEGY: TemplateConfig(
            template=(
                "Getting ready to hit the track at {track}. Strategy is going to be absolutely crucial here, especially with how quickly things can change over a race distance. "
                "Current plan is to start on the {tires} compound, but we're constantly analyzing the data and the latest {weather} forecast to be ready for anything. "
                "Targeting a {stint_length} first stint, but we need to be ready to react to how the race unfolds and manage the tires effectively. Flexibility is absolutely key!"
            ),
            required_context={"track", "tires", "weather", "stint_length"},
            default_values={}
        ),
        TemplateName.PRACTICE_UPDATE: TemplateConfig(
            template=(
                "Practice sessions wrapped up at {track}. Conditions were {weather}. "
                "Best lap time was {lap_times}. The car felt {car_feeling} today - still fine-tuning things to get it exactly where we want it for qualifying and the race, but we're making solid progress on the {focus_area}. "
                "Lots of data for the engineers to crunch through tonight."
            ),
            required_context={"track", "weather", "lap_times", "car_feeling", "focus_area"},
            default_values={}
        ),
        TemplateName.MENTION_TEAMMATE: TemplateConfig(
            template=(
                "Huge congratulations to my teammate {teammate_name} on their {achievement}! "
                "Brilliant job out there. That result is a massive boost for everyone at {team} and really shows the strength of our package this season. "
                "Great teamwork and looking forward to continuing to push together!"
            ),
            required_context={"teammate_name", "achievement", "team"},
            default_values={}
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
