"""
Integration tests for GameSession with StateMachine.

Tests verify:
- GameSession correctly integrates StateMachine
- State transitions work with game actions
- Backward compatibility properties work
- Game over/victory states are properly managed
"""

import pytest
from domain.game_session import GameSession
from domain.services.game_states import GameState

from data.statistics import Statistics
from data.save_manager import SaveManager
from presentation.camera import Camera
from presentation.camera import CameraController


def _make_session(**kwargs):
    from domain.game_session import GameSession
    # Camera factories removed - ViewManager handles camera creation via events
    return GameSession(
        statistics_factory=Statistics,
        save_manager_factory=lambda: SaveManager(),
        **kwargs,
    )


class TestGameSessionStateInitialization:
    """Test GameSession initialization with state machine."""
    
    def test_gamesession_initializes_with_state_machine(self):
        """Test GameSession creates and initializes state machine."""
        session = _make_session(test_mode=True)
        
        assert session.state_machine is not None
        assert session.state_machine.current_state == GameState.PLAYING
    
    def test_gamesession_creates_character(self):
        """Test GameSession creates character on initialization."""
        session = _make_session(test_mode=True)
        
        assert session.character is not None
        assert session.character.health > 0
    
    def test_gamesession_creates_level(self):
        """Test GameSession generates level on initialization."""
        session = _make_session(test_mode=True)
        
        assert session.level is not None
        assert session.current_level_number == 1


class TestGameSessionBackwardCompatibility:
    """Test backward compatibility properties."""
    
    def test_game_over_property_getter(self):
        """Test game_over property reads from state machine."""
        session = _make_session(test_mode=True)
        
        assert session.game_over == False
        
        session.state_machine.transition_to(GameState.GAME_OVER)
        assert session.game_over == True
    
    def test_game_over_property_setter(self):
        """Test game_over property setter updates state machine."""
        session = _make_session(test_mode=True)
        
        session.game_over = True
        assert session.state_machine.is_game_over()
    
    def test_victory_property_getter(self):
        """Test victory property reads from state machine."""
        session = _make_session(test_mode=True)
        
        assert session.victory == False
        
        session.state_machine.transition_to(GameState.VICTORY)
        assert session.victory == True
    
    def test_victory_property_setter(self):
        """Test victory property setter updates state machine."""
        session = _make_session(test_mode=True)
        
        session.victory = True
        assert session.state_machine.is_victory()
    
    def test_player_asleep_property_getter(self):
        """Test player_asleep property reads from state machine."""
        session = _make_session(test_mode=True)
        
        assert session.player_asleep == False
        
        session.state_machine.transition_to(GameState.PLAYER_ASLEEP)
        assert session.player_asleep == True
    
    def test_player_asleep_property_setter_to_true(self):
        """Test player_asleep property setter transitions to asleep."""
        session = _make_session(test_mode=True)
        
        session.player_asleep = True
        assert session.state_machine.is_asleep()
    
    def test_player_asleep_property_setter_to_false(self):
        """Test player_asleep property setter transitions from asleep."""
        session = _make_session(test_mode=True)
        session.state_machine.transition_to(GameState.PLAYER_ASLEEP)
        
        session.player_asleep = False
        assert session.state_machine.is_playing()


class TestGameSessionStateMethods:
    """Test explicit state machine methods."""
    
    def test_set_game_over(self):
        """Test set_game_over method."""
        session = _make_session(test_mode=True)
        
        session.set_game_over("Killed by Zombie")
        
        assert session.state_machine.is_game_over()
        assert session.death_reason == "Killed by Zombie"
    
    def test_set_victory(self):
        """Test set_victory method."""
        session = _make_session(test_mode=True)
        
        session.set_victory()
        
        assert session.state_machine.is_victory()
    
    def test_set_player_asleep(self):
        """Test set_player_asleep method."""
        session = _make_session(test_mode=True)
        
        session.set_player_asleep()
        
        assert session.state_machine.is_asleep()
    
    def test_wake_player(self):
        """Test wake_player method."""
        session = _make_session(test_mode=True)
        session.set_player_asleep()
        
        session.wake_player()
        
        assert session.state_machine.is_playing()
    
    def test_request_item_selection(self):
        """Test request_item_selection method."""
        session = _make_session(test_mode=True)
        
        session.request_item_selection()
        
        assert session.state_machine.is_waiting_for_selection()
    
    def test_return_from_selection(self):
        """Test return_from_selection method."""
        session = _make_session(test_mode=True)
        session.request_item_selection()
        
        session.return_from_selection()
        
        assert session.state_machine.is_playing()
    
    def test_begin_level_transition(self):
        """Test begin_level_transition method."""
        session = _make_session(test_mode=True)
        
        session.begin_level_transition()
        
        assert session.state_machine.is_transitioning_level()
    
    def test_complete_level_transition(self):
        """Test complete_level_transition method."""
        session = _make_session(test_mode=True)
        session.begin_level_transition()
        
        session.complete_level_transition()
        
        assert session.state_machine.is_playing()


