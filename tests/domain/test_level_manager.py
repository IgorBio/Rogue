def test_level_manager_generate_and_advance():
    from domain.services.level_manager import LevelManager
    from domain.entities.character import Character

    lm = LevelManager()
    # Basic generate (no difficulty manager attached)
    level = lm.generate_level(1, character=None, stats=None, test_mode=True)
    assert level is not None
    assert lm.current_level_number == 1

    # Advance to next level (assuming LEVEL_COUNT >= 2)
    from utils.constants import LEVEL_COUNT
    new_num = lm.advance_to_next_level(LEVEL_COUNT)
    if LEVEL_COUNT > 1:
        assert new_num == 2
        assert lm.current_level_number == 2
    else:
        assert new_num is None
