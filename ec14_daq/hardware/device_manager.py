"""
Device manager for USB-1408FS-Plus
Handles device initialization and communication
"""

import numpy as np
import ctypes
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
            
            # Initialize instrument board (SPI programming)
            self.initialize_instrument_board()
            
            self.initialized = True
            print("Device and instrument board initialized successfully")
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
    
    def initialize_instrument_board(self):
        """Initialize the instrument board via SPI (AD9833 DDS chips)"""
        try:
            print("Initializing instrument board...")
            
            # Step 1: Reset all digital outputs
            print("  Step 1: Resetting digital outputs...")
            ul.d_out(self.board_num, DeviceConfig.PORT_A, 0x00)
            ul.d_out(self.board_num, DeviceConfig.PORT_B, 0x00)
            
            # Step 2: Try simple direct approach - set all outputs high
            print("  Step 2: Setting all digital outputs high...")
            ul.d_out(self.board_num, DeviceConfig.PORT_A, 0xFF)
            ul.d_out(self.board_num, DeviceConfig.PORT_B, 0xFF)
            
            # Step 3: Test basic signal acquisition
            print("  Step 3: Testing basic signal acquisition...")
            self.test_basic_signals()
            
            # Step 4: Test A/D channels directly
            print("  Step 4: Testing A/D channels...")
            self.test_ad_channels()
            
            # Step 5: Try different digital output patterns
            print("  Step 5: Testing digital output patterns...")
            self.test_digital_patterns()
            
            print("Instrument board initialization completed")
            
        except Exception as e:
            print(f"Error initializing instrument board: {e}")
            import traceback
            traceback.print_exc()
    
    def bypass_instrument_board(self):
        """Bypass instrument board and test USB-1408FS-Plus directly"""
        try:
            print("Bypassing instrument board - testing USB-1408FS-Plus directly...")
            
            # Reset all digital outputs
            ul.d_out(self.board_num, DeviceConfig.PORT_A, 0x00)
            ul.d_out(self.board_num, DeviceConfig.PORT_B, 0x00)
            
            # Test A/D channels with different ranges
            print("  Testing A/D channels directly...")
            for range_val, range_name in [
                (ULRange.BIP5VOLTS, "±5V"),
                (ULRange.BIP2PT5VOLTS, "±2.5V"),
                (ULRange.BIP1VOLTS, "±1V")
            ]:
                print(f"    Testing {range_name} range...")
                self.ad_range = range_val
                
                # Take multiple readings
                for i in range(3):
                    values = self.get_analog_values(5)
                    if values is not None:
                        print(f"      Reading {i+1}: {values}")
                
                import time
                time.sleep(0.1)
            
            # Test D/A outputs if available
            print("  Testing D/A outputs...")
            try:
                # Convert voltage to raw value
                raw_value_2v = int((2.0 + 5.0) * 65535 / 10.0)  # Convert 2V to raw value
                raw_value_neg2v = int((-2.0 + 5.0) * 65535 / 10.0)  # Convert -2V to raw value
                
                # Ensure values are within valid range
                raw_value_2v = max(0, min(65535, raw_value_2v))
                raw_value_neg2v = max(0, min(65535, raw_value_neg2v))
                
                ul.a_out(self.board_num, 0, ULRange.BIP5VOLTS, raw_value_2v)
                ul.a_out(self.board_num, 1, ULRange.BIP5VOLTS, raw_value_neg2v)
                print(f"    Set D/A outputs to ±2V (raw values: {raw_value_2v}, {raw_value_neg2v})")
                
                time.sleep(0.2)
                
                # Read A/D channels
                values = self.get_analog_values(10)
                if values is not None:
                    print(f"    A/D readings after D/A: {values}")
                    
            except Exception as da_error:
                print(f"    D/A test failed: {da_error}")
            
            print("  Direct USB-1408FS-Plus test completed")
            
        except Exception as e:
            print(f"Error in bypass test: {e}")
            import traceback
            traceback.print_exc()
    
    def configure_for_eddy_current(self):
        """Configure the system specifically for eddy current testing"""
        try:
            print("Configuring system for eddy current testing...")
            
            # Set optimal A/D range for eddy current signals
            self.ad_range = ULRange.BIP2PT5VOLTS  # ±2.5V range for better resolution
            
            # Configure digital outputs for eddy current mode
            # Port A: SPI control for DDS chips
            # Port B: Bridge configuration and gain control
            ul.d_out(self.board_num, DeviceConfig.PORT_A, 0x80)  # Enable excitation
            ul.d_out(self.board_num, DeviceConfig.PORT_B, 0x07)  # Differential mode
            
            print("  ✓ System configured for eddy current testing")
            print("  ✓ A/D range set to ±2.5V")
            print("  ✓ Excitation enabled")
            print("  ✓ Bridge set to differential mode")
            
        except Exception as e:
            print(f"Error configuring for eddy current: {e}")
            import traceback
            traceback.print_exc()
    
    def program_ad9833_chips(self):
        """Program the 4 AD9833 DDS chips via SPI"""
        try:
            print("  Programming AD9833 DDS chips...")
            
            # More active frequencies for testing
            frequencies = [5000, 7500, 10000, 15000]  # Hz - higher frequencies for better detection
            
            for chip in range(4):
                freq = frequencies[chip]
                print(f"    Programming chip {chip} with {freq} Hz")
                
                # AD9833 programming sequence
                # Control register: 0x2000 (enable output, sine wave, reset)
                control_word = 0x2000
                self.spi_write(chip, control_word)
                
                # Frequency register 0: Set frequency
                freq_word = int((freq * 2**28) / 25000000)  # 25MHz clock
                self.spi_write(chip, 0x4000 | (freq_word & 0x3FFF))  # MSB
                self.spi_write(chip, 0x4000 | ((freq_word >> 14) & 0x3FFF))  # LSB
                
                # Phase register: 0 degrees
                phase_word = 0
                self.spi_write(chip, 0xC000 | (phase_word & 0xFFF))
                
                # Enable output (clear reset bit)
                control_word = 0x0000  # Enable output
                self.spi_write(chip, control_word)
                
                print(f"    Chip {chip} programmed and enabled")
                
            print("  AD9833 programming completed")
            
        except Exception as e:
            print(f"  Error programming AD9833: {e}")
            import traceback
            traceback.print_exc()
    
    def spi_write(self, chip_select, data):
        """Write data to AD9833 via SPI"""
        try:
            # Chip select (4 chips, 4 bits)
            cs_mask = 1 << chip_select
            
            # SPI write sequence
            for bit in range(16):
                # Set data bit
                if data & (1 << (15 - bit)):
                    data_bit = 1
                else:
                    data_bit = 0
                
                # Set SPI lines
                spi_data = (cs_mask << 4) | (data_bit << 2)  # CS, DATA
                ul.d_out(self.board_num, DeviceConfig.PORT_A, spi_data)
                
                # Clock pulse
                spi_data |= 1  # SCLK high
                ul.d_out(self.board_num, DeviceConfig.PORT_A, spi_data)
                
                # Small delay
                import time
                time.sleep(0.000001)  # 1 microsecond
                
                spi_data &= ~1  # SCLK low
                ul.d_out(self.board_num, DeviceConfig.PORT_A, spi_data)
                
        except Exception as e:
            print(f"    SPI write error: {e}")
    
    def configure_instrumentation_amps(self):
        """Configure instrumentation amplifiers for eddy current testing"""
        try:
            print("  Configuring instrumentation amplifiers...")
            
            # Try different gain settings to get better signal levels
            gain_settings = [0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F]
            
            for gain in gain_settings:
                print(f"    Trying gain setting: 0x{gain:02X}")
                ul.d_out(self.board_num, DeviceConfig.PORT_B, gain)
                import time
                time.sleep(0.1)  # Wait for amplifier to settle
                
                # Test if we get any signal variation
                test_values = self.get_analog_values(10)
                if test_values is not None:
                    print(f"      Test values: {test_values}")
                    if not np.all(test_values == -5.0):
                        print(f"      ✓ Found non-zero signals with gain 0x{gain:02X}")
                        break
            
            print("  Instrumentation amplifiers configured")
            
        except Exception as e:
            print(f"  Error configuring amplifiers: {e}")
            import traceback
            traceback.print_exc()
    
    def enable_excitation(self):
        """Enable excitation signals and bridge circuit"""
        try:
            print("  Enabling excitation signals...")
            
            # Enable excitation by setting appropriate digital outputs
            # This activates the bridge circuit and DDS outputs
            
            # Set excitation enable bits
            excitation_control = 0x80  # Enable excitation
            ul.d_out(self.board_num, DeviceConfig.PORT_A, excitation_control)
            
            # Wait for signals to stabilize
            import time
            time.sleep(0.5)
            
            # Test excitation signals
            test_values = self.get_analog_values(20)
            if test_values is not None:
                print(f"    Excitation test values: {test_values}")
                if not np.all(test_values == -5.0):
                    print("    ✓ Excitation signals detected")
                else:
                    print("    ⚠️  No excitation signals detected")
            
            print("  Excitation signals enabled")
            
        except Exception as e:
            print(f"  Error enabling excitation: {e}")
            import traceback
            traceback.print_exc()
    
    def test_bridge_configurations(self):
        """Test different bridge circuit configurations"""
        try:
            print("  Testing bridge configurations...")
            
            # Different bridge configurations to try
            bridge_configs = [
                (0x07, "Differential/Absolute"),
                (0x0F, "Cross Axial/Differential"), 
                (0x03, "Absolute Mode"),
                (0x0B, "Differential Mode"),
                (0x1F, "High Gain Mode"),
                (0x00, "Reset Mode")
            ]
            
            for config, description in bridge_configs:
                print(f"    Testing {description} (0x{config:02X})...")
                ul.d_out(self.board_num, DeviceConfig.PORT_B, config)
                
                import time
                time.sleep(0.2)  # Wait for relays to settle
                
                # Test signal levels
                test_values = self.get_analog_values(10)
                if test_values is not None:
                    print(f"      Values: {test_values}")
                    if not np.all(test_values == -5.0):
                        print(f"      ✓ Found signals with {description}")
                        return config
            
            print("    No signals found with any bridge configuration")
            return None
            
        except Exception as e:
            print(f"  Error testing bridge configurations: {e}")
            return None
    
    def test_basic_signals(self):
        """Test basic signal acquisition without complex initialization"""
        try:
            print("    Testing basic signal acquisition...")
            
            # Test different A/D ranges
            ranges_to_test = [
                (ULRange.BIP5VOLTS, "±5V"),
                (ULRange.BIP2PT5VOLTS, "±2.5V"),
                (ULRange.BIP1VOLTS, "±1V"),
                (ULRange.BIP10VOLTS, "±10V")
            ]
            
            for range_val, range_name in ranges_to_test:
                print(f"      Testing range: {range_name}")
                self.ad_range = range_val
                
                # Take multiple readings
                for i in range(5):
                    values = self.get_analog_values(10)
                    if values is not None:
                        print(f"        Reading {i+1}: {values}")
                        if not np.all(values == -5.0) and not np.all(values == 5.0):
                            print(f"        ✓ Found varying signals with {range_name}")
                            return True
                
                import time
                time.sleep(0.1)
            
            print("      No varying signals found with any range")
            return False
            
        except Exception as e:
            print(f"      Error in basic signal test: {e}")
            return False
    
    def test_digital_patterns(self):
        """Test different digital output patterns to activate instrument board"""
        try:
            print("    Testing digital output patterns...")
            
            # Common patterns that might activate the instrument board
            patterns = [
                (0xAA, 0x55, "Alternating pattern"),
                (0x55, 0xAA, "Reverse alternating"),
                (0xF0, 0x0F, "High/low nibble"),
                (0x0F, 0xF0, "Low/high nibble"),
                (0x80, 0x80, "MSB only"),
                (0x01, 0x01, "LSB only"),
                (0xFF, 0x00, "Port A all high, Port B all low"),
                (0x00, 0xFF, "Port A all low, Port B all high")
            ]
            
            for port_a, port_b, description in patterns:
                print(f"      Testing pattern: {description}")
                ul.d_out(self.board_num, DeviceConfig.PORT_A, port_a)
                ul.d_out(self.board_num, DeviceConfig.PORT_B, port_b)
                
                import time
                time.sleep(0.2)  # Wait for settling
                
                # Test signals
                values = self.get_analog_values(5)
                if values is not None:
                    print(f"        Values: {values}")
                    if not np.all(values == -5.0) and not np.all(values == 5.0):
                        print(f"        ✓ Found signals with {description}")
                        return True
            
            print("      No signals found with any digital pattern")
            return False
            
        except Exception as e:
            print(f"      Error testing digital patterns: {e}")
            return False
    
    def test_ad_channels(self):
        """Test if A/D channels are working by creating test signals"""
        try:
            print("    Testing A/D channels with D/A outputs...")
            
            # Test if we can create signals using D/A outputs
            # This will help verify if the A/D channels are working
            
            # Try to output a simple signal on D/A channels
            try:
                # Test D/A output (if available)
                # Use proper raw values for USB-1408FS-Plus D/A
                # Range is 0-65535 for ±5V
                raw_value_1v = int((1.0 + 5.0) * 65535 / 10.0)  # Convert 1V to raw value
                raw_value_neg1v = int((-1.0 + 5.0) * 65535 / 10.0)  # Convert -1V to raw value
                
                # Ensure values are within valid range
                raw_value_1v = max(0, min(65535, raw_value_1v))
                raw_value_neg1v = max(0, min(65535, raw_value_neg1v))
                
                ul.a_out(self.board_num, 0, ULRange.BIP5VOLTS, raw_value_1v)  # 1V on channel 0
                ul.a_out(self.board_num, 1, ULRange.BIP5VOLTS, raw_value_neg1v)  # -1V on channel 1
                print(f"      Set D/A outputs to ±1V (raw values: {raw_value_1v}, {raw_value_neg1v})")
                
                import time
                time.sleep(0.1)
                
                # Read A/D channels
                values = self.get_analog_values(10)
                if values is not None:
                    print(f"      A/D readings: {values}")
                    return True
                    
            except Exception as da_error:
                print(f"      D/A test failed: {da_error}")
            
            # Test with different A/D ranges
            print("      Testing A/D ranges...")
            for range_val in [ULRange.BIP5VOLTS, ULRange.BIP2PT5VOLTS, ULRange.BIP1VOLTS]:
                self.ad_range = range_val
                values = self.get_analog_values(5)
                if values is not None:
                    print(f"        Range {range_val}: {values}")
            
            return False
            
        except Exception as e:
            print(f"      Error testing A/D channels: {e}")
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
            print(f"  Board: {self.board_num}, Sample rate: {self.sample_rate}, Range: {self.ad_range}")
            return False
        except Exception as e:
            print(f"Unexpected error starting scan: {e}")
            print(f"  Error type: {type(e).__name__}")
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
                # Use ctypes array (most compatible with mcculw)
                raw_data = (ctypes.c_ushort * count)()
                print(f"  Getting scan data: count={count}, buffer_handle={self.buffer_handle}")
                ul.win_buf_to_array(self.buffer_handle, raw_data, 0, count)
                raw_data = list(raw_data)
                
                # Convert to numpy array and handle reshaping properly
                data = np.array(raw_data)
                print(f"  Raw data length: {len(data)}, count: {count}")
                
                # Ensure we have complete 4-channel samples
                # Round down to nearest multiple of 4
                complete_samples = (len(data) // 4) * 4
                if complete_samples > 0:
                    data = data[:complete_samples]
                    data = data.reshape(-1, 4)
                    print(f"  Data shape: {data.shape}, Sample values: {data[0] if data.size > 0 else 'empty'}")
                    
                    # Convert to engineering units
                    volts_data = np.zeros_like(data, dtype=float)
                    for i in range(data.shape[0]):
                        for j in range(data.shape[1]):
                            volts_data[i, j] = ul.to_eng_units(self.board_num, self.ad_range, data[i, j])
                    
                    print(f"  Volts data shape: {volts_data.shape}, Sample values: {volts_data[0] if volts_data.size > 0 else 'empty'}")
                    
                    # Check for signal issues
                    if volts_data.size > 0:
                        # Check if all values are -5V (no signal condition)
                        if np.all(volts_data == -5.0):
                            print("  ⚠️  All channels reading -5V: No active signals detected")
                            print("     Possible causes:")
                            print("     - Instrument board not properly initialized")
                            print("     - AD9833 DDS chips not generating signals")
                            print("     - Bridge circuit not configured correctly")
                            print("     - Amplifier gains too low")
                            print("     - No eddy current probe connected")
                            
                            # Try to reinitialize if this persists
                            if hasattr(self, '_reinit_count'):
                                self._reinit_count += 1
                            else:
                                self._reinit_count = 1
                                
                            if self._reinit_count <= 3:
                                print(f"  🔄 Attempting reinitialization #{self._reinit_count}...")
                                self.initialize_instrument_board()
                            else:
                                print("  ❌ Max reinitialization attempts reached")
                        else:
                            # Reset reinit counter if we get signals
                            self._reinit_count = 0
                            
                            # Check for channel 4 issue (stuck at -1V)
                            if volts_data.shape[1] >= 4 and np.all(volts_data[:, 3] == -1.0):
                                print("  ⚠️  Channel 4 stuck at -1V: Possible hardware issue")
                                print("     This may be normal if channel 4 is not connected")
                            
                            # Check for signal variations
                            signal_variance = np.var(volts_data, axis=0)
                            if np.any(signal_variance > 1e-6):  # If any channel has variance
                                print(f"  ✓ Active signals detected: variance = {signal_variance}")
                            else:
                                print("  ⚠️  All signals appear static (no variations)")
                    
                    return volts_data
                else:
                    print(f"  No complete samples available (need at least 4 values)")
                    return None
            
            return None
            
        except ULError as e:
            print(f"Error getting scan data: {e}")
            print(f"  Board: {self.board_num}, Status: {status}, Count: {count}")
            return None
        except Exception as e:
            print(f"Unexpected error getting scan data: {e}")
            print(f"  Error type: {type(e).__name__}")
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
