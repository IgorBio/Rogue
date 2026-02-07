"""LevelManager: encapsulates level generation and progression.

This service delegates to `domain.level_generator.generate_level` and
coordinates level-number tracking and difficulty adjustments.

Statistics are now tracked via events published to the EventBus.
"""
from common.logging_utils import log_exception
from typing import Optional

from domain.level_generator import generate_level
from domain.event_bus import event_bus
from domain.events import LevelReachedEvent


class LevelManager:
    def __init__(self, difficulty_manager=None):
        self.difficulty_manager = difficulty_manager
        self.current_level_number = 1
        self.current_level = None

    def generate_level(self, level_number: int, character=None, stats=None, test_mode: bool = False):
        """Generate and return a Level instance for `level_number`.

        :param level_number: target level number
        :param character: optional Character for difficulty calculation
        :param stats: optional Statistics for difficulty calculation
        :param test_mode: skip difficulty adjustments in test mode
        :return: Level instance
        """
        difficulty_adjustments = None
        if not test_mode and self.difficulty_manager is not None and character is not None and stats is not None:
            difficulty_adjustments = self.difficulty_manager.calculate_difficulty_adjustment(
                character, stats, level_number
            )
            # Keep difficulty manager up-to-date
            try:
                self.difficulty_manager.update_performance(stats, character)
            except Exception as exc:
                    log_exception(exc, __name__)

        level = generate_level(level_number, difficulty_adjustments)
        self.current_level_number = level_number
        self.current_level = level
        return level

    def advance_to_next_level(self, max_levels: int) -> Optional[int]:
        """Advance level number if possible and return new number or None if at max.

        :param max_levels: maximum allowed level number
        :return: new level number or None when cannot advance
        """
        if self.current_level_number >= max_levels:
            return None
        self.current_level_number += 1
        return self.current_level_number

    def advance_and_setup(self, session, max_levels: int):
        """Advance the session to the next level and perform setup.

        This centralizes the level-advance flow previously in GameSession so
        callers can remain thin coordinators.
        """
        # Clear keys (support both old/new mapping keys)
        try:
            session.character.backpack.items[session.character.backpack.KEY] = []
        except (AttributeError, KeyError, TypeError):
            # Backwards-compat: ItemType.KEY may be used as mapping key
            try:
                from config.game_config import ItemType
                session.character.backpack.items[ItemType.KEY] = []
            except (ImportError, AttributeError, KeyError, TypeError):
                # If the structure isn't present, continue; this is non-fatal.
                pass

        new_level_num = self.advance_to_next_level(max_levels)
        if new_level_num is None:
            session.set_victory()
            session.message = "Congratulations! You've completed all levels!"
            return None

        session.current_level_number = new_level_num
        # Publish event for statistics tracking
        try:
            event_bus.publish(LevelReachedEvent(
                level_number=session.current_level_number
            ))
        except Exception as exc:
                log_exception(exc, __name__)

        # Begin level transition state before generating the new level
        if hasattr(session, 'begin_level_transition'):
            try:
                session.begin_level_transition()
            except AttributeError:
                # Older session implementations may not support this method; ignore.
                pass

        # Generate and place character
        session._generate_new_level()

        # Only complete transition if session entered LEVEL_TRANSITION
        if hasattr(session, 'complete_level_transition'):
            session.complete_level_transition()

        if not session.test_mode:
            difficulty_desc = None
            if getattr(session, 'difficulty_manager', None) is not None:
                try:
                    difficulty_desc = session.difficulty_manager.get_difficulty_description()
                except Exception:
                    # If difficulty manager fails to provide a description, fall back.
                    difficulty_desc = None
            if difficulty_desc:
                session.message = f"Advanced to level {session.current_level_number}! (Difficulty: {difficulty_desc})"
            else:
                session.message = f"Advanced to level {session.current_level_number}!"
        else:
            session.message = f"Advanced to level {session.current_level_number}!"

        if not session.test_mode:
            try:
                session.save_to_file()
            except (OSError, IOError) as exc:
                # Persist failures shouldn't stop the game flow in normal operation.
                log_exception(exc, __name__)
                if session.message:
                    session.message += " [Warning: Autosave failed]"
                else:
                    session.message = "Warning: Autosave failed"

        return new_level_num
