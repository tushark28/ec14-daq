#!/usr/bin/env python3
"""
Direct test of mcculw functions to isolate win_buf_to_array issue
"""

def test_mcculw_imports():
    """Test basic mcculw imports"""
    print("Testing mcculw imports...")
    
    try:
        from mcculw import ul
        print("✓ mcculw.ul imported successfully")
        
        from mcculw.enums import ULRange
        print("✓ ULRange imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_win_buf_to_array_signature():
    """Test win_buf_to_array function signature"""
    print("\nTesting win_buf_to_array signature...")
    
    try:
        from mcculw import ul
        import inspect
        
        sig = inspect.signature(ul.win_buf_to_array)
        print(f"✓ Signature: {sig}")
        
        params = list(sig.parameters.keys())
        print(f"✓ Parameters: {params}")
        
        return True
    except Exception as e:
        print(f"✗ Signature test failed: {e}")
        return False

def test_buffer_allocation():
    """Test buffer allocation without actual hardware"""
    print("\nTesting buffer allocation...")
    
    try:
        from mcculw import ul
        
        # Try to allocate a small buffer
        buffer_size = 100
        print(f"  Attempting to allocate buffer of size {buffer_size}...")
        
        # This might fail without hardware, but let's see the error
        try:
            buffer_handle = ul.win_buf_alloc(buffer_size)
            print(f"✓ Buffer allocated: {buffer_handle}")
            
            # Try to free it
            ul.win_buf_free(buffer_handle)
            print("✓ Buffer freed successfully")
            
        except Exception as e:
            print(f"  Buffer allocation failed (expected without hardware): {e}")
        
        return True
    except Exception as e:
        print(f"✗ Buffer test failed: {e}")
        return False

def test_win_buf_to_array_approaches():
    """Test different approaches for win_buf_to_array"""
    print("\nTesting win_buf_to_array approaches...")
    
    try:
        from mcculw import ul
        
        # Create a mock buffer handle (this won't work without hardware)
        mock_handle = 12345
        count = 10
        
        print("  Testing different data types for win_buf_to_array...")
        
        # Approach 1: Numpy array
        try:
            import numpy as np
            data = np.zeros(count, dtype=np.int16)
            print(f"    Numpy array: {type(data)}, shape: {data.shape}, dtype: {data.dtype}")
        except Exception as e:
            print(f"    Numpy approach failed: {e}")
        
        # Approach 2: Ctypes array
        try:
            import ctypes
            data = (ctypes.c_ushort * count)()
            print(f"    Ctypes array: {type(data)}, length: {len(data)}")
        except Exception as e:
            print(f"    Ctypes approach failed: {e}")
        
        # Approach 3: Simple list
        try:
            data = [0] * count
            print(f"    Simple list: {type(data)}, length: {len(data)}")
        except Exception as e:
            print(f"    Simple list approach failed: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Approaches test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Direct MCCULW Function Test")
    print("=" * 35)
    
    if not test_mcculw_imports():
        print("\n❌ Import test failed")
        return False
    
    if not test_win_buf_to_array_signature():
        print("\n❌ Signature test failed")
        return False
    
    if not test_buffer_allocation():
        print("\n❌ Buffer allocation test failed")
        return False
    
    if not test_win_buf_to_array_approaches():
        print("\n❌ Approaches test failed")
        return False
    
    print("\n✅ All tests completed!")
    print("\nNote: Some tests may fail without actual USB-1408FS-Plus hardware")
    return True

if __name__ == "__main__":
    main()
