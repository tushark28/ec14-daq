#!/usr/bin/env python3
"""
EC316K Python Installation Test Script
Verifies that all required components are properly installed and working
"""

import sys
import importlib

def test_imports():
    """Test all required imports"""
    print("Testing Python imports...")
    
    required_packages = [
        ('PyQt5', 'PyQt5'),
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
        ('pyqtgraph', 'pyqtgraph'),
        ('pandas', 'pandas'),
    ]
    
    optional_packages = [
        ('reportlab', 'reportlab'),
        ('mcculw', 'mcculw'),
    ]
    
    print("\nRequired packages:")
    all_required_ok = True
    for package_name, import_name in required_packages:
        try:
            importlib.import_module(import_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} - NOT FOUND")
            all_required_ok = False
    
    print("\nOptional packages:")
    for package_name, import_name in optional_packages:
        try:
            importlib.import_module(import_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ⚠ {package_name} - NOT FOUND (optional)")
    
    return all_required_ok

def test_ec316k_modules():
    """Test EC316K-specific modules"""
    print("\nTesting EC316K modules...")
    
    ec316k_modules = [
        'ec14_config',
        'ec14_signal_processor',
        'ec14_daq',
    ]
    
    all_modules_ok = True
    for module_name in ec316k_modules:
        try:
            importlib.import_module(module_name)
            print(f"  ✓ {module_name}")
        except ImportError as e:
            print(f"  ✗ {module_name} - {e}")
            all_modules_ok = False
    
    return all_modules_ok

def test_daq_connection():
    """Test DAQ hardware connection"""
    print("\nTesting DAQ connection...")
    
    try:
        import mcculw
        from mcculw import ul
        from mcculw.enums import ULRange, AnalogInputMode, BoardInfo, InfoType
        from mcculw.device_info import DaqDeviceInfo
        
        # Try to get board info
        board_num = 0
        try:
            device_info = DaqDeviceInfo(board_num)
            print(f"  ✓ DAQ Device: {device_info.product_name}")
            print(f"  ✓ Board found at index {board_num}")
            return True
        except Exception as e:
            print(f"  ⚠ No DAQ device found at index {board_num}")
            print(f"    (This is normal if hardware is not connected)")
            return True  # Not an error, just no hardware
            
    except ImportError:
        print("  ⚠ MCC Universal Library not available")
        print("    Install InstaCal and mcculw package for hardware support")
        return True  # Not an error, just optional

def test_gui_components():
    """Test GUI components"""
    print("\nTesting GUI components...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        import pyqtgraph as pg
        
        # Create a minimal app to test GUI
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test pyqtgraph
        plot_widget = pg.PlotWidget()
        plot_widget.plot([1, 2, 3], [1, 4, 2])
        
        print("  ✓ PyQt5 GUI components")
        print("  ✓ pyqtgraph plotting")
        
        return True
        
    except Exception as e:
        print(f"  ✗ GUI test failed: {e}")
        return False

def test_signal_processing():
    """Test signal processing capabilities"""
    print("\nTesting signal processing...")
    
    try:
        import numpy as np
        from scipy import signal
        from scipy.fft import fft, fftfreq
        
        # Create test signal
        t = np.linspace(0, 1, 1000)
        test_signal = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(1000)
        
        # Test filtering
        b, a = signal.butter(4, 0.1, btype='low')
        filtered = signal.filtfilt(b, a, test_signal)
        
        # Test FFT
        fft_data = fft(test_signal)
        freqs = fftfreq(len(test_signal), t[1] - t[0])
        
        print("  ✓ NumPy array operations")
        print("  ✓ SciPy signal processing")
        print("  ✓ FFT analysis")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Signal processing test failed: {e}")
        return False

def test_ec316k_configuration():
    """Test EC316K configuration"""
    print("\nTesting EC316K configuration...")
    
    try:
        from ec14_config import EC316KConfig
        
        # Create configuration
        config = EC316KConfig()
        
        # Test configuration validation
        if config.validate_config():
            print("  ✓ Configuration validation")
        else:
            print("  ✗ Configuration validation failed")
            return False
        
        # Test channel mapping
        channels = config.get_all_channels()
        if len(channels) == 4:
            print("  ✓ Channel configuration")
        else:
            print("  ✗ Channel configuration failed")
            return False
        
        # Test operating modes
        mode_desc = config.get_mode_description()
        if mode_desc:
            print("  ✓ Operating mode configuration")
        else:
            print("  ✗ Operating mode configuration failed")
            return False
        
        # Test scan rate calculation
        scan_rate = config.get_scan_rate()
        if scan_rate == config.sample_rate * 4:  # 4 channels
            print("  ✓ Scan rate calculation")
        else:
            print("  ✗ Scan rate calculation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ EC316K configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("EC316K Python Installation Test")
    print("=" * 40)
    
    # Test Python version
    print(f"Python version: {sys.version}")
    
    # Run tests
    imports_ok = test_imports()
    modules_ok = test_ec316k_modules()
    daq_ok = test_daq_connection()
    gui_ok = test_gui_components()
    signal_ok = test_signal_processing()
    config_ok = test_ec316k_configuration()
    
    # Summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    
    all_tests_passed = all([imports_ok, modules_ok, daq_ok, gui_ok, signal_ok, config_ok])
    
    if all_tests_passed:
        print("✓ All tests passed!")
        print("\nEC316K Python is ready to use.")
        print("\nTo start the application, run:")
        print("  python ec14_main.py")
    else:
        print("✗ Some tests failed.")
        print("\nPlease check the installation:")
        print("  1. Install missing packages: pip install -r requirements.txt")
        print("  2. Verify Python version (3.8+)")
        print("  3. Check DAQ hardware connection")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 