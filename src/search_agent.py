"""
Search Agent - Generates optimized search queries and fetches results from DuckDuckGo.
"""

import os
from typing import List, Dict

try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    print("Warning: duckduckgo-search not installed. Search will use fallback mode.")

from src.models import SearchResult


class SearchAgent:
    """Agent responsible for generating search queries and fetching results."""
    
    def __init__(self, llm_client=None):
        """
        Initialize the Search Agent.
        
        Args:
            llm_client: Optional LLM client for query optimization
        """
        self.llm_client = llm_client
        self.ddgs = DDGS() if DUCKDUCKGO_AVAILABLE else None
        self.domain_blacklist = [
            'pinterest.com', 'instagram.com', 'facebook.com',
            'twitter.com', 'tiktok.com', 'youtube.com'
        ]
    
    def generate_search_queries(self, query: str, num_queries: int = 3) -> List[str]:
        """
        Generate optimized search queries from the original research query.
        
        Args:
            query: Original research query
            num_queries: Number of search queries to generate
            
        Returns:
            List of optimized search queries
        """
        if self.llm_client is None:
            # Fallback: use simple variations
            return self._generate_fallback_queries(query, num_queries)
        
        try:
            prompt = f"""Generate {num_queries} diverse search queries to research this topic thoroughly.
Each query should explore a different aspect or angle. Return ONLY a JSON list of strings.

Research topic: {query}

Example output format:
["query 1", "query 2", "query 3"]
"""
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            import json
            queries = json.loads(response.choices[0].message.content.strip())
            return queries[:num_queries]
            
        except Exception as e:
            print(f"LLM query generation failed: {e}")
            return self._generate_fallback_queries(query, num_queries)
    
    def _generate_fallback_queries(self, query: str, num_queries: int) -> List[str]:
        """Generate simple query variations without LLM."""
        base_query = query.strip()
        queries = [base_query]
        
        # Add some common research angles
        angles = [
            f"{base_query} statistics data",
            f"{base_query} recent developments 2024 2025",
            f"{base_query} expert analysis review",
            f"{base_query} pros cons debate"
        ]
        
        queries.extend(angles[:num_queries - 1])
        return queries[:num_queries]
    
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Perform a DuckDuckGo search with domain filtering and deduplication.
        
        Args:
            query: Search query string
            num_results: Maximum number of results to return
            
        Returns:
            List of SearchResult dictionaries
        """
        if not DUCKDUCKGO_AVAILABLE or self.ddgs is None:
            print(f"Search unavailable - returning mock results for: {query}")
            return self._get_mock_results(query, num_results)
        
        try:
            results = []
            seen_urls = set()
            
            ddg_results = self.ddgs.text(query, max_results=num_results * 2)
            
            for result in ddg_results:
                url = result.get('href', '')
                
                # Skip already seen URLs
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                # Filter blacklisted domains
                if any(domain in url for domain in self.domain_blacklist):
                    continue
                
                # Extract domain for credibility scoring
                domain = self._extract_domain(url)
                
                search_result = {
                    'url': url,
                    'title': result.get('title', 'No title'),
                    'snippet': result.get('body', 'No snippet'),
                    'source_domain': domain,
                    'relevance_score': self._calculate_relevance(result, query)
                }
                
                results.append(search_result)
                
                if len(results) >= num_results:
                    break
            
            # Sort by relevance score
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return results[:num_results]
            
        except Exception as e:
            print(f"Search failed for query '{query}': {e}")
            return self._get_mock_results(query, num_results)
    
    def _get_mock_results(self, query: str, num_results: int) -> List[Dict]:
        """Return mock search results when DuckDuckGo is unavailable."""
        return [
            {
                'url': f'https://example.com/{query.replace(" ", "-")}-{i}',
                'title': f'Result {i} for {query}',
                'snippet': f'This is a mock search result about {query}.',
                'source_domain': 'example.com',
                'relevance_score': 0.5 - (i * 0.1)
            }
            for i in range(num_results)
        ]
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return 'unknown'
    
    def _calculate_relevance(self, result: Dict, query: str) -> float:
        """Calculate relevance score based on title and snippet matching."""
        score = 0.0
        query_terms = query.lower().split()
        
        title = result.get('title', '').lower()
        snippet = result.get('body', '').lower()
        
        # Title matches are weighted higher
        for term in query_terms:
            if term in title:
                score += 0.3
            if term in snippet:
                score += 0.1
        
        # Bonus for exact phrase match in title
        if query.lower() in title:
            score += 0.5
        
        return min(score, 1.0)
    
    def execute_search_plan(self, queries: List[str], results_per_query: int = 5) -> List[Dict]:
        """
        Execute searches for multiple queries and combine results.
        
        Args:
            queries: List of search queries
            results_per_query: Results to fetch per query
            
        Returns:
            Combined and deduplicated search results
        """
        all_results = []
        seen_urls = set()
        
        for query in queries:
            print(f"Searching: {query}")
            results = self.search(query, num_results=results_per_query)
            
            for result in results:
                if result['url'] not in seen_urls:
                    seen_urls.add(result['url'])
                    all_results.append(result)
        
        # Sort by relevance
        all_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return all_results


if __name__ == "__main__":
    # Test the search agent
    agent = SearchAgent()
    queries = agent.generate_search_queries("climate change impacts 2025")
    print(f"Generated queries: {queries}")
    
    results = agent.execute_search_plan(queries[:2], results_per_query=3)
    print(f"\nFound {len(results)} results:")
    for r in results:
        print(f"  - {r['title']} ({r['source_domain']})")
