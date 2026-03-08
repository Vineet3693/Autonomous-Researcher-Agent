# Deployment Guide for Streamlit Cloud

## 🚀 Deploying to Streamlit Cloud

### Step 1: Prepare Your Repository

Ensure your GitHub repository contains:
- ✅ `requirements.txt` with all dependencies
- ✅ `streamlit_app/app.py` as the main entry point
- ✅ `.streamlit/config.toml` for configuration
- ✅ All source code in `src/` directory

### Step 2: Connect to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Connect your GitHub repository
4. Configure:
   - **Main file path**: `streamlit_app/app.py`
   - **Python version**: `3.12` (or latest available)
   - **Viewers can download source code**: Optional

### Step 3: Set Environment Variables (Optional)

If using environment-based API keys:

1. In Streamlit Cloud dashboard, click on your app
2. Go to **"Settings"** → **"Secrets"**
3. Add your API keys:

```toml
OPENAI_API_KEY = "sk-..."
GROQ_API_KEY = "gsk_..."
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_API_KEY = "AIza..."
XAI_API_KEY = "xai-..."
```

### Step 4: Deploy

Click **"Deploy!"** and wait for the build to complete (~2-5 minutes).

## 🔧 Troubleshooting Import Errors

### Problem: `ModuleNotFoundError: No module named 'src'`

**Solution:** The app already includes path configuration in `streamlit_app/app.py`:

```python
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))
```

This ensures imports like `from src.orchestrator import Orchestrator` work correctly.

### Problem: Missing Dependencies

**Solution:** Ensure all required packages are in `requirements.txt`:

```txt
# Core
langgraph>=0.2.0
langchain>=0.3.0

# Multi-LLM
openai>=1.50.0
google-generativeai>=0.3.0
anthropic>=0.18.0
langchain-groq>=0.1.0

# Search & Scraping
duckduckgo-search>=6.0.0
newspaper3k>=0.2.8
beautifulsoup4>=4.12.0
lxml_html_clean>=0.1.0

# Report Generation
reportlab>=4.0.0
markdown>=3.5.0
python-docx>=1.0.0

# Web Interface
streamlit>=1.30.0

# Utilities
python-dotenv>=1.0.0
```

### Problem: `ImportError: lxml.html.clean module is now a separate project`

**Solution:** Add `lxml_html_clean` to requirements.txt (already included above).

## 🎯 Using the App on Streamlit Cloud

### Option 1: Manual API Key Entry (Recommended for Cloud)

1. Open the deployed app
2. In the sidebar, select **"🔑 Manual Entry (Cloud)"** mode
3. Choose your LLM provider from dropdown
4. Paste your API key
5. Start researching!

### Option 2: Environment Variables

If you set secrets in Streamlit Cloud settings, select **"🔐 Environment Variables (Local/Cloud)"** mode.

## 📊 Supported Features on Cloud

✅ Multi-LLM provider selection  
✅ API key auto-detection  
✅ PDF report downloads  
✅ DOCX (Word) report downloads  
✅ Markdown report downloads  
✅ Real-time research progress  
✅ Source verification  
✅ Citation generation  

## 🔒 Security Best Practices

- Never commit `.env` files with API keys to GitHub
- Use Streamlit Secrets for environment variables
- Encourage users to use manual entry mode for personal API keys
- API keys are stored only in session state (not persisted)

## 📈 Monitoring & Logs

View deployment logs in Streamlit Cloud:
1. Go to your app dashboard
2. Click **"Manage app"**
3. View **"Logs"** tab for real-time error tracking

## 🆘 Support

For issues:
1. Check deployment logs in Streamlit Cloud
2. Verify all dependencies in `requirements.txt`
3. Ensure `streamlit_app/app.py` has the path fix
4. Test locally first: `streamlit run streamlit_app/app.py`
