# Autonomous Research Agent

A LangGraph-based multi-agent system for autonomous research tasks. Handles query decomposition, search, content extraction, verification, and report generation with proper citations.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator                                │
│                  (LangGraph Workflow)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Planning    │───▶│    Search     │───▶│    Reader     │
│    Agent      │    │    Agent      │    │    Agent      │
└───────────────┘    └───────────────┘    └───────────────┘
                                              │
        ┌─────────────────────────────────────┘
        ▼
┌───────────────┐    ┌───────────────┐
│   Verifier    │───▶│    Writer     │
│    Agent      │    │    Agent      │
└───────────────┘    └───────────────┘
                              │
                              ▼
                    ┌───────────────┐
                    │  Markdown     │
                    │   Report      │
                    └───────────────┘
```

## 📋 Features

- **Query Decomposition**: ReAct pattern for breaking down complex research questions
- **Multi-Source Search**: DuckDuckGo integration with domain filtering
- **Content Extraction**: newspaper3k + BeautifulSoup for clean text extraction
- **Source Credibility**: Domain-based credibility scoring
- **Claim Verification**: Cross-referencing with confidence scores (0.0-1.0)
- **Contradiction Detection**: Identifies conflicting information
- **Report Generation**: Structured markdown reports with auto-citations
- **Fallback Mechanisms**: Graceful degradation when services fail

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
```

### Run CLI

```bash
python src/orchestrator.py
```

### Run Web Interface

```bash
streamlit run streamlit_app/app.py
```

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
│   └── writer_agent.py     # Report generation
├── streamlit_app/
│   └── app.py              # Web interface
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
| `OPENAI_API_KEY` | OpenAI API key for LLM features | No* |

*Optional: System runs in fallback mode without LLM

## 🛠️ Extensibility

Add new agents by:
1. Create agent class in `src/`
2. Add node to orchestrator graph
3. Update `ResearchState` if needed

## 📝 License

MIT License
