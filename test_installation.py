#!/usr/bin/env python3
"""
Test script to verify EC14 application installation
"""

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import numpy as np
        print("✓ NumPy imported successfully")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    try:
        import PyQt5
        print("✓ PyQt5 imported successfully")
    except ImportError as e:
        print(f"✗ PyQt5 import failed: {e}")
        return False
    
    try:
        import pyqtgraph as pg
        print("✓ PyQtGraph imported successfully")
    except ImportError as e:
        print(f"✗ PyQtGraph import failed: {e}")
        return False
    
    try:
        import scipy
        print("✓ SciPy imported successfully")
    except ImportError as e:
        print(f"✗ SciPy import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✓ Pandas imported successfully")
    except ImportError as e:
        print(f"✗ Pandas import failed: {e}")
        return False
    
    try:
        import matplotlib
        print("✓ Matplotlib imported successfully")
    except ImportError as e:
        print(f"✗ Matplotlib import failed: {e}")
        return False
    
    try:
        import mcculw
        print("✓ MCCULW imported successfully")
    except ImportError as e:
        print(f"✗ MCCULW import failed: {e}")
        print("  Note: MCCULW requires Measurement Computing Universal Library")
        return False
    
    return True

def test_ec14_modules():
    """Test EC14 application modules"""
    print("\nTesting EC14 modules...")
    
    try:
        from ec14_daq.config.device_config import DeviceConfig
        print("✓ DeviceConfig imported successfully")
    except ImportError as e:
        print(f"✗ DeviceConfig import failed: {e}")
        return False
    
    try:
        from ec14_daq.hardware.device_manager import DeviceManager
        print("✓ DeviceManager imported successfully")
    except ImportError as e:
        print(f"✗ DeviceManager import failed: {e}")
        return False
    
    try:
        from ec14_daq.ui.main_window import MainWindow
        print("✓ MainWindow imported successfully")
    except ImportError as e:
        print(f"✗ MainWindow import failed: {e}")
        return False
    
    return True

def test_device_config():
    """Test device configuration"""
    print("\nTesting device configuration...")
    
    try:
        from ec14_daq.config.device_config import DeviceConfig
        
        # Test range conversion
        range_value = DeviceConfig.get_range_value("±5V")
        range_name = DeviceConfig.get_range_name(range_value)
        
        if range_name == "±5V":
            print("✓ Range conversion working correctly")
        else:
            print(f"✗ Range conversion failed: {range_name}")
            return False
            
    except Exception as e:
        print(f"✗ Device configuration test failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("EC14 Data Acquisition System - Installation Test")
    print("=" * 50)
    
    # Test basic imports
    if not test_imports():
        print("\n❌ Basic imports failed. Please install missing dependencies:")
        print("   pip install -r requirements.txt")
        return False
    
    # Test EC14 modules
    if not test_ec14_modules():
        print("\n❌ EC14 modules failed. Check project structure.")
        return False
    
    # Test device configuration
    if not test_device_config():
        print("\n❌ Device configuration test failed.")
        return False
    
    print("\n✅ All tests passed! Installation is successful.")
    print("\nNext steps:")
    print("1. Connect USB-1408FS-Plus device")
    print("2. Install Measurement Computing Universal Library")
    print("3. Configure device with InstaCal")
    print("4. Run: python main.py")
    
    return True

if __name__ == "__main__":
    main()
