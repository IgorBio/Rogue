#!/usr/bin/env python3
"""
Test script for texture system validation.
Run this to verify all textures are correctly initialized.
"""

import sys
sys.path.insert(0, '.')

from presentation.rendering.texture_system import TextureManager, get_texture_manager


def _run_texture_initialization():
    """Run texture initialization checks and return success flag."""
    print("=" * 70)
    print("TEXTURE SYSTEM VALIDATION")
    print("=" * 70)
    
    tm = get_texture_manager()
    
    print(f"\n✓ Loaded {len(tm.textures)} textures")
    
    # Test each texture
    errors = []
    for name, texture in tm.textures.items():
        print(f"\nTesting texture: {name}")
        print(f"  Dimensions: {texture.width}x{texture.height}")
        
        # Check dimensions
        if texture.width <= 0 or texture.height <= 0:
            errors.append(f"{name}: Invalid dimensions {texture.width}x{texture.height}")
            continue
        
        # Check pattern
        if not texture.pattern:
            errors.append(f"{name}: Empty pattern")
            continue
        
        if len(texture.pattern) != texture.height:
            errors.append(f"{name}: Pattern height mismatch (expected {texture.height}, got {len(texture.pattern)})")
        
        # Check each row
        for i, row in enumerate(texture.pattern):
            if len(row) != texture.width:
                errors.append(f"{name}: Row {i} width mismatch (expected {texture.width}, got {len(row)})")
                break
        
        # Test sampling at various points
        test_points = [
            (0.0, 0.0), (0.5, 0.5), (0.99, 0.99),
            (0.0, 0.5), (0.5, 0.0), (0.99, 0.0), (0.0, 0.99)
        ]
        
        for x, y in test_points:
            try:
                char = texture.sample(x, y)
                if not isinstance(char, str) or len(char) != 1:
                    errors.append(f"{name}: Invalid character at ({x}, {y}): {repr(char)}")
            except Exception as e:
                errors.append(f"{name}: Sampling error at ({x}, {y}): {e}")
        
        if not errors:
            print(f"  ✓ All tests passed")
    
    print("\n" + "=" * 70)
    if errors:
        print("❌ ERRORS FOUND:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ ALL TEXTURES VALID")
        return True



def test_texture_initialization():
    """Test that all textures are correctly initialized."""
    assert _run_texture_initialization()

def test_texture_manager_methods():
    """Test TextureManager methods."""
    print("\n" + "=" * 70)
    print("TEXTURE MANAGER METHODS TEST")
    print("=" * 70)
    
    tm = get_texture_manager()
    
    # Test get_texture
    print("\n1. Testing get_texture()...")
    textures_to_test = [
        'room_wall', 'room_wall_0', 'room_wall_1', 'room_wall_2', 'room_wall_3',
        'corridor_wall', 'corridor_wall_0', 'corridor_wall_1', 'corridor_wall_2',
        'room_wall_entrance', 'door', 'locked_door',
        'corner_nw', 'corner_ne', 'corner_sw', 'corner_se'
    ]
    
    for name in textures_to_test:
        texture = tm.get_texture(name)
        if texture:
            print(f"  ✓ {name}: {texture.width}x{texture.height}")
        else:
            print(f"  ❌ {name}: NOT FOUND")
    
    # Test get_room_wall_texture
    print("\n2. Testing get_room_wall_texture()...")
    for room_id in range(5):
        texture = tm.get_room_wall_texture(room_id)
        if texture:
            print(f"  ✓ Room {room_id}: {texture.name}")
        else:
            print(f"  ❌ Room {room_id}: FAILED")
    
    # Test get_corridor_wall_texture
    print("\n3. Testing get_corridor_wall_texture()...")
    for corridor_id in range(4):
        texture = tm.get_corridor_wall_texture(corridor_id)
        if texture:
            print(f"  ✓ Corridor {corridor_id}: {texture.name}")
        else:
            print(f"  ❌ Corridor {corridor_id}: FAILED")
    
    # Test sample_texture
    print("\n4. Testing sample_texture()...")
    test_samples = [
        ('room_wall', 0.5, 0.5),
        ('corridor_wall', 0.25, 0.75),
        ('door', 0.5, 0.5),
        ('room_wall_entrance', 0.5, 0.5),
    ]
    
    for name, x, y in test_samples:
        try:
            char = tm.sample_texture(name, x, y)
            print(f"  ✓ {name} at ({x}, {y}): '{char}'")
        except Exception as e:
            print(f"  ❌ {name} at ({x}, {y}): {e}")
    
    print("\n✅ TextureManager methods test complete")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n" + "=" * 70)
    print("EDGE CASES TEST")
    print("=" * 70)
    
    tm = get_texture_manager()
    
    # Test boundary coordinates
    print("\n1. Testing boundary coordinates...")
    test_textures = ['room_wall', 'corridor_wall', 'door']
    boundary_coords = [
        (0.0, 0.0), (1.0, 1.0), (0.0, 1.0), (1.0, 0.0),
        (0.9999, 0.9999), (0.0001, 0.0001)
    ]
    
    errors = []
    for texture_name in test_textures:
        texture = tm.get_texture(texture_name)
        if not texture:
            continue
        
        for x, y in boundary_coords:
            try:
                char = texture.sample(x, y)
                if not char:
                    errors.append(f"{texture_name} at ({x}, {y}): Empty character")
            except Exception as e:
                errors.append(f"{texture_name} at ({x}, {y}): {e}")
    
    if errors:
        print("  ❌ Errors found:")
        for error in errors:
            print(f"    - {error}")
    else:
        print("  ✓ All boundary tests passed")
    
    # Test invalid texture names
    print("\n2. Testing invalid texture names...")
    invalid_names = ['nonexistent', '', None, 'invalid_texture_123']
    for name in invalid_names:
        try:
            result = tm.sample_texture(name, 0.5, 0.5)
            print(f"  ✓ '{name}': Returned fallback '{result}'")
        except Exception as e:
            print(f"  ❌ '{name}': Unexpected error: {e}")
    
    print("\n✅ Edge cases test complete")


def main():
    """Run all tests."""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + " " * 20 + "TEXTURE SYSTEM TEST SUITE" + " " * 23 + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    results = []
    
    # Run tests
    results.append(("Texture Initialization", _run_texture_initialization()))
    results.append(("TextureManager Methods", test_texture_manager_methods()))
    results.append(("Edge Cases", test_edge_cases()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Texture system is ready to use.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED! Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
