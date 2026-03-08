"""
Test suite for the Autonomous Research Agent.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestSearchAgent(unittest.TestCase):
    """Tests for SearchAgent."""
    
    def setUp(self):
        from src.search_agent import SearchAgent
        self.agent = SearchAgent()
    
    def test_fallback_query_generation(self):
        """Test fallback query generation without LLM."""
        queries = self.agent._generate_fallback_queries("climate change", 3)
        
        self.assertEqual(len(queries), 3)
        self.assertIn("climate change", queries[0])
    
    def test_domain_extraction(self):
        """Test domain extraction from URLs."""
        url = "https://www.example.com/path/to/page"
        domain = self.agent._extract_domain(url)
        
        self.assertEqual(domain, "example.com")
    
    def test_relevance_calculation(self):
        """Test relevance score calculation."""
        result = {
            'title': 'Climate Change Statistics',
            'body': 'Recent data shows climate change impacts'
        }
        query = "climate change"
        
        score = self.agent._calculate_relevance(result, query)
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 1.0)
    
    def test_search_result_filtering(self):
        """Test that blacklisted domains are filtered."""
        # Blacklisted domains should be filtered during search
        self.assertIn('pinterest.com', self.agent.domain_blacklist)


class TestReaderAgent(unittest.TestCase):
    """Tests for ReaderAgent."""
    
    def setUp(self):
        from src.reader_agent import ReaderAgent
        self.agent = ReaderAgent()
    
    def test_credibility_assessment_high(self):
        """Test high credibility domain assessment."""
        url = "https://www.nasa.gov/news"
        score = self.agent.assess_credibility(url)
        
        self.assertGreater(score, 0.7)
    
    def test_credibility_assessment_low(self):
        """Test low credibility domain assessment."""
        url = "https://example.blogspot.com/post"
        score = self.agent.assess_credibility(url)
        
        self.assertLess(score, 0.5)
    
    def test_extractive_summary(self):
        """Test extractive summary generation."""
        content = "This is a long sentence. This is another one. Short." * 10
        summary = self.agent._extractive_summary(content, max_length=100)
        
        self.assertLessEqual(len(summary), 100)
        self.assertTrue(len(summary) > 0)


class TestVerifierAgent(unittest.TestCase):
    """Tests for VerifierAgent."""
    
    def setUp(self):
        from src.verifier_agent import VerifierAgent
        self.agent = VerifierAgent()
    
    def test_factual_claim_detection(self):
        """Test factual claim detection."""
        factual = "The study found a 25% increase in temperatures."
        non_factual = "Maybe something could happen possibly."
        
        self.assertTrue(self.agent._is_factual_claim(factual))
        self.assertFalse(self.agent._is_factual_claim(non_factual))
    
    def test_similarity_calculation(self):
        """Test text similarity calculation."""
        claim = "climate change causes warming"
        text = "Research shows climate change is causing global warming"
        
        similarity = self.agent._calculate_similarity(claim, text)
        
        self.assertGreater(similarity, 0.3)
    
    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        supporting = [
            {'credibility': 0.9, 'similarity': 0.8},
            {'credibility': 0.8, 'similarity': 0.7}
        ]
        contradicting = []
        source_cred = 0.85
        
        confidence = self.agent._calculate_confidence(
            supporting, contradicting, source_cred
        )
        
        self.assertGreater(confidence, 0.7)
        self.assertLessEqual(confidence, 1.0)
    
    def test_gap_identification(self):
        """Test research gap identification."""
        claims = [
            {'claim': 'Some general statement', 'confidence': 0.4}
        ]
        
        gaps = self.agent.identify_gaps(claims, "test query")
        
        # Should identify lack of statistics
        self.assertTrue(len(gaps) > 0)


class TestWriterAgent(unittest.TestCase):
    """Tests for WriterAgent."""
    
    def setUp(self):
        from src.writer_agent import WriterAgent
        self.agent = WriterAgent()
    
    def test_title_generation(self):
        """Test report title generation."""
        query = "impacts of climate change on agriculture"
        title = self.agent._generate_title(query)
        
        self.assertIn("Climate", title)
        self.assertIn("Agriculture", title)
    
    def test_executive_summary_generation(self):
        """Test executive summary generation."""
        claims = [
            {
                'claim': 'Temperatures have risen by 1.1°C',
                'confidence': 0.85,
                'verification_status': 'verified'
            }
        ]
        
        summary = self.agent._generate_executive_summary("climate change", claims)
        
        self.assertIn("climate change", summary.lower())
    
    def test_sources_generation(self):
        """Test sources section generation."""
        content = [
            {
                'url': 'https://example.com/article',
                'title': 'Test Article',
                'credibility_score': 0.8,
                'source_domain': 'example.com'
            }
        ]
        
        sources = self.agent._generate_sources(content, [])
        
        self.assertIn("Sources", sources)
        self.assertIn("Test Article", sources)
    
    def test_fallback_report_generation(self):
        """Test fallback report generation."""
        report = self.agent.generate_fallback_report(
            "test query",
            "Test error message"
        )
        
        self.assertIn("test query", report.lower())
        self.assertIn("error", report.lower())


class TestPlanningAgent(unittest.TestCase):
    """Tests for PlanningAgent."""
    
    def setUp(self):
        from src.planning_agent import PlanningAgent
        self.agent = PlanningAgent()
    
    def test_rule_based_plan_creation(self):
        """Test rule-based plan creation."""
        query = "What is climate change?"
        plan = self.agent.create_plan(query, max_steps=5)
        
        self.assertEqual(len(plan), 5)
        
        # Check required fields
        for step in plan:
            self.assertIn('step_id', step)
            self.assertIn('description', step)
            self.assertIn('assigned_agent', step)
            self.assertIn('status', step)
    
    def test_next_steps_execution(self):
        """Test getting next executable steps."""
        plan = [
            {'step_id': 1, 'status': 'pending', 'dependencies': []},
            {'step_id': 2, 'status': 'pending', 'dependencies': [1]},
            {'step_id': 3, 'status': 'pending', 'dependencies': [1, 2]}
        ]
        
        # Initially only step 1 should be available
        next_steps = self.agent.get_next_steps(plan, completed=[])
        self.assertEqual(len(next_steps), 1)
        self.assertEqual(next_steps[0]['step_id'], 1)
        
        # After completing step 1, step 2 becomes available
        next_steps = self.agent.get_next_steps(plan, completed=[1])
        self.assertEqual(len(next_steps), 1)
        self.assertEqual(next_steps[0]['step_id'], 2)
    
    def test_step_completion_marking(self):
        """Test marking steps as complete."""
        plan = [
            {'step_id': 1, 'status': 'pending', 'dependencies': []}
        ]
        
        updated_plan = self.agent.mark_step_complete(plan, step_id=1)
        
        self.assertEqual(updated_plan[0]['status'], 'completed')


class TestOrchestrator(unittest.TestCase):
    """Tests for Orchestrator."""
    
    def setUp(self):
        from src.orchestrator import Orchestrator
        self.orchestrator = Orchestrator(llm_client=None)
    
    def test_graph_construction(self):
        """Test that the workflow graph is properly constructed."""
        self.assertIsNotNone(self.orchestrator.graph)
    
    def test_all_agents_initialized(self):
        """Test that all agents are initialized."""
        self.assertIsNotNone(self.orchestrator.planning_agent)
        self.assertIsNotNone(self.orchestrator.search_agent)
        self.assertIsNotNone(self.orchestrator.reader_agent)
        self.assertIsNotNone(self.orchestrator.verifier_agent)
        self.assertIsNotNone(self.orchestrator.writer_agent)


if __name__ == '__main__':
    unittest.main()
