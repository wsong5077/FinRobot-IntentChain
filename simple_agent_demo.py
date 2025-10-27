"""
Simple FinRobot + IntentCore Demo (No LLM API Required)

This simulates an agent decision without needing OpenAI API keys.
Perfect for testing the IntentCore UI integration.

Usage:
1. Terminal 1: cd intentcore/ui/backend && python3 -m uvicorn api:app --reload
2. Terminal 2: cd intentcore/ui/frontend && npm run dev
3. Terminal 3: python3 simple_agent_demo.py
4. Browser: Open http://localhost:3000 to review the decision
"""

import time
from intentcore import IntentCoreRuntime


def simulate_agent_decision():
    """
    Simulates a FinRobot agent making a high-stakes trading decision.
    This will appear in the UI for human review.
    """

    print("\n" + "="*80)
    print("SIMULATED AGENT: Making Trading Decision")
    print("="*80 + "\n")

    # Initialize IntentCore
    runtime = IntentCoreRuntime(db_path="intentcore.db")

    # Simulate agent conversation (like FinRobot would generate)
    messages = [
        {
            "role": "user",
            "content": "Review our tech portfolio concentration and recommend actions."
        },
        {
            "role": "assistant",
            "content": """
Analyzing portfolio concentration...

Current Situation:
Our technology sector allocation is at 38% of total portfolio ($333M out of $875M total AUM),
which exceeds our 35% sector maximum policy. The top holding is NVDA at $280M (32% of portfolio),
well above our 25% individual position limit.

Quantitative Analysis:
- Portfolio total: $875M
- Tech sector: $333M (38% - exceeds 35% limit)
- NVDA position: $280M (32% - exceeds 25% limit)
- Required NVDA reduction: Minimum $61M to reach 25% limit
- Recommended reduction: $75M to provide buffer

Market Context:
- NVDA trading at $487.50
- Q4 earnings tomorrow (high event risk)
- Recent volatility: 18.2% (elevated)
- Sector rotation signals emerging

Options Considered:
1. Reduce NVDA by minimum ($61M) - Meets policy but no buffer
2. Reduce NVDA by $75M - Provides buffer, reduces earnings risk
3. Wait until post-earnings - Risk of further concentration if stock rises
4. Diversify within tech - Doesn't address NVDA concentration

Risks:
- Execution risk: Large position reduction may impact price
- Timing risk: Pre-earnings trade increases uncertainty
- Opportunity risk: May miss upside if earnings beat expectations
- Compliance risk: Current position violates portfolio policy

Rationale:
Given the clear policy violation (32% vs 25% max), elevated pre-earnings risk, and
fiduciary duty to maintain diversification, I recommend reducing NVDA position by $75M.
This brings us to 23.4% of portfolio, provides compliance buffer, and reduces event risk.

Executing trade: Sell $75M NVDA
"""
        },
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_trade_456",
                    "type": "function",
                    "function": {
                        "name": "execute_trade",
                        "arguments": '{"symbol": "NVDA", "action": "SELL", "amount": "$75M", "reason": "Reduce concentration and pre-earnings risk"}'
                    }
                }
            ]
        }
    ]

    # Process through IntentCore
    print("Agent proposing trade: Sell $75M NVDA")
    print("Submitting to IntentCore for review...\n")

    result = runtime.process_decision(
        agent_id="portfolio_agent_002",
        agent_role="Portfolio_Risk_Manager",
        task="Review tech portfolio concentration and recommend rebalancing",
        messages=messages,
        tool_call=messages[-1]["tool_calls"][0],
    )

    chain = result["reasoning_chain"]
    governance = result["governance_result"]

    print("✓ Reasoning extracted")
    print(f"  - Completeness: {chain.completeness_score:.1%}")
    print(f"  - Risks identified: {len(chain.risks)}")
    print(f"  - Governance decision: {governance.decision}")
    print(f"  - Requires review: {governance.requires_review}")
    print()

    if governance.requires_review:
        print("="*80)
        print("DECISION AWAITING HUMAN REVIEW")
        print("="*80)
        print()
        print("This decision is now in the Review Queue!")
        print()
        print("📊 Open the UI: http://localhost:3000")
        print()
        print("You will see:")
        print("  • Review Queue: The $75M NVDA trade awaiting approval")
        print("  • Click on it to see complete reasoning")
        print("  • Approve, Reject, or Modify the trade")
        print()
        print("Chain ID:", chain.chain_id)
        print()
        print("Waiting for your decision in the UI...")
        print("(You can also press Ctrl+C to exit)")
        print()

        # Poll for human decision
        start_time = time.time()
        while True:
            # Check if decision has been made
            updated_chain = runtime.db.get_reasoning_chain(chain.chain_id)

            if updated_chain.human_decision:
                print()
                print("="*80)
                print("DECISION RECEIVED FROM UI")
                print("="*80)
                print()
                print(f"Reviewer: {updated_chain.reviewer_id}")
                print(f"Decision: {updated_chain.human_decision.upper()}")
                print(f"Rationale: {updated_chain.human_rationale}")

                if updated_chain.human_modification:
                    print(f"Modification: {updated_chain.human_modification}")

                print()

                if updated_chain.human_decision == "approved":
                    print("✅ Trade APPROVED - Agent can execute")

                    # Simulate execution
                    runtime.record_execution(
                        chain_id=chain.chain_id,
                        status="completed",
                        result={
                            "executed_amount": updated_chain.human_modification.get("amount", "$75M") if updated_chain.human_modification else "$75M",
                            "shares_sold": 153_846,
                            "avg_price": "$487.25",
                            "execution_time": "18.7s",
                            "slippage": "0.03%",
                        }
                    )
                    print("✅ Trade executed successfully")

                else:
                    print("❌ Trade REJECTED - Agent will not execute")

                break

            # Timeout after 5 minutes
            if time.time() - start_time > 300:
                print("\n⏱️  Timeout: No decision received within 5 minutes")
                print("The decision is still pending in the UI.")
                break

            # Wait 2 seconds before checking again
            time.sleep(2)

    else:
        print("✅ Decision auto-approved (no review required)")

    print()
    print("="*80)
    print("View full history in UI: http://localhost:3000/history")
    print("="*80)


if __name__ == "__main__":
    print("\n🤖 IntentCore + FinRobot: Simple Agent Demo")
    print("\nThis demonstrates IntentCore governance with a simulated agent.")
    print("The decision will appear in the UI for human review.\n")

    input("Press Enter to start (make sure backend and frontend are running)...")

    simulate_agent_decision()
