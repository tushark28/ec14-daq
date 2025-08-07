# EC316K Python - Eddy Current Testing System

A modern Python implementation of the EC316K eddy current testing system, designed to replace the original TestPoint-based software with a more flexible and maintainable solution.

## Overview

This project replicates the functionality of the original EC316K software using modern Python libraries and provides a professional GUI for eddy current testing applications. The system is designed to work with the USB-1408FS-Plus DAQ device and provides real-time data acquisition, signal processing, and analysis capabilities.

## Features

### Core Functionality
- **Real-time Data Acquisition**: Multi-channel differential and cross-axial measurements
- **Advanced Signal Processing**: Digital filtering, noise reduction, and signal conditioning
- **Defect Detection**: Automated defect detection using amplitude and phase analysis
- **Frequency Analysis**: FFT-based frequency domain analysis
- **Data Logging**: Automatic data saving in CSV and JSON formats
- **Professional GUI**: Modern PyQt5-based interface with real-time plotting

### Hardware Support
- **USB-1408FS-Plus**: 14-bit, 48 KS/s, Multifunction DAQ Device
- **4-Channel Configuration**: 
  - Ch0: Channel 1 Y (differential)
  - Ch1: Channel 1 X (differential)
  - Ch2: Channel 2 Y (cross-axial/absolute)
  - Ch3: Channel 2 X (cross-axial/absolute)
- **Configurable Gains**: Adjustable sensitivity for each channel
- **Multiple Frequencies**: Support for different eddy current test frequencies

### Operating Modes
- **Mode 0**: Differential/Cross-Axial (Single Frequency)
- **Mode 1**: Differential/Absolute (Dual Frequency)
- **Mode 2**: Send/Receive (Single Frequency)
- **Mode 3**: Differential/Differential (Dual Frequency)

### Analysis Capabilities
- **Signal Filtering**: Low-pass, high-pass, and notch filters
- **Defect Classification**: Severity assessment (Minor, Moderate, Major, Critical)
- **Statistical Analysis**: RMS, peak-to-peak, crest factor, kurtosis, skewness
- **Trend Detection**: Linear regression analysis for signal trends
- **Anomaly Detection**: Multiple algorithms for outlier detection

## Installation

### Prerequisites

