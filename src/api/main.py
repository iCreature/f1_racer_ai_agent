from fastapi import FastAPI, HTTPException
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

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
f1_agent: Optional[F1Agent] = None # Initialize as None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes resources on startup and cleans up on shutdown."""
    global f1_agent
    try:
        # Assuming TemplateHandler and TextGenerator initialization can be async if needed
        template_handler = TemplateHandler()
        # If model loading is async, use await here
        text_generator = TextGenerator.from_pretrained(
            model_name="gpt2", # Using a small, readily available model for demonstration
            template_handler=template_handler
        )
        f1_agent = F1Agent.create(text_generator=text_generator)
        logger.info(action="api_startup", response="TextGenerator and F1Agent initialized successfully.")
        yield # Application starts here
    except Exception as e:
        logger.error(action="api_startup_error", response=f"Failed to initialize TextGenerator or F1Agent: {e}")
        # Depending on severity, you might want to exit or just log
        # raise # Uncomment to prevent startup on failure
    finally:
        # Clean up resources if necessary on shutdown
        logger.info(action="api_shutdown", response="Application shutting down.")

app = FastAPI(lifespan=lifespan) # Link the lifespan context manager

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
    except Exception as e: # Catch potential errors from the agent's speak method
        logger.error(action="api_generate_post_error", response=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate post: {e}")

@app.post("/simulate_like", response_model=AgentResponse)
async def simulate_like(request: SimulateLikeRequest):
    """Simulates liking a post."""
    if not f1_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized.")
    try:
        result = f1_agent.act("simulate_like", request.model_dump()) # Use model_dump() for Pydantic v2+
        return AgentResponse(status="success", message="Post like simulated.", data=result)
    except ValueError as e: # Catch ValueError from agent.act
        raise HTTPException(status_code=400, detail=f"Invalid action data: {e}")
    except Exception as e: # Catch other potential errors from agent.act
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
    except ValueError as e: # Catch ValueError from agent.act
        raise HTTPException(status_code=400, detail=f"Invalid action type or data: {e}")
    except Exception as e: # Catch other potential errors from agent.act
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
    except Exception as e: # Catch potential errors from agent.think
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
    except Exception as e: # Catch potential errors from context_manager.get_context_dict
        logger.error(action="api_get_context_error", response=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent context: {e}")

# Add a health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify agent initialization status."""
    if f1_agent:
        return {"status": "ok", "agent_initialized": True}
    else:
        return {"status": "error", "agent_initialized": False, "detail": "Agent failed to initialize"}
