"""
Basic DAQ Signal Reader for USB-1408FS-Plus
Step 1: Reading differential and cross-axial signals
"""

import time
import numpy as np
from mcculw import ul
from mcculw.enums import ULRange, AnalogInputMode, InterfaceType
from mcculw.device_info import DaqDeviceInfo

class DAQReader:
    def __init__(self, board_num=0):
        """Initialize DAQ reader for USB-1408FS-Plus"""
        self.board_num = board_num
        self.device_info = DaqDeviceInfo(board_num)
        self.ai_info = self.device_info.get_ai_info()
        
        # Configure for differential input mode
        self.input_mode = AnalogInputMode.DIFFERENTIAL
        self.range = ULRange.BIP10VOLTS  # ±10V range
        
        # Channel mapping for differential and cross-axial
        self.channels = {
            'differential_1': 0,    # Channel 0 (differential pair 0+/0-)
            'differential_2': 1,    # Channel 1 (differential pair 1+/1-)
            'cross_axial_x': 2,     # Channel 2 (X-axis)
            'cross_axial_y': 3,     # Channel 3 (Y-axis)
        }
        
        # Sensitivity settings (volts per unit)
        self.sensitivity = {
            'differential_1': 1.0,   # 1V per unit
            'differential_2': 1.0,   # 1V per unit
            'cross_axial_x': 0.1,    # 100mV per g (typical accelerometer)
            'cross_axial_y': 0.1,    # 100mV per g (typical accelerometer)
        }
        
        print(f"DAQ Device: {self.device_info.product_name}")
        print(f"Resolution: {self.ai_info.resolution} bits")
        print(f"Input mode: {self.input_mode}")
        
    def read_single_channel(self, channel):
        """Read a single channel value"""
        try:
            # Get raw ADC value
            raw_value = ul.a_in(self.board_num, channel, self.range)
            
            # Convert to voltage
            voltage = ul.to_eng_units(self.board_num, self.range, raw_value)
            
            return voltage
        except Exception as e:
            print(f"Error reading channel {channel}: {e}")
            return 0.0
    
    def read_all_channels(self):
        """Read all configured channels"""
        readings = {}
        
        for channel_name, channel_num in self.channels.items():
            voltage = self.read_single_channel(channel_num)
            
            # Apply sensitivity scaling
            scaled_value = voltage / self.sensitivity[channel_name]
            
            readings[channel_name] = {
                'voltage': voltage,
                'scaled_value': scaled_value,
                'channel': channel_num
            }
        
        return readings
    
    def set_sensitivity(self, channel_name, sensitivity):
        """Adjust sensitivity for a channel"""
        if channel_name in self.sensitivity:
            self.sensitivity[channel_name] = sensitivity
            print(f"Sensitivity for {channel_name} set to {sensitivity}")
        else:
            print(f"Unknown channel: {channel_name}")
    
    def continuous_read(self, duration=10, sample_rate=1000):
        """Continuous reading for specified duration"""
        print(f"Starting continuous reading for {duration} seconds at {sample_rate} Hz")
        
        samples_per_second = sample_rate
        total_samples = duration * samples_per_second
        interval = 1.0 / sample_rate
        
        data = {name: [] for name in self.channels.keys()}
        timestamps = []
        
        start_time = time.time()
        
        for i in range(total_samples):
            current_time = time.time()
            timestamps.append(current_time - start_time)
            
            readings = self.read_all_channels()
            
            for channel_name in self.channels.keys():
                data[channel_name].append(readings[channel_name]['scaled_value'])
            
            # Maintain sample rate
            elapsed = time.time() - current_time
            if elapsed < interval:
                time.sleep(interval - elapsed)
        
        return timestamps, data

# Example usage
if __name__ == "__main__":
    try:
        # Initialize DAQ reader
        daq = DAQReader(board_num=0)
        
        # Test single reading
        print("\n=== Single Reading Test ===")
        readings = daq.read_all_channels()
        
        for channel_name, data in readings.items():
            print(f"{channel_name}: {data['voltage']:.4f}V (scaled: {data['scaled_value']:.4f})")
        
        # Test sensitivity adjustment
        print("\n=== Sensitivity Adjustment Test ===")
        daq.set_sensitivity('cross_axial_x', 0.05)  # 50mV per g
        
        # Test continuous reading (short duration for demo)
        print("\n=== Continuous Reading Test ===")
        timestamps, data = daq.continuous_read(duration=2, sample_rate=100)
        
        print(f"Collected {len(timestamps)} samples")
        for channel_name, values in data.items():
            avg_value = np.mean(values)
            std_value = np.std(values)
            print(f"{channel_name}: avg={avg_value:.4f}, std={std_value:.4f}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure:")
        print("1. InstaCal is installed")
        print("2. Device is recognized in InstaCal")