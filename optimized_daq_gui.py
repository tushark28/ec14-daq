"""
Industrial DAQ Monitoring GUI for USB-1408FS-Plus
Features: Real-time plotting, sensitivity adjustment, data logging
"""

import sys
import time
import numpy as np
from collections import deque
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                            QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QGroupBox, QTabWidget, QTextEdit,
                            QSlider, QLCDNumber, QProgressBar)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg
from mcculw import ul
from mcculw.enums import ULRange, AnalogInputMode

class DAQWorker(QThread):
    """Worker thread for DAQ data acquisition"""
    data_ready = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, board_num=0):
        super().__init__()
        self.board_num = board_num
        self.running = False
        self.sample_rate = 100  # Reduced default sample rate
        self.gui_update_rate = 20  # Update GUI at 20Hz max
        self.channels = {
            'differential_1': 0,
            'differential_2': 1,
            'cross_axial_x': 2,
            'cross_axial_y': 3,
        }
        self.sensitivity = {
            'differential_1': 1.0,
            'differential_2': 1.0,
            'cross_axial_x': 0.1,
            'cross_axial_y': 0.1,
        }
        self.range = ULRange.BIP10VOLTS
        self.last_gui_update = 0
        self.data_buffer = []
        
    def set_sensitivity(self, channel, value):
        """Update sensitivity for a channel"""
        if channel in self.sensitivity:
            self.sensitivity[channel] = value
    
    def set_sample_rate(self, rate):
        """Update sample rate"""
        self.sample_rate = min(rate, 1000)  # Limit max sample rate
    
    def run(self):
        """Main acquisition loop with buffering"""
        self.running = True
        interval = 1.0 / self.sample_rate
        gui_interval = 1.0 / self.gui_update_rate
        
        while self.running:
            try:
                start_time = time.time()
                readings = {}
                
                # Check if DAQ device is available
                try:
                    for channel_name, channel_num in self.channels.items():
                        # Read raw value
                        raw_value = ul.a_in(self.board_num, channel_num, self.range)
                        voltage = ul.to_eng_units(self.board_num, self.range, raw_value)
                        scaled_value = voltage / self.sensitivity[channel_name]
                        
                        readings[channel_name] = {
                            'voltage': voltage,
                            'scaled_value': scaled_value,
                            'timestamp': time.time()
                        }
                except Exception as daq_error:
                    self.error_signal.emit(f"DAQ Read Error: {daq_error}")
                    self.msleep(100)  # Wait before retry
                    continue
                
                # Buffer data
                self.data_buffer.append(readings)
                
                # Update GUI at limited rate
                current_time = time.time()
                if current_time - self.last_gui_update > gui_interval:
                    # Send averaged data to GUI
                    if self.data_buffer:
                        avg_readings = self.average_buffer()
                        self.data_ready.emit(avg_readings)
                        self.data_buffer.clear()
                        self.last_gui_update = current_time
                
                # Maintain sample rate
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    self.msleep(int(sleep_time * 1000))
                    
            except Exception as e:
                self.error_signal.emit(f"Worker Error: {e}")
                self.msleep(100)
    
    def average_buffer(self):
        """Average buffered data"""
        if not self.data_buffer:
            return {}
        
        avg_readings = {}
        for channel_name in self.channels.keys():
            voltages = [reading[channel_name]['voltage'] for reading in self.data_buffer]
            scaled_values = [reading[channel_name]['scaled_value'] for reading in self.data_buffer]
            
            avg_readings[channel_name] = {
                'voltage': np.mean(voltages),
                'scaled_value': np.mean(scaled_values),
                'timestamp': time.time()
            }
        
        return avg_readings
    
    def stop(self):
        """Stop acquisition"""
        self.running = False

