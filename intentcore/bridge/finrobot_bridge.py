"""
FinRobot Bridge

Integration layer between FinRobot agents and IntentCore runtime.

This bridge:
1. Intercepts agent tool calls
2. Extracts reasoning from conversation
3. Enforces governance
4. Manages human reviews
5. Records execution results

Designed for minimal modifications to FinRobot code.
"""

from typing import Dict, List, Any, Optional, Callable, TYPE_CHECKING
from functools import wraps

# Optional imports - only needed when actually wrapping agents
if TYPE_CHECKING:
    import autogen
    from autogen import ConversableAgent
else:
    try:
        import autogen
        from autogen import ConversableAgent
    except ImportError:
        autogen = None
        ConversableAgent = None

from ..core.runtime import IntentCoreRuntime
from ..core.reasoning_chain import ReasoningChain


class FinRobotBridge:
    """
    Bridge between FinRobot agents and IntentCore.

    Usage:
        bridge = FinRobotBridge()

        # Wrap an agent
        agent = FinRobot("Market_Analyst", llm_config)
        bridge.wrap_agent(agent, task="Analyze NVDA portfolio")

        # Or use as context manager
        with bridge.intercept_agent(agent, task="..."):
            agent.chat(message)
    """

    def __init__(
        self,
        runtime: Optional[IntentCoreRuntime] = None,
        auto_approve_below: Optional[float] = None,
        block_mode: str = "review",  # review, monitor, enforce
    ):
        """
        Initialize FinRobot bridge.

        Args:
            runtime: IntentCore runtime instance
            auto_approve_below: Auto-approve trades below this amount
            block_mode:
                - review: Block and wait for human review
                - monitor: Log but don't block
                - enforce: Block on violations, auto-approve otherwise
        """
        self.runtime = runtime or IntentCoreRuntime()
        self.auto_approve_below = auto_approve_below
        self.block_mode = block_mode
        self._review_callback: Optional[Callable] = None

    def set_review_callback(self, callback: Callable):
        """
        Set callback for human review requests.

        Callback signature:
            def review_callback(chain: ReasoningChain) -> Dict[str, Any]:
                # Return: {"decision": "approved/rejected", "rationale": "...", "modification": {...}}
        """
        self._review_callback = callback

    def wrap_agent(
        self,
        agent: Any,  # ConversableAgent when available
        task: str,
        high_stakes_functions: Optional[List[str]] = None,
    ):
        """
        Wrap a FinRobot agent to intercept tool calls.

        Args:
            agent: FinRobot agent to wrap
            task: Task description for context
            high_stakes_functions: List of function names that require governance
                                  (default: all functions starting with "execute_", "trade_", "sell_", "buy_")
        """
        # Store original hook
        original_hook = agent._hookspecs.get("before_function_call")

        # Determine high-stakes functions
        if high_stakes_functions is None:
            high_stakes_functions = self._get_default_high_stakes_functions()

        def intentcore_hook(sender, recipient, messages, sender_name, recipient_name,  **kwargs):
            """Hook that runs before every function call."""

            # Call original hook if it exists
            if original_hook:
                original_hook(sender, recipient, messages, sender_name, recipient_name, **kwargs)

            # Check if this is a high-stakes function
            if messages and len(messages) > 0:
                last_message = messages[-1]

                # Check for tool calls
                if "tool_calls" in last_message:
                    for tool_call in last_message["tool_calls"]:
                        function_name = tool_call.get("function", {}).get("name", "")

                        # Only intercept high-stakes functions
                        if self._is_high_stakes(function_name, high_stakes_functions):
                            # Process through IntentCore
                            self._process_tool_call(
                                agent_id=agent.name,
                                agent_role=agent.name,
                                task=task,
                                messages=messages,
                                tool_call=tool_call,
                            )

        # Register hook
        agent.register_hook("before_function_call", intentcore_hook)

    def intercept_tool_call(
        self,
        agent_id: str,
        agent_role: str,
        task: str,
        messages: List[Dict[str, Any]],
        tool_call: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Intercept and process a tool call through IntentCore.

        This is the main entry point for governance.

        Args:
            agent_id: Agent identifier
            agent_role: Agent role
            task: Task description
            messages: Conversation history
            tool_call: Tool call to process

        Returns:
            Decision dict with:
            - allowed (bool): Whether to execute
            - chain_id (str): Reasoning chain ID
            - modification (dict): Modified parameters if any
            - reason (str): Decision rationale
        """
        # Process through IntentCore
        result = self.runtime.process_decision(
            agent_id=agent_id,
            agent_role=agent_role,
            task=task,
            messages=messages,
            tool_call=tool_call,
        )

        chain = result["reasoning_chain"]
        governance = result["governance_result"]

        # Handle based on mode
        if self.block_mode == "monitor":
            # Just log, don't block
            return {
                "allowed": True,
                "chain_id": chain.chain_id,
                "reason": "Monitor mode: logged but not blocked",
            }

        elif self.block_mode == "enforce":
            # Block on violations, auto-approve otherwise
            if governance.decision == "rejected":
                return {
                    "allowed": False,
                    "chain_id": chain.chain_id,
                    "reason": governance.reasoning,
                }
            else:
                return {
                    "allowed": True,
                    "chain_id": chain.chain_id,
                    "reason": governance.reasoning,
                }

        elif self.block_mode == "review":
            # Block and wait for human review if needed
            if governance.requires_review:
                # Request human review
                human_decision = self._request_human_review(chain)

                # Record decision
                self.runtime.submit_human_decision(
                    chain_id=chain.chain_id,
                    reviewer_id=human_decision.get("reviewer_id", "unknown"),
                    decision=human_decision["decision"],
                    rationale=human_decision.get("rationale"),
                    modification=human_decision.get("modification"),
                )

                # Return result
                if human_decision["decision"] == "approved":
                    return {
                        "allowed": True,
                        "chain_id": chain.chain_id,
                        "modification": human_decision.get("modification"),
                        "reason": f"Human approved: {human_decision.get('rationale', '')}",
                    }
                else:
                    return {
                        "allowed": False,
                        "chain_id": chain.chain_id,
                        "reason": f"Human rejected: {human_decision.get('rationale', '')}",
                    }
            else:
                # Auto-approved
                return {
                    "allowed": True,
                    "chain_id": chain.chain_id,
                    "reason": "Auto-approved: all policy checks passed",
                }

    def _process_tool_call(
        self,
        agent_id: str,
        agent_role: str,
        task: str,
        messages: List[Dict[str, Any]],
        tool_call: Dict[str, Any],
    ):
        """Process tool call and potentially block execution."""

        result = self.intercept_tool_call(
            agent_id=agent_id,
            agent_role=agent_role,
            task=task,
            messages=messages,
            tool_call=tool_call,
        )

        if not result["allowed"]:
            # Block execution by raising exception
            raise ActionBlockedException(
                f"Action blocked by IntentCore: {result['reason']}\n"
                f"Chain ID: {result['chain_id']}"
            )

        # If modification, we'd need to update tool_call parameters
        # This requires deeper AutoGen integration
        if result.get("modification"):
            # TODO: Apply modification to tool_call
            pass

    def _request_human_review(self, chain: ReasoningChain) -> Dict[str, Any]:
        """
        Request human review for a reasoning chain.

        Returns:
            Human decision dict
        """
        if self._review_callback:
            # Use callback
            return self._review_callback(chain)
        else:
            # Fallback: CLI review
            return self._cli_review(chain)

    def _cli_review(self, chain: ReasoningChain) -> Dict[str, Any]:
        """Simple CLI-based review interface."""

        print("\n" + "="*80)
        print("INTENTCORE: HUMAN REVIEW REQUIRED")
        print("="*80)
        print(chain.get_summary())
        print("="*80)

        # Get decision
        while True:
            decision = input("\nDecision (approve/reject/modify): ").strip().lower()
            if decision in ["approve", "reject", "modify"]:
                break
            print("Invalid decision. Please enter: approve, reject, or modify")

        rationale = input("Rationale: ").strip()

        modification = None
        if decision == "modify":
            print("\nCurrent parameters:")
            print(chain.selected_action.get("parameters", {}))
            # For demo, we'll skip complex modification input
            print("(Modification input not implemented in CLI demo)")

        return {
            "reviewer_id": "cli_reviewer",
            "decision": decision + "d",  # approved/rejected/modified
            "rationale": rationale,
            "modification": modification,
        }

    def _is_high_stakes(self, function_name: str, high_stakes_list: List[str]) -> bool:
        """Check if function is high-stakes."""
        # Exact match
        if function_name in high_stakes_list:
            return True

        # Prefix match (e.g., execute_*, trade_*)
        for pattern in high_stakes_list:
            if pattern.endswith("*") and function_name.startswith(pattern[:-1]):
                return True

        return False

    def _get_default_high_stakes_functions(self) -> List[str]:
        """Get default list of high-stakes function patterns."""
        return [
            "execute_*",  # Execution functions
            "trade_*",    # Trading functions
            "sell_*",     # Sell functions
            "buy_*",      # Buy functions
            "transfer_*", # Transfer functions
            "withdraw_*", # Withdrawal functions
        ]


class ActionBlockedException(Exception):
    """Exception raised when IntentCore blocks an action."""
    pass


# ===== Convenience Wrappers =====

def with_intentcore(
    task: str,
    runtime: Optional[IntentCoreRuntime] = None,
    block_mode: str = "review",
):
    """
    Decorator to wrap FinRobot agent execution with IntentCore.

    Usage:
        @with_intentcore(task="Analyze portfolio")
        def run_analysis(agent):
            agent.chat("Analyze NVDA position")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            bridge = FinRobotBridge(runtime=runtime, block_mode=block_mode)

            # Extract agent from args
            agent = args[0] if args else kwargs.get("agent")
            if agent:
                bridge.wrap_agent(agent, task=task)

            return func(*args, **kwargs)

        return wrapper
    return decorator
