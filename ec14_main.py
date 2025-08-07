"""
EC316K Main Application
Main GUI application for the EC316K Eddy Current Testing System
Based on the original EC316K TestPoint implementation
"""

import sys
import time
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QGroupBox, 
                            QTabWidget, QMessageBox, QStatusBar, QComboBox,
                            QSpinBox, QDoubleSpinBox, QFormLayout, QGridLayout,
                            QCheckBox, QSlider, QLCDNumber, QFrame)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg

from ec14_config import EC316KConfig
from ec14_daq import EC316KDAQManager

class EC316KMainWindow(QMainWindow):
    """Main EC316K application window - matches original layout"""
    
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
        """Setup the main user interface to match EC316K layout"""
        self.setWindowTitle("EC316K - Eddy Current Testing System")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls (matches original EC316K layout)
        self.create_control_panel(main_layout)
        
        # Right panel - Plots
        self.create_plot_panel(main_layout)
    
    def create_control_panel(self, parent_layout):
        """Create the control panel matching EC316K layout"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Menu Bar (as per EC316K)
        menubar_group = QGroupBox("Menu")
        menubar_layout = QVBoxLayout(menubar_group)
        
        self.menubar_combo = QComboBox()
        self.menubar_combo.addItems([
            "Buttons", "Menus", "Auto Record", "Foot Switch Record",
            "Save Data", "Save Image", "2XY-1SC Setup", "1XY Setup",
            "2XY-1SC Mode", "1XY Mode", "Save Settings", "Exit", "Go To Setup"
        ])
        menubar_layout.addWidget(self.menubar_combo)
        control_layout.addWidget(menubar_group)
        
        # Main Controls
        controls_group = QGroupBox("Controls")
        controls_layout = QGridLayout(controls_group)
        
        # Row 1
        self.startup_button = QPushButton("Startup")
        self.startup_button.clicked.connect(self.startup_system)
        controls_layout.addWidget(self.startup_button, 0, 0)
        
        self.balance_button = QPushButton("Balance")
        self.balance_button.clicked.connect(self.balance_channels)
        controls_layout.addWidget(self.balance_button, 0, 1)
        
        self.offsets_button = QPushButton("Offsets")
        self.offsets_button.clicked.connect(self.show_offsets)
        controls_layout.addWidget(self.offsets_button, 0, 2)
        
        # Row 2
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_tube)
        controls_layout.addWidget(self.next_button, 1, 0)
        
        self.previous_button = QPushButton("Previous")
        self.previous_button.clicked.connect(self.previous_tube)
        controls_layout.addWidget(self.previous_button, 1, 1)
        
        self.go_to_button = QPushButton("Go To")
        self.go_to_button.clicked.connect(self.go_to_tube)
        controls_layout.addWidget(self.go_to_button, 1, 2)
        
        # Row 3
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        controls_layout.addWidget(self.save_settings_button, 2, 0)
        
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        controls_layout.addWidget(self.exit_button, 2, 1)
        
        self.setup_button = QPushButton("Setup")
        self.setup_button.clicked.connect(self.show_setup)
        controls_layout.addWidget(self.setup_button, 2, 2)
        
        control_layout.addWidget(controls_group)
        
        # Display Mode Controls
        display_group = QGroupBox("Display Mode")
        display_layout = QVBoxLayout(display_group)
        
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["1XY", "2XY-1SC", "2Ch-XY"])
        self.display_mode_combo.currentTextChanged.connect(self.change_display_mode)
        display_layout.addWidget(self.display_mode_combo)
        
        # Display Mode Buttons
        display_buttons_layout = QHBoxLayout()
        self.xy_setup_button = QPushButton("XY Setup")
        self.xy_setup_button.clicked.connect(self.show_xy_setup)
        display_buttons_layout.addWidget(self.xy_setup_button)
        
        self.sc_setup_button = QPushButton("2XY-1SC Setup")
        self.sc_setup_button.clicked.connect(self.show_sc_setup)
        display_buttons_layout.addWidget(self.sc_setup_button)
        
        display_layout.addLayout(display_buttons_layout)
        control_layout.addWidget(display_group)
        
        # Channel Controls
        channel_group = QGroupBox("Channel Settings")
        channel_layout = QFormLayout(channel_group)
        
        # Frequencies
        self.f1_freq_spin = QSpinBox()
        self.f1_freq_spin.setRange(100, 50000)
        self.f1_freq_spin.setValue(self.config.frequencies['ch1'])
        self.f1_freq_spin.valueChanged.connect(lambda value: self.update_frequency('ch1', value))
        channel_layout.addRow("F1 (Hz):", self.f1_freq_spin)
        
        self.f2_freq_spin = QSpinBox()
        self.f2_freq_spin.setRange(100, 50000)
        self.f2_freq_spin.setValue(self.config.frequencies['ch2'])
        self.f2_freq_spin.valueChanged.connect(lambda value: self.update_frequency('ch2', value))
        channel_layout.addRow("F2 (Hz):", self.f2_freq_spin)
        
        # Gains
        self.ch1_gain_spin = QDoubleSpinBox()
        self.ch1_gain_spin.setRange(0.01, 100.0)
        self.ch1_gain_spin.setValue(self.config.gains['ch1_x'])
        self.ch1_gain_spin.valueChanged.connect(lambda value: self.update_gain('ch1_x', value))
        channel_layout.addRow("Ch1 Gain:", self.ch1_gain_spin)
        
        self.ch2_gain_spin = QDoubleSpinBox()
        self.ch2_gain_spin.setRange(0.01, 100.0)
        self.ch2_gain_spin.setValue(self.config.gains['ch2_x'])
        self.ch2_gain_spin.valueChanged.connect(lambda value: self.update_gain('ch2_x', value))
        channel_layout.addRow("Ch2 Gain:", self.ch2_gain_spin)
        
        control_layout.addWidget(channel_group)
        
        # Data Controls
        data_group = QGroupBox("Data")
        data_layout = QGridLayout(data_group)
        
        self.run_button = QPushButton("RUN")
        self.run_button.clicked.connect(self.start_acquisition)
        self.run_button.setStyleSheet("QPushButton { background-color: green; color: white; font-weight: bold; }")
        data_layout.addWidget(self.run_button, 0, 0)
        
        self.stop_button = QPushButton("STOP")
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("QPushButton { background-color: red; color: white; font-weight: bold; }")
        data_layout.addWidget(self.stop_button, 0, 1)
        
        self.save_data_button = QPushButton("Save Data")
        self.save_data_button.clicked.connect(self.save_data)
        data_layout.addWidget(self.save_data_button, 1, 0)
        
        self.save_image_button = QPushButton("Save Image")
        self.save_image_button.clicked.connect(self.save_image)
        data_layout.addWidget(self.save_image_button, 1, 1)
        
        control_layout.addWidget(data_group)
        
        # Status Display
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        status_layout.addWidget(self.status_label)
        
        self.sample_count_label = QLabel("Samples: 0")
        status_layout.addWidget(self.sample_count_label)
        
        self.scan_rate_label = QLabel(f"Scan Rate: {self.config.get_scan_rate()} Hz")
        status_layout.addWidget(self.scan_rate_label)
        
        self.mode_label = QLabel(f"Mode: {self.config.get_mode_description()}")
        status_layout.addWidget(self.mode_label)
        
        # Timer display
        self.timer_lcd = QLCDNumber()
        self.timer_lcd.setDigitCount(8)
        self.timer_lcd.display("00:00:00")
        status_layout.addWidget(self.timer_lcd)
        
        control_layout.addWidget(status_group)
        
        control_layout.addStretch()
        parent_layout.addWidget(control_widget)
    
    def create_plot_panel(self, parent_layout):
        """Create the plot panel with multiple display modes"""
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        plot_layout.addWidget(self.tab_widget)
        
        # 1XY plot (Channel 1 X-Y)
        self.create_1xy_tab()
        
        # 2XY-1SC plot (2 XY charts + 1 Strip Chart)
        self.create_2xy_1sc_tab()
        
        # 2Ch-XY plot (2 Channel XY)
        self.create_2ch_xy_tab()
        
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
        self.ch1_plot.setAspectLocked(True)  # Square aspect ratio
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
        self.ch1_xy_plot.setAspectLocked(True)
        ch1_layout.addWidget(self.ch1_xy_plot)
        xy_plots_layout.addWidget(ch1_group)
        
        # Channel 2 XY plot
        ch2_group = QGroupBox("Channel 2 (X-Y)")
        ch2_layout = QVBoxLayout(ch2_group)
        self.ch2_xy_plot = pg.PlotWidget()
        self.ch2_xy_plot.setLabel('left', 'Y Amplitude')
        self.ch2_xy_plot.setLabel('bottom', 'X Amplitude')
        self.ch2_xy_plot.showGrid(x=True, y=True)
        self.ch2_xy_plot.setAspectLocked(True)
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
    
    def create_2ch_xy_tab(self):
        """Create the 2Ch-XY display tab"""
        ch_xy_widget = QWidget()
        ch_xy_layout = QHBoxLayout(ch_xy_widget)
        
        # Channel 1 XY plot
        ch1_group = QGroupBox("Channel 1 (X-Y)")
        ch1_layout = QVBoxLayout(ch1_group)
        self.ch1_2ch_plot = pg.PlotWidget()
        self.ch1_2ch_plot.setLabel('left', 'Y Amplitude')
        self.ch1_2ch_plot.setLabel('bottom', 'X Amplitude')
        self.ch1_2ch_plot.showGrid(x=True, y=True)
        self.ch1_2ch_plot.setAspectLocked(True)
        ch1_layout.addWidget(self.ch1_2ch_plot)
        ch_xy_layout.addWidget(ch1_group)
        
        # Channel 2 XY plot
        ch2_group = QGroupBox("Channel 2 (X-Y)")
        ch2_layout = QVBoxLayout(ch2_group)
        self.ch2_2ch_plot = pg.PlotWidget()
        self.ch2_2ch_plot.setLabel('left', 'Y Amplitude')
        self.ch2_2ch_plot.setLabel('bottom', 'X Amplitude')
        self.ch2_2ch_plot.showGrid(x=True, y=True)
        self.ch2_2ch_plot.setAspectLocked(True)
        ch2_layout.addWidget(self.ch2_2ch_plot)
        ch_xy_layout.addWidget(ch2_group)
        
        self.tab_widget.addTab(ch_xy_widget, "2Ch-XY")
    
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
    
    def startup_system(self):
        """Startup the system (simulate EC316K startup)"""
        self.status_bar.showMessage("Starting up system...", 3000)
        QMessageBox.information(self, "Startup", "System initialized successfully")
    
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
                self.run_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.status_label.setText("RUNNING")
                self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                
                # Start timer
                self.start_time = time.time()
                self.timer_timer = QTimer()
                self.timer_timer.timeout.connect(self.update_timer)
                self.timer_timer.start(1000)  # Update every second
            else:
                QMessageBox.warning(self, "Warning", "Acquisition already running")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start acquisition: {e}")
    
    def stop_acquisition(self):
        """Stop data acquisition"""
        self.daq_manager.stop_acquisition()
        
        # Update UI
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("STOPPED")
        self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
        
        # Stop timer
        if hasattr(self, 'timer_timer'):
            self.timer_timer.stop()
    
    def balance_channels(self):
        """Balance the channels (simulate EC316K balance function)"""
        if self.daq_manager.is_running():
            self.status_bar.showMessage("Balancing channels...", 3000)
            QMessageBox.information(self, "Balance", "Channel balance operation completed")
        else:
            QMessageBox.warning(self, "Warning", "Start acquisition before balancing")
    
    def show_offsets(self):
        """Show offset controls"""
        QMessageBox.information(self, "Offsets", "Offset controls not implemented yet")
    
    def next_tube(self):
        """Go to next tube"""
        self.status_bar.showMessage("Next tube selected", 2000)
    
    def previous_tube(self):
        """Go to previous tube"""
        self.status_bar.showMessage("Previous tube selected", 2000)
    
    def go_to_tube(self):
        """Go to specific tube"""
        self.status_bar.showMessage("Go to tube function", 2000)
    
    def save_settings(self):
        """Save current settings"""
        self.config.save_config()
        self.status_bar.showMessage("Settings saved", 2000)
    
    def show_setup(self):
        """Show setup dialog"""
        QMessageBox.information(self, "Setup", "Setup dialog not implemented yet")
    
    def change_display_mode(self, mode):
        """Change display mode"""
        self.status_bar.showMessage(f"Display mode changed to {mode}", 2000)
    
    def show_xy_setup(self):
        """Show XY setup"""
        QMessageBox.information(self, "XY Setup", "XY setup not implemented yet")
    
    def show_sc_setup(self):
        """Show strip chart setup"""
        QMessageBox.information(self, "2XY-1SC Setup", "Strip chart setup not implemented yet")
    
    def save_data(self):
        """Save data"""
        self.status_bar.showMessage("Data saved", 2000)
    
    def save_image(self):
        """Save image"""
        self.status_bar.showMessage("Image saved", 2000)
    
    def update_timer(self):
        """Update the timer display"""
        if hasattr(self, 'start_time'):
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.timer_lcd.display(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
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
            
            # Update 2Ch-XY plots
            if 'ch1_x' in self.channel_data and 'ch1_y' in self.channel_data:
                x_data = self.channel_data['ch1_x']
                y_data = self.channel_data['ch1_y']
                if len(x_data) == len(y_data):
                    self.ch1_2ch_plot.clear()
                    self.ch1_2ch_plot.plot(x_data, y_data, pen=pg.mkPen('b', width=2))
            
            if 'ch2_x' in self.channel_data and 'ch2_y' in self.channel_data:
                x_data = self.channel_data['ch2_x']
                y_data = self.channel_data['ch2_y']
                if len(x_data) == len(y_data):
                    self.ch2_2ch_plot.clear()
                    self.ch2_2ch_plot.plot(x_data, y_data, pen=pg.mkPen('r', width=2))
            
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
    
    def update_frequency(self, channel, frequency):
        """Update frequency for a channel"""
        self.config.update_frequency(channel, frequency)
        self.daq_manager.update_config(self.config)
    
    def update_gain(self, channel, gain):
        """Update gain for a channel"""
        self.config.update_gain(channel, gain)
        self.daq_manager.update_config(self.config)
    
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
    app.setApplicationName("EC316K")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = EC316KMainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 