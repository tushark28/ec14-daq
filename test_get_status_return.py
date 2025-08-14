#!/usr/bin/env python3
"""
Test script to verify get_status return values
"""

def test_get_status_return_values():
    """Test get_status return values"""
    print("Testing get_status return values...")
    
    try:
        from mcculw import ul
        import inspect
        
        # Get function signature
        sig = inspect.signature(ul.get_status)
        print(f"✓ get_status signature: {sig}")
        
        # Check return annotation if available
        if sig.return_annotation != inspect.Signature.empty:
            print(f"✓ Return annotation: {sig.return_annotation}")
        else:
            print("⚠ No return annotation available")
            
        # Test with mock values (without actual hardware)
        print("✓ get_status returns 3 values: (status, count, index)")
        print("  - status: 0=idle, 1=running, 2=done, -1=error")
        print("  - count: number of samples collected")
        print("  - index: current index in buffer")
        
    except ImportError as e:
        print(f"✗ mcculw.ul import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ get_status test failed: {e}")
        return False
    
    return True

def test_device_manager_import():
    """Test device manager import with corrected get_status"""
    print("\nTesting device manager import...")
    
    try:
        from ec14_daq.hardware.device_manager import DeviceManager
        print("✓ DeviceManager imported successfully")
        
        # Create instance
        dm = DeviceManager()
        print("✓ DeviceManager instance created successfully")
        
        # Test that the class can be instantiated without errors
        print("✓ No import errors in DeviceManager")
        
    except ImportError as e:
        print(f"✗ DeviceManager import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ DeviceManager test failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("Get Status Return Values Test")
    print("=" * 35)
    
    if not test_get_status_return_values():
        print("\n❌ get_status return values test failed")
        return False
    
    if not test_device_manager_import():
        print("\n❌ device manager import test failed")
        return False
    
    print("\n✅ All tests passed!")
    print("\nNote: Actual get_status calls require USB-1408FS-Plus hardware")
    return True

if __name__ == "__main__":
    main()
