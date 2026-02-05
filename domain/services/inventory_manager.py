"""Inventory and item-selection logic extracted from GameSession.

This manager owns pending selections and pickup/drop logic so the
`GameSession` can delegate and remain small.

Statistics are now tracked via events published to the EventBus.
"""
from domain.logging_utils import log_exception
from config.game_config import ItemType, PlayerConfig
from domain.services.item_selection import SelectionRequest
from domain.event_bus import event_bus
from domain.events import (
    FoodConsumedEvent,
    ElixirUsedEvent,
    ScrollReadEvent,
    WeaponEquippedEvent,
    ItemCollectedEvent,
)


class InventoryManager:
    def __init__(self, session):
        self.session = session

    def request_food_selection(self):
        session = self.session
        food_items = session.character.backpack.get_items(ItemType.FOOD)
        if not food_items:
            session.message = "No food in backpack!"
            return False

        session.pending_selection = SelectionRequest(
            selection_type='food',
            items=food_items,
            title='Select Food to Consume',
            allow_zero=False
        )
        session.request_item_selection()
        return True

    def request_weapon_selection(self):
        session = self.session
        weapon_items = session.character.backpack.get_items(ItemType.WEAPON)

        if not weapon_items and not session.character.current_weapon:
            session.message = "No weapons available!"
            return False

        session.pending_selection = SelectionRequest(
            selection_type='weapon',
            items=weapon_items,
            title='Select Weapon to Equip (0 to unequip current)',
            allow_zero=True
        )
        session.request_item_selection()
        return True

    def request_elixir_selection(self):
        session = self.session
        elixir_items = session.character.backpack.get_items(ItemType.ELIXIR)
        if not elixir_items:
            session.message = "No elixirs in backpack!"
            return False

        session.pending_selection = SelectionRequest(
            selection_type='elixir',
            items=elixir_items,
            title='Select Elixir to Drink',
            allow_zero=False
        )
        session.request_item_selection()
        return True

    def request_scroll_selection(self):
        session = self.session
        scroll_items = session.character.backpack.get_items(ItemType.SCROLL)
        if not scroll_items:
            session.message = "No scrolls in backpack!"
            return False

        session.pending_selection = SelectionRequest(
            selection_type='scroll',
            items=scroll_items,
            title='Select Scroll to Read',
            allow_zero=False
        )
        session.request_item_selection()
        return True

    def complete_item_selection(self, selected_idx):
        session = self.session
        if session.pending_selection is None:
            return False

        selection_type = session.pending_selection.selection_type

        if selected_idx is None:
            session.message = f"Cancelled {selection_type} selection."
            session.pending_selection = None
            session.return_from_selection()
            return False

        if selection_type == 'food':
            result = self._complete_food_selection(selected_idx)
        elif selection_type == 'weapon':
            result = self._complete_weapon_selection(selected_idx)
        elif selection_type == 'elixir':
            result = self._complete_elixir_selection(selected_idx)
        elif selection_type == 'scroll':
            result = self._complete_scroll_selection(selected_idx)
        else:
            result = False

        session.pending_selection = None
        session.return_from_selection()

        if result and not session.state_machine.is_terminal():
            session.process_enemy_turns()

        return result

    def _complete_food_selection(self, selected_idx):
        session = self.session
        food_items = session.character.backpack.get_items(ItemType.FOOD)
        if selected_idx >= len(food_items):
            session.message = "Invalid selection!"
            return False

        food = food_items[selected_idx]
        message = session.character.use_food(food)
        session.character.backpack.remove_item(ItemType.FOOD, selected_idx)
        # Publish event for statistics tracking
        try:
            event_bus.publish(FoodConsumedEvent(
                health_restored=getattr(food, 'health_restoration', 0),
                food_item=food
            ))
        except Exception as exc:
                log_exception(exc, __name__)
        session.message = message
        return True

    def _complete_weapon_selection(self, selected_idx):
        session = self.session
        weapon_items = session.character.backpack.get_items(ItemType.WEAPON)

        if selected_idx == -1:
            old_weapon, message, should_drop = session.character.unequip_weapon()

            if old_weapon and should_drop:
                drop_success = self._drop_weapon_on_ground(old_weapon)
                if drop_success:
                    session.message = f"{message} - dropped on ground"
                else:
                    session.message = f"{message} - no space to drop!"
            else:
                session.message = message

            return True

        if selected_idx < 0 or selected_idx >= len(weapon_items):
            session.message = "Invalid weapon selection!"
            return False

        weapon = weapon_items[selected_idx]
        old_weapon, message = session.character.equip_weapon(weapon)
        session.character.backpack.remove_item(ItemType.WEAPON, selected_idx)

        if old_weapon:
            success = session.character.backpack.add_item(old_weapon)
            if not success:
                drop_success = self._drop_weapon_on_ground(old_weapon)
                if drop_success:
                    session.message = f"{message} - old weapon dropped (backpack full)"
                else:
                    session.message = f"{message} - old weapon vanished (no space)!"
            else:
                session.message = message
        else:
            session.message = message

        # Publish event for statistics tracking
        try:
            event_bus.publish(WeaponEquippedEvent(
                weapon_name=getattr(weapon, 'name', 'unknown'),
                damage_bonus=getattr(weapon, 'damage_bonus', 0)
            ))
        except Exception as exc:
                log_exception(exc, __name__)
        return True

    def _drop_weapon_on_ground(self, weapon):
        session = self.session
        player_x, player_y = int(session.character.position[0]), int(session.character.position[1])

        player_room, player_room_idx = session.level.get_room_at(player_x, player_y)

        for dx, dy in PlayerConfig.ADJACENT_OFFSETS:
            pos_x, pos_y = player_x + dx, player_y + dy

            if not session.level.is_walkable(pos_x, pos_y):
                continue

            if session.get_revealed_enemy_at(pos_x, pos_y):
                continue

            if session.get_item_at(pos_x, pos_y):
                continue

            weapon.position = (pos_x, pos_y)

            drop_room, drop_room_idx = session.level.get_room_at(pos_x, pos_y)

            if drop_room:
                drop_room.add_item(weapon)
            else:
                if player_room:
                    player_room.add_item(weapon)

            return True

        return False

    def _complete_elixir_selection(self, selected_idx):
        session = self.session
        elixir_items = session.character.backpack.get_items(ItemType.ELIXIR)
        if selected_idx >= len(elixir_items):
            session.message = "Invalid selection!"
            return False

        elixir = elixir_items[selected_idx]
        message = session.character.use_elixir(elixir)
        session.character.backpack.remove_item(ItemType.ELIXIR, selected_idx)
        # Publish event for statistics tracking
        try:
            # Determine which stat was boosted
            stat_boosted = 'strength' if hasattr(elixir, 'strength_boost') and elixir.strength_boost > 0 else 'dexterity'
            boost_amount = getattr(elixir, f'{stat_boosted}_boost', 0)
            event_bus.publish(ElixirUsedEvent(
                stat_boosted=stat_boosted,
                boost_amount=boost_amount
            ))
        except Exception as exc:
                log_exception(exc, __name__)
        session.message = message
        return True

    def _complete_scroll_selection(self, selected_idx):
        session = self.session
        scroll_items = session.character.backpack.get_items(ItemType.SCROLL)
        if selected_idx >= len(scroll_items):
            session.message = "Invalid selection!"
            return False

        scroll = scroll_items[selected_idx]
        message = session.character.use_scroll(scroll)
        session.character.backpack.remove_item(ItemType.SCROLL, selected_idx)
        # Publish event for statistics tracking
        try:
            event_bus.publish(ScrollReadEvent(
                scroll_type=getattr(scroll, 'scroll_type', 'unknown'),
                effect_description=getattr(scroll, 'description', '')
            ))
        except Exception as exc:
                log_exception(exc, __name__)
        session.message = message
        return True

    def has_pending_selection(self):
        return self.session.pending_selection is not None

    def get_pending_selection(self):
        return self.session.pending_selection

    def pickup_item(self, item):
        session = self.session
        success = session.character.backpack.add_item(item)

        if success:
            # Publish event for statistics tracking
            try:
                event_bus.publish(ItemCollectedEvent(
                    item_type=getattr(item, 'item_type', 'unknown'),
                    item=item,
                    position=getattr(item, 'position', (0, 0))
                ))
            except Exception as exc:
                    log_exception(exc, __name__)

            item_room = self.get_item_room(item)
            if item_room:
                item_room.remove_item(item)

            if item.item_type == ItemType.TREASURE:
                return f"Picked up {item.value} treasure!"
            elif item.item_type == ItemType.FOOD:
                return f"Picked up food (heals {item.health_restoration} HP)"
            elif item.item_type == ItemType.WEAPON:
                return f"Picked up {item.name}"
            elif item.item_type == ItemType.ELIXIR:
                return f"Picked up elixir ({item.stat_type} +{item.bonus})"
            elif item.item_type == ItemType.SCROLL:
                return f"Picked up scroll ({item.stat_type} +{item.bonus})"
            elif item.item_type == ItemType.KEY:
                return f"Picked up {item.color.value} key!"
            else:
                return "Picked up item"
        else:
            return f"Backpack full! Can't pick up item."

    def get_item_room(self, item):
        for room in self.session.level.rooms:
            if item in room.items:
                return room
        return None
