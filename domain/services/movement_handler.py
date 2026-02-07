"""domain.services.movement_handler
Canonical MovementHandler: single-class, instance-bound to a GameSession.

This file deliberately contains a single, unambiguous definition of
`MovementHandler` with a constructor that accepts the owning `session`.

Statistics are now tracked via events published to the EventBus.
"""
from common.logging_utils import log_exception
from config.game_config import GameConfig


class MovementHandler:
    def __init__(self, session):
        self.session = session

    def handle_2d_movement(self, direction):
        session = self.session

        dx, dy = direction
        current_x, current_y = session.character.position
        new_x = current_x + dx
        new_y = current_y + dy

        door = session.level.get_door_at(new_x, new_y)
        if door and door.is_locked:
            from domain.key_door_system import unlock_door_if_possible

            if unlock_door_if_possible(door, session.character):
                session.message = f"Unlocked {door.color.value} door!"
                return True
            else:
                session.message = f"Locked {door.color.value} door - need {door.color.value} key!"
                return False

        if not session.level.is_walkable(new_x, new_y):
            session.message = "You can't move there - it's a wall!"
            return False

        mimic_at_pos = session.get_disguised_mimic_at(new_x, new_y)
        if mimic_at_pos:
            mimic_at_pos.reveal()
            mimic_at_pos.is_chasing = True
            session.message = "It's a MIMIC! The item was a trap!"

            combat_result = session.handle_combat(mimic_at_pos)

            # Check terminal state immediately after combat (e.g., player died)
            if session.state_machine.is_terminal():
                return combat_result

            if combat_result and not mimic_at_pos.is_alive():
                session.character.move_to(new_x, new_y)
                session.notify_character_moved((current_x, current_y), session.character.position)

                item = session.get_item_at(new_x, new_y)
                if item:
                    pickup_message = session.pickup_item(item)
                    if pickup_message:
                        session.message += " | " + pickup_message

            if not session.state_machine.is_terminal():
                session.process_enemy_turns()

            return combat_result

        enemy = session.get_revealed_enemy_at(new_x, new_y)
        if enemy:
            combat_result = session.handle_combat(enemy)

            # Check terminal state immediately after combat (e.g., player died)
            if session.state_machine.is_terminal():
                return combat_result

            if combat_result and not session.state_machine.is_terminal():
                session.process_enemy_turns()
            return combat_result

        item = session.get_item_at(new_x, new_y)
        if item:
            pickup_message = session.pickup_item(item)
            if pickup_message:
                session.message = pickup_message

        session.character.move_to(new_x, new_y)
        session.notify_character_moved((current_x, current_y), session.character.position)

        if session.level.exit_position == (new_x, new_y):
            session.advance_level()
            return True

        session.process_enemy_turns()
        return True

    def handle_3d_movement(self, direction):
        session = self.session

        # Move camera according to direction
        if direction == "forward":
            success = session.camera_controller.move_forward()
        elif direction == "backward":
            success = session.camera_controller.move_backward()
        elif direction == "strafe_left":
            success = session.camera_controller.strafe_left()
        elif direction == "strafe_right":
            success = session.camera_controller.strafe_right()
        else:
            return False

        if not success:
            session.message = "Can't move there - blocked!"
            return False

        # Sync character to new camera position
        from_pos = session.character.position
        new_x, new_y = session.camera.grid_position
        session.character.move_to(new_x, new_y)
        session.notify_character_moved(from_pos, session.character.position, sync_camera=False)

        session.process_enemy_turns()
        return True

    def wait(self):
        session = self.session
        session.process_enemy_turns()
        return True
