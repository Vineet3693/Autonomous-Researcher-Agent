"""
Orchestrator - Stateful workflow management for the research agent system.
Coordinates Plan → Search → Read → Verify → Write workflow.

Note: Uses a simplified sequential workflow without langgraph dependency.
Install langgraph for full graph-based workflow: pip install langgraph
"""

import os
from typing import TypedDict, List, Annotated, Optional

# Load environment variables from .env file (check parent directory too)
try:
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try parent directory (workspace root)
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
except ImportError:
    pass

from src.models import ResearchState
from src.planning_agent import PlanningAgent
from src.search_agent import SearchAgent
from src.reader_agent import ReaderAgent
from src.verifier_agent import VerifierAgent
from src.writer_agent import WriterAgent


class Orchestrator:
    """Main orchestrator coordinating all research agents."""
    
    def __init__(self, llm_client=None):
        """
        Initialize the Orchestrator with all agents.
        
        Args:
            llm_client: OpenAI client for LLM-powered features
        """
        self.llm_client = llm_client
        
        # Initialize all agents
        self.planning_agent = PlanningAgent(llm_client)
        self.search_agent = SearchAgent(llm_client)
        self.reader_agent = ReaderAgent(llm_client)
        self.verifier_agent = VerifierAgent(llm_client)
        self.writer_agent = WriterAgent(llm_client)
    
    def run(self, query: str) -> dict:
        """
        Run the complete research workflow sequentially.
        
        Args:
            query: Research query
            
        Returns:
            Dictionary with final report and metadata
        """
        state = {
            'query': query,
            'plan': [],
            'current_step': 0,
            'search_queries': [],
            'search_results': [],
            'fetched_content': [],
            'verified_claims': [],
            'contradictions': [],
            'gaps': [],
            'report_sections': {},
            'final_report': '',
            'messages': [],
            'errors': [],
            'completed_steps': []
        }
        
        print("=" * 60)
        print("AUTONOMOUS RESEARCH AGENT")
        print("=" * 60)
        
        try:
            # Step 1: Planning
            plan_result = self._plan_step(state)
            state.update(plan_result)
            
            # Step 2: Search
            search_result = self._search_step(state)
            state.update(search_result)
            
            # Step 3: Read
            read_result = self._read_step(state)
            state.update(read_result)
            
            # Step 4: Verify
            verify_result = self._verify_step(state)
            state.update(verify_result)
            
            # Step 5: Write
            write_result = self._write_step(state)
            state.update(write_result)
            
            return state
            
        except Exception as e:
            # Fallback on execution failure
            print(f"Workflow execution failed: {e}")
            fallback_report = self.writer_agent.generate_fallback_report(
                query,
                f"Workflow execution error: {str(e)}"
            )
            return {
                'query': query,
                'final_report': fallback_report,
                'errors': [str(e)]
            }
    
    def run_streaming(self, query: str):
        """
        Run the research workflow with streaming updates.
        
        Args:
            query: Research query
            
        Yields:
            Tuples of (step_name, state_update)
        """
        state = {
            'query': query,
            'plan': [],
            'current_step': 0,
            'search_queries': [],
            'search_results': [],
            'fetched_content': [],
            'verified_claims': [],
            'contradictions': [],
            'gaps': [],
            'report_sections': {},
            'final_report': '',
            'messages': [],
            'errors': [],
            'completed_steps': []
        }
        
        # Step 1: Planning
        plan_result = self._plan_step(state)
        state.update(plan_result)
        yield "plan", plan_result
        
        # Step 2: Search
        search_result = self._search_step(state)
        state.update(search_result)
        yield "search", search_result
        
        # Step 3: Read
        read_result = self._read_step(state)
        state.update(read_result)
        yield "read", read_result
        
        # Step 4: Verify
        verify_result = self._verify_step(state)
        state.update(verify_result)
        yield "verify", verify_result
        
        # Step 5: Write
        write_result = self._write_step(state)
        state.update(write_result)
        yield "write", write_result
    
    def _plan_step(self, state: ResearchState) -> dict:
        """Execute the planning phase."""
        query = state.get('query', '')
        print(f"\n=== Planning Phase ===")
        print(f"Query: {query}")
        
        try:
            plan = self.planning_agent.create_plan(query, max_steps=5)
            
            # Generate search queries from plan
            search_queries = self.search_agent.generate_search_queries(query, num_queries=3)
            
            return {
                'plan': plan,
                'search_queries': search_queries,
                'current_step': 1,
                'completed_steps': []
            }
        except Exception as e:
            return {'errors': [f"Planning failed: {str(e)}"]}
    
    def _search_step(self, state: ResearchState) -> dict:
        """Execute the search phase."""
        queries = state.get('search_queries', [])
        print(f"\n=== Search Phase ===")
        
        try:
            results = self.search_agent.execute_search_plan(queries, results_per_query=5)
            print(f"Found {len(results)} search results")
            
            return {'search_results': results}
        except Exception as e:
            return {'errors': [f"Search failed: {str(e)}"]}
    
    def _read_step(self, state: ResearchState) -> dict:
        """Execute the reading/extraction phase."""
        search_results = state.get('search_results', [])
        query = state.get('query', '')
        print(f"\n=== Reading Phase ===")
        
        try:
            # Get URLs from search results - limit to top 3 for speed
            urls = [r['url'] for r in search_results[:3]]
            
            if not urls:
                return {'fetched_content': [], 'errors': ['No URLs to fetch']}
            
            print(f"Fetching content from {len(urls)} URLs...")
            content = self.reader_agent.process_urls(urls, query)
            print(f"Successfully fetched {len(content)} articles")
            
            return {'fetched_content': content}
        except Exception as e:
            return {'errors': [f"Reading failed: {str(e)}"]}
    
    def _verify_step(self, state: ResearchState) -> dict:
        """Execute the verification phase."""
        fetched_content = state.get('fetched_content', [])
        query = state.get('query', '')
        print(f"\n=== Verification Phase ===")
        
        try:
            verification_result = self.verifier_agent.verify_all(fetched_content, query)
            
            print(f"Verified {verification_result['verified_count']}/{verification_result['total_claims']} claims")
            
            return {
                'verified_claims': verification_result['verified_claims'],
                'contradictions': verification_result['contradictions'],
                'gaps': verification_result['gaps']
            }
        except Exception as e:
            return {'errors': [f"Verification failed: {str(e)}"]}
    
    def _write_step(self, state: ResearchState) -> dict:
        """Execute the writing/report generation phase."""
        query = state.get('query', '')
        verified_claims = state.get('verified_claims', [])
        search_results = state.get('search_results', [])
        fetched_content = state.get('fetched_content', [])
        gaps = state.get('gaps', [])
        errors = state.get('errors', [])
        
        print(f"\n=== Writing Phase ===")
        
        try:
            if errors:
                # Generate fallback report
                report = self.writer_agent.generate_fallback_report(
                    query,
                    "; ".join(errors)
                )
            else:
                # Generate full report
                report = self.writer_agent.generate_report(
                    query=query,
                    verified_claims=verified_claims,
                    search_results=search_results,
                    fetched_content=fetched_content,
                    gaps=gaps
                )
            
            print("Report generated successfully")
            
            return {'final_report': report}
        except Exception as e:
            fallback = self.writer_agent.generate_fallback_report(query, str(e))
            return {'final_report': fallback, 'errors': [f"Writing failed: {str(e)}"]}


def get_llm_client():
    """Create Groq LLM client from environment variable."""
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        try:
            from langchain_groq import ChatGroq
            print("Using Groq API (Llama 3.1 70B)")
            return ChatGroq(model="llama-3.1-70b-versatile", api_key=api_key)
        except ImportError:
            pass
    
    print("Warning: GROQ_API_KEY not set. Running in fallback mode.")
    return None


if __name__ == "__main__":
    # Test the orchestrator
    llm_client = get_llm_client()
    orchestrator = Orchestrator(llm_client)
    
    test_query = "What are the latest developments in renewable energy?"
    result = orchestrator.run(test_query)
    
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(result.get('final_report', 'No report generated')[:2000])
