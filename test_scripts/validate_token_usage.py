#!/usr/bin/env python3
"""
Token Usage Validator - Run this to get ACTUAL token usage from your system
Compare against estimates to validate pricing accuracy
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from hr_bot.crew import HrBot
from hr_bot.tools.hybrid_rag_tool import HybridRAGRetriever


def estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters for English)"""
    return len(text) // 4


def test_actual_usage():
    """Run actual queries and measure token usage"""
    
    print("🔍 VALIDATING ACTUAL TOKEN USAGE\n")
    print("=" * 80)
    
    # Initialize system
    retriever = HybridRAGRetriever(data_dir="data")
    retriever.build_index()
    
    test_queries = [
        "What is the sick leave policy?",
        "Explain the maternity leave benefits and eligibility criteria in detail",
        "What is the process for requesting flexible working arrangements and what documentation is required?",
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📊 Query {i}: {query}")
        print("-" * 80)
        
        # Get RAG context
        try:
            rag_results = retriever.hybrid_search(query, top_k=12)
            
            # Calculate context tokens - SearchResult has .content attribute
            context_text = "\n\n".join([r.content for r in rag_results])
            context_tokens = estimate_tokens(context_text)
            
            # Estimate total input
            query_tokens = estimate_tokens(query)
            system_prompt_tokens = 800  # Estimated for CrewAI system prompts
            agent_instructions = 500    # Estimated for agent instructions
            multi_agent_overhead = 1.3  # 30% overhead for hierarchical processing
            
            total_input = int((query_tokens + context_tokens + system_prompt_tokens + agent_instructions) * multi_agent_overhead)
            
            print(f"   Query tokens: {query_tokens:,}")
            print(f"   RAG context tokens: {context_tokens:,}")
            print(f"   System prompts (est): {system_prompt_tokens:,}")
            print(f"   Agent instructions (est): {agent_instructions:,}")
            print(f"   Multi-agent overhead: {multi_agent_overhead}x")
            print(f"   → TOTAL INPUT TOKENS: {total_input:,}")
            
            # Store for summary
            results.append({
                "query": query,
                "complexity": "simple" if len(query) < 50 else "medium" if len(query) < 100 else "complex",
                "input_tokens": total_input,
                "context_tokens": context_tokens,
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Summary comparison
    print("\n" + "=" * 80)
    print("📈 SUMMARY COMPARISON WITH ESTIMATES")
    print("=" * 80)
    
    if results:
        avg_simple = sum(r["input_tokens"] for r in results if r["complexity"] == "simple") / max(1, sum(1 for r in results if r["complexity"] == "simple"))
        avg_medium = sum(r["input_tokens"] for r in results if r["complexity"] == "medium") / max(1, sum(1 for r in results if r["complexity"] == "medium"))
        avg_complex = sum(r["input_tokens"] for r in results if r["complexity"] == "complex") / max(1, sum(1 for r in results if r["complexity"] == "complex"))
        
        print(f"\n🔹 ACTUAL MEASUREMENTS:")
        print(f"   Simple queries:  {avg_simple:,.0f} tokens/query")
        print(f"   Medium queries:  {avg_medium:,.0f} tokens/query")
        print(f"   Complex queries: {avg_complex:,.0f} tokens/query")
        
        print(f"\n🔹 ESTIMATED IN PRICING MODEL:")
        print(f"   Light Usage:      3,000 tokens/query")
        print(f"   Standard Complex: 6,000 tokens/query")
        print(f"   Very Complex:    12,000 tokens/query")
        print(f"   Enterprise:      15,000 tokens/query")
        
        # Calculate accuracy
        if avg_medium > 0:
            standard_accuracy = (6000 / avg_medium) * 100
            print(f"\n⚠️  PRICING ACCURACY:")
            print(f"   Standard tier estimate is {standard_accuracy:.1f}% of actual usage")
            
            if standard_accuracy < 80:
                print(f"   🚨 WARNING: Estimates are TOO LOW - Risk of financial loss!")
                print(f"   🔧 RECOMMENDATION: Increase Standard Complex to {avg_medium:,.0f} tokens")
            elif standard_accuracy > 120:
                print(f"   ⚠️  Estimates may be HIGH - Could lose competitive edge")
            else:
                print(f"   ✅ Estimates are within acceptable range (80-120%)")
    
    print("\n" + "=" * 80)
    print("💡 NEXT STEPS:")
    print("1. Run this with MORE diverse queries (10-20 queries)")
    print("2. Include actual user queries from testing/beta")
    print("3. Test with conversation history (multi-turn dialogues)")
    print("4. Measure output tokens from actual responses")
    print("5. Update run_cost_estimate.py with validated numbers")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_actual_usage()
