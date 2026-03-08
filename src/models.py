"""
Autonomous Research Agent Architecture

A LangGraph-based multi-agent system for autonomous research tasks.
Handles query decomposition, search, content extraction, verification, and report generation.
"""

from typing import TypedDict, List, Annotated, Optional


# Simple message accumulator without langgraph dependency
def add_messages(left: List[dict], right: List[dict]) -> List[dict]:
    """Accumulate messages from multiple sources."""
    return left + right


class ResearchState(TypedDict):
    """State dictionary for the research workflow."""
    
    # Original user query
    query: str
    
    # Planning phase
    plan: List[dict]  # List of research steps with agent assignments
    current_step: int
    
    # Search phase
    search_queries: List[str]
    search_results: List[dict]  # {url, title, snippet, source}
    
    # Reading phase
    fetched_content: List[dict]  # {url, content, summary, credibility_score}
    
    # Verification phase
    verified_claims: List[dict]  # {claim, evidence, confidence, sources}
    contradictions: List[str]
    gaps: List[str]
    
    # Writing phase
    report_sections: dict
    final_report: str
    
    # Metadata
    messages: Annotated[List[dict], add_messages]
    errors: List[str]
    completed_steps: List[str]


class PlanStep(TypedDict):
    """Individual step in the research plan."""
    step_id: int
    description: str
    assigned_agent: str  # 'search', 'reader', 'verifier'
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    dependencies: List[int]
    output_key: str


class SearchResult(TypedDict):
    """Search result from DuckDuckGo."""
    url: str
    title: str
    snippet: str
    source_domain: str
    relevance_score: float


class FetchedContent(TypedDict):
    """Content extracted from a URL."""
    url: str
    title: str
    content: str
    summary: str
    credibility_score: float
    domain_authority: float
    extraction_method: str


class VerifiedClaim(TypedDict):
    """A claim verified against multiple sources."""
    claim: str
    evidence: List[str]
    confidence: float  # 0.0 to 1.0
    supporting_sources: List[str]
    contradicting_sources: List[str]
    verification_status: str  # 'verified', 'contradicted', 'unverified'
