from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any

# Define the structure for the agent's internal context
class AgentContext(BaseModel):
    """
    Represents the internal state and context of the F1 Agent.

    This model holds key information that the agent uses to inform its
    thinking, speaking, and acting processes.

    Attributes:
        race_stage: The current stage of the race weekend.
        recent_result: The outcome of the most recent session.
        team_dynamics: Relevant information about the agent's team.
        competitor_dynamics: Relevant information about competitors.
    """
    race_stage: str = Field(default="pre_race", description="Current stage of the race weekend (e.g., practice, qualifying, race, post_race).")
    recent_result: Optional[str] = Field(default=None, description="Result of the most recent session (e.g., 'good', 'bad', 'DNF').")
    team_dynamics: Optional[str] = Field(default=None, description="Information about team dynamics relevant to the agent.")
    competitor_dynamics: Optional[str] = Field(default=None, description="Information about competitor dynamics relevant to the agent.")
    # Add other context relevant fields as needed based on potential future requirements

class ContextManager(BaseModel):
    """
    Manages the F1 Agent's internal context.

    This class provides methods to update and retrieve the agent's
    current state, encapsulated in the AgentContext model.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context: AgentContext = Field(default_factory=AgentContext)

    def update_context(self, new_context_data: Dict[str, Any]):
        """
        Updates the agent's context with new information.

        New data is merged into the existing context, overwriting keys
        if they already exist.

        Args:
            new_context_data: A dictionary containing the new context data.
        """
        updated_data = self.context.model_dump()
        updated_data.update(new_context_data)
        self.context = AgentContext(**updated_data)

    def get_context(self) -> AgentContext:
        """
        Retrieves the current agent context.

        Returns:
            The current AgentContext object.
        """
        return self.context

    def get_context_dict(self) -> Dict[str, Any]:
        """
        Retrieves the current agent context as a dictionary.

        Returns:
            A dictionary representation of the current AgentContext.
        """
        return self.context.model_dump()
