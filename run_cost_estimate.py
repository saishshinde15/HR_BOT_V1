#!/usr/bin/env python3
"""
Professional Cost Estimation for Gemini 2.0 Flash Lite HR Bot
Provides accurate per-user cost estimates in Indian Rupees
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from hr_bot.cost_estimator import (
    CostEstimator,
    UsageProfile,
    STANDARD_COMPLEX_PROFILE,
    VERY_COMPLEX_PROFILE,
)


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_breakdown(quote, profile_name: str):
    """Print detailed cost breakdown"""
    bd = quote.breakdown
    
    print(f"\n📊 {profile_name}")
    print("-" * 80)
    print(f"Model: {bd.model_id}")
    print(f"Queries per user: {bd.profile.queries_per_user:,}")
    print(f"Input tokens per query: {bd.profile.input_tokens_per_query:,}")
    print(f"Output tokens per query: {bd.profile.output_tokens_per_query:,}")
    print(f"Total input tokens: {bd.profile.total_input_tokens:,}")
    print(f"Total output tokens: {bd.profile.total_output_tokens:,}")
    print()
    print(f"💵 Cost (USD): ${bd.usd_cost:.4f}")
    print(f"💰 Cost (INR): ₹{bd.inr_cost:.2f}")
    print(f"📈 Exchange Rate: {bd.fx_rate:.2f} INR/USD")
    print()
    print(f"🎯 QUOTED PRICE (with markup): ₹{quote.quoted_inr:.2f}")
    print(f"💡 Per Query Cost: ₹{quote.per_query_inr:.2f}")
    print(f"   Markup: {quote.markup_percentage}%")
    print(f"   Contingency: {quote.contingency_percentage}%")


def main():
    # Set pricing override path
    pricing_path = Path(__file__).parent / "llm_pricing.json"
    
    print_section("🚀 GEMINI 2.0 FLASH LITE COST ESTIMATOR FOR HR BOT")
    
    print("\n📋 Configuration:")
    print(f"Pricing file: {pricing_path}")
    print(f"Model: gemini/gemini-2.0-flash-lite-001")
    
    # Get current USD to INR rate (you can update this)
    current_fx_rate = 83.50  # Current approximate rate
    
    # Initialize estimator
    estimator = CostEstimator(
        usd_to_inr=current_fx_rate,
        pricing_overrides_path=str(pricing_path)
    )
    
    print(f"Exchange Rate: ₹{estimator.usd_to_inr} per USD")
    print(f"Available models: {', '.join(estimator.available_models())}")
    
    # Define usage scenarios - UPDATED WITH ACTUAL VALIDATED TOKEN USAGE
    # Based on real-world measurements from validate_token_usage.py
    # Your RAG system uses TOP_K=12 with CHUNK_SIZE=700, generating 15K-30K input tokens
    scenarios = [
        {
            "name": "LIGHT USAGE (Basic queries, minimal RAG context)",
            "profile": UsageProfile(
                queries_per_user=50,
                input_tokens_per_query=18_000,  # Validated: 17K-21K actual
                output_tokens_per_query=1_500,
            ),
            "markup": 20,
            "contingency": 10,
        },
        {
            "name": "STANDARD COMPLEX (Typical enterprise usage)",
            "profile": UsageProfile(
                queries_per_user=120,
                input_tokens_per_query=25_000,  # Validated: 20K-31K actual
                output_tokens_per_query=2_500,
            ),
            "markup": 20,
            "contingency": 10,
        },
        {
            "name": "VERY COMPLEX (Heavy RAG + multi-turn conversations)",
            "profile": UsageProfile(
                queries_per_user=200,
                input_tokens_per_query=32_000,  # Validated: 31K+ actual
                output_tokens_per_query=4_000,
            ),
            "markup": 25,
            "contingency": 15,
        },
        {
            "name": "ENTERPRISE HEAVY (Maximum load + conversation history)",
            "profile": UsageProfile(
                queries_per_user=400,  # More realistic for heavy users
                input_tokens_per_query=35_000,  # With conversation history
                output_tokens_per_query=5_000,
            ),
            "markup": 25,
            "contingency": 20,
        },
    ]
    
    print_section("💼 COST ESTIMATES FOR DIFFERENT USAGE SCENARIOS")
    
    all_quotes = []
    for scenario in scenarios:
        quote = estimator.quote_per_user(
            profile=scenario["profile"],
            markup_percentage=scenario["markup"],
            contingency_percentage=scenario["contingency"],
        )
        all_quotes.append((scenario["name"], quote))
        print_breakdown(quote, scenario["name"])
    
    # Summary recommendations
    print_section("📌 PRICING RECOMMENDATIONS FOR CLIENT")
    
    print("\n🎯 Recommended Pricing Tiers (Per User/Month):\n")
    
    for name, quote in all_quotes:
        print(f"• {name:.<50} ₹{quote.quoted_inr:>10,.2f}")
        print(f"  └─ Per Query: ₹{quote.per_query_inr:.2f}")
        print()
    
    # Calculate annual costs
    print_section("📅 ANNUAL COST PROJECTIONS (Per User)")
    
    for name, quote in all_quotes:
        annual = quote.quoted_inr * 12
        print(f"• {name:.<50} ₹{annual:>12,.2f}/year")
    
    # Multi-user calculations
    print_section("👥 MULTI-USER COST ESTIMATES (VERY COMPLEX Scenario)")
    
    very_complex_quote = all_quotes[2][1]  # VERY COMPLEX
    user_counts = [10, 50, 100, 500, 1000]
    
    print("\nMonthly Costs:")
    for users in user_counts:
        total = very_complex_quote.quoted_inr * users
        print(f"  {users:>4} users: ₹{total:>12,.2f}")
    
    print("\nAnnual Costs:")
    for users in user_counts:
        total = very_complex_quote.quoted_inr * users * 12
        print(f"  {users:>4} users: ₹{total:>12,.2f}")
    
    # Key insights
    print_section("💡 KEY INSIGHTS & RECOMMENDATIONS")
    
    print("""
1. PRICING STRATEGY:
   • Light Usage: For basic HR queries, minimal load
   • Standard Complex: Recommended for typical enterprise deployment
   • Very Complex: For heavy usage with complex multi-step queries
   • Enterprise Heavy: Extreme edge case, maximum theoretical load

2. MARKUP EXPLANATION:
   • 20-25%: Covers operational costs, support, infrastructure
   • 10-20% Contingency: Protects against price fluctuations & usage spikes

3. COST DRIVERS:
   • Input tokens: Context, history, document content
   • Output tokens: Detailed responses, recommendations
   • Query complexity: Multi-agent reasoning increases token usage

4. RECOMMENDATIONS FOR CLIENT QUOTE:
   • Use STANDARD COMPLEX as baseline for normal operations
   • Use VERY COMPLEX for SLA guarantees with heavy usage
   • Build in annual adjustment clause for FX fluctuations
   • Consider volume discounts for multi-user deployments

5. RISK MITIGATION:
   • Monitor actual usage vs. estimates monthly
   • Set usage caps per user to prevent runaway costs
   • Implement query optimization to reduce token consumption
   • Regular pricing reviews (quarterly recommended)
    """)
    
    print_section("✅ COST ESTIMATION COMPLETE")
    print("\n📊 All calculations use official Gemini 2.0 Flash Lite pricing")
    print("💰 Estimates include markup and contingency for profitability")
    print("🔄 Exchange rate: ₹{:.2f} per USD (update as needed)\n".format(current_fx_rate))


if __name__ == "__main__":
    main()
