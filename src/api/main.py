from fastapi import FastAPI, HTTPException
from typing import Dict, Any
from src.api.schemas import (
    GeneratePostRequest,
    ReplyCommentRequest,
    SimulateLikeRequest,
    SimulateActionRequest,
    UpdateContextRequest,
    AgentResponse
)
from src.agent.f1_agent import F1Agent
from src.race_nlp.generator import TextGenerator, TemplateHandler
from src.utils.logger import F1Logger

logger = F1Logger()
app = FastAPI()

# Initialize TextGenerator and F1Agent
# In a real application, model loading might be handled differently (e.g., async, background task)
# For this assessment, we'll initialize it directly.
try:
    # Assuming a default model name and template handler setup
    template_handler = TemplateHandler()
    text_generator = TextGenerator.from_pretrained(
        model_name="gpt2", # Using a small, readily available model for demonstration
        template_handler=template_handler
    )
    f1_agent = F1Agent.create(text_generator=text_generator)
    logger.info(action="api_startup", response="TextGenerator and F1Agent initialized successfully.")
except Exception as e:
    logger.error(action="api_startup_error", response=f"Failed to initialize TextGenerator or F1Agent: {e}")
    # Depending on requirements, you might want to raise the exception or handle it differently
    # For now, we'll log and allow the app to start, but endpoints might fail.
    f1_agent = None # Ensure f1_agent is None if initialization fails

@app.post("/generate_post", response_model=AgentResponse)
async def generate_post(request: GeneratePostRequest):
    """Generates a social media post based on context."""
    if not f1_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized.")
    try:
        generated_text = f1_agent.speak(request.template_name, request.context_data)
        return AgentResponse(status="success", message="Post generated successfully.", data={"post_text": generated_text})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request data: {e}")
    except Exception as e:
        logger.error(action="api_generate_post_error", response=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate post: {e}")

@app.post("/reply_comment", response_model=AgentResponse)
async def reply_comment(request: ReplyCommentRequest):
    """Simulates replying to a comment."""
    if not f1_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized.")
    try:
        result = f1_agent.act("reply_comment", request.model_dump()) # Use model_dump() for Pydantic v2+
        return AgentResponse(status="success", message="Comment reply simulated.", data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid action data: {e}")
    except Exception as e:
        logger.error(action="api_reply_comment_error", response=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to simulate comment reply: {e}")

@app.post("/simulate_like", response_model=AgentResponse)
async def simulate_like(request: SimulateLikeRequest):
    """Simulates liking a post."""
    if not f1_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized.")
    try:
        result = f1_agent.act("simulate_like", request.model_dump()) # Use model_dump() for Pydantic v2+
        return AgentResponse(status="success", message="Post like simulated.", data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid action data: {e}")
    except Exception as e:
        logger.error(action="api_simulate_like_error", response=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to simulate post like: {e}")

@app.post("/simulate", response_model=AgentResponse)
async def simulate_action(request: SimulateActionRequest):
    """Simulates a generic social media action."""
    if not f1_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized.")
    try:
        result = f1_agent.act(request.action_type, request.action_data)
        return AgentResponse(status="success", message=f"Action '{request.action_type}' simulated.", data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid action type or data: {e}")
    except Exception as e:
        logger.error(action="api_simulate_action_error", response=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to simulate action '{request.action_type}': {e}")

@app.post("/update_context", response_model=AgentResponse)
async def update_context(request: UpdateContextRequest):
    """Updates the agent's internal context."""
    if not f1_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized.")
    try:
        updated_context = f1_agent.think(request.context_data)
        return AgentResponse(status="success", message="Agent context updated.", data=updated_context.model_dump()) # Use model_dump()
    except Exception as e:
        logger.error(action="api_update_context_error", response=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update agent context: {e}")

@app.get("/get_context", response_model=AgentResponse)
async def get_context():
    """Retrieves the agent's current internal context."""
    if not f1_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized.")
    try:
        current_context = f1_agent.context_manager.get_context_dict()
        return AgentResponse(status="success", message="Agent context retrieved.", data=current_context)
    except Exception as e:
        logger.error(action="api_get_context_error", response=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent context: {e}")
