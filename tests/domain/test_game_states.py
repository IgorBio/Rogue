"""
Unit tests for the game state machine.

Tests verify:
- Valid state transitions are allowed
- Invalid transitions raise ValueError
- Helper methods (is_playing, is_asleep, etc.) work correctly
- State history is preserved
- Terminal states are identified correctly
"""

import pytest
from domain.services.game_states import GameState, StateMachine


class TestGameState:
    """Test GameState enum."""
    
    def test_all_states_defined(self):
        """Verify all expected states are defined."""
        expected_states = {
            'INITIALIZING', 'PLAYING', 'PLAYER_ASLEEP', 'ITEM_SELECTION',
            'LEVEL_TRANSITION', 'GAME_OVER', 'VICTORY'
        }
        actual_states = {s.name for s in GameState}
        assert actual_states == expected_states


class TestStateMachineTransitions:
    """Test state machine transitions."""
    
    def test_initial_state(self):
        """Test machine starts in INITIALIZING state."""
        sm = StateMachine()
        assert sm.current_state == GameState.INITIALIZING
    
    def test_custom_initial_state(self):
        """Test machine can start in different state."""
        sm = StateMachine(GameState.PLAYING)
        assert sm.current_state == GameState.PLAYING
    
    def test_valid_transition_initializing_to_playing(self):
        """Test valid transition from INITIALIZING to PLAYING."""
        sm = StateMachine()
        assert sm.transition_to(GameState.PLAYING)
        assert sm.current_state == GameState.PLAYING
    
    def test_valid_transition_playing_to_asleep(self):
        """Test valid transition from PLAYING to PLAYER_ASLEEP."""
        sm = StateMachine(GameState.PLAYING)
        assert sm.transition_to(GameState.PLAYER_ASLEEP)
        assert sm.current_state == GameState.PLAYER_ASLEEP
    
    def test_valid_transition_playing_to_item_selection(self):
        """Test valid transition from PLAYING to ITEM_SELECTION."""
        sm = StateMachine(GameState.PLAYING)
        assert sm.transition_to(GameState.ITEM_SELECTION)
        assert sm.current_state == GameState.ITEM_SELECTION
    
    def test_valid_transition_playing_to_game_over(self):
        """Test valid transition from PLAYING to GAME_OVER."""
        sm = StateMachine(GameState.PLAYING)
        assert sm.transition_to(GameState.GAME_OVER)
        assert sm.current_state == GameState.GAME_OVER
    
    def test_valid_transition_playing_to_victory(self):
        """Test valid transition from PLAYING to VICTORY."""
        sm = StateMachine(GameState.PLAYING)
        assert sm.transition_to(GameState.VICTORY)
        assert sm.current_state == GameState.VICTORY
    
    def test_valid_transition_asleep_to_playing(self):
        """Test valid transition from PLAYER_ASLEEP back to PLAYING."""
        sm = StateMachine(GameState.PLAYER_ASLEEP)
        assert sm.transition_to(GameState.PLAYING)
        assert sm.current_state == GameState.PLAYING
    
    def test_valid_transition_asleep_to_game_over(self):
        """Test valid transition from PLAYER_ASLEEP to GAME_OVER."""
        sm = StateMachine(GameState.PLAYER_ASLEEP)
        assert sm.transition_to(GameState.GAME_OVER)
        assert sm.current_state == GameState.GAME_OVER
    
    def test_valid_transition_item_selection_to_playing(self):
        """Test valid transition from ITEM_SELECTION to PLAYING."""
        sm = StateMachine(GameState.ITEM_SELECTION)
        assert sm.transition_to(GameState.PLAYING)
        assert sm.current_state == GameState.PLAYING
    
    def test_valid_transition_level_transition_to_playing(self):
        """Test valid transition from LEVEL_TRANSITION to PLAYING."""
        sm = StateMachine(GameState.LEVEL_TRANSITION)
        assert sm.transition_to(GameState.PLAYING)
        assert sm.current_state == GameState.PLAYING
    
    def test_valid_transition_level_transition_to_victory(self):
        """Test valid transition from LEVEL_TRANSITION to VICTORY."""
        sm = StateMachine(GameState.LEVEL_TRANSITION)
        assert sm.transition_to(GameState.VICTORY)
        assert sm.current_state == GameState.VICTORY
    
    def test_invalid_transition_initializing_to_asleep(self):
        """Test invalid transition raises ValueError."""
        sm = StateMachine(GameState.INITIALIZING)
        with pytest.raises(ValueError) as exc_info:
            sm.transition_to(GameState.PLAYER_ASLEEP)
        assert "Invalid state transition" in str(exc_info.value)
    
    def test_invalid_transition_playing_to_initializing(self):
        """Test cannot transition back to INITIALIZING."""
        sm = StateMachine(GameState.PLAYING)
        with pytest.raises(ValueError):
            sm.transition_to(GameState.INITIALIZING)
    
    def test_invalid_transition_game_over_to_playing(self):
        """Test GAME_OVER is terminal - cannot transition from it."""
        sm = StateMachine(GameState.GAME_OVER)
        with pytest.raises(ValueError):
            sm.transition_to(GameState.PLAYING)
    
    def test_invalid_transition_victory_to_playing(self):
        """Test VICTORY is terminal - cannot transition from it."""
        sm = StateMachine(GameState.VICTORY)
        with pytest.raises(ValueError):
            sm.transition_to(GameState.PLAYING)
    
    def test_can_transition_to_valid(self):
        """Test can_transition_to returns True for valid transition."""
        sm = StateMachine(GameState.PLAYING)
        assert sm.can_transition_to(GameState.GAME_OVER)
    
    def test_can_transition_to_invalid(self):
        """Test can_transition_to returns False for invalid transition."""
        sm = StateMachine(GameState.PLAYING)
        assert not sm.can_transition_to(GameState.INITIALIZING)


