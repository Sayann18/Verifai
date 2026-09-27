# 🛡️ VerifAI

> **Verify. Trust. Share. Truth.**

VerifAI is an AI-powered fact-checking platform that helps users evaluate claims, news headlines, and viral statements using trusted fact-checking sources and evidence-based analysis.

## ✨ Features

- 🔍 Search and verify claims or news headlines
- 🤖 AI-assisted claim analysis with Groq
- 📰 Aggregates fact-check articles and related news
- ✅ Generates verdicts such as **True**, **False**, **Misleading**, or **Unverifiable**
- 📚 Displays supporting sources and article links
- 🎨 Modern Streamlit interface with light and dark themes
- 🔐 Secure configuration through environment variables

## 🧰 Tech Stack

| Technology | Purpose |
| --- | --- |
| 🐍 Python | Core application language |
| ⚡ Streamlit | Interactive web interface |
| 🧠 Groq | AI-powered claim analysis |
| 🌐 Tavily | Web search and research |
| 🚀 FastAPI | Backend API support |
| 🔧 Uvicorn | ASGI server |
| 📦 python-dotenv | Environment variable management |

## 📁 Project Structure

```text
Verifai/
├── 📂 app_core/
│   ├── __init__.py
│   ├── llm_agent.py       # AI verification agent
│   ├── search_engine.py   # Search and fact-check pipeline
│   └── utils.py           # Shared models and helper functions
├── 📂 assets/             # Stylesheets and visual assets
├── 📂 backend/            # Backend services
├── 📂 frontend/           # Frontend modules
├── 📂 pages/              # Streamlit pages
├── 📄 main.py             # Application entry point
├── 📄 requirements.txt    # Python dependencies
└── 📄 README.md           # Project documentation
```

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Sayann18/Verifai.git
cd Verifai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 🔑 Environment Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

> ⚠️ Never commit your `.env` file or expose your API keys publicly.

## ▶️ Run the Application

Start VerifAI with Streamlit:

```bash
streamlit run main.py
```

Then open the local URL displayed in your terminal, usually:

```text
http://localhost:8501
```

## 🔄 How It Works

```text
👤 User enters a claim
          ↓
🧹 Input is validated and sanitized
          ↓
🔍 Fact-check and news sources are searched
          ↓
🤖 Evidence is analyzed by the AI agent
          ↓
📊 Verdict and supporting articles are displayed
```

## ⚖️ Verdict Types

| Verdict | Meaning |
| --- | --- |
| 🟢 **TRUE** | Available evidence supports the claim |
| 🔴 **FALSE** | Available evidence contradicts the claim |
| 🟡 **MISLEADING** | The claim lacks context or contains partially incorrect information |
| ⚪ **UNVERIFIABLE** | There is not enough reliable evidence to confirm or reject the claim |

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push your branch: `git push origin feature/my-feature`
5. Open a pull request

## 🔒 Disclaimer

VerifAI is an assistive research tool. Its results depend on the availability and quality of external sources and should be reviewed before being treated as definitive conclusions.

## 📄 License

No license has been specified for this project yet.

---

<div align="center">
  Made with ❤️ for a more informed internet.
</div>
