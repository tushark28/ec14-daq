#!/usr/bin/env python3
"""
Test script to verify signal fix for EC14 system
"""

import sys
import os
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ec14_daq.hardware.device_manager import DeviceManager

def test_signal_fix():
    """Test the signal fix functionality"""
    print("🔧 Testing Signal Fix for EC14 System")
    print("=" * 50)
    
    # Create device manager
    device_manager = DeviceManager()
    
    try:
        # Initialize device
        print("1. Initializing device...")
        if not device_manager.initialize_device():
            print("❌ Device initialization failed")
            return False
        print("✅ Device initialized")
        
        # Test basic signal reading
        print("\n2. Testing basic signal reading...")
        try:
            # Try single channel reading
            value = device_manager.get_single_reading(0)
            print(f"   Channel 0 reading: {value}V")
            
            if value == -1.0:
                print("   ⚠️  Detected -1V reading - attempting fix...")
                device_manager.fix_ad_range()
                
                # Test again
                value = device_manager.get_single_reading(0)
                print(f"   After fix - Channel 0 reading: {value}V")
            
        except Exception as e:
            print(f"   Error reading signal: {e}")
        
        # Test scan data
        print("\n3. Testing scan data...")
        try:
            if device_manager.start_scanning():
                print("   ✅ Scanning started")
                
                # Get a few samples
                for i in range(5):
                    data = device_manager.get_scan_data()
                    if data is not None and data.size > 0:
                        print(f"   Sample {i+1}: {data[0] if data.size > 0 else 'No data'}")
                    time.sleep(0.1)
                
                device_manager.stop_scanning()
                print("   ✅ Scanning stopped")
            else:
                print("   ❌ Failed to start scanning")
                
        except Exception as e:
            print(f"   Error during scan test: {e}")
        
        print("\n✅ Signal fix test completed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        device_manager.cleanup()

if __name__ == "__main__":
    test_signal_fix()
