"""
Main entry point for the roguelike game with 3D rendering mode support.
"""
import curses
import sys
sys.path.insert(0, '.')
from common.logging_utils import setup_logging


def main(stdscr):
    """
    Main game function with 2D/3D mode switching support.
    
    Args:
        stdscr: Curses standard screen object
    """
    setup_logging()

    from domain.game_session import GameSession
    from presentation.game_ui import GameUI
    from presentation.view_manager import ViewManager
    from data.save_manager import SaveManager
    from data.statistics import StatisticsManager, Statistics
    from presentation.camera import Camera
    from presentation.camera import CameraController
    
    # Initialize managers and UI
    save_manager = SaveManager()
    stats_manager = StatisticsManager()
    
    view_manager = ViewManager(
        auto_subscribe=True,
        camera_factory=lambda x, y, angle=0.0, fov=60.0: Camera(x, y, angle=angle, fov=fov),
        camera_controller_factory=lambda cam, lvl: CameraController(cam, lvl)
    )
    ui = GameUI(stdscr, view_manager)
    
    try:
        while True:  # Main menu loop
            # Show main menu
            selection = ui.show_main_menu(save_manager)
            
            if selection == 'quit':
                break
            
            elif selection == 'stats':
                ui.show_statistics(stats_manager)
                continue
            
            elif selection == 'test':
                # Show test mode configuration
                test_config = ui.show_test_mode_menu()
                
                if test_config is None:
                    continue
                
                # Create test game session
                game_session = GameSession(
                    test_mode=True,
                    test_level=test_config['level'],
                    test_fog_of_war=test_config['fog_of_war'],
                    statistics_factory=Statistics,
                    save_manager_factory=lambda: save_manager,
                )
                ui.display_message(f"TEST MODE: Level {test_config['level']}, Fog of War: {test_config['fog_of_war']}")
            
            elif selection == 'new':
                # Create new game
                game_session = GameSession(
                    statistics_factory=Statistics,
                    save_manager_factory=lambda: save_manager,
                )
                ui.display_message("Welcome to the dungeon! Find the exit to proceed.")
            
            elif selection == 'continue':
                # Load saved game
                save_data = save_manager.load_game()
                
                if save_data is None:
                    ui.show_error("Error loading save file!")
                    continue
                
                # Restore game session
                game_session = save_manager.restore_game_session(
                    save_data,
                )
                ui.display_message("Game loaded! Welcome back!")
            
            else:
                continue
            
            # Main game loop
            while not game_session.is_game_over():
                # Check for pending item selection first
                if game_session.has_pending_selection():
                    # Render current state
                    ui.render_game(game_session)
                    
                    # Get selection request
                    selection_request = game_session.get_pending_selection()
                    
                    # Show UI and get user choice
                    selected_idx = ui.show_item_selection(selection_request)
                    
                    # Send result back to domain
                    game_session.complete_item_selection(selected_idx)
                    
                    # Render the result
                    ui.render_game(game_session)
                    
                    # Clear message for next turn
                    game_session.message = ""
                    continue
                
                # Render current state
                ui.render_game(game_session)
                
                # Clear message AFTER rendering
                game_session.message = ""
                
                # Get player input
                action_type, action_data = ui.get_player_action(game_session)
                
                # Handle mode toggle
                if action_type == 'toggle_mode':
                    if action_data and 'new_mode' in action_data:
                        new_mode = action_data['new_mode']
                        mode_name = "3D" if new_mode == '3d' else "2D"
                        game_session.message = f"Switched to {mode_name} mode (Press Tab to switch back)"
                    # Continue to re-render with new mode
                    continue
                
                # Process action (domain logic)
                game_session.process_player_action(action_type, action_data)
                
                # Render immediately to show action results
                ui.render_game(game_session)
                
                # Clear message for next iteration
                game_session.message = ""
            
            # Only save statistics if not in test mode
            if not game_session.test_mode:
                # Game over - save statistics
                stats_manager.save_run(game_session.stats)
                
                # Calculate rank
                leaderboard = stats_manager.load_leaderboard()
                current_treasure = game_session.character.backpack.treasure_value
                rank = sum(1 for run in leaderboard 
                          if run.get('treasure_collected', 0) > current_treasure) + 1
                
                # Prepare stats for display
                stats = game_session.get_game_stats()
                stats['rank'] = rank
                
                # Show game over screen
                result = ui.show_game_over(stats, game_session.victory)
            else:
                # Test mode - just show simple message
                stats = game_session.get_game_stats()
                result = ui.show_game_over(stats, game_session.victory)
            
            if result == 'quit':
                break
            elif result == 'menu':
                ui.clear_messages()
                continue
            elif result == 'restart':
                ui.clear_messages()
                pass
            else:
                continue
    
    finally:
        # Clean up
        ui.cleanup()


if __name__ == "__main__":
    curses.wrapper(main)