class TestStateMachineHistory:
    """Test state history tracking."""
    
    def test_previous_state_updated(self):
        """Test previous_state is updated after transition."""
        sm = StateMachine(GameState.INITIALIZING)
        assert sm.previous_state is None
        
        sm.transition_to(GameState.PLAYING)
        assert sm.previous_state == GameState.INITIALIZING
        
        sm.transition_to(GameState.PLAYER_ASLEEP)
        assert sm.previous_state == GameState.PLAYING
    
    def test_previous_state_chain(self):
        """Test chain of transitions maintains history."""
        sm = StateMachine(GameState.INITIALIZING)
        transitions = [
            GameState.PLAYING,
            GameState.PLAYER_ASLEEP,
            GameState.PLAYING,
            GameState.ITEM_SELECTION,
            GameState.PLAYING,
        ]
        
        for i, target in enumerate(transitions):
            expected_prev = transitions[i-1] if i > 0 else GameState.INITIALIZING
            if i > 0:
                assert sm.previous_state == expected_prev
            sm.transition_to(target)
            assert sm.current_state == target


class TestStateMachineHelpers:
    """Test helper methods."""
    
    def test_is_playing(self):
        """Test is_playing helper."""
        sm_playing = StateMachine(GameState.PLAYING)
        sm_asleep = StateMachine(GameState.PLAYER_ASLEEP)
        sm_over = StateMachine(GameState.GAME_OVER)
        
        assert sm_playing.is_playing()
        assert not sm_asleep.is_playing()
        assert not sm_over.is_playing()
    
    def test_is_asleep(self):
        """Test is_asleep helper."""
        sm_asleep = StateMachine(GameState.PLAYER_ASLEEP)
        sm_playing = StateMachine(GameState.PLAYING)
        
        assert sm_asleep.is_asleep()
        assert not sm_playing.is_asleep()
    
    def test_is_game_over(self):
        """Test is_game_over helper."""
        sm_over = StateMachine(GameState.GAME_OVER)
        sm_playing = StateMachine(GameState.PLAYING)
        
        assert sm_over.is_game_over()
        assert not sm_playing.is_game_over()
    
    def test_is_victory(self):
        """Test is_victory helper."""
        sm_victory = StateMachine(GameState.VICTORY)
        sm_playing = StateMachine(GameState.PLAYING)
        
        assert sm_victory.is_victory()
        assert not sm_playing.is_victory()
    
    def test_is_waiting_for_selection(self):
        """Test is_waiting_for_selection helper."""
        sm_selection = StateMachine(GameState.ITEM_SELECTION)
        sm_playing = StateMachine(GameState.PLAYING)
        
        assert sm_selection.is_waiting_for_selection()
        assert not sm_playing.is_waiting_for_selection()
    
    def test_is_transitioning_level(self):
        """Test is_transitioning_level helper."""
        sm_transition = StateMachine(GameState.LEVEL_TRANSITION)
        sm_playing = StateMachine(GameState.PLAYING)
        
        assert sm_transition.is_transitioning_level()
        assert not sm_playing.is_transitioning_level()
    
    def test_is_terminal(self):
        """Test is_terminal identifies terminal states."""
        terminal_states = [GameState.GAME_OVER, GameState.VICTORY]
        non_terminal_states = [
            GameState.INITIALIZING, GameState.PLAYING, GameState.PLAYER_ASLEEP,
            GameState.ITEM_SELECTION, GameState.LEVEL_TRANSITION
        ]
        
        for state in terminal_states:
            sm = StateMachine(state)
            assert sm.is_terminal(), f"{state.name} should be terminal"
        
        for state in non_terminal_states:
            sm = StateMachine(state)
            assert not sm.is_terminal(), f"{state.name} should not be terminal"
    
    def test_get_state_name(self):
        """Test get_state_name returns readable name."""
        sm = StateMachine(GameState.PLAYER_ASLEEP)
        assert sm.get_state_name() == 'PLAYER_ASLEEP'
        
        sm.transition_to(GameState.PLAYING)
        assert sm.get_state_name() == 'PLAYING'


