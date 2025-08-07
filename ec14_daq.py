"""
EC316K Data Acquisition Module
Handles data acquisition from USB-1408FS-Plus DAQ device and provides
real-time data processing capabilities based on EC316K specifications
"""

import time
import numpy as np
from collections import deque
from typing import Dict, List, Optional, Tuple
from PyQt5.QtCore import QThread, pyqtSignal

# DAQ Libraries
try:
    from mcculw import ul
    from mcculw.enums import ULRange, AnalogInputMode, BoardInfo, InfoType, GlobalInfo
    from mcculw.device_info import DaqDeviceInfo
    MCC_AVAILABLE = True
except ImportError:
    MCC_AVAILABLE = False
    print("Warning: MCC Universal Library not found. Install InstaCal and mcculw package.")

from ec14_config import EC316KConfig
from ec14_signal_processor import SignalProcessor

class EC316KDAQWorker(QThread):
    """Worker thread for DAQ data acquisition based on EC316K specifications"""
    
    data_ready = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    defect_detected = pyqtSignal(dict)
    calibration_complete = pyqtSignal(dict)
    
    def __init__(self, config: EC316KConfig):
        super().__init__()
        self.config = config
        self.signal_processor = SignalProcessor(config)
        self.running = False
        self.paused = False
        
        # Data storage
        self.data_history = {channel: deque(maxlen=config.display['max_points']) 
                           for channel in config.channels.keys()}
        
        # Calibration data
        self.calibration_data = {}
        self.calibration_factors = {channel: 1.0 for channel in config.channels.keys()}
        
        # Statistics
        self.sample_count = 0
        self.start_time = None
        
        # Initialize DAQ if available
        self.board_num = config.board_num
        self.range = ULRange.BIP10VOLTS
        self.initialized = False
        
        # EC316K specific settings
        self.scan_rate = config.get_scan_rate()
        self.max_scan_rate = config.get_max_scan_rate()
        
        if MCC_AVAILABLE:
            self.initialize_daq()
        else:
            self.status_signal.emit("MCC Universal Library not available - using simulation mode")
    
    def initialize_daq(self):
        """Initialize the DAQ device according to EC316K specifications"""
        try:
            # Get device info
            device_info = DaqDeviceInfo(self.board_num)
            ai_info = device_info.get_ai_info()
            
            self.status_signal.emit(f"DAQ Device: {device_info.product_name}")
            self.status_signal.emit(f"Resolution: {ai_info.resolution} bits")
            self.status_signal.emit(f"Channels: {ai_info.num_chans}")
            
            # Configure for differential input mode (as per EC316K)
            ul.set_config(InfoType.BOARDINFO, self.board_num, 0, 
                         BoardInfo.ADINPUTMODE, AnalogInputMode.DIFFERENTIAL)
            
            # Verify scan rate is within limits
            if self.scan_rate > self.max_scan_rate:
                self.status_signal.emit(f"Warning: Scan rate {self.scan_rate} exceeds maximum {self.max_scan_rate}")
            
            self.initialized = True
            self.status_signal.emit("DAQ initialized successfully")
            
        except Exception as e:
            self.error_signal.emit(f"DAQ initialization failed: {e}")
            self.initialized = False
    
    def run(self):
        """Main acquisition loop based on EC316K implementation"""
        self.running = True
        self.start_time = time.time()
        interval = 1.0 / self.config.sample_rate
        gui_interval = 1.0 / self.config.gui_update_rate
        last_gui_update = 0
        
        self.status_signal.emit("Starting data acquisition...")
        
        while self.running:
            try:
                if self.paused:
                    self.msleep(100)
                    continue
                
                start_time = time.time()
                
                # Read data
                if self.initialized and MCC_AVAILABLE:
                    readings = self.read_daq_channels()
                else:
                    readings = self.simulate_ec316k_data()
                
                # Process signals
                processed_readings = self.process_signals(readings)
                
                # Apply calibration
                calibrated_readings = self.apply_calibration(processed_readings)
                
                # Store in history
                for channel, value in calibrated_readings.items():
                    self.data_history[channel].append(value)
                
                # Update sample count
                self.sample_count += 1
                
                # Update GUI at specified rate
                current_time = time.time()
                if current_time - last_gui_update > gui_interval:
                    self.data_ready.emit(calibrated_readings)
                    last_gui_update = current_time
                
                # Maintain sample rate
                elapsed = time.time() - start_time
                if elapsed < interval:
                    self.msleep(int((interval - elapsed) * 1000))
                    
            except Exception as e:
                self.error_signal.emit(f"Acquisition error: {e}")
                self.msleep(100)
    
    def read_daq_channels(self) -> Dict[str, float]:
        """Read all DAQ channels according to EC316K channel mapping"""
        readings = {}
        
        for channel_name, channel_info in self.config.channels.items():
            try:
                # Read raw value
                raw_value = ul.a_in(self.board_num, channel_info['num'], self.range)
                voltage = ul.to_eng_units(self.board_num, self.range, raw_value)
                
                # Apply gain
                scaled_value = voltage * self.config.gains[channel_name]
                
                readings[channel_name] = scaled_value
                
            except Exception as e:
                self.error_signal.emit(f"Error reading {channel_name}: {e}")
                readings[channel_name] = 0.0
        
        return readings
    
    def simulate_ec316k_data(self) -> Dict[str, float]:
        """Simulate EC316K eddy current data for testing"""
        t = time.time()
        readings = {}
        
        # Get frequencies based on operating mode
        ch1_freq = self.config.frequencies['ch1']
        ch2_freq = self.config.frequencies['ch2']
        
        # Simulate eddy current signals based on EC316K specifications
        for channel_name in self.config.channels.keys():
            if 'ch1' in channel_name:
                # Channel 1 (differential) - use ch1 frequency
                base_signal = 0.1 * np.sin(2 * np.pi * ch1_freq * t) + 0.05 * np.random.randn()
            else:
                # Channel 2 (cross-axial/absolute) - use ch2 frequency
                base_signal = 0.1 * np.sin(2 * np.pi * ch2_freq * t) + 0.05 * np.random.randn()
            
            # Add occasional defects (0.1% chance)
            if np.random.random() < 0.001:
                base_signal += 0.5 * np.exp(-((t % 10) - 5)**2 / 0.1)
            
            # Add phase shift for Y channels
            if 'y' in channel_name:
                phase_shift = self.config.phase_settings['ch1_phase'] if 'ch1' in channel_name else self.config.phase_settings['ch2_phase']
                base_signal = 0.1 * np.sin(2 * np.pi * (ch1_freq if 'ch1' in channel_name else ch2_freq) * t + np.radians(phase_shift))
            
            readings[channel_name] = base_signal
        
        return readings
    
    def process_signals(self, readings: Dict[str, float]) -> Dict[str, float]:
        """Process raw signals with filters and analysis"""
        processed = readings.copy()
        
        # Convert to numpy arrays for processing
        x_data = np.array([readings['ch1_x'], readings['ch2_x']])
        y_data = np.array([readings['ch1_y'], readings['ch2_y']])
        
        # Apply filters
        x_filtered = self.signal_processor.apply_filters(x_data)
        y_filtered = self.signal_processor.apply_filters(y_data)
        
        # Update processed readings
        processed['ch1_x'] = x_filtered[0]
        processed['ch1_y'] = y_filtered[0]
        processed['ch2_x'] = x_filtered[1]
        processed['ch2_y'] = y_filtered[1]
        
        # Detect defects
        if len(self.data_history['ch1_x']) > 10:
            x_history = np.array(list(self.data_history['ch1_x']))
            y_history = np.array(list(self.data_history['ch1_y']))
            defects = self.signal_processor.detect_defects(x_history, y_history)
            
            if defects:
                self.defect_detected.emit(defects[0])
        
        return processed
    
    def apply_calibration(self, readings: Dict[str, float]) -> Dict[str, float]:
        """Apply calibration factors to readings"""
        calibrated = {}
        for channel, value in readings.items():
            calibrated[channel] = value * self.calibration_factors[channel]
        return calibrated
    
    def start_calibration(self, channel: str, duration: int = 10):
        """Start calibration for a specific channel"""
        self.calibration_data[channel] = []
        self.status_signal.emit(f"Starting calibration for {channel}...")
        
        # Collect calibration data
        start_time = time.time()
        while time.time() - start_time < duration and self.running:
            if channel in self.data_history and len(self.data_history[channel]) > 0:
                self.calibration_data[channel].append(self.data_history[channel][-1])
            time.sleep(0.1)
        
        # Calculate calibration factor
        if len(self.calibration_data[channel]) > 0:
            mean_value = np.mean(self.calibration_data[channel])
            if mean_value != 0:
                self.calibration_factors[channel] = 1.0 / abs(mean_value)
            
            self.status_signal.emit(f"Calibration complete for {channel}")
            self.calibration_complete.emit({channel: self.calibration_factors[channel]})
    
    def set_calibration_factor(self, channel: str, factor: float):
        """Set calibration factor for a channel"""
        self.calibration_factors[channel] = factor
    
    def get_statistics(self) -> Dict:
        """Get acquisition statistics"""
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        actual_rate = self.sample_count / elapsed_time if elapsed_time > 0 else 0
        
        return {
            'sample_count': self.sample_count,
            'elapsed_time': elapsed_time,
            'actual_rate': actual_rate,
            'target_rate': self.config.sample_rate,
            'scan_rate': self.scan_rate,
            'max_scan_rate': self.max_scan_rate,
            'operating_mode': self.config.operating_mode,
            'mode_description': self.config.get_mode_description(),
            'data_points': {channel: len(data) for channel, data in self.data_history.items()}
        }
    
    def get_data_history(self, channel: str) -> List[float]:
        """Get data history for a specific channel"""
        if channel in self.data_history:
            return list(self.data_history[channel])
        return []
    
    def get_all_data_history(self) -> Dict[str, List[float]]:
        """Get data history for all channels"""
        return {channel: list(data) for channel, data in self.data_history.items()}
    
    def clear_data_history(self):
        """Clear all data history"""
        for channel in self.data_history:
            self.data_history[channel].clear()
        self.sample_count = 0
    
    def pause_acquisition(self):
        """Pause data acquisition"""
        self.paused = True
        self.status_signal.emit("Acquisition paused")
    
    def resume_acquisition(self):
        """Resume data acquisition"""
        self.paused = False
        self.status_signal.emit("Acquisition resumed")
    
    def stop(self):
        """Stop acquisition"""
        self.running = False
        self.status_signal.emit("Acquisition stopped")
    
    def update_config(self, new_config: EC316KConfig):
        """Update configuration"""
        self.config = new_config
        self.signal_processor.update_config(new_config)
        self.scan_rate = new_config.get_scan_rate()
        
        # Update data history maxlen
        for channel in new_config.channels.keys():
            if channel not in self.data_history:
                self.data_history[channel] = deque(maxlen=new_config.display['max_points'])
            else:
                # Create new deque with new maxlen
                old_data = list(self.data_history[channel])
                self.data_history[channel] = deque(old_data, maxlen=new_config.display['max_points'])

class EC316KDAQManager:
    """Manager class for DAQ operations based on EC316K specifications"""
    
    def __init__(self, config: EC316KConfig):
        self.config = config
        self.worker = None
        self.is_acquiring = False
    
    def start_acquisition(self) -> bool:
        """Start data acquisition"""
        if self.is_acquiring:
            return False
        
        self.worker = EC316KDAQWorker(self.config)
        self.worker.start()
        self.is_acquiring = True
        return True
    
    def stop_acquisition(self):
        """Stop data acquisition"""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None
        self.is_acquiring = False
    
    def pause_acquisition(self):
        """Pause data acquisition"""
        if self.worker:
            self.worker.pause_acquisition()
    
    def resume_acquisition(self):
        """Resume data acquisition"""
        if self.worker:
            self.worker.resume_acquisition()
    
    def get_worker(self) -> Optional[EC316KDAQWorker]:
        """Get the current worker instance"""
        return self.worker
    
    def is_running(self) -> bool:
        """Check if acquisition is running"""
        return self.is_acquiring and self.worker and self.worker.isRunning()
    
    def update_config(self, new_config: EC316KConfig):
        """Update configuration"""
        self.config = new_config
        if self.worker:
            self.worker.update_config(new_config) 