# EC14 Data Acquisition System - Phase 1

Python port of the TestPoint EC14 application for USB-1408FS-Plus data acquisition device.

## Overview

This application provides real-time data acquisition and visualization for the EC14 Eddy Current Testing System using a USB-1408FS-Plus device from Measurement Computing.

## Features (Phase 1)

- **4-Channel A/D Acquisition**: Real-time sampling from all 4 analog channels
- **Configurable Sample Rates**: 300, 600, 1000, 2000 Hz per channel
- **Configurable A/D Ranges**: ±5V, ±4V, ±2.5V, ±2V, ±1.25V, ±1V
- **Real-Time Strip Chart**: Live plotting of all 4 channels
- **Data Export**: Save acquired data to CSV files
- **Device Communication**: LED flash test and connection verification

## Requirements

### Hardware
- USB-1408FS-Plus data acquisition device
- Windows 64-bit operating system

### Software
- Python 3.8 or higher
- Measurement Computing Universal Library 6.55 or higher
- InstaCal (for device configuration)

### Python Dependencies
```
mcculw>=1.0.0
PyQt5>=5.15.0
numpy>=1.21.0
pyqtgraph>=0.12.0
scipy>=1.7.0
pandas>=1.3.0
matplotlib>=3.4.0
```

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Measurement Computing Software**:
   - Download and install the latest Universal Library from [MCC website](https://www.mccdaq.com/Software-Downloads.aspx)
   - Install InstaCal for device configuration

3. **Configure Device**:
   - Connect USB-1408FS-Plus device
   - Run InstaCal to configure the device
   - Note the board number (default: 0)

## Usage

### Running the Application

```bash
python main.py
```

### Application Workflow

1. **Initialize Device**: Click "Initialize Device" to establish connection
2. **Test Connection**: Click "Test Connection" to verify communication
3. **Configure Settings**: Select sample rate and A/D range
4. **Start Scanning**: Click "Start Scanning" to begin data acquisition
5. **Monitor Data**: View real-time strip chart and channel values
6. **Save Data**: Click "Save Data" to export to CSV file
7. **Stop Scanning**: Click "Stop Scanning" to end acquisition

### Interface Components

- **Device Controls**: Device initialization and communication
- **Data Acquisition**: Start/stop scanning and parameter configuration
- **Display Controls**: Clear plots and save data
- **Channel Information**: Real-time voltage values for each channel
- **Strip Chart**: Real-time plotting of all 4 channels

## Project Structure

```
ec14_daq/
├── __init__.py                 # Package initialization
├── config/
│   ├── __init__.py
│   └── device_config.py       # Device configuration parameters
├── hardware/
│   ├── __init__.py
│   └── device_manager.py      # USB-1408FS-Plus communication
└── ui/
    ├── __init__.py
    └── main_window.py         # Main PyQt application window

main.py                        # Application entry point
requirements.txt               # Python dependencies
README.md                      # This file
```

## Configuration

### Device Parameters (Matching TestPoint)

- **Board Number**: 0 (default)
- **Channels**: 0-3 (4 channels)
- **Sample Rates**: 300, 600, 1000, 2000 Hz
- **A/D Ranges**: ±5V, ±4V, ±2.5V, ±2V, ±1.25V, ±1V
- **Buffer Size**: 1984 samples (matching TestPoint)
- **Scan Options**: Background + Continuous

### File Paths (Matching TestPoint)

- **Configuration Directory**: `c:\ec14`
- **Data Directory**: `c:\taijob#`
- **Image Directory**: `c:\ectdata`

## Data Format

### CSV Export Format
```
Ch0,Ch1,Ch2,Ch3
-1.234,2.345,-0.123,1.456
-1.235,2.344,-0.124,1.457
...
```

### Real-Time Data Structure
- **4 channels** of voltage data
- **Continuous streaming** with configurable sample rate
- **Engineering units** (volts) conversion
- **Circular buffer** for efficient memory management

## Troubleshooting

### Common Issues

1. **Device Not Found**:
   - Ensure USB-1408FS-Plus is connected
   - Check InstaCal configuration
   - Verify Universal Library installation

2. **Import Errors**:
   - Install all dependencies: `pip install -r requirements.txt`
   - Ensure Python 3.8+ is installed

3. **Performance Issues**:
   - Reduce sample rate for slower systems
   - Close other applications to free resources
   - Check USB connection quality

### Error Messages

- **"Device initialization failed"**: Check device connection and drivers
- **"Failed to start scanning"**: Verify device configuration in InstaCal
- **"Acquisition Error"**: Check USB connection and device status

## Development

### Adding New Features

1. **Signal Processing**: Add phase rotation and gain adjustment
2. **SPI Control**: Implement frequency generation and gain control
3. **Advanced Display**: Add XY plots and phase wand
4. **Data Analysis**: Integrate defect detection algorithms

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings for all functions
- Maintain modular structure

## License

This project is part of the EC14 system port and follows the original project's licensing terms.

## Support

For technical support:
1. Check the troubleshooting section
2. Verify hardware connections
3. Review Measurement Computing documentation
4. Contact the development team

## Version History

### Phase 1 (Current)
- Basic 4-channel A/D acquisition
- Real-time strip chart display
- Device configuration and communication
- Data export functionality
- Matching TestPoint parameters
