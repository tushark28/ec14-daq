#!/usr/bin/env python3
"""
Test script to verify get_status function call
"""

def test_get_status_signature():
    """Test get_status function signature"""
    print("Testing get_status function signature...")
    
    try:
        from mcculw import ul
        print("✓ mcculw.ul imported successfully")
        
        # Test get_status function signature
        import inspect
        sig = inspect.signature(ul.get_status)
        print(f"✓ get_status signature: {sig}")
        
        # Check if it requires function_type parameter
        params = list(sig.parameters.keys())
        if 'function_type' in params or len(params) > 1:
            print("✓ get_status requires function_type parameter")
        else:
            print("⚠ get_status may not require function_type parameter")
            
    except ImportError as e:
        print(f"✗ mcculw.ul import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ get_status test failed: {e}")
        return False
    
    return True

def test_device_manager_import():
    """Test device manager import with fixed get_status"""
    print("\nTesting device manager import...")
    
    try:
        from ec14_daq.hardware.device_manager import DeviceManager
        print("✓ DeviceManager imported successfully")
        
        # Create instance
        dm = DeviceManager()
        print("✓ DeviceManager instance created successfully")
        
    except ImportError as e:
        print(f"✗ DeviceManager import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ DeviceManager test failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("Get Status Function Test")
    print("=" * 30)
    
    if not test_get_status_signature():
        print("\n❌ get_status signature test failed")
        return False
    
    if not test_device_manager_import():
        print("\n❌ device manager import test failed")
        return False
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    main()
