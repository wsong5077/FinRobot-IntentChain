"""
Database Manager

Handles all database operations for IntentCore.
Uses SQLite for demo/production-ready storage.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4
from contextlib import contextmanager

from ..core.reasoning_chain import ReasoningChain


class DatabaseManager:
    """
    Manages SQLite database for IntentCore.

    Handles:
    - Reasoning chain storage
    - Pattern tracking
    - Review queue
    - Audit logs
    - Metrics
    """

    def __init__(self, db_path: str = "intentcore.db"):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self):
        """Ensure database schema exists."""
        schema_path = Path(__file__).parent / "schema.sql"

        with self._get_connection() as conn:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
                conn.executescript(schema_sql)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
        finally:
            conn.close()

    # ===== Reasoning Chain Operations =====

    def save_reasoning_chain(self, chain: ReasoningChain) -> str:
        """
        Save reasoning chain to database.

        Returns:
            chain_id
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO reasoning_chains (
                    chain_id, timestamp, agent_id, agent_role,
                    task, conversation_history,
                    situation, quantitative_analysis, options, selected_action, rationale, risks,
                    completeness_score, missing_components,
                    policy_results, requires_review, governance_decision,
                    reviewer_id, review_timestamp, human_decision, human_rationale, human_modification,
                    execution_status, execution_result, execution_timestamp,
                    pattern_id, template_id, confidence_score
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?
                )
                """,
                (
                    chain.chain_id,
                    chain.timestamp.isoformat(),
                    chain.agent_id,
                    chain.agent_role,
                    chain.task,
                    json.dumps(chain.conversation_history),
                    chain.situation,
                    json.dumps(chain.quantitative_analysis),
                    json.dumps(chain.options),
                    json.dumps(chain.selected_action),
                    chain.rationale,
                    json.dumps(chain.risks),
                    chain.completeness_score,
                    json.dumps(chain.missing_components),
                    json.dumps(chain.policy_results),
                    chain.requires_review,
                    chain.governance_decision,
                    chain.reviewer_id,
                    chain.review_timestamp.isoformat() if chain.review_timestamp else None,
                    chain.human_decision,
                    chain.human_rationale,
                    json.dumps(chain.human_modification) if chain.human_modification else None,
                    chain.execution_status,
                    json.dumps(chain.execution_result) if chain.execution_result else None,
                    chain.execution_timestamp.isoformat() if chain.execution_timestamp else None,
                    chain.pattern_id,
                    chain.template_id,
                    chain.confidence_score,
                ),
            )
            conn.commit()

        return chain.chain_id

    def get_reasoning_chain(self, chain_id: str) -> Optional[ReasoningChain]:
        """Get reasoning chain by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM reasoning_chains WHERE chain_id = ?",
                (chain_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_reasoning_chain(row)

    def update_reasoning_chain(self, chain: ReasoningChain):
        """Update existing reasoning chain."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE reasoning_chains SET
                    governance_decision = ?,
                    reviewer_id = ?,
                    review_timestamp = ?,
                    human_decision = ?,
                    human_rationale = ?,
                    human_modification = ?,
                    execution_status = ?,
                    execution_result = ?,
                    execution_timestamp = ?
                WHERE chain_id = ?
                """,
                (
                    chain.governance_decision,
                    chain.reviewer_id,
                    chain.review_timestamp.isoformat() if chain.review_timestamp else None,
                    chain.human_decision,
                    chain.human_rationale,
                    json.dumps(chain.human_modification) if chain.human_modification else None,
                    chain.execution_status,
                    json.dumps(chain.execution_result) if chain.execution_result else None,
                    chain.execution_timestamp.isoformat() if chain.execution_timestamp else None,
                    chain.chain_id,
                ),
            )
            conn.commit()

    def query_reasoning_chains(
        self,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        requires_review: Optional[bool] = None,
        limit: int = 100,
    ) -> List[ReasoningChain]:
        """Query reasoning chains with filters."""
        query = "SELECT * FROM reasoning_chains WHERE 1=1"
        params = []

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        if requires_review is not None:
            query += " AND requires_review = ?"
            params.append(requires_review)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_reasoning_chain(row) for row in rows]

    def _row_to_reasoning_chain(self, row: sqlite3.Row) -> ReasoningChain:
        """Convert database row to ReasoningChain object."""
        return ReasoningChain(
            chain_id=row["chain_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            agent_id=row["agent_id"],
            agent_role=row["agent_role"],
            task=row["task"],
            conversation_history=json.loads(row["conversation_history"]) if row["conversation_history"] else [],
            situation=row["situation"] or "",
            quantitative_analysis=json.loads(row["quantitative_analysis"]) if row["quantitative_analysis"] else {},
            options=json.loads(row["options"]) if row["options"] else [],
            selected_action=json.loads(row["selected_action"]) if row["selected_action"] else {},
            rationale=row["rationale"] or "",
            risks=json.loads(row["risks"]) if row["risks"] else [],
            completeness_score=row["completeness_score"],
            missing_components=json.loads(row["missing_components"]) if row["missing_components"] else [],
            policy_results=json.loads(row["policy_results"]) if row["policy_results"] else {},
            requires_review=bool(row["requires_review"]),
            governance_decision=row["governance_decision"],
            reviewer_id=row["reviewer_id"],
            review_timestamp=datetime.fromisoformat(row["review_timestamp"]) if row["review_timestamp"] else None,
            human_decision=row["human_decision"],
            human_rationale=row["human_rationale"],
            human_modification=json.loads(row["human_modification"]) if row["human_modification"] else None,
            execution_status=row["execution_status"],
            execution_result=json.loads(row["execution_result"]) if row["execution_result"] else None,
            execution_timestamp=datetime.fromisoformat(row["execution_timestamp"]) if row["execution_timestamp"] else None,
            pattern_id=row["pattern_id"],
            template_id=row["template_id"],
            confidence_score=row["confidence_score"],
        )

    # ===== Review Queue Operations =====

    def add_to_review_queue(
        self,
        chain_id: str,
        priority: str = "normal",
        assigned_to: Optional[str] = None,
    ) -> str:
        """Add reasoning chain to review queue."""
        queue_id = str(uuid4())

        # Calculate priority score (for ordering)
        priority_scores = {"urgent": 100, "high": 75, "normal": 50, "low": 25}
        priority_score = priority_scores.get(priority, 50)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO review_queue (
                    queue_id, chain_id, priority, priority_score, assigned_to
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (queue_id, chain_id, priority, priority_score, assigned_to),
            )
            conn.commit()

        return queue_id

    def get_pending_reviews(self, assigned_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending reviews from queue."""
        query = "SELECT * FROM active_reviews WHERE 1=1"
        params = []

        if assigned_to:
            query += " AND assigned_to = ?"
            params.append(assigned_to)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def complete_review(self, queue_id: str):
        """Mark review as completed."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE review_queue
                SET status = 'completed', completed_at = ?
                WHERE queue_id = ?
                """,
                (datetime.utcnow().isoformat(), queue_id),
            )
            conn.commit()

    # ===== Audit Log Operations =====

    def log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        chain_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Log an event to audit trail."""
        log_id = str(uuid4())

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_log (
                    log_id, event_type, event_data, chain_id, user_id
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (log_id, event_type, json.dumps(event_data), chain_id, user_id),
            )
            conn.commit()

    # ===== Metrics Operations =====

    def get_daily_metrics(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily metrics."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM daily_metrics
                ORDER BY date DESC
                LIMIT ?
                """,
                (days,)
            )
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_decisions,
                    SUM(CASE WHEN requires_review THEN 1 ELSE 0 END) as total_reviews,
                    SUM(CASE WHEN human_decision = 'approved' THEN 1 ELSE 0 END) as total_approved,
                    SUM(CASE WHEN human_decision = 'rejected' THEN 1 ELSE 0 END) as total_rejected,
                    AVG(completeness_score) as avg_completeness
                FROM reasoning_chains
                """
            )
            row = cursor.fetchone()

        return dict(row) if row else {}
