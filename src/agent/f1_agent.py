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

    This agent integrates context management, text generation via an LLM,
    and simulated social media actions. It follows principles from the
    race_nlp package, including using Pydantic for data structures.

    Attributes:
        context_manager: Manages the agent's internal state and context.
        actions: Provides simulated social media action capabilities.
        text_generator: An object implementing the TextGenerationProtocol
                        for generating text based on templates and context.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context_manager: ContextManager = Field(default_factory=ContextManager)
    actions: SocialMediaActions = Field(default_factory=SocialMediaActions)
    text_generator: TextGenerationProtocol # Dependency injection for text generation

    @classmethod
    def create(cls, text_generator: TextGenerationProtocol) -> "F1Agent":
        """
        Factory method to create an F1Agent instance with dependencies.

        Args:
            text_generator: An instance implementing TextGenerationProtocol.

        Returns:
            An instance of F1Agent.
        """
        return cls(text_generator=text_generator)

    def think(self, new_context_data: Dict[str, Any]) -> AgentContext:
        """
        Updates the agent's internal context based on new information.

        This method corresponds to the 'Think' part of the assessment,
        allowing the agent to process new data and update its understanding
        of the current situation.

        Args:
            new_context_data: A dictionary containing new context information
                              to update the agent's state.

        Returns:
            The updated AgentContext object.
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

        This method corresponds to the 'Speak' part of the assessment,
        using the configured text generator to produce human-like text
        relevant to the agent's context and a given template.

        Args:
            template_name: The name of the template to use for text generation.
            additional_context: Optional dictionary of additional context data
                                to be used for this specific generation,
                                overriding or adding to the agent's current context.

        Returns:
            The generated text string.

        Raises:
            ValueError: If the template name is invalid or context is missing
                        for template formatting.
            GenerationError: If text generation by the LLM fails.
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
            # Re-raise the exception after logging
            raise

    def act(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs a simulated social media action.

        This method corresponds to the 'Act' part of the assessment,
        dispatching the action request to the SocialMediaActions handler.

        Args:
            action_type: A string specifying the type of action to perform
                         (e.g., 'simulate_like', 'reply_comment').
            action_data: A dictionary containing the necessary data for the
                         specified action.

        Returns:
            A dictionary containing the result of the simulated action.

        Raises:
            ValueError: If the action_type is unknown or action_data is invalid
                        for the specified action.
            Exception: If an error occurs during the execution of the simulated action.
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
                # Re-raise the exception after logging
                raise
        else:
            logger.error(
                action="agent_acting_error",
                response=f"Unknown action type: {action_type}"
            )
            raise ValueError(f"Unknown action type: {action_type}")
