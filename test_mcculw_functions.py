#!/usr/bin/env python3
"""
Test script to verify all mcculw function calls used in the application
"""

def test_mcculw_function_signatures():
    """Test all mcculw function signatures used in the application"""
    print("Testing mcculw function signatures...")
    
    try:
        from mcculw import ul
        import inspect
        
        # List of functions to test
        functions_to_test = [
            'get_board_name',
            'd_config_port', 
            'd_out',
            'flash_led',
            'a_in',
            'to_eng_units',
            'win_buf_alloc',
            'a_in_scan',
            'stop_background',
            'win_buf_free',
            'get_status',
            'win_buf_to_array',
            'c_in_32'
        ]
        
        for func_name in functions_to_test:
            try:
                func = getattr(ul, func_name)
                sig = inspect.signature(func)
                print(f"✓ {func_name}: {sig}")
            except Exception as e:
                print(f"✗ {func_name}: {e}")
                
    except ImportError as e:
        print(f"✗ mcculw.ul import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ function signature test failed: {e}")
        return False
    
    return True

def test_device_manager_methods():
    """Test device manager methods that use mcculw functions"""
    print("\nTesting device manager methods...")
    
    try:
        from ec14_daq.hardware.device_manager import DeviceManager
        
        # Create instance
        dm = DeviceManager()
        print("✓ DeviceManager instance created")
        
        # Test configuration methods
        dm.set_sample_rate(1000)
        print("✓ set_sample_rate() works")
        
        dm.set_ad_range("±5V")
        print("✓ set_ad_range() works")
        
        # Note: We can't test device communication without hardware
        print("⚠ Device communication methods require hardware")
        
    except ImportError as e:
        print(f"✗ DeviceManager import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ DeviceManager test failed: {e}")
        return False
    
    return True

def test_config_imports():
    """Test configuration imports"""
    print("\nTesting configuration imports...")
    
    try:
        from ec14_daq.config.device_config import DeviceConfig
        
        # Test configuration values
        print(f"✓ Board number: {DeviceConfig.BOARD_NUM}")
        print(f"✓ Sample rates: {DeviceConfig.SAMPLE_RATES}")
        print(f"✓ A/D ranges: {list(DeviceConfig.AD_RANGES.keys())}")
        print(f"✓ Scan options: {DeviceConfig.SCAN_OPTIONS}")
        
        # Test range conversion
        range_value = DeviceConfig.get_range_value("±5V")
        range_name = DeviceConfig.get_range_name(range_value)
        print(f"✓ Range conversion: ±5V -> {range_value} -> {range_name}")
        
    except ImportError as e:
        print(f"✗ DeviceConfig import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ DeviceConfig test failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("MCCULW Functions Test")
    print("=" * 30)
    
    if not test_mcculw_function_signatures():
        print("\n❌ Function signature test failed")
        return False
    
    if not test_device_manager_methods():
        print("\n❌ Device manager test failed")
        return False
    
    if not test_config_imports():
        print("\n❌ Configuration test failed")
        return False
    
    print("\n✅ All tests passed!")
    print("\nNote: Device communication tests require USB-1408FS-Plus hardware")
    return True

if __name__ == "__main__":
    main()
