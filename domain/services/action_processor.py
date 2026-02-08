"""ActionProcessor: centralizes player action handling.

This service delegates to GameSession's 2D/3D handlers and enforces
state checks (sleep, terminal states) so the session stays thin.

Statistics are now tracked via events published to the EventBus.
"""
from common.logging_utils import log_exception
from domain.services.game_states import GameState
from domain.services.action_types import ActionType
from domain.event_bus import event_bus
from domain.events import ItemCollectedEvent


class ActionProcessor:
    # 2D action constants (domain)
    ACTION_MOVE = ActionType.MOVE
    ACTION_USE_FOOD = ActionType.USE_FOOD
    ACTION_USE_WEAPON = ActionType.USE_WEAPON
    ACTION_USE_ELIXIR = ActionType.USE_ELIXIR
    ACTION_USE_SCROLL = ActionType.USE_SCROLL
    ACTION_QUIT = ActionType.QUIT
    ACTION_NONE = ActionType.NONE

    # 3D action constants (domain)
    ACTION_MOVE_FORWARD = ActionType.MOVE_FORWARD
    ACTION_MOVE_BACKWARD = ActionType.MOVE_BACKWARD
    ACTION_STRAFE_LEFT = ActionType.STRAFE_LEFT
    ACTION_STRAFE_RIGHT = ActionType.STRAFE_RIGHT
    ACTION_ROTATE_LEFT = ActionType.ROTATE_LEFT
    ACTION_ROTATE_RIGHT = ActionType.ROTATE_RIGHT
    ACTION_INTERACT = ActionType.INTERACT
    ACTION_ATTACK = ActionType.ATTACK
    ACTION_PICKUP = ActionType.PICKUP

    def __init__(self, session):
        self.session = session

    def _normalize_action_type(self, action_type):
        if isinstance(action_type, ActionType):
            return action_type
        if isinstance(action_type, str):
            try:
                return ActionType.from_string(action_type)
            except Exception:
                return action_type
        return action_type
    def process_action(self, action_type, action_data):
        """Process an action, enforcing state checks and delegating to
        the appropriate 2D/3D handlers implemented on this processor.

        Returns True when action succeeded, False otherwise.
        """
        action_type = self._normalize_action_type(action_type)

        # Sleep handling: wake player and process enemy turns
        if self.session.state_machine.is_asleep():
            self.session.message = "You are asleep and cannot act this turn!"
            # wake player for next turn
            self.session.state_machine.transition_to(GameState.PLAYING)
            # process enemy turns after being asleep
            try:
                self.session.process_enemy_turns()
            except Exception as exc:
                    log_exception(exc, __name__)
            return False

        # Terminal states: no actions allowed
        if self.session.state_machine.is_terminal():
            self.session.message = "Game is over!"
            return False

        # Clear transient message
        self.session.message = ""

        # Delegate to internal 3D or 2D processor (direct calls).
        if self.session.is_3d_mode():
            return self._process_action_3d(action_type, action_data)
        else:
            return self._process_action_2d(action_type, action_data)

    def _process_action_2d(self, action_type, action_data):
        """Process actions in 2D mode."""

        if action_type == self.ACTION_MOVE:
            return self.session.handle_movement(action_data)
        elif action_type == self.ACTION_USE_FOOD:
            return self.session.request_food_selection()
        elif action_type == self.ACTION_USE_WEAPON:
            return self.session.request_weapon_selection()
        elif action_type == self.ACTION_USE_ELIXIR:
            return self.session.request_elixir_selection()
        elif action_type == self.ACTION_USE_SCROLL:
            return self.session.request_scroll_selection()
        elif action_type == self.ACTION_QUIT:
            self.session.set_game_over("Game quit by player")
            self.session.message = "Game quit by player."
            return True
        elif action_type == self.ACTION_NONE:
            return False
        else:
            self.session.message = "Action not yet implemented."
            return False

    def _process_action_3d(self, action_type, action_data):
        """Process actions in 3D mode."""

        if action_type == self.ACTION_MOVE_FORWARD:
            return self.session.handle_movement('forward')
        elif action_type == self.ACTION_MOVE_BACKWARD:
            return self.session.handle_movement('backward')
        elif action_type == self.ACTION_STRAFE_LEFT:
            return self.session.handle_movement('strafe_left')
        elif action_type == self.ACTION_STRAFE_RIGHT:
            return self.session.handle_movement('strafe_right')
        elif action_type == self.ACTION_ROTATE_LEFT:
            if self.session.camera_controller:
                self.session.camera_controller.rotate_left()
                self.session.message = f"Facing {self.session.camera_controller.get_direction_name()}"
            return True
        elif action_type == self.ACTION_ROTATE_RIGHT:
            if self.session.camera_controller:
                self.session.camera_controller.rotate_right()
                self.session.message = f"Facing {self.session.camera_controller.get_direction_name()}"
            return True
        elif action_type == self.ACTION_INTERACT:
            return self._handle_3d_interact()
        elif action_type == self.ACTION_ATTACK:
            return self._handle_3d_attack()
        elif action_type == self.ACTION_PICKUP:
            return self._handle_3d_pickup()
        elif action_type == self.ACTION_USE_FOOD:
            return self.session.request_food_selection()
        elif action_type == self.ACTION_USE_WEAPON:
            return self.session.request_weapon_selection()
        elif action_type == self.ACTION_USE_ELIXIR:
            return self.session.request_elixir_selection()
        elif action_type == self.ACTION_USE_SCROLL:
            return self.session.request_scroll_selection()
        elif action_type == self.ACTION_QUIT:
            self.session.set_game_over("Game quit by player")
            self.session.message = "Game quit by player."
            return True
        elif action_type == self.ACTION_NONE:
            return False
        else:
            return False

    def _handle_3d_interact(self):
        """Handle smart interaction in 3D mode."""
        if not self.session.camera_controller:
            return False

        entity, entity_type, distance = self.session.camera_controller.get_entity_in_front(self.session.level)

        # Priority order: doors -> enemies -> items -> exit
        door_success, door_message = self.session.camera_controller.try_open_door(self.session.character)
        if door_success or door_message != "No door nearby":
            self.session.message = door_message
            return door_success

        if entity_type == 'enemy':
            return self._handle_3d_attack()
        elif entity_type == 'item':
            return self._handle_3d_pickup()
        elif entity_type == 'exit':
            return self.session.handle_movement('forward')

        self.session.message = "Nothing to interact with"
        return False

    def _handle_3d_attack(self):
        """Handle attack in 3D mode."""
        if not self.session.camera_controller:
            return False

        success, message, enemy = self.session.camera_controller.attack_entity_in_front(
            self.session.character, self.session.level
        )

        self.session.message = message

        if success and enemy:
            # Use coordinator's CombatSystem which carries statistics and full handling
            try:
                return self.session.handle_combat(enemy)
            except Exception:
                # As a conservative fallback, signal failure but avoid duplicating
                # statistics or side-effects that may be handled elsewhere.
                try:
                    return False
                except Exception:
                    return False

        return success

    def _handle_3d_pickup(self):
        """Handle item pickup in 3D mode."""
        if not self.session.camera_controller:
            return False

        success, message, item = self.session.camera_controller.pickup_item_in_front(
            self.session.character, self.session.level
        )

        self.session.message = message

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

        return success
