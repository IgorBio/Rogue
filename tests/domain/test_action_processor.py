import pytest

from domain.services.action_processor import ActionProcessor
from domain.services.game_states import GameState
from presentation.input_handler import InputHandler


def test_action_none_returns_false():
    from domain.game_session import GameSession
    session = GameSession(test_mode=True)
    ap = ActionProcessor(session)

    # ACTION_NONE should return False
    res = ap.process_action(InputHandler.ACTION_NONE, None)
    assert res is False


def test_asleep_wakes_and_processes_enemy_turns(monkeypatch):
    from domain.game_session import GameSession
    session = GameSession(test_mode=True)
    ap = ActionProcessor(session)

    # Put player to sleep
    session.state_machine.transition_to(GameState.PLAYER_ASLEEP)

    # Monkeypatch _process_enemy_turns to record call
    called = {"count": 0}

    def fake_proc():
        called['count'] += 1

    monkeypatch.setattr(session, '_process_enemy_turns', fake_proc)

    res = ap.process_action(InputHandler.ACTION_MOVE, (1, 0))
    assert res is False
    # Player should be awakened
    assert session.state_machine.is_playing()
    assert called['count'] == 1


def test_3d_mode_delegates(monkeypatch):
    from domain.game_session import GameSession
    session = GameSession(test_mode=True)
    ap = ActionProcessor(session)

    # Set 3D mode and monkeypatch the 3D handler
    session.rendering_mode = '3d'
    called = {"args": None}

    def fake_3d(a_type, a_data):
        called['args'] = (a_type, a_data)
        return True

    monkeypatch.setattr(session, '_process_action_3d', fake_3d)

    res = ap.process_action('attack', None)
    assert res is True
    assert called['args'] == ('attack', None)
