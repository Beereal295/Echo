# Echo - Personal Journal with AI

Echo is a local-first journaling application with AI-powered insights. It provides three ways to process journal entries: raw transcription, enhanced style, and structured summaries.

## Features

- 🎙️ Voice-to-text journaling with Whisper
- 🤖 AI-powered text enhancement via Ollama
- 💎 Pattern detection after 30 entries
- 💬 "Talk to Your Diary" conversational interface
- 🔒 Complete privacy - all data stays local
- 📊 Semantic search using embeddings

## Tech Stack

- **Backend**: Python with FastAPI
- **Frontend**: React with TypeScript, shadcn/ui
- **Desktop**: Electron
- **Database**: SQLite
- **AI**: Ollama (local LLM) and Whisper (STT)
- **Embeddings**: BGE-small model

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Ollama installed and running locally

### Installation

1. Clone the repository
2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   # On Windows: venv\Scripts\activate
   # On Unix: source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   ```

4. Set up Electron:
   ```bash
   cd electron
   npm install
   ```

### Running the Application

1. Start the backend:
   ```bash
   cd backend
   python run.py
   # Or: uvicorn app.main:app --reload
   ```

2. Start the frontend (development):
   ```bash
   cd frontend
   npm run dev
   ```

3. Or run as desktop app:
   ```bash
   cd electron
   npm start
   ```

## Project Structure

```
echo/
├── backend/          # FastAPI backend
│   ├── app/         # Application code
│   ├── data/        # Local data storage
│   └── venv/        # Python virtual environment
├── frontend/        # React frontend
│   ├── src/         # Source code
│   └── dist/        # Build output
├── electron/        # Electron desktop wrapper
└── Documentation/   # Project documentation
```

## License

MIT