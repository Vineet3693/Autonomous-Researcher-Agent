# Autonomous Research Agent

A LangGraph-based multi-agent system for autonomous research tasks. Handles query decomposition, search, content extraction, verification, and report generation with proper citations.

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      Orchestrator                          │
│                  (LangGraph Workflow)                      │
└────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Planning       │───▶│   Search         │───▶│   Reader         │
│   Agent          │    │   Agent          │    │   Agent          │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                              │
        ┌─────────────────────────────────────┘
        ▼
┌──────────────────┐    ┌──────────────────┐
│   Verifier       │───▶│   Writer         │
│   Agent          │    │   Agent          │
└──────────────────┘    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  PDF/DOCX/MD     │
                    │   Reports        │
                    └──────────────────┘
```

## 📋 Features

### Core Research Capabilities
- **Query Decomposition**: ReAct pattern for breaking down complex research questions
- **Multi-Source Search**: DuckDuckGo integration with domain filtering
- **Content Extraction**: newspaper3k + BeautifulSoup for clean text extraction
- **Source Credibility**: Domain-based credibility scoring
- **Claim Verification**: Cross-referencing with confidence scores (0.0-1.0)
- **Contradiction Detection**: Identifies conflicting information
- **Report Generation**: Structured reports with auto-citations

### Multi-LLM Support 🔥
- **OpenAI** (GPT-4, GPT-3.5)
- **Google Gemini** (Gemini Pro)
- **Anthropic Claude** (Claude 3 Haiku/Sonnet)
- **Groq** (Llama 3.1 70B)
- **xAI Grok** (Grok Beta)
- **Auto-Detection**: Automatically detects API key provider
- **Flexible Configuration**: Environment variables or manual entry

### Report Export Formats 📄
- **PDF**: Professional formatting with custom styles
- **DOCX**: Microsoft Word compatible
- **Markdown**: Native format with syntax highlighting

### Web Interface Features
- Dual configuration mode (Local/Cloud)
- Real-time workflow progress tracking
- Multi-format download buttons
- Provider status indicators
- Responsive design

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file:

```bash
# Single provider
OPENAI_API_KEY=sk-...

# Multiple providers (optional)
GEMINI_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
XAI_API_KEY=xai-...
```

### Run CLI

```bash
python src/orchestrator.py
```

### Run Web Interface

```bash
streamlit run streamlit_app/app.py
```

Access at: `http://localhost:8501`

## 📁 Project Structure

```
/workspace/
├── src/
│   ├── models.py           # Typed state dictionaries
│   ├── orchestrator.py     # LangGraph workflow coordinator
│   ├── planning_agent.py   # Query decomposition (ReAct)
│   ├── search_agent.py     # DuckDuckGo search
│   ├── reader_agent.py     # Content extraction
│   ├── verifier_agent.py   # Claim verification
│   ├── writer_agent.py     # Report generation
│   ├── multi_llm.py        # Multi-LLM provider support ✨ NEW
│   └── report_generator.py # PDF/DOCX export ✨ NEW
├── streamlit_app/
│   └── app.py              # Enhanced web interface
├── tests/
│   └── test_agents.py      # Unit tests
├── requirements.txt
└── README.md
```

## 🔧 Components

### 1. Orchestrator (`src/orchestrator.py`)
- LangGraph-based stateful workflow
- Coordinates Plan → Search → Read → Verify → Write
- Typed state with reducers for message accumulation

### 2. Planning Agent (`src/planning_agent.py`)
- ReAct pattern implementation
- Dynamic plan adjustment based on findings
- Dependency-aware step execution

### 3. Search Agent (`src/search_agent.py`)
- LLM-optimized query generation
- DuckDuckGo API (no key required)
- Domain filtering and deduplication

### 4. Reader Agent (`src/reader_agent.py`)
- HTML fetching with newspaper3k
- BeautifulSoup fallback
- Source credibility assessment

### 5. Verifier Agent (`src/verifier_agent.py`)
- Multi-source cross-referencing
- Confidence scoring (0.0-1.0)
- Contradiction detection

### 6. Writer Agent (`src/writer_agent.py`)
- Verified claim synthesis
- Auto-generated citations
- Executive Summary, Key Findings, Analysis, Sources sections

### 7. Multi-LLM Manager (`src/multi_llm.py`) ✨ NEW
- Support for 5+ LLM providers
- API key auto-detection from format
- Unified invocation interface
- Session-based provider management

### 8. Report Generator (`src/report_generator.py`) ✨ NEW
- PDF export with professional styling
- DOCX export for Word compatibility
- Markdown native format
- Batch format generation

## 🧪 Testing

```bash
python -m pytest tests/
```

## 📊 Example Output

```markdown
# Research Report: Climate Change Impacts On Agriculture

*Generated on: 2025-01-15 10:30:00*

---

## Executive Summary

This research report examines: climate change impacts on agriculture

- Global temperatures have risen 1.1°C since pre-industrial times
- Crop yields declining in tropical regions by 5-15%
- Adaptation strategies showing promise in temperate zones

---

## Key Findings

### Finding 1: ✓

**Claim:** Global temperatures have risen by 1.1°C...
**Confidence Score:** 0.85
**Supporting Evidence:**
- Studies show consistent warming trend
- Multiple independent datasets confirm

---

## Sources

[1] **Climate Change Overview**
   - Source: nasa.gov
   - URL: https://www.nasa.gov/climate
   - Credibility Score: 0.80
```

## 🔐 Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | No* |
| `GEMINI_API_KEY` | Google Gemini API key | No |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | No |
| `GROQ_API_KEY` | Groq API key | No |
| `XAI_API_KEY` | xAI Grok API key | No |

*Optional: System runs in fallback mode without LLM

## 🛠️ Extensibility

Add new agents by:
1. Create agent class in `src/`
2. Add node to orchestrator graph
3. Update `ResearchState` if needed

Add new LLM providers by:
1. Add provider to `LLMProvider` enum in `multi_llm.py`
2. Add API key pattern to `API_KEY_PATTERNS`
3. Implement client creation in `get_llm_client()`
4. Add invocation logic in `invoke_llm()`

## 📝 License

MIT License
