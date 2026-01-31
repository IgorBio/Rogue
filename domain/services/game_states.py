"""
Game state management using a finite state machine.

REFACTORING NOTE (Step 2.1):
- Replaces scattered boolean flags (game_over, victory, player_asleep) with explicit states
- Ensures only valid state transitions occur
- Simplifies game logic and makes state management explicit
- All states are now first-class concepts with clear semantics
"""

from enum import Enum, auto
from typing import Set


class GameState(Enum):
    """Enumeration of all possible game states."""
    INITIALIZING = auto()      # Game is initializing, player cannot act
    PLAYING = auto()           # Normal gameplay, player can act
    PLAYER_ASLEEP = auto()     # Player affected by sleep (snake mage effect)
    ITEM_SELECTION = auto()    # Waiting for item selection
    LEVEL_TRANSITION = auto()  # Transitioning between levels
    GAME_OVER = auto()         # Game ended (died)
    VICTORY = auto()           # Game won (all levels completed)


class StateMachine:
    """
    Finite state machine for managing game states.
    
    Enforces valid transitions and prevents invalid state changes.
    Transitions are defined in TRANSITIONS dict - only listed transitions are allowed.
    """
    
    # Define all valid state transitions
    TRANSITIONS = {
        GameState.INITIALIZING: [
            GameState.PLAYING,
        ],
        GameState.PLAYING: [
            GameState.PLAYER_ASLEEP,
            GameState.ITEM_SELECTION,
            GameState.LEVEL_TRANSITION,
            GameState.GAME_OVER,
            GameState.VICTORY,
        ],
        GameState.PLAYER_ASLEEP: [
            GameState.PLAYING,
            GameState.GAME_OVER,
        ],
        GameState.ITEM_SELECTION: [
            GameState.PLAYING,
            GameState.GAME_OVER,
        ],
        GameState.LEVEL_TRANSITION: [
            GameState.PLAYING,
            GameState.VICTORY,
        ],
        GameState.GAME_OVER: [
            # No transitions from game over - terminal state
        ],
        GameState.VICTORY: [
            # No transitions from victory - terminal state
        ],
    }
    
    def __init__(self, initial_state: GameState = GameState.INITIALIZING):
        """
        Initialize the state machine.
        
        Args:
            initial_state: Initial game state
        """
        self._state = initial_state
        self._previous_state = None
    
    @property
    def current_state(self) -> GameState:
        """Get the current state."""
        return self._state
    
    @property
    def previous_state(self) -> GameState:
        """Get the previous state."""
        return self._previous_state
    
    def can_transition_to(self, new_state: GameState) -> bool:
        """
        Check if a transition to new_state is valid.
        
        Args:
            new_state: Target state
            
        Returns:
            bool: True if transition is valid
        """
        if new_state not in self.TRANSITIONS.get(self._state, []):
            return False
        return True
    
    def transition_to(self, new_state: GameState) -> bool:
        """
        Perform a state transition.
        
        Args:
            new_state: Target state
            
        Returns:
            bool: True if transition succeeded
            
        Raises:
            ValueError: If transition is invalid
        """
        if not self.can_transition_to(new_state):
            raise ValueError(
                f"Invalid state transition: {self._state.name} -> {new_state.name}"
            )
        
        self._previous_state = self._state
        self._state = new_state
        return True
    
    def is_terminal(self) -> bool:
        """
        Check if the current state is terminal (game has ended).
        
        Returns:
            bool: True if in GAME_OVER or VICTORY state
        """
        return self._state in [GameState.GAME_OVER, GameState.VICTORY]
    
    def is_playing(self) -> bool:
        """
        Check if player can currently act.
        
        Returns:
            bool: True if in PLAYING state
        """
        return self._state == GameState.PLAYING
    
    def is_asleep(self) -> bool:
        """
        Check if player is asleep.
        
        Returns:
            bool: True if in PLAYER_ASLEEP state
        """
        return self._state == GameState.PLAYER_ASLEEP
    
    def is_game_over(self) -> bool:
        """
        Check if game is over (died).
        
        Returns:
            bool: True if in GAME_OVER state
        """
        return self._state == GameState.GAME_OVER
    
    def is_victory(self) -> bool:
        """
        Check if game is won.
        
        Returns:
            bool: True if in VICTORY state
        """
        return self._state == GameState.VICTORY
    
    def is_waiting_for_selection(self) -> bool:
        """
        Check if waiting for item selection.
        
        Returns:
            bool: True if in ITEM_SELECTION state
        """
        return self._state == GameState.ITEM_SELECTION
    
    def is_transitioning_level(self) -> bool:
        """
        Check if transitioning between levels.
        
        Returns:
            bool: True if in LEVEL_TRANSITION state
        """
        return self._state == GameState.LEVEL_TRANSITION
    
    def get_state_name(self) -> str:
        """
        Get human-readable name of current state.
        
        Returns:
            str: State name
        """
        return self._state.name
    
    def reset_to_initial(self) -> None:
        """Reset state machine to initial state."""
        self._previous_state = self._state
        self._state = GameState.INITIALIZING
    
    def restore_state(self, state: GameState) -> None:
        """
        Restore the internal state without validating transitions.

        This is intended for use during deserialization/loading only. It will
        set the current state directly and clear the previous state to avoid
        triggering transition validation logic.
        """
        self._previous_state = None
        self._state = state

    def __repr__(self) -> str:
        """String representation of state machine including current and previous states."""
        return f"StateMachine(current={self._state.name}, previous={self._previous_state.name if self._previous_state else 'None'})"
