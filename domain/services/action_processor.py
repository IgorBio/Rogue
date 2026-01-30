"""ActionProcessor: centralizes player action handling.

This service delegates to GameSession's 2D/3D handlers and enforces
state checks (sleep, terminal states) so the session stays thin.
"""
from domain.services.game_states import GameState


class ActionProcessor:
    def __init__(self, session):
        self.session = session

    def process_action(self, action_type, action_data):
        """Process an action, enforcing state checks and delegating to
        the appropriate 2D/3D handlers on the `GameSession`.

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

        # Delegate to 3D or 2D processor
        if self.session.is_3d_mode():
            return self.session._process_action_3d(action_type, action_data)
        else:
            return self.session._process_action_2d(action_type, action_data)
