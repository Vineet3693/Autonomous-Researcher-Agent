"""
Reader Agent - Fetches web content, extracts main text, and summarizes.
"""

import os
from typing import List, Dict, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import newspaper


class ReaderAgent:
    """Agent responsible for fetching and extracting content from URLs."""
    
    def __init__(self, llm_client=None):
        """
        Initialize the Reader Agent.
        
        Args:
            llm_client: Optional LLM client for summarization
        """
        self.llm_client = llm_client
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Credible domain patterns for scoring
        self.high_credibility_domains = [
            '.edu', '.gov', '.org', 'reuters.com', 'apnews.com',
            'bbc.com', 'nytimes.com', 'washingtonpost.com',
            'theguardian.com', 'nature.com', 'science.org',
            'pubmed.gov', 'arxiv.org', 'scholar.google.com'
        ]
        
        self.low_credibility_patterns = [
            'medium.com', 'substack.com', 'blogspot.com',
            'wordpress.com', 'quora.com', 'reddit.com'
        ]
    
    def fetch_content(self, url: str, timeout: int = 10) -> Optional[Dict]:
        """
        Fetch and extract content from a URL.
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with extracted content or None if failed
        """
        try:
            # Try newspaper3k first for better extraction
            article = newspaper.Article(url)
            article.download(timeout=timeout)
            article.parse()
            
            if article.text and len(article.text) > 100:
                return {
                    'url': url,
                    'title': article.title or 'No title',
                    'content': article.text,
                    'authors': article.authors,
                    'publish_date': article.publish_date,
                    'extraction_method': 'newspaper3k'
                }
            
            # Fallback to BeautifulSoup
            return self._fetch_with_bs(url, timeout)
            
        except Exception as e:
            print(f"Newspaper extraction failed for {url}: {e}")
            return self._fetch_with_bs(url, timeout)
    
    def _fetch_with_bs(self, url: str, timeout: int) -> Optional[Dict]:
        """Fallback content extraction using BeautifulSoup."""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.string.strip() if title else 'No title'
            
            # Extract main content (simplified)
            paragraphs = soup.find_all('p')
            content = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            if len(content) < 100:
                return None
            
            return {
                'url': url,
                'title': title_text,
                'content': content,
                'authors': [],
                'publish_date': None,
                'extraction_method': 'beautifulsoup'
            }
            
        except Exception as e:
            print(f"BeautifulSoup extraction failed for {url}: {e}")
            return None
    
    def assess_credibility(self, url: str) -> float:
        """
        Assess source credibility based on domain analysis.
        
        Args:
            url: Source URL
            
        Returns:
            Credibility score from 0.0 to 1.0
        """
        domain = urlparse(url).netloc.lower()
        score = 0.5  # Base score
        
        # High credibility domains
        for pattern in self.high_credibility_domains:
            if pattern in domain:
                score += 0.3
                break
        
        # Low credibility patterns
        for pattern in self.low_credibility_patterns:
            if pattern in domain:
                score -= 0.2
                break
        
        # .com domains get slight penalty vs .org/.edu/.gov
        if domain.endswith('.com'):
            score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    def summarize(self, content: str, query: str, max_length: int = 300) -> str:
        """
        Summarize extracted content relevant to the research query.
        
        Args:
            content: Full article content
            query: Original research query for context
            max_length: Maximum summary length
            
        Returns:
            Summary string
        """
        if not content or len(content) < max_length:
            return content[:max_length] if content else ""
        
        if self.llm_client is None:
            return self._extractive_summary(content, max_length)
        
        try:
            prompt = f"""Summarize the following content in relation to this research query: "{query}"

Provide a concise summary (max {max_length} characters) capturing key facts and findings.

Content:
{content[:3000]}  # Limit input length

Summary:"""
            
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()[:max_length]
            
        except Exception as e:
            print(f"LLM summarization failed: {e}")
            return self._extractive_summary(content, max_length)
    
    def _extractive_summary(self, content: str, max_length: int) -> str:
        """Generate extractive summary by selecting key sentences."""
        # Simple sentence extraction
        sentences = content.replace('\n', ' ').split('.')
        summary_sentences = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip() + '.'
            if len(sentence) > 20 and current_length + len(sentence) <= max_length:
                summary_sentences.append(sentence)
                current_length += len(sentence)
        
        return ' '.join(summary_sentences)
    
    def process_urls(self, urls: List[str], query: str) -> List[Dict]:
        """
        Process multiple URLs: fetch, extract, assess credibility, and summarize.
        
        Args:
            urls: List of URLs to process
            query: Research query for context
            
        Returns:
            List of processed content dictionaries
        """
        results = []
        
        for url in urls:
            print(f"Fetching: {url}")
            content_data = self.fetch_content(url)
            
            if content_data:
                # Add credibility assessment
                credibility_score = self.assess_credibility(url)
                content_data['credibility_score'] = credibility_score
                
                # Generate summary
                summary = self.summarize(content_data['content'], query)
                content_data['summary'] = summary
                
                # Calculate domain authority (simplified)
                content_data['domain_authority'] = credibility_score * 10
                
                results.append(content_data)
            else:
                print(f"Failed to fetch content from {url}")
        
        return results


if __name__ == "__main__":
    # Test the reader agent
    agent = ReaderAgent()
    
    test_urls = [
        "https://www.bbc.com/news",
        "https://www.nasa.gov"
    ]
    
    results = agent.process_urls(test_urls[:1], "space exploration")
    for r in results:
        print(f"\nTitle: {r['title']}")
        print(f"Credibility: {r['credibility_score']}")
        print(f"Summary: {r['summary'][:200]}...")
