import pytest
from data.save_manager import SaveManager
from domain.services.game_states import GameState


def _make_minimal_save(**overrides):
    data = {
        'version': '1.1',
        'current_level_number': 1,
        'rendering_mode': '2d',
        'player_asleep': False,
        'game_over': False,
        'victory': False,
        'message': '',
        'death_reason': '',
        'pending_selection': None,
        'difficulty_manager': None,
        'camera': None,
        'test_mode': False,
        'test_fog_of_war_enabled': False,
        'character': {
            'position': [1, 1],
            'health': 100,
            'max_health': 100,
            'strength': 10,
            'dexterity': 10,
            'active_elixirs': [],
            'current_weapon': None,
            'backpack': {'treasure_value': 0, 'items': {'food': [], 'elixir': [], 'scroll': [], 'weapon': [], 'key': []}}
        },
        'level': {
            'level_number': 1,
            'starting_room_index': 0,
            'exit_room_index': None,
            'exit_position': None,
            'rooms': [],
            'corridors': [],
            'doors': []
        },
        'fog_of_war': None,
        'statistics': {'enemies_defeated': 0}
    }
    data.update(overrides)
    return data


class TestRestoreState:
    def test_restore_victory_over_game_over(self):
        sm = SaveManager()
        save = _make_minimal_save(victory=True, game_over=True)
        session = sm.restore_game_session(save)
        assert session.state_machine.current_state == GameState.VICTORY

    def test_restore_game_over(self):
        sm = SaveManager()
        save = _make_minimal_save(game_over=True)
        session = sm.restore_game_session(save)
        assert session.state_machine.current_state == GameState.GAME_OVER

    def test_restore_player_asleep(self):
        sm = SaveManager()
        save = _make_minimal_save(player_asleep=True)
        session = sm.restore_game_session(save)
        assert session.state_machine.current_state == GameState.PLAYER_ASLEEP

    def test_restore_item_selection(self):
        sm = SaveManager()
        save = _make_minimal_save(pending_selection={'type': 'food'})
        session = sm.restore_game_session(save)
        assert session.state_machine.current_state == GameState.ITEM_SELECTION

    def test_restore_defaults_to_playing(self):
        sm = SaveManager()
        save = _make_minimal_save()
        session = sm.restore_game_session(save)
        assert session.state_machine.current_state == GameState.PLAYING
