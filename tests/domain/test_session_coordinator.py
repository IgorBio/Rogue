"""
Tests for SessionCoordinator.
"""

import pytest
from unittest.mock import Mock, MagicMock
from domain.session_coordinator import SessionCoordinator


class MockSession:
    """Mock GameSession for testing."""
    pass


class MockStats:
    """Mock Statistics for testing."""
    pass


class MockDifficultyManager:
    """Mock DifficultyManager for testing."""
    pass


@pytest.fixture
def coordinator():
    """Create a coordinator with mocked dependencies."""
    session = MockSession()
    stats = MockStats()
    difficulty = MockDifficultyManager()
    return SessionCoordinator(session, stats, difficulty)


class TestSessionCoordinatorInit:
    """Test SessionCoordinator initialization."""
    
    def test_stores_references(self):
        """Test that coordinator stores session, stats, difficulty."""
        session = MockSession()
        stats = MockStats()
        difficulty = MockDifficultyManager()
        
        coord = SessionCoordinator(session, stats, difficulty)
        
        assert coord.session is session
        assert coord.stats is stats
        assert coord.difficulty_manager is difficulty
    
    def test_services_none_before_init(self):
        """Test that services are None before initialize_services."""
        coord = SessionCoordinator(MockSession(), MockStats(), MockDifficultyManager())
        
        assert coord._combat_system is None
        assert coord._action_processor is None
        assert coord._level_manager is None


class TestSessionCoordinatorServices:
    """Test SessionCoordinator service access."""
    
    def test_lazy_init_combat_system(self, coordinator):
        """Test combat_system property lazy initialization."""
        cs = coordinator.combat_system
        
        assert cs is not None
        assert coordinator._combat_system is cs  # Same instance on second access
    
    def test_lazy_init_action_processor(self, coordinator):
        """Test action_processor property lazy initialization."""
        ap = coordinator.action_processor
        
        assert ap is not None
        assert coordinator._action_processor is ap
    
    def test_lazy_init_level_manager(self, coordinator):
        """Test level_manager property lazy initialization."""
        lm = coordinator.level_manager
        
        assert lm is not None
        assert coordinator._level_manager is lm
    
    def test_lazy_init_movement_handler(self, coordinator):
        """Test movement_handler property lazy initialization."""
        mh = coordinator.movement_handler
        
        assert mh is not None
        assert coordinator._movement_handler is mh
    
    def test_lazy_init_enemy_turn_processor(self, coordinator):
        """Test enemy_turn_processor property lazy initialization."""
        etp = coordinator.enemy_turn_processor
        
        assert etp is not None
        assert coordinator._enemy_turn_processor is etp
    
    def test_lazy_init_inventory_manager(self, coordinator):
        """Test inventory_manager property lazy initialization."""
        im = coordinator.inventory_manager
        
        assert im is not None
        assert coordinator._inventory_manager is im
    
    def test_lazy_init_enemy_locator(self, coordinator):
        """Test enemy_locator property lazy initialization."""
        el = coordinator.enemy_locator
        
        assert el is not None
        assert coordinator._enemy_locator is el


class TestSessionCoordinatorDelegation:
    """Test that coordinator correctly delegates to services."""
    
    def test_process_action_delegates(self, coordinator):
        """Test process_action delegates to action_processor."""
        coordinator._action_processor = Mock()
        coordinator._action_processor.process_action.return_value = True
        
        result = coordinator.process_action('move', {'direction': 'north'})
        
        coordinator._action_processor.process_action.assert_called_once_with('move', {'direction': 'north'})
        assert result is True
    
    def test_process_enemy_turns_delegates(self, coordinator):
        """Test process_enemy_turns delegates to enemy_turn_processor."""
        coordinator._enemy_turn_processor = Mock()
        
        coordinator.process_enemy_turns()
        
        coordinator._enemy_turn_processor.process_enemy_turns.assert_called_once()
    
    def test_handle_movement_delegates_2d(self, coordinator):
        """Test handle_movement delegates to handle_2d_movement for tuple directions."""
        coordinator._movement_handler = Mock()
        coordinator._movement_handler.handle_2d_movement.return_value = True

        result = coordinator.handle_movement((0, -1))  # north as tuple

        coordinator._movement_handler.handle_2d_movement.assert_called_once_with((0, -1))
        assert result is True

    def test_handle_movement_delegates_3d(self, coordinator):
        """Test handle_movement delegates to handle_3d_movement for string directions."""
        coordinator._movement_handler = Mock()
        coordinator._movement_handler.handle_3d_movement.return_value = True

        result = coordinator.handle_movement('forward')

        coordinator._movement_handler.handle_3d_movement.assert_called_once_with(
            'forward', camera_controller=None
        )
        assert result is True
    
    def test_handle_combat_delegates(self, coordinator):
        """Test handle_combat delegates to combat_system."""
        coordinator._combat_system = Mock()
        coordinator._combat_system.process_player_attack.return_value = 'result'
        enemy = Mock()
        
        result = coordinator.handle_combat(enemy)
        
        coordinator._combat_system.process_player_attack.assert_called_once_with(coordinator.session, enemy)
        assert result == 'result'
    
    def test_pickup_item_delegates(self, coordinator):
        """Test pickup_item delegates to inventory_manager."""
        coordinator._inventory_manager = Mock()
        coordinator._inventory_manager.pickup_item.return_value = 'Picked up sword'
        item = Mock()
        
        result = coordinator.pickup_item(item)
        
        coordinator._inventory_manager.pickup_item.assert_called_once_with(item)
        assert result == 'Picked up sword'
    
    def test_has_pending_selection_delegates(self, coordinator):
        """Test has_pending_selection delegates to inventory_manager."""
        coordinator._inventory_manager = Mock()
        coordinator._inventory_manager.has_pending_selection.return_value = True
        
        result = coordinator.has_pending_selection()
        
        coordinator._inventory_manager.has_pending_selection.assert_called_once()
        assert result is True


