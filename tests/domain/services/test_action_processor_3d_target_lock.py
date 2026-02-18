from types import SimpleNamespace

from domain.services.action_processor import ActionProcessor


class _DummyStateMachine:
    @staticmethod
    def is_terminal():
        return False


class _Enemy:
    def __init__(self):
        self.position = (3, 3)
        self.enemy_type = "zombie"


class _Item:
    def __init__(self):
        from config.game_config import ItemType

        self.item_type = ItemType.FOOD
        self.position = (3, 3)
        self.health_restoration = 10


def test_interact_enemy_uses_selected_target_without_second_lookup():
    enemy = _Enemy()
    calls = {"lookups": 0, "combat_with": None, "enemy_turns": 0}

    class _Controller:
        interaction_range = 2.5

        @staticmethod
        def try_open_door(character):
            return (False, "No door nearby")

        def get_entity_in_front(self, level):
            calls["lookups"] += 1
            if calls["lookups"] > 1:
                raise AssertionError("unexpected second entity lookup")
            return (enemy, "enemy", 1.0)

    class _Session:
        def __init__(self):
            self.character = SimpleNamespace()
            self.level = SimpleNamespace(exit_position=None, rooms=[])
            self.message = ""
            self.state_machine = _DummyStateMachine()
            self._controller = _Controller()

        def get_camera(self):
            return None

        def get_camera_controller(self):
            return self._controller

        def handle_combat(self, target):
            calls["combat_with"] = target
            return True

        def process_enemy_turns(self):
            calls["enemy_turns"] += 1

    session = _Session()
    processor = ActionProcessor(session)

    assert processor._handle_3d_interact() is True
    assert calls["lookups"] == 1
    assert calls["combat_with"] is enemy
    assert calls["enemy_turns"] == 1


def test_interact_item_uses_selected_target_without_second_lookup():
    item = _Item()
    calls = {"lookups": 0, "enemy_turns": 0}

    class _Room:
        def __init__(self, value):
            self.items = [value]

        def remove_item(self, value):
            self.items.remove(value)

    room = _Room(item)

    class _Backpack:
        @staticmethod
        def add_item(value):
            return value is item

    class _Controller:
        interaction_range = 2.5

        @staticmethod
        def try_open_door(character):
            return (False, "No door nearby")

        def get_entity_in_front(self, level):
            calls["lookups"] += 1
            if calls["lookups"] > 1:
                raise AssertionError("unexpected second entity lookup")
            return (item, "item", 1.0)

    class _Session:
        def __init__(self):
            self.character = SimpleNamespace(backpack=_Backpack())
            self.level = SimpleNamespace(exit_position=None, rooms=[room])
            self.message = ""
            self.state_machine = _DummyStateMachine()
            self._controller = _Controller()

        def get_camera(self):
            return None

        def get_camera_controller(self):
            return self._controller

        def process_enemy_turns(self):
            calls["enemy_turns"] += 1

    session = _Session()
    processor = ActionProcessor(session)

    assert processor._handle_3d_interact() is True
    assert calls["lookups"] == 1
    assert item not in room.items
    assert "Picked up" in session.message
    assert calls["enemy_turns"] == 1
