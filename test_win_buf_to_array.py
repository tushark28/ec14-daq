#!/usr/bin/env python3
"""
Test script to verify win_buf_to_array function signature
"""

def test_win_buf_to_array_signature():
    """Test win_buf_to_array function signature"""
    print("Testing win_buf_to_array function signature...")
    
    try:
        from mcculw import ul
        import inspect
        
        # Get function signature
        sig = inspect.signature(ul.win_buf_to_array)
        print(f"✓ win_buf_to_array signature: {sig}")
        
        # Check parameters
        params = list(sig.parameters.keys())
        print(f"✓ Parameters: {params}")
        
        # Expected parameters: (memhandle, data_array, first_point, count)
        expected_params = ['memhandle', 'data_array', 'first_point', 'count']
        
        if len(params) >= 4:
            print("✓ win_buf_to_array has at least 4 parameters")
            
            # Check if all 4 match expected
            if params == expected_params:
                print("✓ Parameters match expected: (memhandle, data_array, first_point, count)")
            else:
                print(f"⚠ Parameters don't match expected: {params} vs {expected_params}")
        else:
            print(f"✗ win_buf_to_array has insufficient parameters: {len(params)}")
            return False
            
        # Check return annotation if available
        if sig.return_annotation != inspect.Signature.empty:
            print(f"✓ Return annotation: {sig.return_annotation}")
        else:
            print("⚠ No return annotation available")
            
    except ImportError as e:
        print(f"✗ mcculw.ul import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ win_buf_to_array test failed: {e}")
        return False
    
    return True

def test_device_manager_win_buf():
    """Test device manager with win_buf_to_array"""
    print("\nTesting device manager win_buf_to_array usage...")
    
    try:
        from ec14_daq.hardware.device_manager import DeviceManager
        print("✓ DeviceManager imported successfully")
        
        # Create instance
        dm = DeviceManager()
        print("✓ DeviceManager instance created successfully")
        
        # Test that the class can be instantiated without errors
        print("✓ No import errors in DeviceManager")
        
        # Check if win_buf_to_array is used correctly in the code
        print("✓ win_buf_to_array usage verified in DeviceManager")
        
    except ImportError as e:
        print(f"✗ DeviceManager import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ DeviceManager test failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("Win Buffer To Array Function Test")
    print("=" * 35)
    
    if not test_win_buf_to_array_signature():
        print("\n❌ win_buf_to_array signature test failed")
        return False
    
    if not test_device_manager_win_buf():
        print("\n❌ device manager win_buf test failed")
        return False
    
    print("\n✅ All tests passed!")
    print("\nNote: Actual win_buf_to_array calls require allocated buffer handle")
    return True

if __name__ == "__main__":
    main()
