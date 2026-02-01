"""Item selection types and helpers.

Problem 2: Create explicit SelectionRequest dataclass instead of using
dict with implicit contract.
"""
from dataclasses import dataclass
from typing import List, Any, Optional


@dataclass
class SelectionRequest:
    """
    Request for item selection from the player.
    
    Attributes:
        selection_type: Type of selection ('food', 'weapon', 'elixir', 'scroll')
        items: List of items to choose from
        title: Dialog title to display
        allow_zero: Whether player can select 0 to cancel/unequip
    """
    selection_type: str
    items: List[Any]
    title: str
    allow_zero: bool
    
    def to_dict(self) -> dict:
        """Convert to dict for serialization (save/load compatibility)."""
        return {
            'type': self.selection_type,
            'items': self.items,
            'title': self.title,
            'allow_zero': self.allow_zero
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Optional['SelectionRequest']:
        """Create SelectionRequest from dict (save/load compatibility)."""
        if data is None:
            return None
        return cls(
            selection_type=data.get('type', ''),
            items=data.get('items', []),
            title=data.get('title', ''),
            allow_zero=data.get('allow_zero', False)
        )
