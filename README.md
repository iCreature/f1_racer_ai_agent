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

The application takes some time to run roughly 4 minutes, 

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

### API as a Simulation Pipeline

The API endpoints are designed to simulate the data flow and interactions that an AI agent would experience in a real-world social media environment.

-   **`/update_context`**: Represents the agent receiving new information from the environment (e.g., race data updates, fan comments, team communications). This information is processed and integrated into the agent's internal state or "context".
-   **`/get_context`**: Allows external systems or monitoring tools to inspect the agent's current understanding and state based on the information it has received.
-   **`/generate_post`**: Simulates the agent deciding to generate a social media post or reply. It takes the current context and a specific prompt template as input and produces the desired text output. This represents the agent's "speak" action.
-   **`/simulate_like` / `/simulate`**: Represent the agent performing actions in the simulated environment, such as liking a post, commenting, or sharing. These endpoints trigger the agent's "act" functionality based on simulated external events or internal decisions.

This API structure allows for testing and interacting with the agent's core logic (thinking, speaking, acting) by providing simulated inputs and observing the outputs and state changes, mimicking a simplified data pipeline.

### Available Prompts

The `src/race_nlp/prompts.py` file defines the available templates for generating text. Each template requires specific context data.

-   **`post_race`**: Generates a social media post about a race.
    -   **Required Context:** `race_name`, `team`, `result`, `car_feeling`, `weather`, `race_hashtag`, `team_hashtag`
    -   **Optional Context:** `sentiment` (default: "challenging")
    -   **Placeholders:** `race_name`, `team`, `result`, `sentiment`, `car_feeling`, `weather`, `race_hashtag`, `team_hashtag`
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
            "car_feeling": "great",
            "weather": "sunny",
            "race_hashtag": "#MonacoGP",
            "team_hashtag": "#RedBullRacing"
          }
        }'
        ```

-   **`reply_fan`**: Generates a reply to a fan comment.
    -   **Required Context:** `fan_comment`, `topic`, `race_context`, `tone`
    -   **Optional Context:** None
    -   **Placeholders:** `fan_comment`, `topic`, `race_context`, `tone`
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
    -   **Required Context:** `track`, `tires`, `weather`, `stint_length`
    -   **Optional Context:** None
    -   **Placeholders:** `track`, `tires`, `weather`, `stint_length`
    -   **Example Request:**
        ```bash
        curl -X POST http://localhost:8000/generate_post \
        -H "Content-Type: application/json" \
        -d '{
          "template_name": "race_strategy",
          "context_data": {
            "track": "Silverstone",
            "tires": "Mediums",
            "weather": "cloudy",
            "stint_length": "20 laps"
          }
        }'
        ```

-   **`practice_update`**: Generates a practice session update.
    -   **Required Context:** `track`, `weather`, `lap_times`, `car_feeling`, `focus_area`
    -   **Optional Context:** None
    -   **Placeholders:** `track`, `weather`, `lap_times`, `car_feeling`, `focus_area`
    -   **Example Request:**
        ```bash
        curl -X POST http://localhost:8000/generate_post \
        -H "Content-Type: application/json" \
        -d '{
          "template_name": "practice_update",
          "context_data": {
            "track": "Spa-Francorchamps",
            "weather": "wet",
            "lap_times": "1:50.123",
            "car_feeling": "tricky",
            "focus_area": "long run pace"
          }
        }'
        ```

-   **`mention_teammate`**: Generates text mentioning a teammate's achievement.
    -   **Required Context:** `teammate_name`, `achievement`, `team`
    -   **Optional Context:** None
    -   **Placeholders:** `teammate_name`, `achievement`, `team`
    -   **Example Request:**
        ```bash
        curl -X POST http://localhost:8000/generate_post \
        -H "Content-Type: application/json" \
        -d '{
          "template_name": "mention_teammate",
          "context_data": {
            "teammate_name": "Sergio Perez",
            "achievement": "a great qualifying lap",
            "team": "Red Bull Racing"
          }
        }'
        ```

## Running Tests

To run the unit tests:

```bash
pytest
