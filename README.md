<div align="center">
  <img src="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/bot.svg" width="80" height="80" alt="NL2SQL Agent Logo">
  <h1>NL2SQL Autonomous Agent</h1>
  <p><strong>A 5-Agent LangGraph Pipeline for Natural Language to SQL Translation, Execution, and Visualization</strong></p>
  
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![LangChain](https://img.shields.io/badge/LangChain-0.2.6-1C3C3C?style=flat-square)](https://www.langchain.com/)
  [![LangGraph](https://img.shields.io/badge/LangGraph-0.1.19-orange?style=flat-square)](https://langchain-ai.github.io/langgraph/)
  [![React](https://img.shields.io/badge/React-18.x-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
  [![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5.3-FF6F00?style=flat-square)](https://www.trychroma.com/)
</div>

<br/>

NL2SQL Agent is an advanced, autonomous AI pipeline that allows users to query complex PostgreSQL databases using plain English. Built with **LangGraph**, it features a multi-agent architecture with built-in self-correction (Critic Validator), semantic few-shot learning (ChromaDB), and an interactive glassmorphic React frontend that streams real-time agent reasoning via WebSockets.

## 🌟 Key Features

- **Multi-Agent Pipeline:** Orchestrated using LangGraph for a deterministic, stateful, and self-healing execution flow.
- **Self-Correction & Reflection:** The *Critic Validator* agent evaluates execution results against the original user intent. If the SQL fails or yields nonsensical results, it provides targeted feedback back to the generator, automatically retrying until successful.
- **RAG-Powered Few-Shot Learning:** Uses **ChromaDB** as a semantic memory store. It retrieves the top-k most relevant successful historical queries to inject into the LLM prompt, vastly improving SQL generation accuracy.
- **SQL Safety Guard:** A robust two-layer security mechanism (Regex + AST token walking via `sqlparse`) that strictly blocks destructive DML/DDL operations (e.g., `DROP`, `DELETE`, `UPDATE`) from reaching the database.
- **Real-Time Streaming UI:** The React frontend connects via WebSockets to stream the exact reasoning and status of the AI pipeline as it works.
- **Dynamic Data Visualization:** Automatically determines the best way to represent data and renders interactive charts (Bar, Line, Pie) using Recharts.

---

## 🧠 System Architecture

The core of the application is a directed cyclic graph (DCG) of 5 specialized LangChain agents.

```mermaid
graph TD
    User([User Question]) --> A
    A[1. Schema Inspector] --> B
    B[2. SQL Generator] --> C
    C[3. SQL Executor] --> D
    D[4. Critic / Validator] -->|Invalid / Error| B
    D -->|Valid| E
    E[5. Response Synthesizer] --> Output([Final Answer + Chart])
    
    subgraph Memory
        DB[(ChromaDB)] -.->|Semantic Few-Shot Retrieval| B
    end
    
    subgraph Security
        Guard[SQL Safety Guard] -.->|AST Parsing| C
    end
```

### The 5 Agents
1. **Schema Inspector:** Reflects the live PostgreSQL database and extracts the current schema (tables, columns, types) to provide accurate context.
2. **SQL Generator:** Uses RAG to retrieve similar successful queries from ChromaDB, then translates the natural language question into a PostgreSQL query.
3. **SQL Executor:** Validates the query against the **Safety Guard**, then securely executes the query against the database.
4. **Critic Validator:** Analyzes the result set against the original question. If an error occurred or the result is illogical, it generates a critique and loops back to the SQL Generator.
5. **Response Synthesizer:** Converts the raw SQL result set into a conversational English response and intelligently recommends/formats data for Recharts visualizations.

---

## 🛠️ Technology Stack

### Backend
- **Python 3.12**
- **Framework:** FastAPI (REST + WebSockets)
- **AI Orchestration:** LangChain, LangGraph, OpenAI / OpenRouter Models
- **Vector Database:** ChromaDB (Local persistent storage)
- **Database Connection:** SQLAlchemy, psycopg2
- **Security:** sqlparse (AST tokenization)

### Frontend
- **Framework:** React + Vite
- **State Management:** Zustand
- **Styling:** Vanilla CSS (Glassmorphism design system)
- **Visualizations:** Recharts
- **Icons:** Lucide React

---

## 🚀 Getting Started

You can run the entire application (Frontend, Backend, and a bundled Postgres Database) easily using Docker Compose.

### Prerequisites
- Docker & Docker Compose
- An OpenRouter API Key (or OpenAI API Key)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/bhushanchaware25/nl-sql-agent.git
   cd nl-sql-agent
   ```

2. **Set up Environment Variables**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and add your `OPENROUTER_API_KEY`.

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the Application**
   - Frontend UI: http://localhost:3000
   - Backend API Docs: http://localhost:8000/docs
   
*Note: On first startup, the PostgreSQL database is automatically seeded with a sample E-Commerce dataset (Customers, Products, Orders, Reviews, etc.) and ChromaDB is populated with 20 base example pairs.*

---

## 💻 Local Development Setup (Without Docker)

If you prefer to run the components directly on your machine:

1. **Start a local PostgreSQL database**
   Ensure you have a database created and run the seed files:
   ```bash
   psql -U postgres -d your_db -f backend/seed/schema.sql
   psql -U postgres -d your_db -f backend/seed/data.sql
   ```

2. **Backend Setup**
   ```bash
   cd backend
   cp .env.example .env   # Configure your DB connection string here
   python -m venv venv
   source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 📸 Application Preview

<div align="center">
  <img src="assets/screenshot.png" alt="NL2SQL Agent Dashboard" width="900" style="border-radius: 8px; border: 1px solid #333;">
  <p><em>The main dashboard displaying a natural language query, the LangGraph pipeline trace, and a generated chart.</em></p>
</div>

---

## 🛡️ Security Considerations

This tool is designed to query databases autonomously. To prevent prompt injection and destructive operations:
- A strict AST parser (`sqlparse`) validates all queries before execution.
- Only `SELECT` statements are allowed.
- By default, the application connects to a containerized sandbox database. If connecting to a production environment, ensure the provided database credentials map to a strict **Read-Only** user.

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
