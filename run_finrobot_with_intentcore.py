"""
Real FinRobot Agent with IntentCore Integration

This shows how to use IntentCore with a real FinRobot agent.

Setup:
1. Start backend: cd intentcore/ui/backend && python3 -m uvicorn api:app --reload
2. Start frontend: cd intentcore/ui/frontend && npm run dev
3. Run this script: python3 run_finrobot_with_intentcore.py
"""

import autogen
from finrobot.utils import register_keys_from_json
from finrobot.agents.workflow import SingleAssistant

# Import IntentCore
from intentcore import IntentCoreRuntime, FinRobotBridge


def main():
    """Run FinRobot Market Analyst with IntentCore governance."""

    print("="*80)
    print("FINROBOT + INTENTCORE: Live Agent Integration")
    print("="*80)
    print()
    print("Make sure you have:")
    print("  1. Backend API running: http://127.0.0.1:8000")
    print("  2. Frontend UI running: http://localhost:3000")
    print()
    print("The agent will run, and high-stakes decisions will:")
    print("  - Appear in the Review Queue UI")
    print("  - Wait for human approval")
    print("  - Execute based on your decision")
    print()

    # 1. Configure FinRobot
    llm_config = {
        "config_list": autogen.config_list_from_json(
            "OAI_CONFIG_LIST",
            filter_dict={"model": ["gpt-4-0125-preview"]},
        ),
        "timeout": 120,
        "temperature": 0,
    }

    # Register API keys for FinRobot tools
    register_keys_from_json("config_api_keys")

    # 2. Initialize IntentCore
    print("Initializing IntentCore...")
    runtime = IntentCoreRuntime(db_path="intentcore.db")
    bridge = FinRobotBridge(runtime=runtime, block_mode="review")
    print("✓ IntentCore ready")
    print()

    # 3. Create FinRobot agent
    print("Creating FinRobot Market Analyst agent...")
    agent = SingleAssistant(
        "Market_Analyst",
        llm_config,
        human_input_mode="NEVER",  # Agent runs autonomously
    )
    print("✓ Agent created")
    print()

    # 4. Define the task
    company = "NVDA"
    task = f"""
    Analyze {company}'s current position in our portfolio and recommend rebalancing actions.

    Context:
    - Current portfolio: $875M total
    - {company} position: $280M (32% of portfolio)
    - Policy maximum: 25% per position
    - Earnings announcement: Tomorrow

    Provide your analysis and recommendation.
    """

    # 5. Wrap agent with IntentCore
    print("Wrapping agent with IntentCore governance...")
    bridge.wrap_agent(
        agent.assistant,  # Wrap the underlying assistant
        task=task,
        high_stakes_functions=[
            "execute_*",  # Any function starting with execute_
            "trade_*",    # Any trading functions
            "sell_*",     # Sell functions
            "buy_*",      # Buy functions
        ]
    )
    print("✓ Agent wrapped - high-stakes actions will be intercepted")
    print()

    # 6. Set up review callback for CLI fallback
    def cli_review_callback(chain):
        """
        Fallback CLI review if portfolio manager hasn't reviewed in UI.
        In production, you'd typically just wait for UI review.
        """
        print("\n" + "="*80)
        print("INTENTCORE: REVIEW REQUIRED")
        print("="*80)
        print(f"Task: {chain.task}")
        print(f"Agent: {chain.agent_role}")
        print(f"Action: {chain.selected_action.get('function')}")
        print(f"Completeness: {chain.completeness_score:.1%}")
        print()
        print("This decision is now in the Review Queue.")
        print("Go to: http://localhost:3000")
        print()

        # In production, you could:
        # - Wait for UI review (poll database)
        # - Send notification to portfolio manager
        # - Use timeout with auto-reject

        # For this demo, we'll use CLI input as fallback
        decision = input("Decision (approve/reject) or 'ui' to check UI: ").strip().lower()

        if decision == 'ui':
            print("\nPlease make your decision in the UI, then come back here.")
            input("Press Enter after you've made your decision in the UI...")

            # Check database for decision
            updated_chain = runtime.db.get_reasoning_chain(chain.chain_id)
            if updated_chain.human_decision:
                return {
                    "reviewer_id": updated_chain.reviewer_id,
                    "decision": updated_chain.human_decision,
                    "rationale": updated_chain.human_rationale,
                    "modification": updated_chain.human_modification,
                }
            else:
                print("No decision found in UI. Using CLI...")
                decision = input("Decision (approve/reject): ").strip().lower()

        return {
            "reviewer_id": "cli_user",
            "decision": "approved" if decision == "approve" else "rejected",
            "rationale": "CLI review",
        }

    bridge.set_review_callback(cli_review_callback)

    # 7. Run the agent
    print("="*80)
    print("AGENT STARTING")
    print("="*80)
    print()
    print(f"Task: {task}")
    print()
    print("The agent will now analyze and may propose actions.")
    print("If it proposes high-stakes actions, they will appear in the UI.")
    print()

    try:
        agent.chat(task)
        print()
        print("="*80)
        print("AGENT COMPLETED")
        print("="*80)
        print()
        print("Check the UI to see the decision history:")
        print("  http://localhost:3000/history")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nThis might be because:")
        print("  1. No API keys configured")
        print("  2. Action was blocked by governance")
        print("  3. Human review was rejected")


if __name__ == "__main__":
    main()
