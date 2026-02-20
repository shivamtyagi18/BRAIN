"""
Working memory — conversation buffer for short-term context.

Models the Dorsolateral PFC's working memory function: holds recent
conversation turns so all agents have conversational continuity.
"""

from typing import List, Tuple


class WorkingMemory:
    """In-memory sliding window of recent conversation turns."""

    def __init__(self, max_turns: int = 15):
        self.max_turns = max_turns
        self._turns: List[Tuple[str, str]] = []

    def add_turn(self, user_message: str, brain_response: str):
        """Record a conversation turn (user message + brain response)."""
        self._turns.append((user_message, brain_response))
        if len(self._turns) > self.max_turns:
            self._turns = self._turns[-self.max_turns:]

    def get_context(self, last_n: int = 10) -> str:
        """Return formatted recent turns for agent injection.

        Returns an empty string if no conversation history exists.
        """
        recent = self._turns[-last_n:]
        if not recent:
            return ""

        lines = []
        for user_msg, brain_resp in recent:
            lines.append(f"User: {user_msg}")
            lines.append(f"Brain: {brain_resp}")

        return "\n".join(lines)

    def clear(self):
        """Reset conversation history."""
        self._turns.clear()

    @property
    def turn_count(self) -> int:
        return len(self._turns)
