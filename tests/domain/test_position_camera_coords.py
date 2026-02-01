"""
Tests for Position camera coordinate conversion methods.
"""

import pytest
from domain.entities.position import Position


class TestPositionToCameraCoords:
    """Test Position.to_camera_coords method."""
    
    def test_to_camera_coords_default_offset(self):
        """Test conversion with default 0.5 offset."""
        pos = Position(10, 20)
        cam_x, cam_y = pos.to_camera_coords()
        
        assert cam_x == 10.5
        assert cam_y == 20.5
    
    def test_to_camera_coords_custom_offset(self):
        """Test conversion with custom offset."""
        pos = Position(10, 20)
        cam_x, cam_y = pos.to_camera_coords(offset=0.3)
        
        assert cam_x == 10.3
        assert cam_y == 20.3
    
    def test_to_camera_coords_zero_offset(self):
        """Test conversion with zero offset."""
        pos = Position(10, 20)
        cam_x, cam_y = pos.to_camera_coords(offset=0.0)
        
        assert cam_x == 10.0
        assert cam_y == 20.0
    
    def test_to_camera_coords_returns_float(self):
        """Test that result is float."""
        pos = Position(10, 20)
        cam_x, cam_y = pos.to_camera_coords()
        
        assert isinstance(cam_x, float)
        assert isinstance(cam_y, float)


class TestPositionFromCameraCoords:
    """Test Position.from_camera_coords class method."""
    
    def test_from_camera_coords_floor_mode(self):
        """Test conversion with floor mode (default)."""
        pos = Position.from_camera_coords(10.7, 20.3)
        
        assert pos.x == 10
        assert pos.y == 20
    
    def test_from_camera_coords_round_mode(self):
        """Test conversion with round mode."""
        pos = Position.from_camera_coords(10.7, 20.3, snap_mode='round')
        
        assert pos.x == 11
        assert pos.y == 20
    
    def test_from_camera_coords_round_half_to_even(self):
        """Test rounding behavior at .5 (banker's rounding)."""
        # Python uses "round half to even" (banker's rounding)
        # 10.5 rounds to 10 (even)
        # 20.5 rounds to 20 (even)
        # 11.5 rounds to 12 (even)
        pos = Position.from_camera_coords(10.5, 20.5, snap_mode='round')
        
        assert pos.x == 10  # Even
        assert pos.y == 20  # Even
        
        # 11.5 rounds to 12
        pos2 = Position.from_camera_coords(11.5, 21.5, snap_mode='round')
        assert pos2.x == 12
        assert pos2.y == 22
    
    def test_from_camera_coords_returns_position(self):
        """Test that result is Position instance."""
        pos = Position.from_camera_coords(10.7, 20.3)
        
        assert isinstance(pos, Position)
    
    def test_from_camera_coords_invalid_mode(self):
        """Test that invalid snap_mode raises error."""
        with pytest.raises(ValueError, match="Unknown snap_mode"):
            Position.from_camera_coords(10.7, 20.3, snap_mode='invalid')


class TestPositionCameraCoordsRoundTrip:
    """Test round-trip conversion between Position and camera coordinates."""
    
    def test_round_trip_position_to_camera_and_back(self):
        """Test converting Position → Camera → Position."""
        original = Position(10, 20)
        cam_x, cam_y = original.to_camera_coords()
        result = Position.from_camera_coords(cam_x, cam_y)
        
        assert result.x == original.x
        assert result.y == original.y
    
    def test_round_trip_camera_to_position_and_back(self):
        """Test converting Camera → Position → Camera."""
        original_cam_x, original_cam_y = 10.5, 20.5
        position = Position.from_camera_coords(original_cam_x, original_cam_y)
        result_cam_x, result_cam_y = position.to_camera_coords()
        
        assert result_cam_x == original_cam_x
        assert result_cam_y == original_cam_y
    
    def test_round_trip_not_exact_for_non_centered(self):
        """Test that non-centered camera coords lose precision."""
        original_cam_x, original_cam_y = 10.7, 20.8
        position = Position.from_camera_coords(original_cam_x, original_cam_y)
        result_cam_x, result_cam_y = position.to_camera_coords()
        
        # Result is at 10.5, 20.5 (position 10, 20 + 0.5 offset)
        assert result_cam_x == 10.5
        assert result_cam_y == 20.5


class TestPositionCameraCoordsEdgeCases:
    """Test edge cases for camera coordinate conversion."""
    
    def test_negative_coordinates(self):
        """Test conversion with negative coordinates."""
        pos = Position(-10, -20)
        cam_x, cam_y = pos.to_camera_coords()
        
        assert cam_x == -9.5
        assert cam_y == -19.5
    
    def test_zero_coordinates(self):
        """Test conversion with zero coordinates."""
        pos = Position(0, 0)
        cam_x, cam_y = pos.to_camera_coords()
        
        assert cam_x == 0.5
        assert cam_y == 0.5
    
    def test_large_coordinates(self):
        """Test conversion with large coordinates."""
        pos = Position(1000, 2000)
        cam_x, cam_y = pos.to_camera_coords()
        
        assert cam_x == 1000.5
        assert cam_y == 2000.5
