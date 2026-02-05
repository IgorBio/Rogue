import pytest

from domain.services.action_processor import ActionProcessor
from domain.services.game_states import GameState
from domain.services.action_types import ActionType

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


def test_action_none_returns_false():
    session = _make_session(test_mode=True)
    ap = ActionProcessor(session)

    # ACTION_NONE should return False
    res = ap.process_action(ActionType.NONE, None)
    assert res is False


def test_asleep_wakes_and_processes_enemy_turns():
    session = _make_session(test_mode=True)
    ap = ActionProcessor(session)

    # Put player to sleep
    session.state_machine.transition_to(GameState.PLAYER_ASLEEP)
    assert session.state_machine.is_asleep()

    # When asleep, action should return False (wake up, no movement)
    res = ap.process_action(ActionType.MOVE, (1, 0))
    assert res is False

    # Player should be awakened by the action processor
    assert session.state_machine.is_playing()


def test_3d_mode_delegates(monkeypatch):
    session = _make_session(test_mode=True)
    ap = ActionProcessor(session)

    # Set 3D mode and monkeypatch the ActionProcessor's 3D handler
    session.rendering_mode = '3d'
    called = {"args": None}

    def fake_3d(a_type, a_data):
        called['args'] = (a_type, a_data)
        return True

    monkeypatch.setattr(ap, '_process_action_3d', fake_3d)

    res = ap.process_action(ActionType.ATTACK, None)
    assert res is True
    assert called['args'] == (ActionType.ATTACK, None)
