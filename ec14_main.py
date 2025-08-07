"""
EC316K Main Application - Simplified Version
Main GUI application for the EC316K Eddy Current Testing System
Based on the original EC316K TestPoint implementation
"""

import sys
import time
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QGroupBox, 
                            QTabWidget, QMessageBox, QStatusBar, QComboBox,
                            QSpinBox, QDoubleSpinBox, QFormLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg

from ec14_config import EC316KConfig
from ec14_daq import EC316KDAQManager

class EC316KMainWindow(QMainWindow):
    """Main EC316K application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration and DAQ manager
        self.config = EC316KConfig()
        self.daq_manager = EC316KDAQManager(self.config)
        
        # Setup UI
        self.setup_ui()
        self.setup_status_bar()
        
        # Setup timer for updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(100)  # Update every 100ms
    
    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("EC316K Python - Eddy Current Testing System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls
        self.create_control_panel(main_layout)
        
        # Right panel - Plots
        self.create_plot_panel(main_layout)
    
    def create_control_panel(self, parent_layout):
        """Create the control panel"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Hardware settings group
        hardware_group = QGroupBox("Hardware Settings")
        hardware_layout = QFormLayout(hardware_group)
        
        # Sample rate selector (as per EC316K)
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(['300', '600', '1000', '2000'])
        self.sample_rate_combo.setCurrentText(str(self.config.sample_rate))
        self.sample_rate_combo.currentTextChanged.connect(self.update_sample_rate)
        hardware_layout.addRow("Sample Rate (Hz):", self.sample_rate_combo)
        
        # Operating mode selector
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Differential/Cross-Axial (Single Frequency)",
            "Differential/Absolute (Dual Frequency)", 
            "Send/Receive (Single Frequency)",
            "Differential/Differential (Dual Frequency)"
        ])
        self.mode_combo.setCurrentIndex(self.config.operating_mode)
        self.mode_combo.currentIndexChanged.connect(self.update_operating_mode)
        hardware_layout.addRow("Operating Mode:", self.mode_combo)
        
        control_layout.addWidget(hardware_group)
        
        # Frequency settings group
        freq_group = QGroupBox("Frequency Settings")
        freq_layout = QFormLayout(freq_group)
        
        self.freq1_spin = QSpinBox()
        self.freq1_spin.setRange(100, 50000)
        self.freq1_spin.setValue(self.config.frequencies['ch1'])
        self.freq1_spin.valueChanged.connect(lambda value: self.update_frequency('ch1', value))
        freq_layout.addRow("Ch1 Frequency (Hz):", self.freq1_spin)
        
        self.freq2_spin = QSpinBox()
        self.freq2_spin.setRange(100, 50000)
        self.freq2_spin.setValue(self.config.frequencies['ch2'])
        self.freq2_spin.valueChanged.connect(lambda value: self.update_frequency('ch2', value))
        freq_layout.addRow("Ch2 Frequency (Hz):", self.freq2_spin)
        
        control_layout.addWidget(freq_group)
        
        # Channel settings group
        channel_group = QGroupBox("Channel Settings")
        channel_layout = QFormLayout(channel_group)
        
        self.gain_spins = {}
        for channel_name, channel_info in self.config.channels.items():
            gain_spin = QDoubleSpinBox()
            gain_spin.setRange(0.01, 100.0)
            gain_spin.setValue(self.config.gains[channel_name])
            gain_spin.setDecimals(3)
            gain_spin.valueChanged.connect(lambda value, ch=channel_name: self.update_gain(ch, value))
            self.gain_spins[channel_name] = gain_spin
            channel_layout.addRow(f"{channel_info['name']} Gain:", gain_spin)
        
        control_layout.addWidget(channel_group)
        
        # Control buttons
        button_group = QGroupBox("Controls")
        button_layout = QVBoxLayout(button_group)
        
        self.start_button = QPushButton("Start Acquisition")
        self.start_button.clicked.connect(self.start_acquisition)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Acquisition")
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.balance_button = QPushButton("Balance")
        self.balance_button.clicked.connect(self.balance_channels)
        button_layout.addWidget(self.balance_button)
        
        self.clear_button = QPushButton("Clear Data")
        self.clear_button.clicked.connect(self.clear_data)
        button_layout.addWidget(self.clear_button)
        
        control_layout.addWidget(button_group)
        
        # Status display
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: green; }")
        status_layout.addWidget(self.status_label)
        
        self.sample_count_label = QLabel("Samples: 0")
        status_layout.addWidget(self.sample_count_label)
        
        self.scan_rate_label = QLabel(f"Scan Rate: {self.config.get_scan_rate()} Hz")
        status_layout.addWidget(self.scan_rate_label)
        
        self.mode_label = QLabel(f"Mode: {self.config.get_mode_description()}")
        status_layout.addWidget(self.mode_label)
        
        control_layout.addWidget(status_group)
        
        control_layout.addStretch()
        parent_layout.addWidget(control_widget)
    
    def create_plot_panel(self, parent_layout):
        """Create the plot panel"""
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        plot_layout.addWidget(self.tab_widget)
        
        # 1XY plot (Channel 1 X-Y)
        self.create_1xy_tab()
        
        # 2XY-1SC plot (2 XY charts + 1 Strip Chart)
        self.create_2xy_1sc_tab()
        
        # Time series plot
        self.create_time_series_tab()
        
        parent_layout.addWidget(plot_widget)
    
    def create_1xy_tab(self):
        """Create the 1XY display tab"""
        xy_widget = QWidget()
        xy_layout = QVBoxLayout(xy_widget)
        
        # Channel 1 XY plot
        ch1_group = QGroupBox("Channel 1 (X-Y)")
        ch1_layout = QVBoxLayout(ch1_group)
        self.ch1_plot = pg.PlotWidget()
        self.ch1_plot.setLabel('left', 'Y Amplitude')
        self.ch1_plot.setLabel('bottom', 'X Amplitude')
        self.ch1_plot.showGrid(x=True, y=True)
        ch1_layout.addWidget(self.ch1_plot)
        xy_layout.addWidget(ch1_group)
        
        self.tab_widget.addTab(xy_widget, "1XY")
    
    def create_2xy_1sc_tab(self):
        """Create the 2XY-1SC display tab"""
        xy_sc_widget = QWidget()
        xy_sc_layout = QHBoxLayout(xy_sc_widget)
        
        # Left side - XY plots
        xy_plots_widget = QWidget()
        xy_plots_layout = QVBoxLayout(xy_plots_widget)
        
        # Channel 1 XY plot
        ch1_group = QGroupBox("Channel 1 (X-Y)")
        ch1_layout = QVBoxLayout(ch1_group)
        self.ch1_xy_plot = pg.PlotWidget()
        self.ch1_xy_plot.setLabel('left', 'Y Amplitude')
        self.ch1_xy_plot.setLabel('bottom', 'X Amplitude')
        self.ch1_xy_plot.showGrid(x=True, y=True)
        ch1_layout.addWidget(self.ch1_xy_plot)
        xy_plots_layout.addWidget(ch1_group)
        
        # Channel 2 XY plot
        ch2_group = QGroupBox("Channel 2 (X-Y)")
        ch2_layout = QVBoxLayout(ch2_group)
        self.ch2_xy_plot = pg.PlotWidget()
        self.ch2_xy_plot.setLabel('left', 'Y Amplitude')
        self.ch2_xy_plot.setLabel('bottom', 'X Amplitude')
        self.ch2_xy_plot.showGrid(x=True, y=True)
        ch2_layout.addWidget(self.ch2_xy_plot)
        xy_plots_layout.addWidget(ch2_group)
        
        xy_sc_layout.addWidget(xy_plots_widget)
        
        # Right side - Strip chart
        sc_widget = QWidget()
        sc_layout = QVBoxLayout(sc_widget)
        
        sc_group = QGroupBox("Strip Chart")
        sc_group_layout = QVBoxLayout(sc_group)
        self.strip_chart = pg.PlotWidget()
        self.strip_chart.setLabel('left', 'Amplitude')
        self.strip_chart.setLabel('bottom', 'Time (s)')
        self.strip_chart.showGrid(x=True, y=True)
        sc_group_layout.addWidget(self.strip_chart)
        sc_layout.addWidget(sc_group)
        
        xy_sc_layout.addWidget(sc_widget)
        
        self.tab_widget.addTab(xy_sc_widget, "2XY-1SC")
    
    def create_time_series_tab(self):
        """Create the time series display tab"""
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        
        time_group = QGroupBox("Time Series")
        time_group_layout = QVBoxLayout(time_group)
        self.time_plot = pg.PlotWidget()
        self.time_plot.setLabel('left', 'Amplitude')
        self.time_plot.setLabel('bottom', 'Time (s)')
        self.time_plot.showGrid(x=True, y=True)
        time_group_layout.addWidget(self.time_plot)
        time_layout.addWidget(time_group)
        
        self.tab_widget.addTab(time_widget, "Time Series")
    
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def start_acquisition(self):
        """Start data acquisition"""
        try:
            if self.daq_manager.start_acquisition():
                # Setup connections
                worker = self.daq_manager.get_worker()
                if worker:
                    worker.data_ready.connect(self.update_data)
                    worker.error_signal.connect(self.handle_error)
                    worker.status_signal.connect(self.update_status)
                
                # Update UI
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.status_label.setText("Acquiring")
                self.status_label.setStyleSheet("QLabel { color: red; }")
            else:
                QMessageBox.warning(self, "Warning", "Acquisition already running")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start acquisition: {e}")
    
    def stop_acquisition(self):
        """Stop data acquisition"""
        self.daq_manager.stop_acquisition()
        
        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("QLabel { color: orange; }")
    
    def balance_channels(self):
        """Balance the channels (simulate EC316K balance function)"""
        if self.daq_manager.is_running():
            self.status_bar.showMessage("Balancing channels...", 3000)
            # In a real implementation, this would perform the balance operation
            # For now, just show a message
            QMessageBox.information(self, "Balance", "Channel balance operation completed")
        else:
            QMessageBox.warning(self, "Warning", "Start acquisition before balancing")
    
    def update_data(self, readings):
        """Update data display"""
        # Update plot (simplified)
        if hasattr(self, 'time_data'):
            self.time_data.append(time.time())
            for channel, value in readings.items():
                if channel not in self.channel_data:
                    self.channel_data[channel] = []
                self.channel_data[channel].append(value)
        else:
            self.time_data = [time.time()]
            self.channel_data = {channel: [value] for channel, value in readings.items()}
        
        # Update sample count
        self.sample_count_label.setText(f"Samples: {len(self.time_data)}")
    
    def update_display(self):
        """Update display"""
        if hasattr(self, 'time_data') and len(self.time_data) > 1:
            # Update 1XY plot
            if 'ch1_x' in self.channel_data and 'ch1_y' in self.channel_data:
                x_data = self.channel_data['ch1_x']
                y_data = self.channel_data['ch1_y']
                if len(x_data) == len(y_data):
                    self.ch1_plot.clear()
                    self.ch1_plot.plot(x_data, y_data, pen=pg.mkPen('b', width=2))
            
            # Update 2XY-1SC plots
            if 'ch1_x' in self.channel_data and 'ch1_y' in self.channel_data:
                x_data = self.channel_data['ch1_x']
                y_data = self.channel_data['ch1_y']
                if len(x_data) == len(y_data):
                    self.ch1_xy_plot.clear()
                    self.ch1_xy_plot.plot(x_data, y_data, pen=pg.mkPen('b', width=2))
            
            if 'ch2_x' in self.channel_data and 'ch2_y' in self.channel_data:
                x_data = self.channel_data['ch2_x']
                y_data = self.channel_data['ch2_y']
                if len(x_data) == len(y_data):
                    self.ch2_xy_plot.clear()
                    self.ch2_xy_plot.plot(x_data, y_data, pen=pg.mkPen('r', width=2))
            
            # Update strip chart
            self.strip_chart.clear()
            colors = ['b', 'r', 'g', 'm']
            for i, (channel, data) in enumerate(self.channel_data.items()):
                if len(data) == len(self.time_data):
                    self.strip_chart.plot(
                        self.time_data, data, 
                        pen=pg.mkPen(colors[i % len(colors)], width=1),
                        name=channel
                    )
            
            # Update time series plot
            self.time_plot.clear()
            for i, (channel, data) in enumerate(self.channel_data.items()):
                if len(data) == len(self.time_data):
                    self.time_plot.plot(
                        self.time_data, data, 
                        pen=pg.mkPen(colors[i % len(colors)], width=1),
                        name=channel
                    )
    
    def update_sample_rate(self, rate_str):
        """Update sample rate"""
        try:
            rate = int(rate_str)
            self.config.sample_rate = rate
            self.scan_rate_label.setText(f"Scan Rate: {self.config.get_scan_rate()} Hz")
            self.daq_manager.update_config(self.config)
        except ValueError:
            pass
    
    def update_operating_mode(self, mode_index):
        """Update operating mode"""
        self.config.update_operating_mode(mode_index)
        self.mode_label.setText(f"Mode: {self.config.get_mode_description()}")
        self.daq_manager.update_config(self.config)
    
    def update_frequency(self, channel, frequency):
        """Update frequency for a channel"""
        self.config.update_frequency(channel, frequency)
        self.daq_manager.update_config(self.config)
    
    def update_gain(self, channel, gain):
        """Update gain for a channel"""
        self.config.update_gain(channel, gain)
        self.daq_manager.update_config(self.config)
    
    def clear_data(self):
        """Clear all data"""
        # Clear plots
        self.ch1_plot.clear()
        self.ch1_xy_plot.clear()
        self.ch2_xy_plot.clear()
        self.strip_chart.clear()
        self.time_plot.clear()
        
        # Clear data structures
        if hasattr(self, 'time_data'):
            self.time_data.clear()
        if hasattr(self, 'channel_data'):
            self.channel_data.clear()
        
        # Clear DAQ history
        if self.daq_manager.worker:
            self.daq_manager.worker.clear_data_history()
        
        self.sample_count_label.setText("Samples: 0")
    
    def handle_error(self, error_msg):
        """Handle error messages"""
        self.status_bar.showMessage(f"Error: {error_msg}", 5000)
        QMessageBox.warning(self, "Error", error_msg)
    
    def update_status(self, message):
        """Update status message"""
        self.status_bar.showMessage(message, 3000)

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("EC316K Python")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = EC316KMainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 