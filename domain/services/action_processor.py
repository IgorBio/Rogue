"""ActionProcessor: centralizes player action handling.

This service delegates to GameSession's 2D/3D handlers and enforces
state checks (sleep, terminal states) so the session stays thin.

Statistics are now tracked via events published to the EventBus.
"""
from domain.services.game_states import GameState
from domain.event_bus import event_bus
from domain.events import ItemCollectedEvent


class ActionProcessor:
    # 2D action constants (decoupled from presentation layer)
    ACTION_MOVE = "move"
    ACTION_USE_FOOD = "use_food"
    ACTION_USE_WEAPON = "use_weapon"
    ACTION_USE_ELIXIR = "use_elixir"
    ACTION_USE_SCROLL = "use_scroll"
    ACTION_QUIT = "quit"
    ACTION_NONE = "none"

    # 3D action constants
    ACTION_MOVE_FORWARD = "move_forward"
    ACTION_MOVE_BACKWARD = "move_backward"
    ACTION_STRAFE_LEFT = "strafe_left"
    ACTION_STRAFE_RIGHT = "strafe_right"
    ACTION_ROTATE_LEFT = "rotate_left"
    ACTION_ROTATE_RIGHT = "rotate_right"
    ACTION_INTERACT = "interact"
    ACTION_ATTACK = "attack"
    ACTION_PICKUP = "pickup"

    def __init__(self, session):
        self.session = session
    def process_action(self, action_type, action_data):
        """Process an action, enforcing state checks and delegating to
        the appropriate 2D/3D handlers implemented on this processor.

        Returns True when action succeeded, False otherwise.
        """
        # Sleep handling: wake player and process enemy turns
        if self.session.state_machine.is_asleep():
            self.session.message = "You are asleep and cannot act this turn!"
            # wake player for next turn
            self.session.state_machine.transition_to(GameState.PLAYING)
            # process enemy turns after being asleep
            try:
                self.session._process_enemy_turns()
            except Exception:
                pass
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
            return self.session.movement_handler.handle_2d_movement(action_data)
        elif action_type == self.ACTION_USE_FOOD:
            return self.session.inventory_manager.request_food_selection()
        elif action_type == self.ACTION_USE_WEAPON:
            return self.session.inventory_manager.request_weapon_selection()
        elif action_type == self.ACTION_USE_ELIXIR:
            return self.session.inventory_manager.request_elixir_selection()
        elif action_type == self.ACTION_USE_SCROLL:
            return self.session.inventory_manager.request_scroll_selection()
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
            return self.session.movement_handler.handle_3d_movement('forward')
        elif action_type == self.ACTION_MOVE_BACKWARD:
            return self.session.movement_handler.handle_3d_movement('backward')
        elif action_type == self.ACTION_STRAFE_LEFT:
            return self.session.movement_handler.handle_3d_movement('strafe_left')
        elif action_type == self.ACTION_STRAFE_RIGHT:
            return self.session.movement_handler.handle_3d_movement('strafe_right')
        elif action_type == self.ACTION_ROTATE_LEFT:
            self.session.camera_controller.rotate_left()
            self.session.message = f"Facing {self.session.camera_controller.get_direction_name()}"
            return True
        elif action_type == self.ACTION_ROTATE_RIGHT:
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
            return self.session.inventory_manager.request_food_selection()
        elif action_type == self.ACTION_USE_WEAPON:
            return self.session.inventory_manager.request_weapon_selection()
        elif action_type == self.ACTION_USE_ELIXIR:
            return self.session.inventory_manager.request_elixir_selection()
        elif action_type == self.ACTION_USE_SCROLL:
            return self.session.inventory_manager.request_scroll_selection()
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
        entity, entity_type, distance = self.session.camera_controller.get_entity_in_front(self.session.level)

        if entity_type == 'enemy':
            return self._handle_3d_attack()
        elif entity_type == 'item':
            return self._handle_3d_pickup()
        elif entity_type == 'exit':
            return self.session.movement_handler.handle_3d_movement('forward')
        else:
            success, message = self.session.camera_controller.try_open_door(self.session.character)
            self.session.message = message
            return success

    def _handle_3d_attack(self):
        """Handle attack in 3D mode."""
        success, message, enemy = self.session.camera_controller.attack_entity_in_front(
            self.session.character, self.session.level
        )

        self.session.message = message

        if success and enemy:
            # Use session's CombatSystem which carries statistics and full handling
            try:
                return self.session.combat_system.process_player_attack(self.session, enemy)
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
            except Exception:
                pass

        return success
