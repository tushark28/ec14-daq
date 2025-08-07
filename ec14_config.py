"""
EC316K Configuration Module
Handles all system settings and configuration for the EC316K eddy current testing system
Based on the original EC316K TestPoint implementation
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class EC316KConfig:
    """Configuration class for EC316K system settings based on original implementation"""
    
    # Hardware settings
    board_num: int = 0
    sample_rate: int = 1000  # Hz per channel (300, 600, 1000, 2000)
    gui_update_rate: int = 50  # Hz
    
    # Channel configuration - matches EC316K hardware setup
    channels: Dict[str, Dict[str, Any]] = None
    
    # Frequency settings for eddy current testing (default: 12kHz/3kHz)
    frequencies: Dict[str, int] = None
    
    # Gain/sensitivity settings
    gains: Dict[str, float] = None
    
    # Operating modes (0-3 as per EC316K documentation)
    operating_mode: int = 0  # 0=differential/cross-axial, 1=differential/absolute, 2=send/receive, 3=differential/differential
    
    # Filter settings
    filters: Dict[str, Any] = None
    
    # Display settings
    display: Dict[str, Any] = None
    
    # Analysis settings
    analysis: Dict[str, Any] = None
    
    # Data logging
    logging: Dict[str, Any] = None
    
    # Phase and offset settings
    phase_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values based on EC316K specifications"""
        if self.channels is None:
            # Channel mapping based on EC316K hardware
            # Ch0 = Channel 1 Y (differential)
            # Ch1 = Channel 1 X (differential) 
            # Ch2 = Channel 2 Y (cross-axial/absolute)
            # Ch3 = Channel 2 X (cross-axial/absolute)
            self.channels = {
                'ch1_y': {'num': 0, 'name': 'Channel 1 Y', 'type': 'differential'},
                'ch1_x': {'num': 1, 'name': 'Channel 1 X', 'type': 'differential'},
                'ch2_y': {'num': 2, 'name': 'Channel 2 Y', 'type': 'cross_axial'},
                'ch2_x': {'num': 3, 'name': 'Channel 2 X', 'type': 'cross_axial'},
            }
        
        if self.frequencies is None:
            # Default frequencies as per EC316K documentation
            self.frequencies = {
                'ch1': 12000,  # Hz - Channel 1 differential frequency
                'ch2': 3000,   # Hz - Channel 2 cross-axial/absolute frequency
            }
        
        if self.gains is None:
            self.gains = {
                'ch1_x': 1.0,
                'ch1_y': 1.0,
                'ch2_x': 1.0,
                'ch2_y': 1.0,
            }
        
        if self.filters is None:
            self.filters = {
                'low_pass_freq': 1000,  # Hz
                'high_pass_freq': 10,   # Hz
                'notch_freq': 60,       # Hz (power line frequency)
                'filter_order': 4,
            }
        
        if self.display is None:
            self.display = {
                'max_points': 1000,
                'auto_scale': True,
                'show_grid': True,
                'plot_style': 'line',  # 'line', 'scatter', 'both'
                'display_mode': '1XY',  # '1XY', '2XY-1SC', '2Ch-XY'
                'chart_display_time': 10.0,  # seconds
            }
        
        if self.analysis is None:
            self.analysis = {
                'defect_threshold': 0.1,  # Voltage threshold for defect detection
                'noise_threshold': 0.01,  # Noise floor
                'smoothing_window': 5,    # Moving average window
            }
        
        if self.logging is None:
            self.logging = {
                'auto_save': True,
                'save_interval': 60,  # seconds
                'file_format': 'csv',  # 'csv', 'json', 'hdf5'
                'data_directory': './ec316k_data',
                'save_strip_chart': False,
            }
        
        if self.phase_settings is None:
            self.phase_settings = {
                'ch1_phase': 0.0,  # degrees
                'ch2_phase': 0.0,  # degrees
                'phase_wand_rotation': 0.0,  # degrees
                'x_compression': 1.0,  # X-axis compression factor
                'y_compression': 1.0,  # Y-axis compression factor
            }
    
    def save_config(self, filename: str = None):
        """Save configuration to file"""
        if filename is None:
            filename = "ec316k_config.json"
        
        config_dict = asdict(self)
        with open(filename, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def load_config(self, filename: str = "ec316k_config.json"):
        """Load configuration from file"""
        if Path(filename).exists():
            with open(filename, 'r') as f:
                config_dict = json.load(f)
            
            # Update current instance with loaded values
            for key, value in config_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)
    
    def get_channel_number(self, channel_name: str) -> int:
        """Get channel number for a given channel name"""
        if channel_name in self.channels:
            return self.channels[channel_name]['num']
        return -1
    
    def get_channel_name(self, channel_num: int) -> str:
        """Get channel name for a given channel number"""
        for name, info in self.channels.items():
            if info['num'] == channel_num:
                return name
        return f"Unknown_{channel_num}"
    
    def update_gain(self, channel: str, gain: float):
        """Update gain for a specific channel"""
        if channel in self.gains:
            self.gains[channel] = gain
    
    def update_frequency(self, channel: str, frequency: int):
        """Update frequency for a specific channel"""
        if channel in self.frequencies:
            self.frequencies[channel] = frequency
    
    def update_operating_mode(self, mode: int):
        """Update operating mode (0-3)"""
        if 0 <= mode <= 3:
            self.operating_mode = mode
    
    def get_mode_description(self) -> str:
        """Get description of current operating mode"""
        mode_descriptions = {
            0: "Differential/Cross-Axial (Single Frequency)",
            1: "Differential/Absolute (Dual Frequency)", 
            2: "Send/Receive (Single Frequency)",
            3: "Differential/Differential (Dual Frequency)"
        }
        return mode_descriptions.get(self.operating_mode, "Unknown Mode")
    
    def update_filter(self, filter_type: str, value: Any):
        """Update filter settings"""
        if filter_type in self.filters:
            self.filters[filter_type] = value
    
    def get_all_channels(self) -> list:
        """Get list of all channel names"""
        return list(self.channels.keys())
    
    def get_differential_channels(self) -> list:
        """Get list of differential channel names"""
        return [name for name, info in self.channels.items() 
                if info['type'] == 'differential']
    
    def get_cross_axial_channels(self) -> list:
        """Get list of cross-axial channel names"""
        return [name for name, info in self.channels.items() 
                if info['type'] == 'cross_axial']
    
    def validate_config(self) -> bool:
        """Validate configuration settings"""
        # Check sample rate (must be one of the allowed values)
        allowed_sample_rates = [300, 600, 1000, 2000]
        if self.sample_rate not in allowed_sample_rates:
            return False
        
        # Check frequencies
        for freq in self.frequencies.values():
            if freq <= 0 or freq > 100000:
                return False
        
        # Check gains
        for gain in self.gains.values():
            if gain <= 0:
                return False
        
        # Check operating mode
        if not 0 <= self.operating_mode <= 3:
            return False
        
        return True
    
    def get_scan_rate(self) -> int:
        """Get total scan rate (sample_rate * num_channels)"""
        return self.sample_rate * len(self.channels)
    
    def get_max_scan_rate(self) -> int:
        """Get maximum allowed scan rate (50,000 as per EC316K)"""
        return 50000 