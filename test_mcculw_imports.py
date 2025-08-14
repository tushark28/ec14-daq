#!/usr/bin/env python3
"""
Test script to verify mcculw imports work correctly
"""

def test_mcculw_imports():
    """Test mcculw imports"""
    print("Testing mcculw imports...")
    
    try:
        from mcculw import ul
        print("✓ mcculw.ul imported successfully")
    except ImportError as e:
        print(f"✗ mcculw.ul import failed: {e}")
        return False
    
    try:
        from mcculw.enums import ULRange
        print("✓ ULRange imported successfully")
    except ImportError as e:
        print(f"✗ ULRange import failed: {e}")
        return False
    
    try:
        from mcculw.enums import ScanOptions
        print("✓ ScanOptions imported successfully")
    except ImportError as e:
        print(f"✗ ScanOptions import failed: {e}")
        return False
    
    try:
        from mcculw.ul import ULError
        print("✓ ULError imported successfully")
    except ImportError as e:
        print(f"✗ ULError import failed: {e}")
        return False
    
    # Test enum values
    try:
        from mcculw.enums import ULRange
        print(f"✓ ULRange.BIP5VOLTS = {ULRange.BIP5VOLTS}")
    except Exception as e:
        print(f"✗ ULRange.BIP5VOLTS failed: {e}")
        return False
    
    return True

def test_ec14_imports():
    """Test EC14 application imports"""
    print("\nTesting EC14 imports...")
    
    try:
        from ec14_daq.config.device_config import DeviceConfig
        print("✓ DeviceConfig imported successfully")
        
        # Test range conversion
        range_value = DeviceConfig.get_range_value("±5V")
        print(f"✓ Range conversion: ±5V -> {range_value}")
        
    except ImportError as e:
        print(f"✗ DeviceConfig import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ DeviceConfig test failed: {e}")
        return False
    
    try:
        from ec14_daq.hardware.device_manager import DeviceManager
        print("✓ DeviceManager imported successfully")
    except ImportError as e:
        print(f"✗ DeviceManager import failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("MCCULW Import Test")
    print("=" * 30)
    
    if not test_mcculw_imports():
        print("\n❌ MCCULW imports failed")
        return False
    
    if not test_ec14_imports():
        print("\n❌ EC14 imports failed")
        return False
    
    print("\n✅ All imports successful!")
    return True

if __name__ == "__main__":
    main()
