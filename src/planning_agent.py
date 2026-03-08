"""
Planning Agent - Uses ReAct pattern for query decomposition and dynamic plan adjustment.
"""

from typing import List, Dict, Optional
import json


class PlanningAgent:
    """Agent responsible for decomposing queries into research plans."""
    
    def __init__(self, llm_client=None):
        """
        Initialize the Planning Agent.
        
        Args:
            llm_client: Optional LLM client for plan generation
        """
        self.llm_client = llm_client
    
    def create_plan(self, query: str, max_steps: int = 5) -> List[Dict]:
        """
        Create a research plan using ReAct pattern.
        
        Args:
            query: Research query to decompose
            max_steps: Maximum number of steps in the plan
            
        Returns:
            List of plan step dictionaries
        """
        if self.llm_client is None:
            return self._create_rule_based_plan(query, max_steps)
        
        try:
            prompt = f"""You are a research planning assistant. Decompose this research query into actionable steps.

Research Query: {query}

Create a plan with up to {max_steps} steps. Each step should:
1. Be specific and actionable
2. Assign an appropriate agent (search, reader, or verifier)
3. Have clear dependencies on previous steps

Return ONLY a JSON array of steps in this format:
[
    {{
        "step_id": 1,
        "description": "Search for recent statistics on X",
        "assigned_agent": "search",
        "dependencies": [],
        "output_key": "search_results_1"
    }}
]
"""
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=800
            )
            
            plan = json.loads(response.choices[0].message.content.strip())
            return self._validate_plan(plan, max_steps)
            
        except Exception as e:
            print(f"LLM planning failed: {e}")
            return self._create_rule_based_plan(query, max_steps)
    
    def _create_rule_based_plan(self, query: str, max_steps: int) -> List[Dict]:
        """Create a plan using rule-based heuristics."""
        plan = [
            {
                "step_id": 1,
                "description": f"Search for overview information about: {query}",
                "assigned_agent": "search",
                "dependencies": [],
                "output_key": "overview_search"
            },
            {
                "step_id": 2,
                "description": "Fetch and extract content from top search results",
                "assigned_agent": "reader",
                "dependencies": [1],
                "output_key": "overview_content"
            },
            {
                "step_id": 3,
                "description": f"Search for specific data and statistics about: {query}",
                "assigned_agent": "search",
                "dependencies": [],
                "output_key": "data_search"
            },
            {
                "step_id": 4,
                "description": "Fetch detailed content from data-rich sources",
                "assigned_agent": "reader",
                "dependencies": [3],
                "output_key": "data_content"
            },
            {
                "step_id": 5,
                "description": "Cross-reference and verify all extracted claims",
                "assigned_agent": "verifier",
                "dependencies": [2, 4],
                "output_key": "verified_claims"
            }
        ]
        
        return plan[:max_steps]
    
    def _validate_plan(self, plan: List[Dict], max_steps: int) -> List[Dict]:
        """Validate and normalize a generated plan."""
        validated = []
        seen_ids = set()
        
        for i, step in enumerate(plan[:max_steps]):
            # Ensure required fields
            step['step_id'] = step.get('step_id', i + 1)
            step['description'] = step.get('description', f'Step {i + 1}')
            step['assigned_agent'] = step.get('assigned_agent', 'search')
            step['dependencies'] = step.get('dependencies', [])
            step['output_key'] = step.get('output_key', f'step_{i + 1}_output')
            step['status'] = 'pending'
            
            # Avoid duplicate IDs
            if step['step_id'] not in seen_ids:
                seen_ids.add(step['step_id'])
                validated.append(step)
        
        return validated
    
    def adjust_plan(
        self,
        current_plan: List[Dict],
        findings: Dict,
        query: str
    ) -> List[Dict]:
        """
        Dynamically adjust the plan based on findings.
        
        Args:
            current_plan: Current research plan
            findings: Dictionary of findings so far
            query: Original research query
            
        Returns:
            Adjusted plan
        """
        # Check if we need more searches
        search_results = findings.get('search_results', [])
        fetched_content = findings.get('fetched_content', [])
        
        # If few results, add more search steps
        if len(search_results) < 5:
            new_step = {
                "step_id": len(current_plan) + 1,
                "description": f"Expand search with alternative queries for: {query}",
                "assigned_agent": "search",
                "dependencies": [],
                "output_key": "expanded_search",
                "status": "pending"
            }
            current_plan.append(new_step)
        
        # If little content fetched, prioritize reading
        if len(fetched_content) < 3 and len(search_results) >= 5:
            new_step = {
                "step_id": len(current_plan) + 1,
                "description": "Fetch additional content from available search results",
                "assigned_agent": "reader",
                "dependencies": [],
                "output_key": "additional_content",
                "status": "pending"
            }
            current_plan.append(new_step)
        
        return current_plan
    
    def get_next_steps(self, plan: List[Dict], completed: List[int]) -> List[Dict]:
        """
        Get the next executable steps based on dependencies.
        
        Args:
            plan: Full research plan
            completed: List of completed step IDs
            
        Returns:
            List of steps ready to execute
        """
        next_steps = []
        completed_set = set(completed)
        
        for step in plan:
            if step.get('status') == 'completed':
                continue
            
            # Check if all dependencies are met
            dependencies = step.get('dependencies', [])
            if all(dep in completed_set for dep in dependencies):
                next_steps.append(step)
        
        return next_steps
    
    def mark_step_complete(self, plan: List[Dict], step_id: int) -> List[Dict]:
        """Mark a step as completed."""
        for step in plan:
            if step['step_id'] == step_id:
                step['status'] = 'completed'
                break
        return plan
    
    def generate_react_trace(self, query: str, plan: List[Dict]) -> str:
        """
        Generate a ReAct-style trace for debugging/analysis.
        
        Args:
            query: Original query
            plan: Current plan
            
        Returns:
            Formatted ReAct trace string
        """
        trace = f"Query: {query}\n\n"
        trace += "=== Research Plan ===\n\n"
        
        for step in plan:
            status_icon = "✓" if step.get('status') == 'completed' else "○"
            trace += f"{status_icon} Step {step['step_id']}: [{step['assigned_agent']}]\n"
            trace += f"   {step['description']}\n"
            if step.get('dependencies'):
                trace += f"   Dependencies: {step['dependencies']}\n"
            trace += "\n"
        
        return trace


if __name__ == "__main__":
    # Test the planning agent
    agent = PlanningAgent()
    
    test_query = "What are the impacts of climate change on agriculture in 2025?"
    plan = agent.create_plan(test_query, max_steps=5)
    
    print(f"Research Plan for: {test_query}\n")
    for step in plan:
        print(f"Step {step['step_id']}: [{step['assigned_agent']}]")
        print(f"  {step['description']}")
        print(f"  Dependencies: {step['dependencies']}\n")
    
    # Test ReAct trace
    trace = agent.generate_react_trace(test_query, plan)
    print("\n=== ReAct Trace ===")
    print(trace)
