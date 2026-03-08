"""
Writer Agent - Synthesizes verified claims into markdown reports with citations.
"""

from typing import List, Dict, Optional
from datetime import datetime


class WriterAgent:
    """Agent responsible for generating research reports from verified information."""
    
    def __init__(self, llm_client=None):
        """
        Initialize the Writer Agent.
        
        Args:
            llm_client: Optional LLM client for report generation
        """
        self.llm_client = llm_client
    
    def generate_report(
        self,
        query: str,
        verified_claims: List[Dict],
        search_results: List[Dict],
        fetched_content: List[Dict],
        gaps: List[str] = None
    ) -> str:
        """
        Generate a complete research report in markdown format.
        
        Args:
            query: Original research query
            verified_claims: List of verified claims from Verifier Agent
            search_results: List of search results
            fetched_content: List of fetched content
            gaps: List of identified research gaps
            
        Returns:
            Complete markdown report string
        """
        sections = {
            'title': self._generate_title(query),
            'executive_summary': self._generate_executive_summary(query, verified_claims),
            'key_findings': self._generate_key_findings(verified_claims),
            'analysis': self._generate_analysis(verified_claims, gaps),
            'sources': self._generate_sources(fetched_content, search_results),
            'metadata': self._generate_metadata(query)
        }
        
        return self._assemble_report(sections)
    
    def _generate_title(self, query: str) -> str:
        """Generate a report title from the query."""
        # Capitalize important words
        words = query.split()
        title_words = []
        for word in words:
            if len(word) > 3 or word == words[0]:
                title_words.append(word.capitalize())
            else:
                title_words.append(word.lower())
        
        return f"Research Report: {' '.join(title_words)}"
    
    def _generate_executive_summary(self, query: str, verified_claims: List[Dict]) -> str:
        """Generate an executive summary of key findings."""
        # Get top verified claims
        high_confidence = [
            c for c in verified_claims 
            if c.get('verification_status') == 'verified' and c.get('confidence', 0) >= 0.7
        ]
        
        if not high_confidence:
            return f"This report presents research findings on: {query}"
        
        summary_parts = [f"This research report examines: {query}"]
        
        # Add top 3 findings
        for claim in high_confidence[:3]:
            claim_text = claim['claim']
            # Clean up the claim text
            if len(claim_text) > 150:
                claim_text = claim_text[:147] + "..."
            summary_parts.append(f"- {claim_text}")
        
        return '\n\n'.join(summary_parts)
    
    def _generate_key_findings(self, verified_claims: List[Dict]) -> str:
        """Generate the key findings section."""
        findings = []
        
        # Sort by confidence
        sorted_claims = sorted(
            verified_claims,
            key=lambda x: x.get('confidence', 0),
            reverse=True
        )
        
        for i, claim in enumerate(sorted_claims[:10], 1):
            confidence = claim.get('confidence', 0)
            status = claim.get('verification_status', 'unknown')
            
            # Status indicator
            if status == 'verified':
                indicator = "✓"
            elif status == 'contradicted':
                indicator = "✗"
            else:
                indicator = "?"
            
            finding = f"### Finding {i}: {indicator}\n\n"
            finding += f"**Claim:** {claim['claim']}\n\n"
            finding += f"**Confidence Score:** {confidence:.2f}\n\n"
            
            # Add evidence if available
            if claim.get('evidence'):
                finding += "**Supporting Evidence:**\n"
                for evidence in claim['evidence'][:2]:
                    if evidence:
                        finding += f"- {evidence}\n"
            
            findings.append(finding)
        
        return '\n---\n\n'.join(findings) if findings else "No key findings extracted."
    
    def _generate_analysis(self, verified_claims: List[Dict], gaps: List[str] = None) -> str:
        """Generate the analysis section."""
        analysis_parts = []
        
        # Statistics
        total = len(verified_claims)
        verified_count = len([c for c in verified_claims if c.get('verification_status') == 'verified'])
        contradicted_count = len([c for c in verified_claims if c.get('verification_status') == 'contradicted'])
        avg_confidence = sum(c.get('confidence', 0) for c in verified_claims) / total if total > 0 else 0
        
        if total > 0:
            percent_str = f"{verified_count/total*100:.1f}%"
        else:
            percent_str = "N/A"
        
        stats = f"""## Research Quality Metrics

- **Total Claims Analyzed:** {total}
- **Verified Claims:** {verified_count} ({percent_str})
- **Contradicted Claims:** {contradicted_count}
- **Average Confidence Score:** {avg_confidence:.2f}
"""
        analysis_parts.append(stats)
        
        # Gaps and limitations
        if gaps:
            gaps_section = "## Research Gaps & Limitations\n\n"
            for gap in gaps:
                gaps_section += f"- {gap}\n"
            analysis_parts.append(gaps_section)
        
        # Methodology note
        methodology = """## Methodology

This report was generated using an autonomous research agent that:
1. Decomposed the research query into targeted search strategies
2. Gathered information from multiple web sources
3. Extracted and summarized relevant content
4. Cross-referenced claims across sources for verification
5. Assigned confidence scores based on source credibility and corroboration
"""
        analysis_parts.append(methodology)
        
        return '\n---\n\n'.join(analysis_parts)
    
    def _generate_sources(self, fetched_content: List[Dict], search_results: List[Dict]) -> str:
        """Generate the sources section with citations."""
        sources_list = []
        seen_urls = set()
        
        # Add fetched content first (these have been read)
        for i, content in enumerate(fetched_content, 1):
            url = content.get('url', '')
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            title = content.get('title', 'Untitled')
            credibility = content.get('credibility_score', 0.5)
            domain = content.get('source_domain', self._extract_domain(url))
            
            citation = f"[{i}] **{title}**\n"
            citation += f"   - Source: {domain}\n"
            citation += f"   - URL: {url}\n"
            citation += f"   - Credibility Score: {credibility:.2f}\n"
            
            if content.get('authors'):
                citation += f"   - Authors: {', '.join(content['authors'])}\n"
            
            sources_list.append(citation)
        
        # Add additional search results
        for result in search_results:
            url = result.get('url', '')
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            i = len(sources_list) + 1
            title = result.get('title', 'Untitled')
            domain = result.get('source_domain', self._extract_domain(url))
            
            citation = f"[{i}] **{title}**\n"
            citation += f"   - Source: {domain}\n"
            citation += f"   - URL: {url}\n"
            
            sources_list.append(citation)
        
        if not sources_list:
            return "No sources were successfully retrieved."
        
        return "## Sources\n\n" + '\n---\n\n'.join(sources_list)
    
    def _generate_metadata(self, query: str) -> Dict:
        """Generate report metadata."""
        return {
            'query': query,
            'generated_at': datetime.now().isoformat(),
            'agent_version': '1.0.0'
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return 'Unknown'
    
    def _assemble_report(self, sections: Dict) -> str:
        """Assemble all sections into a complete markdown report."""
        report = f"# {sections['title']}\n\n"
        report += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        report += "---\n\n"
        
        report += f"## Executive Summary\n\n{sections['executive_summary']}\n\n"
        report += "---\n\n"
        
        report += f"## Key Findings\n\n{sections['key_findings']}\n\n"
        report += "---\n\n"
        
        report += f"{sections['analysis']}\n\n"
        report += "---\n\n"
        
        report += f"{sections['sources']}\n\n"
        
        return report
    
    def generate_fallback_report(self, query: str, error_message: str) -> str:
        """
        Generate a minimal fallback report when full generation fails.
        
        Args:
            query: Original research query
            error_message: Error that occurred
            
        Returns:
            Minimal markdown report
        """
        return f"""# Research Report: {query.title()}

*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

---

## Executive Summary

This report could not be fully generated due to technical difficulties.

**Error:** {error_message}

## Recommendations

Please try the following:
1. Check your internet connection
2. Verify API keys are properly configured
3. Try a simpler research query
4. Retry the request

---

*This is a fallback report. Full research capabilities are temporarily unavailable.*
"""


if __name__ == "__main__":
    # Test the writer agent
    agent = WriterAgent()
    
    # Mock data for testing
    test_claims = [
        {
            'claim': 'Climate change is causing global temperatures to rise.',
            'confidence': 0.85,
            'verification_status': 'verified',
            'evidence': ['Studies show temperature increase']
        },
        {
            'claim': 'Renewable energy adoption is accelerating worldwide.',
            'confidence': 0.72,
            'verification_status': 'verified',
            'evidence': ['Solar capacity doubled in 5 years']
        }
    ]
    
    test_content = [
        {
            'url': 'https://example.com/climate',
            'title': 'Climate Change Overview',
            'credibility_score': 0.8,
            'source_domain': 'example.com'
        }
    ]
    
    report = agent.generate_report(
        query="climate change impacts",
        verified_claims=test_claims,
        search_results=[],
        fetched_content=test_content,
        gaps=["Need more recent data"]
    )
    
    print(report[:1000])  # Print first 1000 chars
