# F1 Racer AI Agent

This project implements an AI agent designed to generate social media posts and replies from the perspective of an F1 driver. It uses natural language processing (NLP) techniques to format responses based on predefined templates and provided context.

## Project Structure

-   `src/agent/`: Contains the core AI agent logic, context management, and actions.
-   `src/api/`: Implements the FastAPI web server to expose the agent's functionality via a REST API.
-   `src/race_nlp/`: Handles prompt templating and generation using Pydantic for configuration.
-   `src/utils/`: Utility functions, including a custom logger.
-   `data/`: Placeholder for potential data files (e.g., context data).
-   `tests/`: Unit tests for various components.

## Setup

### Prerequisites

-   Python 3.8+
-   Docker and Docker Compose (for containerized setup)

### Local Development

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd f1_racer_ai_agent
    checkout master branch
    ```
2.  Create a virtual environment (recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running with Docker Compose

Ensure Docker and Docker Compose are installed and running.

```bash
docker-compose up --build
```

This will build the Docker image and start the FastAPI application, accessible at `http://localhost:8000`.

## Running the Application

### Local Development

After installing dependencies and activating the virtual environment:

```bash
uvicorn src.api.main:app --reload
```

The API will be available at `http://localhost:8000`.

### API Endpoints

The application exposes several endpoints via the FastAPI web server.

#### `POST /generate_post`

Generates a social media post or reply based on a specified template and context.

-   **Request Body:** `GeneratePostRequest` schema (see `src/api/schemas.py`)
    ```json
    {
      "template_name": "string", // Name of the template (e.g., "post_race", "reply_fan")
      "context_data": {
        "key": "value" // Context data required by the template
      }
    }
    ```
-   **Response:** `AgentResponse` schema (see `src/api/schemas.py`)
    ```json
    {
      "status": "success" | "error",
      "message": "string",
      "data": {} // Contains the generated text under the key "post_text" on success
    }
    ```
-   **Example Request:** See below in "Available Prompts".

#### `POST /simulate_like`

Simulates liking a post. This is an example action the agent can perform.

-   **Request Body:** `SimulateLikeRequest` schema (see `src/api/schemas.py`)
    ```json
    {
      "post_id": "string", // Identifier for the post
      "user_id": "string" // Identifier for the user liking the post
    }
    ```
-   **Response:** `AgentResponse` schema

#### `POST /simulate`

Simulates a generic social media action.

-   **Request Body:** `SimulateActionRequest` schema (see `src/api/schemas.py`)
    ```json
    {
      "action_type": "string", // Type of action (e.g., "comment", "share")
      "action_data": {} // Data specific to the action type
    }
    ```
-   **Response:** `AgentResponse` schema

#### `POST /update_context`

Updates the agent's internal context with new information.

-   **Request Body:** `UpdateContextRequest` schema (see `src/api/schemas.py`)
    ```json
    {
      "context_data": {} // Dictionary of context key-value pairs to update
    }
    ```
-   **Response:** `AgentResponse` schema (data contains the updated context)

#### `GET /get_context`

Retrieves the agent's current internal context.

-   **Request Body:** None
-   **Response:** `AgentResponse` schema (data contains the current context dictionary)

### Available Prompts

The `src/race_nlp/prompts.py` file defines the available templates for generating text. Each template requires specific context data.

-   **`post_race`**: Generates a social media post about a race.
    -   **Required Context:** `race_name`, `team`, `result`
    -   **Optional Context:** `sentiment` (default: "neutral")
    -   **Placeholders:** `race_name`, `team`, `result`, `sentiment`, `race_hashtag`, `team_hashtag`
    -   **Example Request:**
        ```bash
        curl -X POST http://localhost:8000/generate_post \
        -H "Content-Type: application/json" \
        -d '{
          "template_name": "post_race",
          "context_data": {
            "race_name": "Monaco Grand Prix",
            "team": "Red Bull Racing",
            "result": "P1",
            "sentiment": "thrilled",
            "race_hashtag": "#MonacoGP",
            "team_hashtag": "#RedBullRacing"
          }
        }'
        ```

-   **`reply_fan`**: Generates a reply to a fan comment.
    -   **Required Context:** `fan_comment`, `topic`
    -   **Optional Context:** `tone` (default: "positive"), `race_context` (default: "current situation")
    -   **Placeholders:** `fan_comment`, `topic`, `tone`, `race_context`
    -   **Example Request:**
        ```bash
        curl -X POST http://localhost:8000/generate_post \
        -H "Content-Type: application/json" \
        -d '{
          "template_name": "reply_fan",
          "context_data": {
            "fan_comment": "Great drive today! Loved your overtake on lap 50!",
            "topic": "overtake",
            "tone": "appreciative",
            "race_context": "Monaco Grand Prix"
          }
        }'
        ```

-   **`race_strategy`**: Generates text about race strategy.
    -   **Required Context:** `track`, `tires`
    -   **Optional Context:** None
    -   **Placeholders:** `track`, `tires`
    -   **Example Request:**
        ```bash
        curl -X POST http://localhost:8000/generate_post \
        -H "Content-Type: application/json" \
        -d '{
          "template_name": "race_strategy",
          "context_data": {
            "track": "Silverstone",
            "tires": "Mediums"
          }
        }'
        ```

-   **`practice_update`**: Generates a practice session update.
    -   **Required Context:** `weather`, `lap_times`
    -   **Optional Context:** None
    -   **Placeholders:** `weather`, `lap_times`
    -   **Example Request:**
        ```bash
        curl -X POST http://localhost:8000/generate_post \
        -H "Content-Type: application/json" \
        -d '{
          "template_name": "practice_update",
          "context_data": {
            "weather": "Sunny",
            "lap_times": "1:28.500"
          }
        }'
        ```

-   **`mention_teammate`**: Generates text mentioning a teammate's achievement.
    -   **Required Context:** `teammate_name`, `achievement`
    -   **Optional Context:** None
    -   **Placeholders:** `teammate_name`, `achievement`
    -   **Example Request:**
        ```bash
        curl -X POST http://localhost:8000/generate_post \
        -H "Content-Type: application/json" \
        -d '{
          "template_name": "mention_teammate",
          "context_data": {
            "teammate_name": "Sergio Perez",
            "achievement": "a great qualifying lap"
          }
        }'
        ```

## Running Tests

To run the unit tests:

```bash
pytest
