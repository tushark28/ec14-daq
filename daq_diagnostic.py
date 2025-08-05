"""
DAQ Diagnostic Tool - USB-1408FS-Plus
Use this to test your DAQ connection before running the GUI
"""

import time
import sys
from mcculw import ul
from mcculw.enums import ULRange, AnalogInputMode
from mcculw.device_info import DaqDeviceInfo

def test_daq_connection():
    """Test basic DAQ connection"""
    print("=== DAQ Connection Test ===")
    
    try:
        # Test device info
        device_info = DaqDeviceInfo(0)
        print(f"Device found: {device_info.product_name}")
        
        ai_info = device_info.get_ai_info()
        print(f"AI Resolution: {ai_info.resolution} bits")
        print(f"AI Channels: {ai_info.num_chans}")
        
        return True
        
    except Exception as e:
        print(f"Device detection failed: {e}")
        return False

def test_single_reads():
    """Test individual channel reads"""
    print("\n=== Single Channel Read Test ===")
    
    channels = [0, 1, 2, 3]
    range_val = ULRange.BIP10VOLTS
    
    for channel in channels:
        try:
            raw_value = ul.a_in(0, channel, range_val)
            voltage = ul.to_eng_units(0, range_val, raw_value)
            print(f"Channel {channel}: Raw={raw_value}, Voltage={voltage:.4f}V")
        except Exception as e:
            print(f"Channel {channel}: Error - {e}")

def test_continuous_reading():
    """Test continuous reading performance"""
    print("\n=== Continuous Reading Test ===")
    
    channel = 0
    range_val = ULRange.BIP10VOLTS
    num_samples = 100
    
    print(f"Reading {num_samples} samples from channel {channel}...")
    
    start_time = time.time()
    successful_reads = 0
    
    for i in range(num_samples):
        try:
            raw_value = ul.a_in(0, channel, range_val)
            voltage = ul.to_eng_units(0, range_val, raw_value)
            successful_reads += 1
            
            if i % 25 == 0:
                print(f"Sample {i}: {voltage:.4f}V")
                
        except Exception as e:
            print(f"Sample {i}: Error - {e}")
    
    elapsed_time = time.time() - start_time
    sample_rate = successful_reads / elapsed_time
    
    print(f"Completed: {successful_reads}/{num_samples} successful reads")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"Effective sample rate: {sample_rate:.1f} Hz")
    
    return sample_rate

def test_threading_performance():
    """Test if threading causes issues"""
    print("\n=== Threading Performance Test ===")
    
    import threading
    import queue
    
    def read_worker(result_queue, num_reads):
        """Worker function for threading test"""
        channel = 0
        range_val = ULRange.BIP10VOLTS
        
        for i in range(num_reads):
            try:
                raw_value = ul.a_in(0, channel, range_val)
                voltage = ul.to_eng_units(0, range_val, raw_value)
                result_queue.put(('success', voltage))
                time.sleep(0.01)  # 100Hz simulation
            except Exception as e:
                result_queue.put(('error', str(e)))
    
    result_queue = queue.Queue()
    num_reads = 50
    
    # Start worker thread
    worker_thread = threading.Thread(target=read_worker, args=(result_queue, num_reads))
    worker_thread.start()
    
    # Monitor results
    successful_reads = 0
    errors = 0
    
    while worker_thread.is_alive() or not result_queue.empty():
        try:
            status, value = result_queue.get(timeout=1)
            if status == 'success':
                successful_reads += 1
                if successful_reads % 10 == 0:
                    print(f"Threading test: {successful_reads} reads completed")
            else:
                errors += 1
                print(f"Threading error: {value}")
        except queue.Empty:
            continue
    
    worker_thread.join()
    
    print(f"Threading test completed: {successful_reads} successful, {errors} errors")
    
    return errors == 0

def main():
    """Main diagnostic function"""
    print("USB-1408FS-Plus Diagnostic Tool")
    print("=" * 40)
    
    # Test 1: Basic connection
    if not test_daq_connection():
        print("\nFATAL: Cannot connect to DAQ device")
        print("Please check:")
        print("1. Device is connected to USB")
        print("2. InstaCal recognizes the device")
        print("3. No other applications are using the device")
        return
    
    # Test 2: Single reads
    test_single_reads()
    
    # Test 3: Continuous reading performance
    sample_rate = test_continuous_reading()
    
    if sample_rate < 10:
        print("\nWARNING: Very low sample rate detected")
        print("This may cause GUI freezing issues")
    
    # Test 4: Threading performance
    threading_ok = test_threading_performance()
    
    if not threading_ok:
        print("\nWARNING: Threading issues detected")
        print("This may cause GUI instability")
    
    # Final recommendations
    print("\n=== Recommendations ===")
    if sample_rate > 100:
        print("✓ Sample rate is good for real-time applications")
    else:
        print("⚠ Consider reducing GUI update frequency")
    
    if threading_ok:
        print("✓ Threading works properly")
    else:
        print("⚠ Use single-threaded approach or add error handling")
    
    print("\nFor GUI application:")
    print(f"- Recommended sample rate: {min(100, int(sample_rate * 0.5))} Hz")
    print("- Use data buffering to prevent GUI freezing")
    print("- Update plots at maximum 20 Hz")

if __name__ == "__main__":
    main()