from data.statistics import Statistics
from domain.entities.character import Character


def test_statistics_recording_and_summary():
    stats = Statistics()
    stats.record_enemy_defeated(10)
    stats.record_food_used()
    stats.record_elixir_used()
    stats.record_scroll_used()
    stats.record_weapon_equipped()
    stats.record_attack(hit=True, damage=5)
    stats.record_attack(hit=False, damage=0)
    stats.record_hit_taken(3)
    stats.record_movement()
    stats.record_item_collected()
    stats.record_level_reached(2)

    character = Character(0, 0)
    character.health = 50
    character.strength = 12
    character.dexterity = 8

    stats.record_game_end(character, victory=False)

    summary = stats.get_summary_text()
    assert any("PROGRESSION" in line for line in summary)
    assert any("COMBAT" in line for line in summary)
    assert any("ITEMS" in line for line in summary)

    data = stats.to_dict()
    restored = Statistics.from_dict(data)
    assert restored.treasure_collected == stats.treasure_collected
    assert restored.level_reached == stats.level_reached
