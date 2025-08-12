# Echo Journal - Installation Guide

Complete step-by-step installation instructions for Windows, macOS, and Linux.

---

## 📋 Prerequisites

Before installing Echo, you need to install these required components:

### Required Software

| Component | Minimum Version | Recommended | Purpose |
|-----------|----------------|-------------|---------|
| **Python** | 3.9+ | 3.11+ | Backend API server |
| **Node.js** | 18+ | 20+ | Frontend development server |
| **npm** | 9+ | 10+ | Package manager (comes with Node.js) |
| **Git** | 2.0+ | Latest | Version control and cloning repository |
| **Ollama** | Latest | Latest | Local AI language models |

### Hardware Requirements

- **RAM**: 8GB minimum, 16GB recommended (for AI models)
- **Storage**: 5GB free space (more for additional AI models)
- **CPU**: Any modern processor (AI processing benefits from faster CPUs)

---

## 🔧 Step 1: Install Prerequisites

### Windows

#### 1.1 Install Python
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.11 or newer
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

#### 1.2 Install Node.js & npm
1. Go to [nodejs.org](https://nodejs.org/)
2. Download the LTS version (20.x or newer)
3. Run the installer with default settings
4. Verify installation:
   ```cmd
   node --version
   npm --version
   ```

#### 1.3 Install Git
1. Go to [git-scm.com/download/win](https://git-scm.com/download/win)
2. Download and install with default settings
3. Verify installation:
   ```cmd
   git --version
   ```

#### 1.4 Install Ollama
1. Go to [ollama.ai](https://ollama.ai/)
2. Download Ollama for Windows
3. Run the installer
4. Verify installation:
   ```cmd
   ollama --version
   ```

### macOS

#### 1.1 Install Homebrew (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 1.2 Install Python
```bash
brew install python@3.11
python3.11 --version
pip3 --version
```

#### 1.3 Install Node.js & npm
```bash
brew install node
node --version
npm --version
```

#### 1.4 Install Git
```bash
brew install git
git --version
```

#### 1.5 Install Ollama
```bash
brew install ollama
ollama --version
```

### Linux (Ubuntu/Debian)

#### 1.1 Update package manager
```bash
sudo apt update && sudo apt upgrade -y
```

#### 1.2 Install Python
```bash
sudo apt install python3.11 python3.11-venv python3-pip -y
python3.11 --version
pip3 --version
```

#### 1.3 Install Node.js & npm
```bash
# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version
npm --version
```

#### 1.4 Install Git
```bash
sudo apt install git -y
git --version
```

#### 1.5 Install Ollama
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama --version
```

### Linux (CentOS/RHEL/Fedora)

#### 1.1 Update package manager
```bash
# For CentOS/RHEL
sudo yum update -y
# For Fedora
sudo dnf update -y
```

#### 1.2 Install Python
```bash
# For CentOS/RHEL
sudo yum install python3.11 python3-pip -y
# For Fedora
sudo dnf install python3.11 python3-pip -y

python3.11 --version
pip3 --version
```

#### 1.3 Install Node.js & npm
```bash
# For CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install nodejs -y
# For Fedora
sudo dnf install nodejs npm -y

node --version
npm --version
```

#### 1.4 Install Git
```bash
# For CentOS/RHEL
sudo yum install git -y
# For Fedora
sudo dnf install git -y

git --version
```

#### 1.5 Install Ollama
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama --version
```

---

## 📦 Step 2: Download Echo Journal

### 2.1 Clone the Repository

Choose a location for the project (e.g., Desktop, Documents, or a dedicated `Projects` folder):

```bash
# Navigate to your desired directory
cd ~/Desktop
# or
cd ~/Documents
# or
mkdir ~/Projects && cd ~/Projects

# Clone the repository
git clone https://github.com/YOUR_USERNAME/echo.git
cd echo
```

> **Note**: Replace `YOUR_USERNAME` with the actual GitHub username/organization where Echo is hosted.

### 2.2 Verify Project Structure

After cloning, you should see this structure:
```
echo/
├── backend/           # Python FastAPI server
├── frontend/          # React TypeScript app
├── Documentation/     # Project documentation
└── launch-echo.bat   # Windows launcher script
```

---

## 🚀 Step 3: Setup Backend (Python API)

### 3.1 Navigate to Backend Directory
```bash
cd backend
```

### 3.2 Create Python Virtual Environment

#### Windows:
```cmd
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux:
```bash
python3.11 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

### 3.3 Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: This will install all required packages including:
- FastAPI (web framework)
- Whisper (speech-to-text)
- Sentence Transformers (embeddings)
- LangChain (AI integration)
- PyTorch (machine learning)
- And many more...

### 3.4 Verify Backend Installation
```bash
python run.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Press Ctrl+C to stop the server** and continue with frontend setup.

---

## 🎨 Step 4: Setup Frontend (React App)

### 4.1 Open New Terminal

Keep the backend terminal open and open a **new terminal window/tab**.

### 4.2 Navigate to Frontend Directory
```bash
cd echo/frontend
```

### 4.3 Install Node.js Dependencies
```bash
npm install
```

This will install all required packages including:
- React & TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Radix UI (components)
- Framer Motion (animations)

### 4.4 Verify Frontend Installation
```bash
npm run dev
```

You should see:
```
  VITE v5.0.8  ready in 1234 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

**Press Ctrl+C to stop the server**.

---

## 🤖 Step 5: Setup Ollama AI Models

### 5.1 Start Ollama Service

#### Windows:
Ollama should start automatically. If not, search for "Ollama" in Start menu and run it.

#### macOS/Linux:
```bash
ollama serve
```

**Note**: Ollama runs on `localhost:11434` by default. If you're running Ollama on a different host or port, you can configure this later in the Settings page.

### 5.2 Install AI Models

You can install any Ollama-compatible models. Here are the **developer recommendations**:

```bash
# Developer recommended models:
ollama pull mistral:7b     # For text processing
ollama pull qwen3:8b       # For chat service

# Verify models are installed
ollama list
```

**Developer Recommended Settings:**
- **Mistral**: Temperature 0.2, Context Window 8192
- **Qwen**: Temperature 0.5, Context Window 32768

(You can configure any models and settings in the Settings page)

---

## 🔊 Step 6: Download TTS Models (Optional)

### 6.1 Download Piper TTS Models

Echo uses Piper TTS for text-to-speech. Download voice models from Hugging Face:

**Note**: If you don't want TTS functionality, you can skip this step and disable TTS later in Settings → Voice section using the toggle.

1. Go to [Piper Voices on Hugging Face](https://huggingface.co/rhasspy/piper-voices/tree/main/en)
2. Navigate to your preferred voice (e.g., `en_US-lessac-high`)
3. Download both files:
   - `[voice-name].onnx` (the model file)
   - `[voice-name].onnx.json` (the config file)

### 6.2 Install TTS Models

1. Create the TTS directory in your backend folder:
   ```bash
   mkdir backend/TTS
   ```

2. Place the downloaded `.onnx` and `.onnx.json` files in `backend/TTS/`

Example structure:
```
backend/TTS/
├── en_US-lessac-high.onnx
├── en_US-lessac-high.onnx.json
├── en_US-bryce-medium.onnx
└── en_US-bryce-medium.onnx.json
```

You can configure which voice to use later in the Settings page.

---

## 🎯 Step 7: Launch Echo Journal

### 7.1 Using Individual Commands (All Platforms)

**Terminal 1 - Backend:**
```bash
cd echo/backend
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

python run.py
```

**Terminal 2 - Frontend:**
```bash
cd echo/frontend
npm run dev
```

### 7.2 Using Launcher Script (Windows Only)

Double-click `launch-echo.bat` in the project root directory. This will automatically start both backend and frontend in separate windows.

### 7.3 Access the Application

Once both servers are running:

1. **Frontend (Main App)**: http://localhost:3000
2. **Backend API**: http://localhost:8000

---

## ✅ Step 8: Verify Installation

1. Open http://localhost:3000 in your browser
2. You should see the Echo Journal landing page
3. Create a new user account or sign in
4. Go to Settings → Ollama Configuration to verify connection
5. Test creating a new text entry

---

## 🔧 Installation Troubleshooting

### Common Installation Issues

#### "Python not found" or "pip not found"
- **Windows**: Reinstall Python and check "Add Python to PATH"
- **macOS/Linux**: Use `python3.11` and `pip3` instead of `python` and `pip`

#### "Node not found" or "npm not found"
- Restart your terminal after installing Node.js
- Verify installation with `node --version` and `npm --version`

#### Backend fails to start
```bash
# Check if virtual environment is activated
# You should see (venv) in your prompt

# If not activated:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### Frontend fails to start
```bash
# Clear npm cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

#### Ollama connection fails
1. Ensure Ollama is running:
   ```bash
   ollama serve
   ```
2. Test Ollama manually:
   ```bash
   ollama run mistral:7b "Hello world"
   ```
3. Check if models are installed:
   ```bash
   ollama list
   ```

#### Port conflicts
If ports 3000 or 8000 are already in use:

**Frontend (port 3000):**
```bash
npm run dev -- --port 3001
```

**Backend (port 8000):**
Edit `backend/run.py` and change the port in the uvicorn command.

---

**Installation complete!** Your Echo Journal should now be running at http://localhost:3000