"""
MiniAdventure — interface all adventures must implement.
"""

from abc import ABC, abstractmethod


class MiniAdventure(ABC):
    NAME = "Unnamed"
    DESCRIPTION = ""

    @abstractmethod
    def start(self, players: list[dict]) -> None:
        """Initialize and begin the adventure."""

    @abstractmethod
    def handle_input(self, player_index: int, action: str) -> str:
        """Process a player action. Return a message."""

    @abstractmethod
    def get_state(self) -> dict:
        """Return current game state as a dict."""

    @abstractmethod
    def is_over(self) -> bool:
        """Return True when the adventure has ended."""

    @abstractmethod
    def get_result(self) -> str:
        """Return a win/lose/complete message."""