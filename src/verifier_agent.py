"""
Verifier Agent - Cross-references claims, detects contradictions, and scores confidence.
"""

from typing import List, Dict, Optional
from difflib import SequenceMatcher


class VerifierAgent:
    """Agent responsible for verifying claims across multiple sources."""
    
    def __init__(self, llm_client=None):
        """
        Initialize the Verifier Agent.
        
        Args:
            llm_client: Optional LLM client for advanced verification
        """
        self.llm_client = llm_client
    
    def extract_claims(self, content_list: List[Dict]) -> List[Dict]:
        """
        Extract factual claims from content with source attribution.
        
        Args:
            content_list: List of content dictionaries from Reader Agent
            
        Returns:
            List of extracted claims with metadata
        """
        claims = []
        
        for content in content_list:
            text = content.get('content', '')
            url = content.get('url', 'unknown')
            credibility = content.get('credibility_score', 0.5)
            
            # Simple claim extraction (sentences with numbers or specific facts)
            sentences = text.replace('\n', ' ').split('.')
            
            for sentence in sentences:
                sentence = sentence.strip()
                
                # Filter for potentially factual statements
                if self._is_factual_claim(sentence):
                    claims.append({
                        'claim': sentence + '.',
                        'source_url': url,
                        'source_credibility': credibility,
                        'extraction_confidence': 0.7
                    })
        
        return claims
    
    def _is_factual_claim(self, sentence: str) -> bool:
        """Check if a sentence appears to be a factual claim."""
        if len(sentence) < 20 or len(sentence) > 300:
            return False
        
        # Look for indicators of factual statements
        indicators = [
            ' is ', ' are ', ' was ', ' were ', ' has ', ' have ',
            ' will ', ' according ', ' reported ', ' found ',
            ' study ', ' research ', ' data ', ' percent ', '%',
            ' increased ', ' decreased ', ' shows ', ' indicates '
        ]
        
        sentence_lower = sentence.lower()
        return any(indicator in sentence_lower for indicator in indicators)
    
    def cross_reference(self, claims: List[Dict], content_list: List[Dict]) -> List[Dict]:
        """
        Cross-reference claims against all available content.
        
        Args:
            claims: List of extracted claims
            content_list: List of all content for cross-referencing
            
        Returns:
            List of verified claims with confidence scores
        """
        verified_claims = []
        
        for claim in claims:
            claim_text = claim['claim']
            supporting_sources = []
            contradicting_sources = []
            evidence_snippets = []
            
            # Check each content source for support/contradiction
            for content in content_list:
                text = content.get('content', '').lower()
                url = content.get('url', 'unknown')
                credibility = content.get('credibility_score', 0.5)
                
                # Check for similarity or mention
                similarity = self._calculate_similarity(claim_text, text)
                
                if similarity > 0.3:
                    # Found relevant mention
                    if self._supports_claim(claim_text, text):
                        supporting_sources.append({
                            'url': url,
                            'credibility': credibility,
                            'similarity': similarity
                        })
                        evidence_snippets.append(self._extract_relevant_snippet(claim_text, text))
                    elif self._contradicts_claim(claim_text, text):
                        contradicting_sources.append({
                            'url': url,
                            'credibility': credibility
                        })
            
            # Calculate confidence score
            confidence = self._calculate_confidence(
                supporting_sources,
                contradicting_sources,
                claim['source_credibility']
            )
            
            # Determine verification status
            if confidence >= 0.7 and len(contradicting_sources) == 0:
                status = 'verified'
            elif confidence <= 0.3 or len(contradicting_sources) > len(supporting_sources):
                status = 'contradicted'
            else:
                status = 'unverified'
            
            verified_claims.append({
                'claim': claim_text,
                'evidence': evidence_snippets[:3],  # Top 3 snippets
                'confidence': confidence,
                'supporting_sources': [s['url'] for s in supporting_sources],
                'contradicting_sources': [s['url'] for s in contradicting_sources],
                'verification_status': status
            })
        
        return verified_claims
    
    def _calculate_similarity(self, claim: str, text: str) -> float:
        """Calculate similarity between claim and text."""
        claim_words = set(claim.lower().split())
        text_words = set(text.lower().split())
        
        if not text_words:
            return 0.0
        
        intersection = claim_words & text_words
        return len(intersection) / len(claim_words)
    
    def _supports_claim(self, claim: str, text: str) -> bool:
        """Determine if text supports the claim."""
        claim_lower = claim.lower()
        text_lower = text.lower()
        
        # Check for key terms from claim in text
        important_words = [w for w in claim_lower.split() if len(w) > 4]
        matches = sum(1 for word in important_words if word in text_lower)
        
        return matches >= len(important_words) * 0.5
    
    def _contradicts_claim(self, claim: str, text: str) -> bool:
        """Determine if text contradicts the claim."""
        contradiction_indicators = [
            'however', 'but', 'contrary', 'dispute', 'debunk',
            'false', 'incorrect', 'wrong', 'not true', 'myth'
        ]
        
        text_lower = text.lower()
        claim_lower = claim.lower()
        
        # Check if contradiction words appear near claim terms
        for indicator in contradiction_indicators:
            if indicator in text_lower:
                # Simple heuristic: if contradiction word exists, might be contradictory
                return True
        
        return False
    
    def _extract_relevant_snippet(self, claim: str, text: str, max_length: int = 150) -> str:
        """Extract a relevant snippet from text that relates to the claim."""
        sentences = text.replace('\n', ' ').split('.')
        
        claim_words = set(claim.lower().split())
        
        best_snippet = ""
        best_score = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            sentence_words = set(sentence.lower().split())
            
            overlap = len(claim_words & sentence_words)
            if overlap > best_score and len(sentence) <= max_length:
                best_score = overlap
                best_snippet = sentence
        
        return best_snippet + '.' if best_snippet else ""
    
    def _calculate_confidence(
        self,
        supporting: List[Dict],
        contradicting: List[Dict],
        source_credibility: float
    ) -> float:
        """
        Calculate confidence score for a claim.
        
        Args:
            supporting: List of supporting source info
            contradicting: List of contradicting source info
            source_credibility: Credibility of original source
            
        Returns:
            Confidence score from 0.0 to 1.0
        """
        if not supporting and not contradicting:
            return 0.5  # Neutral if no evidence
        
        # Weight by credibility
        support_score = sum(s['credibility'] * s['similarity'] for s in supporting)
        contradict_score = sum(c['credibility'] for c in contradicting)
        
        # Normalize
        num_support = len(supporting)
        num_contradict = len(contradicting)
        
        if num_support + num_contradict == 0:
            return source_credibility
        
        base_confidence = support_score / (support_score + contradict_score + 0.1)
        
        # Adjust for number of sources
        source_bonus = min(num_support * 0.1, 0.3)
        
        # Factor in original source credibility
        final_confidence = (base_confidence * 0.6) + (source_credibility * 0.2) + source_bonus
        
        return max(0.0, min(1.0, final_confidence))
    
    def identify_gaps(self, verified_claims: List[Dict], query: str) -> List[str]:
        """
        Identify gaps in the research based on low-confidence claims.
        
        Args:
            verified_claims: List of verified claims
            query: Original research query
            
        Returns:
            List of identified research gaps
        """
        gaps = []
        
        # Find low-confidence claims
        low_confidence = [c for c in verified_claims if c['confidence'] < 0.5]
        
        if len(low_confidence) > len(verified_claims) * 0.3:
            gaps.append("Multiple claims lack sufficient verification - more authoritative sources needed")
        
        # Check for missing perspectives
        if not any('statistic' in c['claim'].lower() or 'percent' in c['claim'].lower() 
                   for c in verified_claims):
            gaps.append("Lack of quantitative data or statistics")
        
        # Check for recency
        if not any('2024' in c['claim'] or '2025' in c['claim'] for c in verified_claims):
            gaps.append("Missing recent developments or current year information")
        
        return gaps
    
    def verify_all(self, content_list: List[Dict], query: str) -> Dict:
        """
        Complete verification pipeline.
        
        Args:
            content_list: List of content from Reader Agent
            query: Original research query
            
        Returns:
            Dictionary with verified claims, contradictions, and gaps
        """
        # Extract claims
        claims = self.extract_claims(content_list)
        
        # Cross-reference
        verified = self.cross_reference(claims, content_list)
        
        # Identify contradictions
        contradictions = [
            c['claim'] for c in verified 
            if c['verification_status'] == 'contradicted'
        ]
        
        # Identify gaps
        gaps = self.identify_gaps(verified, query)
        
        return {
            'verified_claims': verified,
            'contradictions': contradictions,
            'gaps': gaps,
            'total_claims': len(claims),
            'verified_count': len([c for c in verified if c['verification_status'] == 'verified'])
        }


if __name__ == "__main__":
    # Test the verifier agent
    agent = VerifierAgent()
    
    # Mock content for testing
    test_content = [
        {
            'content': 'Climate change is causing global temperatures to rise. Studies show a 1.1°C increase since pre-industrial times.',
            'url': 'https://example.com/climate',
            'credibility_score': 0.8
        },
        {
            'content': 'Global warming has led to more extreme weather events. The past decade was the warmest on record.',
            'url': 'https://science.org/warming',
            'credibility_score': 0.9
        }
    ]
    
    result = agent.verify_all(test_content, "climate change impacts")
    print(f"Total claims: {result['total_claims']}")
    print(f"Verified: {result['verified_count']}")
    print(f"Gaps: {result['gaps']}")
