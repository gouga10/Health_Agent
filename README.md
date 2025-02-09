# Medical Data Querying API

## Overview
This API enables medical professionals to query a structured medical database using natural language. It reformulates user questions into SQL queries, executes them against an SQLite database, and returns relevant results.

## Features
- Reformulates natural language questions into SQL queries.
- Executes queries against a predefined SQLite database containing electronic medical records (EMR).
- Supports conversational context for refining queries.
- Uses OpenAI's GPT models via LiteLLM for question reformulation and response generation.
- Built with FastAPI and Uvicorn for a lightweight and scalable API.

## Technologies Used
- **FastAPI**: Backend framework for API development.
- **Uvicorn**: ASGI server for running FastAPI.
- **SQLite**: Database for medical records.
- **LiteLLM**: Lightweight interface for OpenAI models.
- **CrewAI Flow**: Manages conversation flow and decision-making.
- **LangChain**: SQL database utilities.

## Installation
### Prerequisites
- Python 3.12.8 (recommended)
- Virtual environment (recommended)

### Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/gouga10/Health_Agent.git
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   cd Health_Agent
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   Create a `.env` file and add:
   ```
   OPEN_AI_API=your_openai_api_key
   ```

## Running the API
Start the server using Uvicorn:
```bash
cd src/health
python HealthFlow.py
```

## Running the Streamlit UI
Start the server using Uvicorn:
```bash
cd src/health
streamlit run streamlit.py
```



## Terminal Usage Example
You can test the API using `curl`:
```bash
curl -X 'POST' \
  'http://localhost:8001/generate' \
  -H 'Content-Type: application/json' \
  -d '{ "conv": [ {"role": "user", "content": "how old is Bobby Jackson"}, {"role": "assistant", "content": "Bobby Jackson is 30 years old"}, {"role": "user", "content": "who is his doctor"} ] }'
```

## Deployment
To deploy using Docker compose:

   ```bash
   docker compose up -d --build 
   ```

## License
This project is licensed under the MIT License.