class TestSessionCoordinatorLocatorMethods:
    """Test locator method delegations."""
    
    def test_get_disguised_mimic_at_delegates(self, coordinator):
        """Test get_disguised_mimic_at delegates to enemy_locator."""
        coordinator._enemy_locator = Mock()
        coordinator._enemy_locator.get_disguised_mimic_at.return_value = 'mimic'
        level = Mock()
        
        result = coordinator.get_disguised_mimic_at(level, 10, 20)
        
        coordinator._enemy_locator.get_disguised_mimic_at.assert_called_once_with(level, 10, 20)
        assert result == 'mimic'
    
    def test_get_revealed_enemy_at_delegates(self, coordinator):
        """Test get_revealed_enemy_at delegates to enemy_locator."""
        coordinator._enemy_locator = Mock()
        level = Mock()
        
        coordinator.get_revealed_enemy_at(level, 10, 20)
        
        coordinator._enemy_locator.get_revealed_enemy_at.assert_called_once_with(level, 10, 20)
    
    def test_get_item_at_delegates(self, coordinator):
        """Test get_item_at delegates to enemy_locator."""
        coordinator._enemy_locator = Mock()
        level = Mock()
        
        coordinator.get_item_at(level, 10, 20)
        
        coordinator._enemy_locator.get_item_at.assert_called_once_with(level, 10, 20)


class TestSessionCoordinatorSelectionMethods:
    """Test selection method delegations."""
    
    def test_request_food_selection_delegates(self, coordinator):
        """Test request_food_selection delegates to inventory_manager."""
        coordinator._inventory_manager = Mock()
        
        coordinator.request_food_selection()
        
        coordinator._inventory_manager.request_food_selection.assert_called_once()
    
    def test_request_weapon_selection_delegates(self, coordinator):
        """Test request_weapon_selection delegates to inventory_manager."""
        coordinator._inventory_manager = Mock()
        
        coordinator.request_weapon_selection()
        
        coordinator._inventory_manager.request_weapon_selection.assert_called_once()
    
    def test_complete_food_selection_delegates(self, coordinator):
        """Test complete_food_selection delegates to inventory_manager."""
        coordinator._inventory_manager = Mock()
        
        coordinator.complete_food_selection(0)
        
        coordinator._inventory_manager._complete_food_selection.assert_called_once_with(0)


class TestSessionCoordinatorGenerateLevel:
    """Test generate_level method."""
    
    def test_generate_level_delegates(self, coordinator):
        """Test generate_level delegates to level_manager."""
        coordinator._level_manager = Mock()
        coordinator._level_manager.generate_level.return_value = 'level'
        character = Mock()
        
        result = coordinator.generate_level(5, character, test_mode=True)
        
        coordinator._level_manager.generate_level.assert_called_once_with(
            5, character=character, stats=coordinator.stats, test_mode=True
        )
        assert result == 'level'


class TestSessionCoordinatorAdvanceLevel:
    """Test advance_level method."""
    
    def test_advance_level_delegates(self, coordinator):
        """Test advance_level delegates to level_manager."""
        coordinator._level_manager = Mock()
        coordinator._level_manager.advance_and_setup.return_value = True
        session = Mock()
        
        result = coordinator.advance_level(session, 21)
        
        coordinator._level_manager.advance_and_setup.assert_called_once_with(session, 21)
        assert result is True
