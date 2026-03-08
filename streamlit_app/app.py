"""
Streamlit Web Interface for the Autonomous Research Agent.
Features:
- Multi-LLM provider support (OpenAI, Gemini, Claude, Groq, Grok)
- API key auto-detection
- Environment variable and manual entry modes
- PDF, DOCX, and Markdown report downloads
"""

import streamlit as st
import os
from datetime import datetime

# Import from src
from src.orchestrator import Orchestrator, get_llm_client
from src.multi_llm import (
    MultiLLMManager,
    LLMProvider,
    detect_provider_from_key,
    validate_api_key,
    get_provider_display_name,
    get_available_providers,
    initialize_multi_llm_session_state,
    render_api_configuration_sidebar
)
from src.report_generator import get_report_download_button, ReportGenerator


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'report' not in st.session_state:
        st.session_state.report = None
    if 'errors' not in st.session_state:
        st.session_state.errors = []
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    
    # Initialize multi-LLM session state
    initialize_multi_llm_session_state()


def render_sidebar():
    """Render sidebar with configuration and info."""
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # Multi-LLM API Configuration
        selected_provider, api_key, config_mode = render_api_configuration_sidebar()
        
        st.divider()
        
        # Configure LLM if API key provided
        if api_key and selected_provider:
            try:
                llm_manager = st.session_state.llm_manager
                detected_provider = llm_manager.add_api_key(api_key, selected_provider)
                st.success(f"✅ {get_provider_display_name(detected_provider)} configured!")
                
                # Set as current provider
                llm_manager.set_current_provider(detected_provider)
                
            except Exception as e:
                st.error(f"Failed to configure API: {str(e)}")
        
        # Display current provider status
        if 'llm_manager' in st.session_state:
            current = st.session_state.llm_manager.get_current_provider()
            if current:
                st.info(f"🎯 Active: {get_provider_display_name(current)}")
        
        st.divider()
        
        st.markdown("### About")
        st.markdown("""
        **Autonomous Research Agent**
        
        An AI-powered research assistant that:
        - Decomposes complex queries
        - Searches multiple sources
        - Extracts and verifies information
        - Generates cited reports
        
        **Supported LLM Providers:**
        - 🟢 OpenAI (GPT-4, GPT-3.5)
        - 🔵 Google Gemini
        - 🟠 Anthropic Claude
        - ⚡ Groq (Llama models)
        - ✖️ xAI Grok
        
        **Workflow:**
        1. 📋 Planning
        2. 🔍 Search
        3. 📖 Reading
        4. ✓ Verification
        5. 📝 Report Generation
        """)
        
        st.divider()
        st.caption(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


def render_main_interface():
    """Render the main research interface."""
    st.title("🔬 Autonomous Research Agent")
    st.markdown("Enter your research query below to generate a comprehensive report.")
    
    # Query input
    query = st.text_area(
        "Research Query",
        placeholder="e.g., What are the impacts of climate change on global agriculture?",
        height=100
    )
    
    # Advanced options
    with st.expander("Advanced Options"):
        max_sources = st.slider("Maximum Sources", 3, 15, 8)
        include_statistics = st.checkbox("Prioritize Statistical Data", value=True)
    
    # Submit button
    col1, col2 = st.columns([3, 1])
    with col1:
        submit_button = st.button("🚀 Start Research", type="primary", use_container_width=True)
    
    if submit_button and query:
        run_research(query, max_sources)
    elif submit_button and not query:
        st.warning("Please enter a research query.")
    
    # Display results
    if st.session_state.report:
        display_report(query)


def run_research(query: str, max_sources: int):
    """Run the research workflow."""
    st.session_state.is_processing = True
    st.session_state.start_time = datetime.now()
    st.session_state.errors = []
    
    progress_placeholder = st.empty()
    
    try:
        # Get LLM client from multi-LLM manager
        llm_client = None
        if 'llm_manager' in st.session_state:
            llm_client = st.session_state.llm_manager.get_current_client()
        
        # Fallback to environment-based client
        if llm_client is None:
            llm_client = get_llm_client()
        
        orchestrator = Orchestrator(llm_client)
        
        with progress_placeholder.container():
            st.info("🔄 Starting research workflow...")
            
            # Run with streaming updates
            steps_completed = []
            output = {}
            for step_name, step_output in orchestrator.run_streaming(query):
                steps_completed.append(step_name)
                output = step_output
                
                status_messages = {
                    'plan': "📋 Creating research plan...",
                    'search': "🔍 Searching web sources...",
                    'read': "📖 Extracting content...",
                    'verify': "✓ Verifying claims...",
                    'write': "📝 Generating report..."
                }
                
                status = status_messages.get(step_name, f"Processing {step_name}...")
                st.info(status)
                
                # Show intermediate results
                if step_name == 'search' and 'search_results' in output:
                    st.success(f"Found {len(output['search_results'])} search results")
                elif step_name == 'read' and 'fetched_content' in output:
                    st.success(f"Extracted {len(output['fetched_content'])} articles")
        
        # Store final report
        st.session_state.report = output.get('final_report', '')
        if 'errors' in output and output['errors']:
            st.session_state.errors = output['errors']
        
        st.session_state.is_processing = False
        
    except Exception as e:
        st.session_state.is_processing = False
        st.session_state.errors = [str(e)]
        st.error(f"Research failed: {str(e)}")


def display_report(query: str):
    """Display the generated report with download options."""
    st.divider()
    
    if st.session_state.errors:
        st.warning("⚠️ Some errors occurred during research:")
        for error in st.session_state.errors:
            st.code(error)
        st.divider()
    
    # Report header
    st.subheader("📄 Research Report")
    
    # Download buttons for multiple formats
    if st.session_state.report:
        # Create filename base from query
        filename_base = query[:30].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename_base = "".join(c for c in filename_base if c.isalnum() or c in '_-')
        
        # Multi-format download buttons
        get_report_download_button(
            st,
            content=st.session_state.report,
            filename_base=filename_base,
            title=query[:100]
        )
        
        st.divider()
        
        # Display report content
        st.markdown(st.session_state.report)


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title="Autonomous Research Agent",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize
    initialize_session_state()
    
    # Render UI
    render_sidebar()
    render_main_interface()
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 0.9rem;'>
            Powered by LangGraph • Multi-Agent Architecture • Multi-LLM Support • Open Source
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
