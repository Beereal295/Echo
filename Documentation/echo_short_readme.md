# 🎙️ Echo - Your Private AI Journal

## The Problem: Your Thoughts Deserve Better

Ever wanted to remember that brilliant idea from last Tuesday's meeting? Or find that conversation where your friend mentioned the perfect restaurant? Most journaling apps are glorified text boxes. Note-taking apps scatter your thoughts. Voice memos pile up unused.

**Got voice recordings scattered across your phone?** Just drop them into Echo's voice upload page - it transcribes and processes everything so your thoughts become searchable and connected.

**Echo is different.** It's not just storage - it's your personal AI that actually remembers and connects your thoughts.

## What is Echo?

Echo turns your scattered thoughts into an intelligent, searchable memory system:

- **🔒 100% Local**: Your data stays on your device. No cloud. No subscriptions. No spying.
- **🧠 Smart Memory**: AI extracts facts, preferences, and patterns from your entries
- **🎯 Powerful Search**: Find entries by meaning, keywords, or context
- **💬 Natural Chat**: Ask Echo about your thoughts like talking to a friend
- **🎤 Voice-First**: Speak naturally, Echo transcribes and processes everything

## Real Use Cases (Not Just "Dear Diary")

**Work User Profile:**
- Track daily meetings, decisions, and deal progress
- Remember client preferences and conversation details  
- Search "what did I discuss with Sarah about the Q3 strategy?"
- Analyze patterns: "Show me all blockers from last month"

**Personal User Profile:**
- Journal relationships, goals, and life decisions
- Remember friend recommendations and important conversations
- Find patterns in your mood and energy levels
- Vent freely knowing it's completely private

**Project User Profile:**
- Document research, ideas, and progress
- Track what worked and what didn't
- Connect related concepts across time
- Build a knowledge base that grows with you

## Quick Start

**You need:** Python 3.11+, Node.js 20+, and [Ollama](https://ollama.ai)

```bash
# Clone and setup
git clone https://github.com/29sayantanc/echo.git
cd echo

# 2. Start backend (Terminal 1)
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py

# 3. Start frontend (Terminal 2) 
cd frontend
npm install
npm run dev

# 4. Install AI models
ollama pull qwen3:8b
ollama pull mistral:7b
```

Open http://localhost:3000 and start capturing your thoughts!

## Why Local Matters

- **Privacy**: Your thoughts, your device, your control
- **Speed**: No internet lag for search or AI processing
- **Reliability**: Works offline, always available
- **Cost**: No monthly fees or usage limits
- **Ownership**: Export your data anytime, no lock-in

## The Magic Under the Hood

Echo isn't just a pretty interface - it's a complete AI pipeline:

- **Speech-to-Text**: Whisper for accurate transcription
- **Smart Processing**: Local LLMs enhance and structure your thoughts  
- **Hybrid Search**: Semantic similarity + keyword matching
- **Memory Extraction**: AI identifies and categorizes important information
- **Pattern Analysis**: Discover trends in your thinking and behavior
- **Voice Responses**: Natural conversations with text-to-speech

## My Story

*I Googled "what is an LLM" 2 months ago because I wanted to understand how AI actually work. I came into this with no formal coding experience—just curiosity, a lot of reading, and the help of AI tools. Echo started as weekend curiosity, turned into something I use daily. Always open to suggestions and feedback!*

## Built With

- **Backend**: Python + FastAPI + SQLite + Sentence Transformers
- **Frontend**: React + TypeScript + Tailwind CSS  
- **AI**: Ollama + Whisper + BGE embeddings + Piper TTS
- **Architecture**: Async processing, memory systems, tool-calling agents

## Development Credits

**AI Coding Assistants:**
- [Claude Code](https://claude.ai/code) - Primary development and architecture implementation
- [Cursor](https://cursor.sh/) - Code editing and debugging assistance  
- [Gemini CLI](https://github.com/google/generative-ai-cli) - Additional coding support

**Documentation & Design:**
- [Claude Desktop](https://claude.ai/) - Technical documentation and user guides
- [GPT + Monday](https://openai.com/) - Additional documentation support

**Open Source Projects:**
- [Ollama](https://ollama.ai/) - Local LLM inference engine
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech-to-text transcription
- [Piper TTS](https://github.com/rhasspy/piper) - Neural text-to-speech synthesis
- [BGE Embeddings](https://huggingface.co/BAAI/bge-small-en-v1.5) - Semantic embeddings model
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLite](https://sqlite.org/) - Embedded database engine

**Development Approach:**
This project demonstrates AI-assisted development - I provided the vision, architecture decisions, and user experience design, while AI coding assistants handled the implementation. Every line of code was written by AI according to my specifications and requirements.

## Contributing

Echo is for people who believe your thoughts are too valuable for cloud storage and too important for basic text boxes. Whether you're:

- Adding new features
- Fixing bugs  
- Improving documentation
- Just trying it out and sharing feedback

**You're welcome here.** Star ⭐ if this resonates with you!

---

*Your thoughts, enhanced by AI, secured by design.*