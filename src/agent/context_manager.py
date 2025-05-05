from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any

# Define the structure for the agent's internal context
class AgentContext(BaseModel):
    """Represents the internal state and context of the F1 Agent."""
    race_stage: str = Field(default="pre_race", description="Current stage of the race weekend (e.g., practice, qualifying, race, post_race).")
    recent_result: Optional[str] = Field(default=None, description="Result of the most recent session (e.g., 'good', 'bad', 'DNF').")
    team_dynamics: Optional[str] = Field(default=None, description="Information about team dynamics relevant to the agent.")
    competitor_dynamics: Optional[str] = Field(default=None, description="Information about competitor dynamics relevant to the agent.")
    # Add other context relevant fields as needed based on potential future requirements

class ContextManager(BaseModel):
    """Manages the F1 Agent's internal context."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context: AgentContext = Field(default_factory=AgentContext)

    def update_context(self, new_context_data: Dict[str, Any]):
        """Updates the agent's context with new information."""
        updated_data = self.context.model_dump()
        updated_data.update(new_context_data)
        self.context = AgentContext(**updated_data)

    def get_context(self) -> AgentContext:
        """Retrieves the current agent context."""
        return self.context

    def get_context_dict(self) -> Dict[str, Any]:
        """Retrieves the current agent context as a dictionary."""
        return self.context.model_dump()
