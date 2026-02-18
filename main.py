"""
Main entry point for the roguelike game with 3D rendering mode support.
"""
import curses
from common.logging_utils import setup_logging


def _create_view_manager():
    from presentation.view_manager import ViewManager
    from presentation.camera import Camera
    from presentation.camera import CameraController

    return ViewManager(
        auto_subscribe=True,
        camera_factory=lambda x, y, angle=0.0, fov=60.0: Camera(x, y, angle=angle, fov=fov),
        camera_controller_factory=lambda cam, lvl: CameraController(cam, lvl),
    )


def _create_new_session(save_manager, view_manager):
    from domain.game_session import GameSession
    from data.statistics import Statistics

    session = GameSession(
        statistics_factory=Statistics,
        save_manager_factory=lambda: save_manager,
    )
    session.set_view_adapter(view_manager)
    return session


def _create_test_session(save_manager, view_manager, test_config):
    from domain.game_session import GameSession
    from data.statistics import Statistics

    session = GameSession(
        test_mode=True,
        test_level=test_config['level'],
        test_fog_of_war=test_config['fog_of_war'],
        statistics_factory=Statistics,
        save_manager_factory=lambda: save_manager,
    )
    session.set_view_adapter(view_manager)
    return session


def _run_game_loop(ui, game_session):
    while not game_session.is_game_over():
        if game_session.has_pending_selection():
            ui.render_game(game_session)
            selection_request = game_session.get_pending_selection()
            selected_idx = ui.show_item_selection(selection_request)
            game_session.complete_item_selection(selected_idx)
            ui.render_game(game_session)
            game_session.message = ""
            continue

        ui.render_game(game_session)
        game_session.message = ""
        action_type, action_data = ui.get_player_action(game_session)

        if action_type == 'toggle_mode':
            if action_data and 'new_mode' in action_data:
                new_mode = action_data['new_mode']
                mode_name = "3D" if new_mode == '3d' else "2D"
                game_session.message = f"Switched to {mode_name} mode (Press Tab to switch back)"
            continue

        game_session.process_player_action(action_type, action_data)
        ui.render_game(game_session)
        game_session.message = ""


def _show_game_over(ui, stats_manager, game_session):
    stats = game_session.get_game_stats()
    if not game_session.test_mode:
        stats_manager.save_run(game_session.stats)
        current_treasure = game_session.character.backpack.treasure_value
        stats['rank'] = stats_manager.get_player_rank(current_treasure)
    return ui.show_game_over(stats, game_session.victory)


def main(stdscr):
    """Main game function with 2D/3D mode switching support."""
    setup_logging()

    from presentation.game_ui import GameUI
    from data.save_manager import SaveManager
    from data.statistics import StatisticsManager

    save_manager = SaveManager()
    stats_manager = StatisticsManager()
    view_manager = _create_view_manager()
    ui = None

    try:
        ui = GameUI(stdscr, view_manager)

        while True:
            selection = ui.show_main_menu(save_manager)

            if selection == 'quit':
                break
            if selection == 'stats':
                ui.show_statistics(stats_manager)
                continue

            game_session = None
            if selection == 'test':
                test_config = ui.show_test_mode_menu()
                if test_config is None:
                    continue
                game_session = _create_test_session(save_manager, view_manager, test_config)
                ui.display_message(
                    f"TEST MODE: Level {test_config['level']}, Fog of War: {test_config['fog_of_war']}"
                )
            elif selection == 'new':
                game_session = _create_new_session(save_manager, view_manager)
                ui.display_message("Welcome to the dungeon! Find the exit to proceed.")
            elif selection == 'continue':
                save_data = save_manager.load_game()
                if save_data is None:
                    ui.show_error("Error loading save file!")
                    continue
                game_session = save_manager.restore_game_session(save_data, view_manager=view_manager)
                game_session.set_view_adapter(view_manager)
                ui.display_message("Game loaded! Welcome back!")

            if game_session is None:
                continue

            _run_game_loop(ui, game_session)
            result = _show_game_over(ui, stats_manager, game_session)

            if result == 'quit':
                break
            if result in ('menu', 'restart'):
                ui.clear_messages()
                continue
    finally:
        if ui is not None:
            ui.cleanup()


if __name__ == "__main__":
    curses.wrapper(main)