class DAQMonitorGUI(QMainWindow):
    def __init__(self, board_num = 0):
        super().__init__()
        self.setWindowTitle("Industrial DAQ Monitor - USB-1408FS-Plus")
        self.setGeometry(100, 100, 1400, 900)
        
        # Data storage
        self.max_points = 500  # Reduced for better performance
        self.data_history = {
            'differential_1': deque(maxlen=self.max_points),
            'differential_2': deque(maxlen=self.max_points),
            'cross_axial_x': deque(maxlen=self.max_points),
            'cross_axial_y': deque(maxlen=self.max_points),
        }
        self.time_history = deque(maxlen=self.max_points)
        self.start_time = time.time()
        
        # Performance optimization
        self.update_counter = 0
        self.plot_update_frequency = 2  # Update plots every 2 data points
        
        # Initialize DAQ worker
        self.daq_worker = DAQWorker(board_num=board_num)
        self.daq_worker.data_ready.connect(self.update_data)
        self.daq_worker.error_signal.connect(self.handle_error)
        
        # GUI update timer (fallback)
        self.gui_timer = QTimer()
        self.gui_timer.timeout.connect(self.process_gui_events)
        self.gui_timer.start(50)  # 50ms intervals
        
        self.init_ui()
        self.setup_plots()
        
    def init_ui(self):
        """Initialize user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
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
        
        # Settings tab
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "Settings")
        
        main_layout.addWidget(tab_widget)
        
        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
    def create_control_panel(self):
        """Create control panel"""
        group = QGroupBox("Control Panel")
        layout = QHBoxLayout(group)
        
        # Start/Stop buttons
        self.start_btn = QPushButton("Start Acquisition")
        self.start_btn.clicked.connect(self.start_acquisition)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Acquisition")
        self.stop_btn.clicked.connect(self.stop_acquisition)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        # Sample rate control
        layout.addWidget(QLabel("Sample Rate (Hz):"))
        self.sample_rate_spin = QSpinBox()
        self.sample_rate_spin.setRange(1, 1000)  # Limited range for stability
        self.sample_rate_spin.setValue(100)  # Lower default
        self.sample_rate_spin.valueChanged.connect(self.update_sample_rate)
        layout.addWidget(self.sample_rate_spin)
        
        # Clear data button
        clear_btn = QPushButton("Clear Data")
        clear_btn.clicked.connect(self.clear_data)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        return group
    
    def create_data_display_tab(self):
        """Create data display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Current values display
        values_group = QGroupBox("Current Values")
        values_layout = QGridLayout(values_group)
        
        self.value_displays = {}
        channels = ['differential_1', 'differential_2', 'cross_axial_x', 'cross_axial_y']
        
        for i, channel in enumerate(channels):
            label = QLabel(f"{channel.replace('_', ' ').title()}:")
            values_layout.addWidget(label, i, 0)
            
            lcd = QLCDNumber()
            lcd.setDigitCount(8)
            lcd.setSegmentStyle(QLCDNumber.Flat)
            self.value_displays[channel] = lcd
            values_layout.addWidget(lcd, i, 1)
            
            unit_label = QLabel("V" if "differential" in channel else "g")
            values_layout.addWidget(unit_label, i, 2)
        
        layout.addWidget(values_group)
        
        # Statistics display
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        layout.addStretch()
        
        return widget
    
    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Sensitivity settings
        sens_group = QGroupBox("Sensitivity Settings")
        sens_layout = QGridLayout(sens_group)
        
        self.sensitivity_controls = {}
        channels = ['differential_1', 'differential_2', 'cross_axial_x', 'cross_axial_y']
        defaults = [1.0, 1.0, 0.1, 0.1]
        
        for i, (channel, default) in enumerate(zip(channels, defaults)):
            label = QLabel(f"{channel.replace('_', ' ').title()}:")
            sens_layout.addWidget(label, i, 0)
            
            spin = QDoubleSpinBox()
            spin.setRange(0.001, 10.0)
            spin.setDecimals(3)
            spin.setValue(default)
            spin.setSuffix(" V/unit")
            spin.valueChanged.connect(lambda val, ch=channel: self.update_sensitivity(ch, val))
            self.sensitivity_controls[channel] = spin
            sens_layout.addWidget(spin, i, 1)
        
        layout.addWidget(sens_group)
        
        # Plot settings
        plot_group = QGroupBox("Plot Settings")
        plot_layout = QGridLayout(plot_group)
        
        plot_layout.addWidget(QLabel("Time Window (s):"), 0, 0)
        self.time_window_spin = QSpinBox()
        self.time_window_spin.setRange(1, 300)
        self.time_window_spin.setValue(10)
        plot_layout.addWidget(self.time_window_spin, 0, 1)
        
        plot_layout.addWidget(QLabel("Max Points:"), 1, 0)
        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(100, 2000)  # Reduced maximum
        self.max_points_spin.setValue(500)  # Lower default
        self.max_points_spin.valueChanged.connect(self.update_max_points)
        plot_layout.addWidget(self.max_points_spin, 1, 1)
        
        layout.addWidget(plot_group)
        layout.addStretch()
        
        return widget
    
    def setup_plots(self):
        """Setup real-time plots"""
        self.plot_widget.clear()
        
        # Create subplots
        self.plots = {}
        self.curves = {}
        
        channels = ['differential_1', 'differential_2', 'cross_axial_x', 'cross_axial_y']
        colors = ['r', 'g', 'b', 'y']
        
        for i, (channel, color) in enumerate(zip(channels, colors)):
            plot = self.plot_widget.addPlot(row=i//2, col=i%2)
            plot.setLabel('left', channel.replace('_', ' ').title())
            plot.setLabel('bottom', 'Time (s)')
            plot.addLegend()
            
            curve = plot.plot(pen=color, name=channel)
            
            self.plots[channel] = plot
            self.curves[channel] = curve
    
    def start_acquisition(self):
        """Start data acquisition"""
        try:
            # Test DAQ connection first
            try:
                test_read = ul.a_in(0, 0, ULRange.BIP10VOLTS)
                self.status_label.setText("DAQ device connected successfully")
            except Exception as e:
                self.handle_error(f"DAQ connection failed: {e}")
                return
            
            self.daq_worker.start()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Acquiring data...")
            self.start_time = time.time()
            
        except Exception as e:
            self.handle_error(f"Start error: {e}")
    
    def stop_acquisition(self):
        """Stop data acquisition"""
        self.daq_worker.stop()
        self.daq_worker.wait(3000)  # Wait up to 3 seconds
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Stopped")
    
    def process_gui_events(self):
        """Process GUI events to prevent freezing"""
        QApplication.processEvents()
    
    def update_data(self, readings):
        """Update data and plots with throttling"""
        self.update_counter += 1
        
        current_time = time.time() - self.start_time
        self.time_history.append(current_time)
        
        # Update data history
        for channel, data in readings.items():
            self.data_history[channel].append(data['scaled_value'])
            
            # Update LCD displays
            if channel in self.value_displays:
                self.value_displays[channel].display(data['scaled_value'])
        
        # Update plots less frequently
        if self.update_counter % self.plot_update_frequency == 0:
            self.update_plots()
        
        # Update statistics even less frequently
        if self.update_counter % 10 == 0:
            self.update_statistics()
    
    def update_plots(self):
        """Update plots with optimized rendering"""
        if len(self.time_history) < 2:
            return
            
        try:
            time_array = np.array(self.time_history)
            
            for channel in self.data_history.keys():
                if channel in self.curves and len(self.data_history[channel]) > 0:
                    data_array = np.array(self.data_history[channel])
                    
                    # Downsample if too many points
                    if len(data_array) > 1000:
                        step = len(data_array) // 1000
                        time_array = time_array[::step]
                        data_array = data_array[::step]
                    
                    self.curves[channel].setData(time_array, data_array)
                    
        except Exception as e:
            print(f"Plot update error: {e}")  # Debug print, don't crash GUI
    
    def update_statistics(self):
        """Update statistics display (throttled)"""
        try:
            stats_text = "Channel Statistics:\n\n"
            
            for channel, data in self.data_history.items():
                if len(data) > 0:
                    data_array = np.array(data)
                    mean_val = np.mean(data_array)
                    std_val = np.std(data_array)
                    min_val = np.min(data_array)
                    max_val = np.max(data_array)
                    
                    stats_text += f"{channel.replace('_', ' ').title()}:\n"
                    stats_text += f"  Mean: {mean_val:.4f}\n"
                    stats_text += f"  Std:  {std_val:.4f}\n"
                    stats_text += f"  Min:  {min_val:.4f}\n"
                    stats_text += f"  Max:  {max_val:.4f}\n\n"
            
            self.stats_text.setText(stats_text)
        except Exception as e:
            print(f"Statistics update error: {e}")  # Debug print
    
    def update_sensitivity(self, channel, value):
        """Update sensitivity setting"""
        self.daq_worker.set_sensitivity(channel, value)
    
    def update_sample_rate(self, rate):
        """Update sample rate"""
        self.daq_worker.set_sample_rate(rate)
    
    def update_max_points(self, points):
        """Update maximum number of points"""
        self.max_points = points
        for channel in self.data_history:
            self.data_history[channel] = deque(self.data_history[channel], maxlen=points)
        self.time_history = deque(self.time_history, maxlen=points)
    
    def clear_data(self):
        """Clear all data"""
        for channel in self.data_history:
            self.data_history[channel].clear()
        self.time_history.clear()
        self.start_time = time.time()
    
    def handle_error(self, error_msg):
        """Handle errors gracefully"""
        self.status_label.setText(f"Error: {error_msg}")
        print(f"DAQ Error: {error_msg}")  # Debug print
        self.stop_acquisition()
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.gui_timer.stop()
        if self.daq_worker.isRunning():
            self.daq_worker.stop()
            self.daq_worker.wait(5000)  # Wait up to 5 seconds
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
    
    window = DAQMonitorGUI(1)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()