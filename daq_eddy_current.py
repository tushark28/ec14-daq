"""
Eddy Current Testing System - Step 1: Basic Signal Reading
Hardware: USB-1408FS-Plus 14-Bit, 48 KS/s, Multifunction DAQ Device
"""

import sys
import time
import numpy as np
from collections import deque
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                            QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QGroupBox, QTabWidget, QTextEdit,
                            QSlider, QLCDNumber, QProgressBar, QMessageBox)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg

# Check if MCC DAQ library is available
try:
    from mcculw import ul
    from mcculw.enums import ULRange, AnalogInputMode, BoardInfo, InfoType, GlobalInfo
    MCC_AVAILABLE = True
except ImportError:
    MCC_AVAILABLE = False
    print("Warning: MCC Universal Library not found. Install InstaCal and mcculw package.")

class DAQWorker(QThread):
    """Worker thread for DAQ data acquisition"""
    data_ready = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    
    def __init__(self, board_num=0):
        super().__init__()
        self.board_num = board_num
        self.running = False
        self.sample_rate = 1000  # Default sample rate
        self.gui_update_rate = 50  # Update GUI at 50Hz
        
        # Channel mapping for your 4-channel system
        # Based on your screenshots: Ch1-X, Ch1-Y, Ch2-X, Ch2-Y
        self.channels = {
            'ch1_x': 0,  # Differential channel 1 X
            'ch1_y': 1,  # Differential channel 1 Y
            'ch2_x': 2,  # Differential channel 2 X
            'ch2_y': 3,  # Differential channel 2 Y
        }
        
        # Gain settings (corresponds to sensitivity in your old app)
        self.gains = {
            'ch1_x': 1,  # Default gain
            'ch1_y': 1,
            'ch2_x': 1,
            'ch2_y': 1,
        }
         
        # Frequency settings for differential channels
        self.frequencies = {
            'ch1': 26000,  # Hz
            'ch2': 8000,   # Hz
        }
        
        self.input_range = ULRange.BIP10VOLTS  # ±10V range
        self.last_gui_update = 0
        self.data_buffer = []
        self.mode = "cross_axial"  # or "absolute"
        
    def set_gain(self, channel, gain_value):
        """Set gain for a specific channel"""
        if channel in self.gains:
            self.gains[channel] = gain_value
            self.status_signal.emit(f"Gain set for {channel}: {gain_value}")
    
    def set_frequency(self, channel, freq):
        """Set frequency for differential channels"""
        if channel in self.frequencies:
            self.frequencies[channel] = freq
            self.status_signal.emit(f"Frequency set for {channel}: {freq} Hz")
    
    def set_sample_rate(self, rate):
        """Update sample rate"""
        self.sample_rate = min(rate, 2000)  # Limit based on your hardware
        self.status_signal.emit(f"Sample rate set to: {rate} Hz")
    
    def set_mode(self, mode):
        """Set measurement mode"""
        self.mode = mode
        self.status_signal.emit(f"Mode set to: {mode}")
    
    def test_daq_connection(self):
        """Test DAQ device connection"""
        if not MCC_AVAILABLE:
            return False, "MCC Universal Library not available"
        
        try:
            # Try to get board info
            board_name = ul.get_board_name(self.board_num)
            num_ai_channels = ul.get_config(InfoType.BOARDINFO, self.board_num, 
                                          0, BoardInfo.NUMADCHANS)
            return True, f"Connected to {board_name} with {num_ai_channels} AI channels"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def run(self):
        """Main acquisition loop"""
        self.running = True
        interval = 1.0 / self.sample_rate
        gui_interval = 1.0 / self.gui_update_rate
        
        # Test connection first
        success, message = self.test_daq_connection()
        if not success:
            self.error_signal.emit(message)
            return
        
        self.status_signal.emit("Starting data acquisition...")
        
        while self.running:
            try:
                start_time = time.time()
                readings = {}
                
                # Read all channels
                for channel_name, channel_num in self.channels.items():
                    try:
                        # Read raw ADC value
                        raw_value = ul.a_in(self.board_num, channel_num, self.input_range)
                        
                        # Convert to voltage
                        voltage = ul.to_eng_units(self.board_num, self.input_range, raw_value)
                        
                        # Apply gain (sensitivity adjustment)
                        gain = self.gains[channel_name]
                        scaled_value = voltage * gain if gain > 0 else voltage
                        
                        readings[channel_name] = {
                            'raw': raw_value,
                            'voltage': voltage,
                            'scaled_value': scaled_value,
                            'gain': gain,
                            'timestamp': time.time()
                        }
                        
                    except Exception as channel_error:
                        self.error_signal.emit(f"Error reading {channel_name}: {channel_error}")
                        continue
                
                # Buffer data for GUI updates
                if readings:
                    self.data_buffer.append(readings)
                
                # Update GUI at controlled rate
                current_time = time.time()
                if current_time - self.last_gui_update > gui_interval:
                    if self.data_buffer:
                        # Send latest reading to GUI
                        latest_reading = self.data_buffer[-1]
                        self.data_ready.emit(latest_reading)
                        self.data_buffer.clear()
                        self.last_gui_update = current_time
                
                # Maintain sample rate
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    self.msleep(int(sleep_time * 1000))
                    
            except Exception as e:
                self.error_signal.emit(f"Acquisition error: {e}")
                self.msleep(100)  # Brief pause before retry
    
    def stop(self):
        """Stop acquisition"""
        self.running = False
        self.status_signal.emit("Stopping data acquisition...")

class EddyCurrentTestGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eddy Current Testing System - USB-1408FS-Plus")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Data storage
        self.max_points = 1000
        self.data_history = {
            'ch1_x': deque(maxlen=self.max_points),
            'ch1_y': deque(maxlen=self.max_points),
            'ch2_x': deque(maxlen=self.max_points),
            'ch2_y': deque(maxlen=self.max_points),
        }
        self.time_history = deque(maxlen=self.max_points)
        self.start_time = time.time()
        
        # Initialize DAQ worker
        self.daq_worker = DAQWorker(board_num=0)
        self.daq_worker.data_ready.connect(self.update_data)
        self.daq_worker.error_signal.connect(self.handle_error)
        self.daq_worker.status_signal.connect(self.update_status)
        
        self.init_ui()
        self.setup_plots()
        
        # Test connection on startup
        self.test_connection()
        
    def init_ui(self):
        """Initialize user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Hardware settings panel
        hardware_panel = self.create_hardware_panel()
        main_layout.addWidget(hardware_panel)
        
        # Tabs for different views
        tab_widget = QTabWidget()
        
        # Real-time plots tab
        plots_tab = QWidget()
        plots_layout = QVBoxLayout(plots_tab)
        
        # Plot widget
        self.plot_widget = pg.GraphicsLayoutWidget()
        plots_layout.addWidget(self.plot_widget)
        
        tab_widget.addTab(plots_tab, "Real-time Plots")
        
        # Data display tab
        data_tab = self.create_data_display_tab()
        tab_widget.addTab(data_tab, "Data Display")
        
        main_layout.addWidget(tab_widget)
        
        # Status bar
        self.status_label = QLabel("Ready - Click 'Test Connection' to verify hardware")
        main_layout.addWidget(self.status_label)
        
    def create_control_panel(self):
        """Create control panel"""
        group = QGroupBox("Control Panel")
        layout = QHBoxLayout(group)
        
        # Test connection button
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        layout.addWidget(self.test_btn)
        
        # Start/Stop buttons
        self.start_btn = QPushButton("Start Acquisition")
        self.start_btn.clicked.connect(self.start_acquisition)
        self.start_btn.setEnabled(False)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Acquisition")
        self.stop_btn.clicked.connect(self.stop_acquisition)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        # Sample rate control
        layout.addWidget(QLabel("Sample Rate/Ch:"))
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["300", "600", "1000", "2000"])
        self.sample_rate_combo.setCurrentText("1000")
        self.sample_rate_combo.currentTextChanged.connect(self.update_sample_rate)
        layout.addWidget(self.sample_rate_combo)
        
        # Mode selection
        layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Cross Axial", "Absolute"])
        self.mode_combo.currentTextChanged.connect(self.update_mode)
        layout.addWidget(self.mode_combo)
        
        # Clear data button
        clear_btn = QPushButton("Clear Data")
        clear_btn.clicked.connect(self.clear_data)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        return group
    
    def create_hardware_panel(self):
        """Create hardware settings panel"""
        group = QGroupBox("Hardware Settings")
        layout = QGridLayout(group)
        
        # Frequency settings
        freq_group = QGroupBox("Frequencies")
        freq_layout = QGridLayout(freq_group)
        
        freq_layout.addWidget(QLabel("Ch1 Frequency (Hz):"), 0, 0)
        self.ch1_freq_spin = QSpinBox()
        self.ch1_freq_spin.setRange(1000, 50000)
        self.ch1_freq_spin.setValue(26000)
        self.ch1_freq_spin.valueChanged.connect(lambda v: self.update_frequency('ch1', v))
        freq_layout.addWidget(self.ch1_freq_spin, 0, 1)
        
        freq_layout.addWidget(QLabel("Ch2 Frequency (Hz):"), 0, 2)
        self.ch2_freq_spin = QSpinBox()
        self.ch2_freq_spin.setRange(1000, 50000)
        self.ch2_freq_spin.setValue(8000)
        self.ch2_freq_spin.valueChanged.connect(lambda v: self.update_frequency('ch2', v))
        freq_layout.addWidget(self.ch2_freq_spin, 0, 3)
        
        # Gain settings
        gain_group = QGroupBox("Gain Settings")
        gain_layout = QGridLayout(gain_group)
        
        self.gain_combos = {}
        channels = ['ch1_x', 'ch1_y', 'ch2_x', 'ch2_y']
        gain_values = ["1", "2", "4", "8", "16", "32", "64"]
        
        for i, channel in enumerate(channels):
            label = QLabel(f"{channel.replace('_', '-').upper()}:")
            gain_layout.addWidget(label, i//2, (i%2)*2)
            
            combo = QComboBox()
            combo.addItems(gain_values)
            combo.setCurrentText("1")
            combo.currentTextChanged.connect(lambda v, ch=channel: self.update_gain(ch, int(v)))
            self.gain_combos[channel] = combo
            gain_layout.addWidget(combo, i//2, (i%2)*2 + 1)
        
        layout.addWidget(freq_group, 0, 0)
        layout.addWidget(gain_group, 0, 1)
        
        return group
    
    def create_data_display_tab(self):
        """Create data display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Current values display
        values_group = QGroupBox("Current Values")
        values_layout = QGridLayout(values_group)
        
        self.value_displays = {}
        channels = ['ch1_x', 'ch1_y', 'ch2_x', 'ch2_y']
        
        for i, channel in enumerate(channels):
            label = QLabel(f"{channel.replace('_', '-').upper()}:")
            values_layout.addWidget(label, i//2, (i%2)*3)
            
            lcd = QLCDNumber()
            lcd.setDigitCount(8)
            lcd.setSegmentStyle(QLCDNumber.Flat)
            self.value_displays[channel] = lcd
            values_layout.addWidget(lcd, i//2, (i%2)*3 + 1)
            
            unit_label = QLabel("V")
            values_layout.addWidget(unit_label, i//2, (i%2)*3 + 2)
        
        layout.addWidget(values_group)
        
        # Statistics display
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(300)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        layout.addStretch()
        
        return widget
    
    def setup_plots(self):
        """Setup real-time plots"""
        self.plot_widget.clear()
        
        # Create subplots in 2x2 grid
        self.plots = {}
        self.curves = {}
        
        channels = ['ch1_x', 'ch1_y', 'ch2_x', 'ch2_y']
        colors = ['r', 'g', 'b', 'y']
        
        for i, (channel, color) in enumerate(zip(channels, colors)):
            plot = self.plot_widget.addPlot(row=i//2, col=i%2)
            plot.setLabel('left', f"{channel.replace('_', '-').upper()} (V)")
            plot.setLabel('bottom', 'Time (s)')
            plot.setTitle(f"{channel.replace('_', '-').upper()} Signal")
            
            curve = plot.plot(pen=color, name=channel)
            
            self.plots[channel] = plot
            self.curves[channel] = curve
    
    def test_connection(self):
        """Test DAQ connection"""
        if not MCC_AVAILABLE:
            QMessageBox.warning(self, "Library Missing", 
                              "MCC Universal Library not found.\n"
                              "Please install InstaCal and the mcculw Python package.")
            return
        
        success, message = self.daq_worker.test_daq_connection()
        if success:
            QMessageBox.information(self, "Connection Test", message)
            self.start_btn.setEnabled(True)
            self.update_status("Hardware connection verified")
        else:
            QMessageBox.critical(self, "Connection Error", message)
            self.update_status("Hardware connection failed")
    
    def start_acquisition(self):
        """Start data acquisition"""
        if not self.daq_worker.isRunning():
            self.daq_worker.start()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.start_time = time.time()
    
    def stop_acquisition(self):
        """Stop data acquisition"""
        self.daq_worker.stop()
        self.daq_worker.wait(3000)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def update_data(self, readings):
        """Update data and plots"""
        current_time = time.time() - self.start_time
        self.time_history.append(current_time)
        
        # Update data history and displays
        for channel, data in readings.items():
            self.data_history[channel].append(data['scaled_value'])
            
            # Update LCD displays
            if channel in self.value_displays:
                self.value_displays[channel].display(data['scaled_value'])
        
        # Update plots
        self.update_plots()
        
        # Update statistics periodically
        if len(self.time_history) % 50 == 0:  # Every 50 samples
            self.update_statistics()
    
    def update_plots(self):
        """Update real-time plots"""
        if len(self.time_history) < 2:
            return
        
        try:
            time_array = np.array(self.time_history)
            
            for channel in self.data_history.keys():
                if channel in self.curves and len(self.data_history[channel]) > 0:
                    data_array = np.array(self.data_history[channel])
                    self.curves[channel].setData(time_array, data_array)
                    
        except Exception as e:
            print(f"Plot update error: {e}")
    
    def update_statistics(self):
        """Update statistics display"""
        try:
            stats_text = "Channel Statistics:\n\n"
            
            for channel, data in self.data_history.items():
                if len(data) > 0:
                    data_array = np.array(data)
                    mean_val = np.mean(data_array)
                    std_val = np.std(data_array)
                    min_val = np.min(data_array)
                    max_val = np.max(data_array)
                    
                    stats_text += f"{channel.replace('_', '-').upper()}:\n"
                    stats_text += f"  Mean: {mean_val:.4f} V\n"
                    stats_text += f"  Std:  {std_val:.4f} V\n"
                    stats_text += f"  Min:  {min_val:.4f} V\n"
                    stats_text += f"  Max:  {max_val:.4f} V\n\n"
            
            self.stats_text.setText(stats_text)
        except Exception as e:
            print(f"Statistics update error: {e}")
    
    def update_gain(self, channel, gain):
        """Update gain setting"""
        self.daq_worker.set_gain(channel, gain)
    
    def update_frequency(self, channel, freq):
        """Update frequency setting"""
        self.daq_worker.set_frequency(channel, freq)
    
    def update_sample_rate(self, rate_str):
        """Update sample rate"""
        rate = int(rate_str)
        self.daq_worker.set_sample_rate(rate)
    
    def update_mode(self, mode_str):
        """Update measurement mode"""
        mode = mode_str.lower().replace(' ', '_')
        self.daq_worker.set_mode(mode)
    
    def clear_data(self):
        """Clear all data"""
        for channel in self.data_history:
            self.data_history[channel].clear()
        self.time_history.clear()
        self.start_time = time.time()
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.setText(message)
    
    def handle_error(self, error_msg):
        """Handle errors"""
        self.status_label.setText(f"Error: {error_msg}")
        QMessageBox.critical(self, "DAQ Error", error_msg)
        self.stop_acquisition()
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.daq_worker.isRunning():
            self.daq_worker.stop()
            self.daq_worker.wait(5000)
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Dark theme
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    window = EddyCurrentTestGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()