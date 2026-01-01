"""Query expansion using LLM to improve retrieval"""
import os
from openai import OpenAI
from config import LLM_MODEL


class QueryExpander:
    """Expand and diversify user queries for better retrieval"""
    
    def __init__(self, api_key=None, model=None):
        """
        Initialize query expander
        
        Args:
            api_key (str): OpenAI API key
            model (str): Model to use (default: gpt-4o-mini)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or LLM_MODEL
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            self.client = OpenAI(api_key=self.api_key)
            print(f"✅ Query Expander initialized ({self.model})")
        else:
            print("⚠️ Query expansion disabled (no API key)")
    
    def expand_query(self, query: str) -> str:
        """
        Expand a short query with technical terms and context
        
        Args:
            query (str): Original user query
            
        Returns:
            str: Expanded query with keywords
        """
        if not self.enabled:
            return query
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a query expansion assistant for technical documentation search.
Given a user query, expand it with ALL relevant technical terms, table-related keywords, specifications, and synonyms.
Include variations of key terms and related concepts. Be comprehensive (up to 80 words).

**IMPORTANT EXPANSION STRATEGIES:**

For SPECIFICATION/VALUE queries (torque, voltage, dimensions, etc.):
- Include: "table", "specification", "spec", "wiring rules", "technical data"
- Include measurement variations: write "Nm" also as "Newton meter", "N·m"
- Include related terms: "connection", "terminal", "connector", "front connector"
- Include numerical context: if asking about a range, include words like "range", "value", "minimum", "maximum"

For COMPONENT queries:
- Include full component names and abbreviations
- Include related components and assembly context
- Include action verbs: "connect", "install", "configure", "wire"

For PROCEDURE queries:
- Include: "step", "procedure", "instruction", "guide", "manual"
- Include action sequences: "first", "then", "next", "initialize", "startup"

For ERROR/DIAGNOSTIC queries:
- Include: "error", "fault", "diagnostic", "troubleshooting", "LED", "indicator"
- Include related concepts: "code", "message", "alarm", "buffer", "status"

**FORMAT:**
Output ONLY the expanded query with added keywords. No explanations, no formatting.

**Example pattern:**
User asks about "X specification" → Include: X, specification, spec, table, technical data, related component names, measurement units

Just output the expanded query keywords, nothing else."""
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            expanded = response.choices[0].message.content.strip()
            print(f"🔍 Expanded query: '{query}' → '{expanded}'")
            return expanded
            
        except Exception as e:
            print(f"⚠️ Query expansion failed: {e}")
            return query
    
    def generate_multi_queries(self, query: str, num_queries: int = 3) -> list:
        """
        Generate multiple variations of the same query
        
        Args:
            query (str): Original query
            num_queries (int): Number of variations to generate
            
        Returns:
            list: List of query variations (including original)
        """
        if not self.enabled:
            return [query]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a query diversification assistant.
Given a user query, generate {num_queries} different variations that mean the same thing but use different words/phrasings.
This helps retrieve more relevant documents.

Output format: One query per line, no numbering or bullets.

Example:
Input: "How to power on the CPU?"
Output:
Steps to start the CPU 1511-1 PN
CPU power on procedure and initialization
Turn on SIMATIC CPU mains connection

Input: "What are the error codes?"
Output:
List of fault codes and diagnostics
CPU error messages and LED indicators
Diagnostic codes and troubleshooting
"""
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            variations = response.choices[0].message.content.strip().split('\n')
            variations = [v.strip() for v in variations if v.strip()]
            
            # Add original query at the beginning
            all_queries = [query] + variations[:num_queries]
            
            print(f"🔄 Generated {len(all_queries)} query variations")
            return all_queries
            
        except Exception as e:
            print(f"⚠️ Multi-query generation failed: {e}")
            return [query]


# Singleton
_expander = None

def get_expander():
    """Get or create expander instance"""
    global _expander
    if _expander is None:
        _expander = QueryExpander()
    return _expander
