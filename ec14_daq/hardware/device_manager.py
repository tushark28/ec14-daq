"""
Device manager for USB-1408FS-Plus
Handles device initialization and communication
"""

import numpy as np
from mcculw import ul
from mcculw.enums import ULRange, ScanOptions
from mcculw.ul import ULError

from ..config.device_config import DeviceConfig

class DeviceManager:
    """Manages USB-1408FS-Plus device communication"""
    
    def __init__(self):
        self.board_num = DeviceConfig.BOARD_NUM
        self.initialized = False
        self.scanning = False
        self.buffer_handle = None
        self.sample_rate = DeviceConfig.DEFAULT_SAMPLE_RATE
        self.ad_range = DeviceConfig.DEFAULT_AD_RANGE
        
    def initialize_device(self):
        """Initialize the USB-1408FS-Plus device"""
        try:
            # Get board name to verify connection
            board_name = ul.get_board_name(self.board_num)
            print(f"Connected to: {board_name}")
            
            # Configure Port A as output
            ul.d_config_port(self.board_num, DeviceConfig.PORT_A, 1)  # 1 = OUTPUT
            ul.d_out(self.board_num, DeviceConfig.PORT_A, DeviceConfig.PORT_A_DEFAULT)
            
            # Configure Port B as output  
            ul.d_config_port(self.board_num, DeviceConfig.PORT_B, 1)  # 1 = OUTPUT
            ul.d_out(self.board_num, DeviceConfig.PORT_B, DeviceConfig.PORT_B_DEFAULT)
            
            self.initialized = True
            print("Device initialized successfully")
            return True
            
        except ULError as e:
            print(f"Device initialization failed: {e}")
            return False
    
    def test_connection(self):
        """Test device communication by flashing LED"""
        try:
            ul.flash_led(self.board_num)
            print("Device communication test successful")
            return True
        except ULError as e:
            print(f"Device communication test failed: {e}")
            return False
    
    def get_analog_values(self, num_samples=1000):
        """Get single reading from all 4 channels"""
        try:
            values = []
            for channel in range(DeviceConfig.LOW_CHANNEL, DeviceConfig.HIGH_CHANNEL + 1):
                value = ul.a_in(self.board_num, channel, self.ad_range)
                eng_value = ul.to_eng_units(self.board_num, self.ad_range, value)
                values.append(eng_value)
            
            return np.array(values)
            
        except ULError as e:
            print(f"Analog input error: {e}")
            return None
    
    def start_scanning(self):
        """Start continuous background scanning"""
        if not self.initialized:
            print("Device not initialized")
            return False
            
        try:
            # Allocate buffer
            self.buffer_handle = ul.win_buf_alloc(DeviceConfig.NUM_SAMPLES * 4)
            
            # Start background scan
            ul.a_in_scan(
                self.board_num,
                DeviceConfig.LOW_CHANNEL,
                DeviceConfig.HIGH_CHANNEL,
                DeviceConfig.NUM_SAMPLES,
                self.sample_rate,
                self.ad_range,
                self.buffer_handle,
                DeviceConfig.SCAN_OPTIONS
            )
            
            self.scanning = True
            print(f"Started scanning at {self.sample_rate} Hz")
            return True
            
        except ULError as e:
            print(f"Failed to start scanning: {e}")
            return False
    
    def stop_scanning(self):
        """Stop background scanning"""
        if self.scanning:
            try:
                ul.stop_background(self.board_num, 1)  # Stop A/D
                self.scanning = False
                print("Scanning stopped")
            except ULError as e:
                print(f"Error stopping scan: {e}")
        
        if self.buffer_handle:
            try:
                ul.win_buf_free(self.buffer_handle)
                self.buffer_handle = None
            except ULError as e:
                print(f"Error freeing buffer: {e}")
    
    def get_scan_data(self):
        """Get current scan data"""
        if not self.scanning or not self.buffer_handle:
            return None
            
        try:
            # Get scan status (function_type = 1 for A/D scan)
            # Returns: (status, count, index) - only 3 values
            status, count, index = ul.get_status(self.board_num, 1)
            
            if status == 1 and count > 0:  # 1 = RUNNING status
                # Get data from buffer
                # win_buf_to_array(buffer_handle, first_element, count)
                raw_data = ul.win_buf_to_array(self.buffer_handle, 0, count)
                
                # Convert to numpy array and reshape to 4 channels
                data = np.array(raw_data).reshape(-1, 4)
                
                # Convert to engineering units
                volts_data = np.zeros_like(data, dtype=float)
                for i in range(data.shape[0]):
                    for j in range(data.shape[1]):
                        volts_data[i, j] = ul.to_eng_units(self.board_num, self.ad_range, data[i, j])
                
                return volts_data
            
            return None
            
        except ULError as e:
            print(f"Error getting scan data: {e}")
            return None
    
    def set_sample_rate(self, rate):
        """Set sample rate"""
        if rate in DeviceConfig.SAMPLE_RATES:
            self.sample_rate = rate
            print(f"Sample rate set to {rate} Hz")
        else:
            print(f"Invalid sample rate: {rate}")
    
    def set_ad_range(self, range_name):
        """Set A/D range"""
        range_value = DeviceConfig.get_range_value(range_name)
        self.ad_range = range_value
        print(f"A/D range set to {range_name}")
    
    def get_counter_value(self):
        """Get counter value (for footswitch)"""
        try:
            count = ul.c_in_32(self.board_num, DeviceConfig.COUNTER_NUM)
            return count
        except ULError as e:
            print(f"Counter read error: {e}")
            return 0
    
    def cleanup(self):
        """Clean up device resources"""
        self.stop_scanning()
        print("Device cleanup completed")
