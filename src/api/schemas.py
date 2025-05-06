from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class GeneratePostRequest(BaseModel):
    """Schema for the /generate_post endpoint request body."""
    template_name: str = Field(..., description="The name of the template to use for text generation.")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context data for the template.")

class ReplyCommentRequest(BaseModel):
    """Schema for the /reply_comment endpoint request body."""
    comment_text: str = Field(..., description="The text of the comment to reply to.")
    agent_response: str = Field(..., description="The agent's generated response.")

class SimulateLikeRequest(BaseModel):
    """Schema for the /simulate_like endpoint request body."""
    post_id: str = Field(..., description="The ID of the post to simulate liking.")

class SimulateActionRequest(BaseModel):
    """Schema for the generic /simulate endpoint request body."""
    action_type: str = Field(..., description="The type of action to simulate (e.g., 'post_status_update', 'mention_teammate_or_competitor').")
    action_data: Dict[str, Any] = Field(..., description="Data required for the specific action.")

class UpdateContextRequest(BaseModel):
    """Schema for updating the agent's context."""
    context_data: Dict[str, Any] = Field(..., description="New context data to update the agent's state.")

class AgentResponse(BaseModel):
    """Base schema for API responses."""
    status: str = Field(..., description="Status of the operation (e.g., 'success', 'error').")
    message: str = Field(..., description="A descriptive message about the operation result.")
    data: Optional[Any] = Field(None, description="Optional data returned by the operation.")
