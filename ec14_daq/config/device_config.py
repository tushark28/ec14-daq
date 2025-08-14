"""
Device configuration for USB-1408FS-Plus
Matching TestPoint EC14 parameters
"""

from mcculw.enums import ULRange

class DeviceConfig:
    """Configuration matching TestPoint EC14 settings"""
    
    # Board configuration
    BOARD_NUM = 0
    LOW_CHANNEL = 0
    HIGH_CHANNEL = 3  # 4 channels (0,1,2,3)
    
    # Sampling configuration (matching TestPoint)
    NUM_SAMPLES = 1984  # Based on 4*31*16 from TestPoint
    SAMPLE_RATES = [300, 600, 1000, 2000]  # Hz per channel
    DEFAULT_SAMPLE_RATE = 1000
    
    # A/D ranges (matching TestPoint)
    AD_RANGES = {
        "±5V": ULRange.BIP5VOLTS,
        "±4V": ULRange.BIP4VOLTS, 
        "±2.5V": ULRange.BIP2PT5VOLTS,
        "±2V": ULRange.BIP2VOLTS,
        "±1.25V": ULRange.BIP1PT25VOLTS,
        "±1V": ULRange.BIP1VOLTS
    }
    DEFAULT_AD_RANGE = ULRange.BIP5VOLTS
    
    # Scan options (using numeric values for compatibility)
    SCAN_OPTIONS = 3  # BACKGROUND | CONTINUOUS
    
    # Digital I/O configuration
    PORT_A = 10
    PORT_B = 11
    PORT_A_DEFAULT = 255  # All high
    PORT_B_DEFAULT = 7    # Lines 0,1,2 high
    
    # Counter configuration
    COUNTER_NUM = 1
    
    # Display configuration
    MAX_PLOT_POINTS = 50000  # Matching TestPoint
    STRIP_CHART_RANGE = (-20, 20)  # ±20V range for 4 channels
    XY_PLOT_RANGE = (-5, 5)  # ±5V range for XY plots
    
    # File paths (matching TestPoint)
    CONFIG_DIR = "c:\\ec14"
    DATA_DIR = "c:\\taijob#"
    IMAGE_DIR = "c:\\ectdata"
    
    @classmethod
    def get_range_value(cls, range_name):
        """Get ULRange value from range name"""
        return cls.AD_RANGES.get(range_name, cls.DEFAULT_AD_RANGE)
    
    @classmethod
    def get_range_name(cls, range_value):
        """Get range name from ULRange value"""
        for name, value in cls.AD_RANGES.items():
            if value == range_value:
                return name
        return "±5V"