class TestGameSessionActionProcessing:
    """Test action processing with state machine."""
    
    def test_cannot_act_when_asleep(self):
        """Test player cannot perform actions while asleep."""
        session = _make_session(test_mode=True)
        session.set_player_asleep()
        
        # Try to move
        result = session.process_player_action('move', (1, 0))
        
        # Should fail and wake up
        assert result == False
        assert session.state_machine.is_playing()
    
    def test_cannot_act_when_game_over(self):
        """Test player cannot perform actions after game over."""
        session = _make_session(test_mode=True)
        session.set_game_over("Test death")
        
        # Try to move
        result = session.process_player_action('move', (1, 0))
        
        assert result == False
    
    def test_cannot_act_when_victory(self):
        """Test player cannot perform actions after victory."""
        session = _make_session(test_mode=True)
        session.set_victory()
        
        # Try to move
        result = session.process_player_action('move', (1, 0))
        
        assert result == False


class TestGameSessionIsGameOver:
    """Test is_game_over method with state machine."""
    
    def test_is_game_over_false_when_playing(self):
        """Test is_game_over returns False in PLAYING state."""
        session = _make_session(test_mode=True)
        
        assert session.is_game_over() == False
    
    def test_is_game_over_true_when_dead(self):
        """Test is_game_over returns True in GAME_OVER state."""
        session = _make_session(test_mode=True)
        session.set_game_over("Test")
        
        assert session.is_game_over() == True
    
    def test_is_game_over_true_when_victory(self):
        """Test is_game_over returns True in VICTORY state."""
        session = _make_session(test_mode=True)
        session.set_victory()
        
        assert session.is_game_over() == True


class TestGameSessionReset:
    """Test game reset functionality."""
    
    def test_reset_returns_to_playing(self):
        """Test reset_game returns state machine to initial then playing."""
        session = _make_session(test_mode=True)
        session.set_game_over("Test death")
        
        assert session.state_machine.is_game_over()
        
        session.reset_game()
        
        assert session.state_machine.is_playing()
        assert session.current_level_number == 1
    
    def test_reset_resets_level(self):
        """Test reset_game resets to level 1."""
        session = _make_session(test_mode=True, test_level=5)
        
        session.reset_game()
        
        assert session.current_level_number == 1


class TestGameSessionStateTransitionSequence:
    """Test realistic state transition sequences."""
    
    def test_normal_gameplay_sequence(self):
        """Test normal gameplay: init -> playing -> game_over."""
        session = _make_session(test_mode=True)
        
        # Should be playing after init
        assert session.state_machine.is_playing()
        
        # Simulate death
        session.set_game_over("Death")
        assert session.state_machine.is_game_over()
    
    def test_sleep_interrupt_sequence(self):
        """Test sleep effect: playing -> asleep -> playing."""
        session = _make_session(test_mode=True)
        
        assert session.state_machine.is_playing()
        
        session.set_player_asleep()
        assert session.state_machine.is_asleep()
        
        session.wake_player()
        assert session.state_machine.is_playing()
    
    def test_item_selection_sequence(self):
        """Test item selection: playing -> selection -> playing."""
        session = _make_session(test_mode=True)
        
        assert session.state_machine.is_playing()
        
        session.request_item_selection()
        assert session.state_machine.is_waiting_for_selection()
        
        session.return_from_selection()
        assert session.state_machine.is_playing()
    
    def test_victory_sequence(self):
        """Test victory: playing -> level_transition -> victory."""
        session = _make_session(test_mode=True)
        
        session.begin_level_transition()
        assert session.state_machine.is_transitioning_level()
        
        session.set_victory()
        assert session.state_machine.is_victory()


class TestGameSessionGetStateMachine:
    """Test get_state_machine accessor."""
    
    def test_get_state_machine_returns_machine(self):
        """Test get_state_machine returns the state machine instance."""
        session = _make_session(test_mode=True)
        
        sm = session.get_state_machine()
        
        assert sm is not None
        assert sm == session.state_machine
    
    def test_get_state_machine_reflects_changes(self):
        """Test returned state machine reflects current state."""
        session = _make_session(test_mode=True)
        
        session.set_player_asleep()
        sm = session.get_state_machine()
        
        assert sm.is_asleep()


class TestGameSessionGameStatsWithState:
    """Test game stats with state machine."""
    
    def test_game_stats_victory_true(self):
        """Test game stats shows victory=True after victory."""
        session = _make_session(test_mode=True)
        session.set_victory()
        
        stats = session.get_game_stats()
        
        assert stats['victory'] == True
    
    def test_game_stats_victory_false_after_death(self):
        """Test game stats shows victory=False after death."""
        session = _make_session(test_mode=True)
        session.set_game_over("Test death")
        
        stats = session.get_game_stats()
        
        assert stats['victory'] == False
        assert stats['death_reason'] == "Test death"
    
    def test_game_stats_death_reason_none_on_victory(self):
        """Test game stats has no death reason on victory."""
        session = _make_session(test_mode=True)
        session.set_victory()
        
        stats = session.get_game_stats()
        
        assert stats['death_reason'] is None
