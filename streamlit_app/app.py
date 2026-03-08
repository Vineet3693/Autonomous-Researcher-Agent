"""
Streamlit Web Interface for the Autonomous Research Agent.
"""

import streamlit as st
import os
from datetime import datetime

# Import from src
from src.orchestrator import Orchestrator, get_llm_client


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


def render_sidebar():
    """Render sidebar with configuration and info."""
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv('OPENAI_API_KEY', ''),
            help="Optional: Required for LLM-powered features"
        )
        
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
        
        st.divider()
        
        st.markdown("### About")
        st.markdown("""
        **Autonomous Research Agent**
        
        An AI-powered research assistant that:
        - Decomposes complex queries
        - Searches multiple sources
        - Extracts and verifies information
        - Generates cited reports
        
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
        display_report()


def run_research(query: str, max_sources: int):
    """Run the research workflow."""
    st.session_state.is_processing = True
    st.session_state.start_time = datetime.now()
    st.session_state.errors = []
    
    progress_placeholder = st.empty()
    
    try:
        # Initialize orchestrator
        llm_client = get_llm_client()
        orchestrator = Orchestrator(llm_client)
        
        with progress_placeholder.container():
            st.info("🔄 Starting research workflow...")
            
            # Run with streaming updates
            steps_completed = []
            for step_name, output in orchestrator.run_streaming(query):
                steps_completed.append(step_name)
                
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


def display_report():
    """Display the generated report."""
    st.divider()
    
    if st.session_state.errors:
        st.warning("⚠️ Some errors occurred during research:")
        for error in st.session_state.errors:
            st.code(error)
        st.divider()
    
    # Report header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("📄 Research Report")
    with col2:
        if st.button("📥 Download Markdown"):
            download_report()
    
    # Display report
    if st.session_state.report:
        st.markdown(st.session_state.report)
        
        # Copy to clipboard button (using JavaScript workaround)
        st.download_button(
            label="📋 Copy Report",
            data=st.session_state.report,
            file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )


def download_report():
    """Trigger report download."""
    if st.session_state.report:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        st.download_button(
            label="Downloading...",
            data=st.session_state.report,
            file_name=f"research_report_{timestamp}.md",
            mime="text/markdown",
            key='download_btn'
        )


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
            Powered by LangGraph • Multi-Agent Architecture • Open Source
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
