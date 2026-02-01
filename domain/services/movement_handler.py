"""domain.services.movement_handler
Canonical MovementHandler: single-class, instance-bound to a GameSession.

This file deliberately contains a single, unambiguous definition of
`MovementHandler` with a constructor that accepts the owning `session`.

Statistics are now tracked via events published to the EventBus.
"""
from domain.event_bus import event_bus
from domain.events import PlayerMovedEvent


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

        mimic_at_pos = session._get_disguised_mimic_at(new_x, new_y)
        if mimic_at_pos:
            mimic_at_pos.reveal()
            mimic_at_pos.is_chasing = True
            session.message = "It's a MIMIC! The item was a trap!"

            combat_result = session._handle_combat(mimic_at_pos)

            # Check terminal state immediately after combat (e.g., player died)
            if session.state_machine.is_terminal():
                return combat_result

            if combat_result and not mimic_at_pos.is_alive():
                session.character.move_to(new_x, new_y)

                if session.is_3d_mode():
                    session.camera.x = new_x
                    session.camera.y = new_y

                if session.should_use_fog_of_war():
                    session.fog_of_war.update_visibility(session.character.position)

                # Publish movement event for statistics tracking
                try:
                    event_bus.publish(PlayerMovedEvent(
                        from_pos=(current_x, current_y),
                        to_pos=(new_x, new_y)
                    ))
                except Exception:
                    pass

                item = session._get_item_at(new_x, new_y)
                if item:
                    pickup_message = session._pickup_item(item)
                    if pickup_message:
                        session.message += " | " + pickup_message

            if not session.state_machine.is_terminal():
                session._process_enemy_turns()

            return combat_result

        enemy = session._get_revealed_enemy_at(new_x, new_y)
        if enemy:
            combat_result = session._handle_combat(enemy)

            # Check terminal state immediately after combat (e.g., player died)
            if session.state_machine.is_terminal():
                return combat_result

            if combat_result and not session.state_machine.is_terminal():
                session._process_enemy_turns()
            return combat_result

        item = session._get_item_at(new_x, new_y)
        if item:
            pickup_message = session._pickup_item(item)
            if pickup_message:
                session.message = pickup_message

        session.character.move_to(new_x, new_y)

        if session.is_3d_mode():
            session.camera.x = new_x
            session.camera.y = new_y

        if session.should_use_fog_of_war():
            session.fog_of_war.update_visibility(session.character.position)

        # Publish movement event for statistics tracking
        try:
            event_bus.publish(PlayerMovedEvent(
                from_pos=(current_x, current_y),
                to_pos=(new_x, new_y)
            ))
        except Exception:
            pass

        if session.level.exit_position == (new_x, new_y):
            session._advance_level()
            return True

        session._process_enemy_turns()
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
        new_x, new_y = session.camera.grid_position
        session.character.move_to(new_x, new_y)

        if session.should_use_fog_of_war():
            session.fog_of_war.update_visibility(session.character.position)

        # Publish movement event for statistics tracking
        try:
            old_pos = (current_x, current_y)
        except NameError:
            old_pos = (0, 0)
        try:
            event_bus.publish(PlayerMovedEvent(
                from_pos=old_pos,
                to_pos=(new_x, new_y)
            ))
        except Exception:
            pass

        # Check for level exit
        if session.level.exit_position == (new_x, new_y):
            session._advance_level()
            return True

        session._check_automatic_pickup()
        session._process_enemy_turns()
        return True