1. **Python 3.8 or higher**
2. **MCC Universal Library** (for DAQ hardware support)
   - Download and install from [Measurement Computing](https://www.mccdaq.com/Software-Downloads)
   - Install InstaCal for device configuration

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ec14-daq
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**:
   ```bash
   python test_installation.py
   ```

## Usage

### Basic Operation

1. **Start the application**:
   ```bash
   python ec14_main.py
   ```

2. **Configure hardware settings**:
   - Set sample rate (300, 600, 1000, or 2000 Hz per channel)
   - Select operating mode (0-3)
   - Configure frequencies (default: 12kHz/3kHz)
   - Adjust channel gains as needed

3. **Start acquisition**:
   - Click "Start Acquisition" to begin data collection
   - Monitor real-time plots and statistics
   - Use "Stop Acquisition" to halt data collection

### Display Modes

#### 1XY Mode
- Single XY plot showing Channel 1 (X-Y) data
- Ideal for focused analysis of differential signals

#### 2XY-1SC Mode
- Two XY plots: Channel 1 and Channel 2
- Strip chart showing all four channels over time
- Comprehensive view of all signals

#### Time Series Mode
- Continuous monitoring of all channel amplitudes
- Real-time signal tracking

### Advanced Features

#### Signal Processing
- **Filter Configuration**: Adjust low-pass and high-pass filter frequencies
- **Defect Threshold**: Set sensitivity for defect detection
- **Calibration**: Perform channel calibration for accurate measurements

#### Data Management
- **Data Export**: Save data in CSV or JSON format
- **Configuration Save/Load**: Preserve settings between sessions
- **Report Generation**: Create PDF reports with test results

#### Analysis Tools
- **Real-time Plots**: X-Y plots for eddy current analysis
- **Time Series**: Continuous monitoring of signal amplitude
- **Frequency Analysis**: FFT-based spectral analysis
- **Defect Detection**: Automated identification of anomalies

## Configuration

### System Configuration

The system uses a JSON-based configuration file (`ec316k_config.json`) that stores:

```json
{
  "board_num": 0,
  "sample_rate": 1000,
  "operating_mode": 0,
  "channels": {
    "ch1_y": {"num": 0, "name": "Channel 1 Y", "type": "differential"},
    "ch1_x": {"num": 1, "name": "Channel 1 X", "type": "differential"},
    "ch2_y": {"num": 2, "name": "Channel 2 Y", "type": "cross_axial"},
    "ch2_x": {"num": 3, "name": "Channel 2 X", "type": "cross_axial"}
  },
  "frequencies": {
    "ch1": 12000,
    "ch2": 3000
  },
  "gains": {
    "ch1_x": 1.0,
    "ch1_y": 1.0,
    "ch2_x": 1.0,
    "ch2_y": 1.0
  },
  "filters": {
    "low_pass_freq": 1000,
    "high_pass_freq": 10,
    "notch_freq": 60,
    "filter_order": 4
  }
}
```

### Hardware Setup

1. **Connect USB-1408FS-Plus** to your computer
2. **Run InstaCal** to configure the device
3. **Set input mode** to differential
4. **Verify channel mapping** matches your probe configuration

## File Structure

```
ec14-daq/
├── ec14_main.py              # Main application entry point
├── ec14_config.py            # Configuration management
├── ec14_daq.py               # Data acquisition module
├── ec14_signal_processor.py  # Signal processing and analysis
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── test_installation.py      # Installation verification script
├── daq_eddy_current.py       # Original DAQ implementation
├── daq_gui.py               # Original GUI implementation
├── daq_reader.py            # Basic DAQ reader
├── daq_diagnostic.py        # Diagnostic tools
└── EC14/                    # Original EC316K software files
    ├── CB.CFG               # Hardware configuration
    ├── TESTPT.INI           # TestPoint configuration
    └── *.tst                # TestPoint test files
```

## Troubleshooting

### Common Issues

1. **DAQ Device Not Found**:
   - Verify USB-1408FS-Plus is connected
   - Check InstaCal configuration
   - Ensure MCC Universal Library is installed

2. **Import Errors**:
   - Install all required dependencies: `pip install -r requirements.txt`
   - Check Python version compatibility

3. **Performance Issues**:
   - Reduce sample rate for better performance
   - Close other applications to free system resources
   - Use simulation mode for testing without hardware

4. **GUI Not Responding**:
   - Check for error messages in status bar
   - Restart the application
   - Verify PyQt5 installation

### Simulation Mode

If hardware is not available, the system will automatically switch to simulation mode, generating synthetic eddy current data for testing and development.

## Development

### Adding New Features

1. **Signal Processing**: Extend `SignalProcessor` class in `ec14_signal_processor.py`
2. **GUI Components**: Add new widgets to `EC316KMainWindow` in `ec14_main.py`
3. **Data Formats**: Implement new export formats in data logging functions
4. **Hardware Support**: Add new DAQ devices in `ec14_daq.py`

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters
- Add docstrings for all classes and methods
- Include error handling for robust operation

### Testing

```bash
# Run basic tests
python test_installation.py

# Run with coverage
python -m pytest --cov=ec316k tests/
```

## Comparison with Original EC316K

| Feature | Original EC316K | Python EC316K |
|---------|----------------|---------------|
| Platform | Windows + TestPoint | Windows + Python |
| GUI | TestPoint panels | PyQt5 modern interface |
| Data Acquisition | MCC Universal Library | MCC Universal Library |
| Signal Processing | Basic filtering | Advanced DSP algorithms |
| Data Export | Limited formats | CSV, JSON, PDF reports |
| Extensibility | Limited | Highly extensible |
| Maintenance | Proprietary | Open source |

## License

This project is provided as-is for educational and development purposes. Please ensure compliance with any applicable licenses for the original EC316K software and hardware components.

## Support

For technical support or questions:
1. Check the troubleshooting section above
2. Review the original EC316K documentation
3. Consult the MCC Universal Library documentation
4. Open an issue in the project repository

## Acknowledgments

- Original EC316K software developers
- Measurement Computing for hardware and drivers
- PyQt5 and pyqtgraph developers
- Scientific Python community

---

**Note**: This is a replication project for educational and development purposes. Ensure you have proper authorization to use and modify the original EC316K software components. 