class TestStateMachineReset:
    """Test state machine reset."""
    
    def test_reset_to_initial(self):
        """Test reset_to_initial returns to INITIALIZING."""
        sm = StateMachine(GameState.PLAYING)
        sm.transition_to(GameState.PLAYER_ASLEEP)
        sm.transition_to(GameState.GAME_OVER)
        
        sm.reset_to_initial()
        assert sm.current_state == GameState.INITIALIZING
    
    def test_reset_preserves_previous(self):
        """Test reset preserves previous state in history."""
        sm = StateMachine(GameState.PLAYING)
        sm.transition_to(GameState.GAME_OVER)
        previous_before_reset = sm.previous_state
        
        sm.reset_to_initial()
        assert sm.previous_state == GameState.GAME_OVER


class TestStateMachineComplexScenarios:
    """Test complex state machine scenarios."""
    
    def test_full_game_flow_victory(self):
        """Test complete flow from start to victory."""
        sm = StateMachine()
        assert sm.current_state == GameState.INITIALIZING
        
        sm.transition_to(GameState.PLAYING)
        assert sm.is_playing()
        
        sm.transition_to(GameState.LEVEL_TRANSITION)
        sm.transition_to(GameState.PLAYING)
        
        sm.transition_to(GameState.LEVEL_TRANSITION)
        sm.transition_to(GameState.VICTORY)
        
        assert sm.is_victory()
        assert sm.is_terminal()
    
    def test_full_game_flow_death(self):
        """Test complete flow from start to death."""
        sm = StateMachine()
        sm.transition_to(GameState.PLAYING)
        sm.transition_to(GameState.PLAYER_ASLEEP)
        sm.transition_to(GameState.PLAYING)
        sm.transition_to(GameState.GAME_OVER)
        
        assert sm.is_game_over()
        assert sm.is_terminal()
    
    def test_sleep_interrupt(self):
        """Test sleep effect during gameplay."""
        sm = StateMachine(GameState.PLAYING)
        
        # Normal play
        assert sm.is_playing()
        
        # Get hit by sleep
        sm.transition_to(GameState.PLAYER_ASLEEP)
        assert sm.is_asleep()
        
        # Wake up next turn
        sm.transition_to(GameState.PLAYING)
        assert sm.is_playing()
    
    def test_item_selection_flow(self):
        """Test item selection interruption."""
        sm = StateMachine(GameState.PLAYING)
        
        sm.transition_to(GameState.ITEM_SELECTION)
        assert sm.is_waiting_for_selection()
        
        sm.transition_to(GameState.PLAYING)
        assert sm.is_playing()
    
    def test_death_from_asleep(self):
        """Test can die while asleep."""
        sm = StateMachine(GameState.PLAYING)
        sm.transition_to(GameState.PLAYER_ASLEEP)
        sm.transition_to(GameState.GAME_OVER)
        
        assert sm.is_game_over()
        assert sm.previous_state == GameState.PLAYER_ASLEEP


class TestStateMachineRepr:
    """Test string representation."""
    
    def test_repr_initial(self):
        """Test __repr__ for initial state."""
        sm = StateMachine()
        repr_str = repr(sm)
        assert 'INITIALIZING' in repr_str
        assert 'None' in repr_str
    
    def test_repr_after_transition(self):
        """Test __repr__ after transition."""
        sm = StateMachine()
        sm.transition_to(GameState.PLAYING)
        repr_str = repr(sm)
        assert 'PLAYING' in repr_str
        assert 'INITIALIZING' in repr_str
