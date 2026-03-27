# InsureBot AI

A complete **offline Insurance AI system** built with FastAPI, Next.js, Ollama (local LLM), ChromaDB (RAG), and SQLite.

---

## Architecture

| Layer | Technology |
|---|---|
| Backend | Python FastAPI |
| Frontend | Next.js (TypeScript + Tailwind, dark UI) |
| LLM | Ollama (local, mistral model) |
| RAG | ChromaDB + sentence-transformers |
| Database | SQLite (SQLAlchemy) |

---

## Project Structure

```
InsureBot-AI/
├── backend/
│   ├── crawler/
│   │   └── crawler.py         # Web crawler for insurance PDFs
│   ├── rag/
│   │   ├── ingest.py          # PDF ingestion & ChromaDB embedding
│   │   ├── retriever.py       # ChromaDB retrieval
│   │   └── qa.py              # RAG Q&A pipeline
│   ├── lib/
│   │   └── ollama.py          # Ollama LLM client
│   ├── db/
│   │   ├── models.py          # SQLAlchemy models (Policy)
│   │   └── crud.py            # CRUD operations
│   ├── agents/
│   │   └── recommender.py     # Insurance recommendation engine
│   └── main.py                # FastAPI application
├── frontend/                  # Next.js app
│   ├── app/
│   │   ├── chat/page.tsx      # Chat UI
│   │   ├── recommend/page.tsx # Recommendation form
│   │   ├── dashboard/page.tsx # Policy management
│   │   ├── layout.tsx
│   │   └── page.tsx           # Home page
│   └── lib/
│       └── api.ts             # API client
├── data/
│   └── policies/              # Downloaded PDFs (created at runtime)
├── chroma_db/                 # ChromaDB vector store (created at runtime)
└── requirements.txt
```

---

## Setup & Running

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.ai) installed

### Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Pull the Ollama model (requires Ollama to be installed)
ollama pull mistral

# Step 1 (optional): Crawl insurance websites for PDFs
python -m backend.crawler.crawler

# Step 2 (optional): Ingest PDFs into ChromaDB
python -m backend.rag.ingest

# Step 3: Start the FastAPI server
uvicorn backend.main:app --reload
# → http://localhost:8000
# → API docs: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/chat` | RAG + Ollama Q&A |
| `POST` | `/recommend` | Insurance recommendations |
| `GET` | `/policies` | List policies |
| `POST` | `/policy` | Create a policy |
| `DELETE` | `/policy/{id}` | Cancel a policy |

### Example: Chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What does a term life insurance policy cover?"}'
```

### Example: Recommend

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"age": 35, "income": 1200000, "dependents": 2, "has_vehicle": true, "has_house": false}'
```

---

## Features

- **Chat**: Ask questions about insurance — answers grounded in real policy PDFs via RAG
- **Recommendations**: Rule-based + AI-explained insurance suggestions tailored to your profile
- **Dashboard**: Create, view, and cancel insurance policies stored in SQLite
- **100% offline**: All AI inference runs locally via Ollama; no data leaves your machine
