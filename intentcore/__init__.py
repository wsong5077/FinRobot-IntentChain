"""
IntentCore: Runtime Governance for High-Stakes AI Agents

MVP Focus: Proving we can extract structured reasoning from live agent executions.

Core Innovation:
- Zero-modification interception of FinRobot agents
- Structured reasoning extraction (80%+ completeness)
- Low overhead (<100ms)
- Clean SDK swap interface

Built for FinRobot integration.
"""

__version__ = "0.1.0-mvp"

# Core Components
from .core.reasoning_chain import ReasoningChain, ValidationResult, GovernanceResult
from .core.extractor import ReasoningExtractor
from .core.interceptor import ReasoningInterceptor, IntentCoreSDK
from .core.runtime import IntentCoreRuntime

# Wrappers (KEY: This is the main integration point)
from .wrappers.finrobot_wrapper import (
    FinRobotReasoningWrapper,
    with_reasoning_capture,
    capture_reasoning_from_agent,
)

# Legacy bridge (for full demo)
from .bridge.finrobot_bridge import FinRobotBridge

__all__ = [
    # Data Models
    "ReasoningChain",
    "ValidationResult",
    "GovernanceResult",

    # Core Extraction (MVP Focus)
    "ReasoningInterceptor",
    "ReasoningExtractor",

    # Wrappers (Recommended for FinRobot)
    "FinRobotReasoningWrapper",
    "with_reasoning_capture",
    "capture_reasoning_from_agent",

    # Full Runtime (Optional)
    "IntentCoreRuntime",
    "FinRobotBridge",

    # SDK Interface
    "IntentCoreSDK",
]
