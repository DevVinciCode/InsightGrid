"""
In-memory conversation state keyed by session_id. A follow-up question
modifies the existing AnalyticalIntent (via IntentExtractor.extract_followup)
rather than starting over.

This is intentionally in-process/in-memory for the MVP (single backend
instance, demo use). Swapping to Redis for multi-instance deployments is a
one-file change — implement the same get/set interface.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models.intent import AnalyticalIntent


@dataclass
class Turn:
    question: str
    intent: AnalyticalIntent
    sql: str
    chart_type: str


@dataclass
class ConversationSession:
    session_id: str
    turns: list[Turn] = field(default_factory=list)

    @property
    def current_intent(self) -> AnalyticalIntent | None:
        return self.turns[-1].intent if self.turns else None

    def add_turn(self, turn: Turn) -> None:
        self.turns.append(turn)


class ConversationStore:
    """Simple in-memory session store. Swap for Redis/DB-backed store to scale."""

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSession] = {}

    def get_or_create(self, session_id: str) -> ConversationSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationSession(session_id=session_id)
        return self._sessions[session_id]

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


conversation_store = ConversationStore()
