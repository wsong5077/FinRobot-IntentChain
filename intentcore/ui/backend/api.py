"""
IntentCore API Server

FastAPI server that provides REST API for the React UI.

Endpoints:
- GET /api/reviews/pending - Get pending reviews
- GET /api/chains/{chain_id} - Get reasoning chain details
- POST /api/reviews/{chain_id}/decision - Submit review decision
- GET /api/metrics - Get system metrics
- GET /api/chains - Get reasoning chain history
"""

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from ...core.runtime import IntentCoreRuntime
except ImportError:
    # Support running via `uvicorn api:app` where package context is missing
    # api.py -> backend -> ui -> intentcore -> project_root
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from intentcore.core.runtime import IntentCoreRuntime


# ===== API Models =====

class ReviewDecision(BaseModel):
    """Review decision submission."""
    reviewer_id: str
    decision: str  # approved, rejected, modified
    rationale: Optional[str] = None
    modification: Optional[Dict[str, Any]] = None


class ExecutionResult(BaseModel):
    """Execution result submission."""
    status: str  # completed, failed
    result: Optional[Dict[str, Any]] = None


# ===== FastAPI App =====

app = FastAPI(
    title="IntentCore API",
    description="Runtime governance for AI agents",
    version="0.1.0",
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize IntentCore runtime
# Use absolute path to ensure we use the same DB as demo script
db_path = Path(__file__).resolve().parents[3] / "intentcore.db"
runtime = IntentCoreRuntime(db_path=str(db_path))


# ===== API Endpoints =====

@app.get("/")
def root():
    """API root."""
    return {
        "service": "IntentCore API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/api/reviews/pending")
def get_pending_reviews(reviewer_id: Optional[str] = None):
    """
    Get pending reviews from queue.

    Query params:
        reviewer_id: Optional filter for specific reviewer
    """
    reviews = runtime.get_pending_reviews(reviewer_id=reviewer_id)

    # Enrich with reasoning chain data
    enriched = []
    for review in reviews:
        chain = runtime.db.get_reasoning_chain(review["chain_id"])
        if chain:
            enriched.append({
                "queue_id": review["queue_id"],
                "priority": review["priority"],
                "queued_at": review["queued_at"],
                "chain": chain.to_dict(),
            })

    return enriched


@app.get("/api/chains/{chain_id}")
def get_chain(chain_id: str):
    """Get reasoning chain by ID."""
    chain = runtime.db.get_reasoning_chain(chain_id)

    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")

    return chain.to_dict()


@app.post("/api/reviews/{chain_id}/decision")
def submit_review_decision(chain_id: str, decision: ReviewDecision):
    """
    Submit review decision for a reasoning chain.

    Body:
        reviewer_id: Reviewer identifier
        decision: approved/rejected/modified
        rationale: Optional reasoning
        modification: Optional parameter modifications
    """
    try:
        chain = runtime.submit_human_decision(
            chain_id=chain_id,
            reviewer_id=decision.reviewer_id,
            decision=decision.decision,
            rationale=decision.rationale,
            modification=decision.modification,
        )

        return {
            "success": True,
            "chain_id": chain_id,
            "decision": decision.decision,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chains/{chain_id}/execution")
def record_execution(chain_id: str, execution: ExecutionResult):
    """
    Record execution result for a reasoning chain.

    Body:
        status: completed/failed
        result: Optional execution result data
    """
    try:
        runtime.record_execution(
            chain_id=chain_id,
            status=execution.status,
            result=execution.result,
        )

        return {
            "success": True,
            "chain_id": chain_id,
            "status": execution.status,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chains")
def get_chains(
    agent_id: Optional[str] = None,
    limit: int = 100,
    requires_review: Optional[bool] = None,
):
    """
    Query reasoning chains.

    Query params:
        agent_id: Filter by agent
        limit: Max results (default 100)
        requires_review: Filter by review requirement
    """
    chains = runtime.db.query_reasoning_chains(
        agent_id=agent_id,
        limit=limit,
        requires_review=requires_review,
    )

    return [chain.to_dict() for chain in chains]


@app.get("/api/metrics")
def get_metrics():
    """Get system metrics."""
    return runtime.get_metrics()


@app.get("/api/metrics/summary")
def get_summary_stats():
    """Get summary statistics."""
    return runtime.db.get_summary_stats()


# ===== Run Server =====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
