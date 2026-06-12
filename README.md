# Developer Profile Analyzer

AI-powered developer profile analysis tool. Upload your resume and share your GitHub profile to receive deep insights: strengths, weaknesses, skill gaps, and a personalized 3-month learning roadmap.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js_14-000000?style=flat&logo=next.js&logoColor=white)
![Gemini AI](https://img.shields.io/badge/Gemini_AI-4285F4?style=flat&logo=google&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F61?style=flat)

## Architecture

```
┌──────────────┐     ┌──────────────────────────────────────┐
│   Next.js    │────▶│           FastAPI Backend             │
│   Frontend   │◀────│                                      │
│  (port 3000) │     │  ┌─────────┐  ┌──────────────────┐  │
└──────────────┘     │  │ PyMuPDF │  │ GitHub REST API   │  │
                     │  │  (PDF)  │  │   (httpx)         │  │
                     │  └────┬────┘  └────────┬──────────┘  │
                     │       │                │             │
                     │       ▼                ▼             │
                     │  ┌─────────────────────────────┐    │
                     │  │  sentence-transformers       │    │
                     │  │  (all-MiniLM-L6-v2)         │    │
                     │  └──────────────┬──────────────┘    │
                     │                 ▼                    │
                     │  ┌─────────────────────────────┐    │
                     │  │  ChromaDB (Vector Store)     │    │
                     │  └──────────────┬──────────────┘    │
                     │                 ▼                    │
                     │  ┌─────────────────────────────┐    │
                     │  │  Google Gemini (RAG LLM)     │    │
                     │  └─────────────────────────────┘    │
                     └──────────────────────────────────────┘
```

## Features

- **Resume Analysis** — Upload a PDF resume; text is extracted, chunked, embedded, and stored for semantic retrieval
- **GitHub Scraping** — Provide a GitHub URL; repos, READMEs, and language stats are fetched and embedded
- **RAG-Powered Insights** — Claude analyzes your profile using retrieved context to identify:
  - 💪 Technical strengths
  - ⚠️ Skill gaps and weaknesses
  - 🚀 Top projects by technical depth
  - 🗺️ Personalized 3-month learning roadmap
- **Follow-up Chat** — Ask any question about your profile with streaming AI responses

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm**
- **Google Gemini API Key** — Get one at [aistudio.google.com](https://aistudio.google.com/apikey)
- **GitHub Personal Access Token** (optional, but recommended for higher rate limits) — [Create one here](https://github.com/settings/tokens)

## Quick Start

### 1. Clone and configure

```bash
cd profile-analyzer

# Set up backend environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys:
#   GEMINI_API_KEY=your-gemini-api-key-here
#   GITHUB_TOKEN=ghp_your-token-here
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive Swagger UI.

### 3. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app will be available at `http://localhost:3000`.

## Project Structure

```
profile-analyzer/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── .env                     # Environment variables (your API keys)
│   ├── .env.example             # Environment template
│   ├── requirements.txt         # Python dependencies
│   ├── api/
│   │   └── routes/
│   │       ├── upload.py        # POST /upload/resume
│   │       ├── github.py        # POST /upload/github
│   │       ├── analyze.py       # POST /analyze
│   │       └── chat.py          # POST /chat (SSE streaming)
│   ├── core/
│   │   ├── config.py            # Settings from .env
│   │   ├── pdf_extractor.py     # PyMuPDF text extraction
│   │   ├── github_scraper.py    # GitHub API scraper
│   │   ├── embedder.py          # sentence-transformers embeddings
│   │   ├── vector_store.py      # ChromaDB operations
│   │   └── rag_pipeline.py      # RAG: retrieve → context → Claude
│   └── models/
│       └── schemas.py           # Pydantic request/response models
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Landing page (upload form)
│   │   ├── analyze/page.tsx     # Results dashboard
│   │   └── chat/page.tsx        # Follow-up chat
│   ├── components/
│   │   ├── UploadForm.tsx       # PDF dropzone + GitHub input
│   │   ├── InsightCard.tsx      # Strength/weakness cards
│   │   ├── RoadmapTimeline.tsx  # Visual timeline
│   │   └── ChatBox.tsx          # Streaming chat UI
│   └── lib/
│       └── api.ts               # Backend API client
│
└── README.md
```

## API Endpoints

| Method | Endpoint          | Description                              |
|--------|-------------------|------------------------------------------|
| GET    | `/`               | Health check                             |
| POST   | `/upload/resume`  | Upload PDF resume (multipart)            |
| POST   | `/upload/github`  | Submit GitHub URL for scraping           |
| POST   | `/analyze`        | Run full profile analysis                |
| POST   | `/chat`           | Follow-up chat (SSE streaming response)  |

## RAG Pipeline

The following files power the RAG pipeline and must exist:

- **`core/embedder.py`** — Converts text chunks to 384-dim vectors using `all-MiniLM-L6-v2`
- **`core/vector_store.py`** — ChromaDB storage with cosine similarity search
- **`core/rag_pipeline.py`** — Orchestrates retrieval + Gemini LLM call
- Uploaded resume PDF is stored temporarily at `backend/tmp/resume.pdf`
- GitHub data is stored as text documents in ChromaDB (not as files on disk)

## Environment Variables

| Variable           | Required | Description                        |
|--------------------|----------|------------------------------------|
| `GEMINI_API_KEY`   | Yes      | Google Gemini API key              |
| `GITHUB_TOKEN`     | No       | GitHub PAT (higher rate limits)    |
| `CHROMA_PERSIST_DIR`| No     | ChromaDB storage path (default: `./chroma_db`) |
| `EMBED_MODEL_NAME` | No       | Embedding model (default: `all-MiniLM-L6-v2`)  |

## License

MIT
