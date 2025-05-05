from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from src.utils.logger import F1Logger
from src.race_nlp.generator import TextGenerator, TextGenerationProtocol
from .context_manager import ContextManager, AgentContext
from .actions import SocialMediaActions

logger = F1Logger()

class F1Agent(BaseModel):
    """
    Represents the F1 AI Agent capable of thinking, speaking, and acting.
    Follows principles from race_nlp package (e.g., Pydantic for structure).
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context_manager: ContextManager = Field(default_factory=ContextManager)
    actions: SocialMediaActions = Field(default_factory=SocialMediaActions)
    text_generator: TextGenerationProtocol # Dependency injection for text generation

    @classmethod
    def create(cls, text_generator: TextGenerationProtocol) -> "F1Agent":
        """Factory method to create an F1Agent instance with dependencies."""
        return cls(text_generator=text_generator)

    def think(self, new_context_data: Dict[str, Any]) -> AgentContext:
        """
        Updates the agent's internal context based on new information.
        Corresponds to the 'Think' part of the assessment.
        """
        logger.info(
            action="agent_thinking",
            response={"new_context_data": new_context_data}
        )
        self.context_manager.update_context(new_context_data)
        return self.context_manager.get_context()

    def speak(self, template_name: str, additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates text based on the current context and a specified template.
        Corresponds to the 'Speak' part of the assessment.
        """
        current_context = self.context_manager.get_context_dict()
        if additional_context:
            current_context.update(additional_context)

        logger.info(
            action="agent_speaking",
            response={"template_name": template_name, "context_used": current_context}
        )

        try:
            generated_text = self.text_generator.generate(template_name, current_context)
            logger.info(
                action="agent_speaking_success",
                response={"generated_text": generated_text}
            )
            return generated_text
        except Exception as e:
            logger.error(
                action="agent_speaking_error",
                response=str(e)
            )
            raise

    def act(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs a simulated social media action.
        Corresponds to the 'Act' part of the assessment.
        """
        logger.info(
            action="agent_acting",
            response={"action_type": action_type, "action_data": action_data}
        )

        action_method = getattr(self.actions, action_type, None)

        if action_method and callable(action_method):
            try:
                result = action_method(**action_data)
                logger.info(
                    action="agent_acting_success",
                    response={"result": result}
                )
                return result
            except Exception as e:
                logger.error(
                    action="agent_acting_error",
                    response=str(e)
                )
                raise
        else:
            logger.error(
                action="agent_acting_error",
                response=f"Unknown action type: {action_type}"
            )
            raise ValueError(f"Unknown action type: {action_type}")
