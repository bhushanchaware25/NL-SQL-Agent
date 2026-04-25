# 🤖 NL2SQL Agent

> Query any relational database using plain English — powered by a multi-agent AI pipeline.

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1-purple)](https://langchain-ai.github.io/langgraph)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev)

---

## Architecture

```
User Question
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LangGraph Pipeline                          │
│                                                                 │
│  [1] Schema Inspector → [2] SQL Generator → [3] SQL Executor   │
│                               ↑                    │           │
│                               └────────────────────┘           │
│                           (Critic retry loop)      │           │
│                                                    ▼           │
│                         [4] Critic/Validator → [5] Synthesizer │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
WebSocket Stream → React Frontend
  - Natural language answer
  - Auto-rendered Recharts visualization
  - Generated SQL with explanation
  - Raw data table
```

### The 5 Agents

| Agent | Role |
|-------|------|
| **Schema Inspector** | Reflects all tables, columns, PKs & FKs from the DB |
| **SQL Generator** | Generates SQL using schema + ChromaDB few-shot examples |
| **SQL Executor** | Runs SQL against the DB, captures results or errors |
| **Critic / Validator** | LLM judges quality; triggers retry loop if needed |
| **Response Synthesizer** | Writes natural language answer + recommends chart type |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | LangGraph |
| LLM | OpenRouter (`openrouter/auto`) via LangChain |
| Few-Shot Memory | ChromaDB (RAG-style) |
| SQL Safety | `sqlparse` + regex guard |
| Backend | FastAPI + WebSocket |
| Database | PostgreSQL 16 |
| Validation | Pydantic v2 |
| Frontend | React 18 + Vite |
| Charts | Recharts |
| State | Zustand |
| Containerization | Docker Compose |

---

## Quick Start

### Option A — Docker Compose (Recommended)

```bash
# 1. Clone and enter the project
cd "NL-SQL Agent"

# 2. Create your .env from the template
copy .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# 3. Build and start all services
docker compose up --build

# App is live at http://localhost:3000
# API docs at http://localhost:8000/docs
```

### Option B — Local Development

**Prerequisites:** Python 3.11+, Node 20+, PostgreSQL 16

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env: set OPENROUTER_API_KEY and DATABASE_URL

# Seed the demo database (run against your local PostgreSQL)
psql -U nl2sql -d ecommerce -f seed/schema.sql
psql -U nl2sql -d ecommerce -f seed/data.sql

# Start the backend
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies to backend automatically)
npm run dev
# App at http://localhost:3000
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | **Required.** Your OpenRouter key | — |
| `OPENROUTER_MODEL` | LLM model to use | `openrouter/auto` |
| `DATABASE_URL` | PostgreSQL connection string | demo DB |
| `MAX_RETRIES` | Critic retry limit | `3` |
| `SQL_SAFETY_ENABLED` | Block destructive SQL | `true` |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | `./chroma_data` |

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

---

## Sample Queries to Try

- *"What are the top 5 products by total revenue?"*
- *"Show me monthly revenue for the past 6 months"*
- *"Which customers have spent more than $500 total?"*
- *"What is the average order value by city?"*
- *"List all products with a rating below 3 stars"*
- *"How many orders were placed last month?"*

---

## Security

- All SQL passes through a two-layer safety guard (regex + sqlparse AST) before execution.
- `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`, `CREATE` are blocked by default.
- Set `SQL_SAFETY_ENABLED=false` only in development environments.

---

## Project Structure

```
NL-SQL Agent/
├── backend/
│   ├── app/
│   │   ├── agents/          # 5 LangGraph agent nodes
│   │   ├── graph/           # LangGraph pipeline + state
│   │   ├── memory/          # ChromaDB few-shot store
│   │   ├── safety/          # SQL guard
│   │   ├── db/              # SQLAlchemy connector
│   │   ├── api/             # FastAPI routes + schemas
│   │   ├── core/            # Config + LLM factory
│   │   └── main.py
│   ├── seed/                # E-commerce schema + data
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/      # React UI components
│       ├── hooks/           # useWebSocket
│       └── store/           # Zustand state
└── docker-compose.yml
```
