"""
Main application window for EC14 Data Acquisition
"""

import sys
import time
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QComboBox, QLabel, QGroupBox, QGridLayout,
                             QStatusBar, QMessageBox, QApplication)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont

import pyqtgraph as pg

from ..hardware.device_manager import DeviceManager
from ..config.device_config import DeviceConfig

class DataAcquisitionThread(QThread):
    """Thread for data acquisition to prevent UI blocking"""
    data_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self.running = False
        
    def run(self):
        """Main data acquisition loop"""
        self.running = True
        print("Data acquisition thread started")
        while self.running:
            try:
                data = self.device_manager.get_scan_data()
                if data is not None:
                    self.data_ready.emit(data)
                self.msleep(10)  # 10ms delay
            except Exception as e:
                error_msg = f"Data acquisition error: {e}"
                print(f"✗ {error_msg}")
                self.error_occurred.emit(error_msg)
                break
        print("Data acquisition thread stopped")
    
    def stop(self):
        """Stop the acquisition thread"""
        self.running = False

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.device_manager = DeviceManager()
        self.acquisition_thread = None
        self.data_buffer = []
        self.max_buffer_size = 1000  # Keep last 1000 data points
        
        self.init_ui()
        self.init_plots()
        self.init_timers()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("EC14 Data Acquisition System - Phase 1")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 1)
        
        # Create plot area
        plot_area = self.create_plot_area()
        main_layout.addWidget(plot_area, 4)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def create_control_panel(self):
        """Create the control panel"""
        control_group = QGroupBox("Device Controls")
        layout = QVBoxLayout(control_group)
        
        # Device initialization
        init_group = QGroupBox("Device Initialization")
        init_layout = QGridLayout(init_group)
        
        self.init_button = QPushButton("Initialize Device")
        self.init_button.clicked.connect(self.initialize_device)
        init_layout.addWidget(self.init_button, 0, 0)
        
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        self.test_button.setEnabled(False)
        init_layout.addWidget(self.test_button, 0, 1)
        
        layout.addWidget(init_group)
        
        # Acquisition controls
        acq_group = QGroupBox("Data Acquisition")
        acq_layout = QGridLayout(acq_group)
        
        self.start_button = QPushButton("Start Scanning")
        self.start_button.clicked.connect(self.start_scanning)
        self.start_button.setEnabled(False)
        acq_layout.addWidget(self.start_button, 0, 0)
        
        self.stop_button = QPushButton("Stop Scanning")
        self.stop_button.clicked.connect(self.stop_scanning)
        self.stop_button.setEnabled(False)
        acq_layout.addWidget(self.stop_button, 0, 1)
        
        # Sample rate selection
        acq_layout.addWidget(QLabel("Sample Rate:"), 1, 0)
        self.sample_rate_combo = QComboBox()
        for rate in DeviceConfig.SAMPLE_RATES:
            self.sample_rate_combo.addItem(f"{rate} Hz", rate)
        self.sample_rate_combo.setCurrentText("1000 Hz")
        self.sample_rate_combo.currentTextChanged.connect(self.on_sample_rate_changed)
        acq_layout.addWidget(self.sample_rate_combo, 1, 1)
        
        # A/D range selection
        acq_layout.addWidget(QLabel("A/D Range:"), 2, 0)
        self.ad_range_combo = QComboBox()
        for range_name in DeviceConfig.AD_RANGES.keys():
            self.ad_range_combo.addItem(range_name)
        self.ad_range_combo.setCurrentText("±5V")
        self.ad_range_combo.currentTextChanged.connect(self.on_ad_range_changed)
        acq_layout.addWidget(self.ad_range_combo, 2, 1)
        
        layout.addWidget(acq_group)
        
        # Display controls
        display_group = QGroupBox("Display Controls")
        display_layout = QGridLayout(display_group)
        
        self.clear_button = QPushButton("Clear Plots")
        self.clear_button.clicked.connect(self.clear_plots)
        display_layout.addWidget(self.clear_button, 0, 0)
        
        self.save_button = QPushButton("Save Data")
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setEnabled(False)
        display_layout.addWidget(self.save_button, 0, 1)
        
        layout.addWidget(display_group)
        
        # Channel information
        info_group = QGroupBox("Channel Information")
        info_layout = QGridLayout(info_group)
        
        self.channel_labels = []
        for i in range(4):
            label = QLabel(f"Ch{i}: 0.000V")
            label.setFont(QFont("Courier", 10))
            self.channel_labels.append(label)
            info_layout.addWidget(label, i, 0)
        
        layout.addWidget(info_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return control_group
    
    def create_plot_area(self):
        """Create the plotting area"""
        plot_widget = QWidget()
        layout = QVBoxLayout(plot_widget)
        
        # Create strip chart
        self.strip_chart = pg.PlotWidget(title="4-Channel Strip Chart")
        self.strip_chart.setLabel('left', 'Voltage (V)')
        self.strip_chart.setLabel('bottom', 'Time (s)')
        self.strip_chart.setYRange(*DeviceConfig.STRIP_CHART_RANGE)
        self.strip_chart.addLegend()
        
        # Create curves for each channel
        colors = ['r', 'g', 'b', 'y']
        self.strip_curves = []
        for i in range(4):
            curve = self.strip_chart.plot(pen=colors[i], name=f'Ch{i}')
            self.strip_curves.append(curve)
        
        layout.addWidget(self.strip_chart)
        
        return plot_widget
    
    def init_plots(self):
        """Initialize plot data"""
        self.time_data = np.array([])
        self.channel_data = [np.array([]) for _ in range(4)]
        
    def init_timers(self):
        """Initialize timers"""
        # Timer for updating channel values display
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_channel_display)
        self.update_timer.start(100)  # Update every 100ms
        
    def initialize_device(self):
        """Initialize the USB-1408FS-Plus device"""
        print("Initializing device...")
        self.status_bar.showMessage("Initializing device...")
        
        try:
            if self.device_manager.initialize_device():
                self.init_button.setEnabled(False)
                self.test_button.setEnabled(True)
                self.start_button.setEnabled(True)
                self.status_bar.showMessage("Device initialized successfully")
                print("✓ Device initialized successfully")
            else:
                error_msg = "Failed to initialize device"
                print(f"✗ {error_msg}")
                QMessageBox.critical(self, "Error", error_msg)
                self.status_bar.showMessage("Device initialization failed")
        except Exception as e:
            error_msg = f"Exception during device initialization: {e}"
            print(f"✗ {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
            self.status_bar.showMessage("Device initialization failed")
    
    def test_connection(self):
        """Test device communication"""
        print("Testing device connection...")
        try:
            if self.device_manager.test_connection():
                self.status_bar.showMessage("Device communication test successful")
                print("✓ Device communication test successful")
            else:
                self.status_bar.showMessage("Device communication test failed")
                print("✗ Device communication test failed")
        except Exception as e:
            error_msg = f"Exception during connection test: {e}"
            print(f"✗ {error_msg}")
            self.status_bar.showMessage("Device communication test failed")
    
    def start_scanning(self):
        """Start data acquisition"""
        print("Starting data acquisition...")
        if self.device_manager.start_scanning():
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.save_button.setEnabled(True)
            
            # Start acquisition thread
            self.acquisition_thread = DataAcquisitionThread(self.device_manager)
            self.acquisition_thread.data_ready.connect(self.process_data)
            self.acquisition_thread.error_occurred.connect(self.handle_error)
            self.acquisition_thread.start()
            
            self.status_bar.showMessage("Scanning started")
            print("✓ Scanning started successfully")
        else:
            error_msg = "Failed to start scanning"
            print(f"✗ {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
    
    def stop_scanning(self):
        """Stop data acquisition"""
        print("Stopping scanning...")
        try:
            if self.acquisition_thread:
                print("  Stopping acquisition thread...")
                self.acquisition_thread.stop()
                self.acquisition_thread.wait()
                self.acquisition_thread = None
                print("  Acquisition thread stopped")
            
            print("  Stopping device manager scanning...")
            self.device_manager.stop_scanning()
            
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_bar.showMessage("Scanning stopped")
            print("✓ Scanning stopped successfully")
        except Exception as e:
            error_msg = f"Exception during stop scanning: {e}"
            print(f"✗ {error_msg}")
            self.status_bar.showMessage("Error stopping scanning")
    
    def process_data(self, data):
        """Process incoming data"""
        if data is None or data.size == 0:
            print("  Received empty data")
            return
            
        print(f"  Received data: shape={data.shape}, size={data.size}")
        
        # Add to buffer
        self.data_buffer.append(data)
        if len(self.data_buffer) > self.max_buffer_size:
            self.data_buffer.pop(0)
        
        # Update plots
        self.update_plots()
    
    def update_plots(self):
        """Update the strip chart plots"""
        if not self.data_buffer:
            return
            
        # Combine all data
        all_data = np.vstack(self.data_buffer)
        
        # Create time axis
        sample_period = 1.0 / self.device_manager.sample_rate
        time_axis = np.arange(len(all_data)) * sample_period
        
        # Update each channel
        for i in range(4):
            channel_values = all_data[:, i]
            self.strip_curves[i].setData(time_axis, channel_values)
    
    def update_channel_display(self):
        """Update channel value display"""
        if self.data_buffer:
            latest_data = self.data_buffer[-1]
            if latest_data is not None and latest_data.size >= 4:
                for i in range(4):
                    value = latest_data[0, i] if latest_data.shape[0] > 0 else 0
                    self.channel_labels[i].setText(f"Ch{i}: {value:.3f}V")
    
    def clear_plots(self):
        """Clear all plots"""
        self.data_buffer.clear()
        for curve in self.strip_curves:
            curve.clear()
        self.status_bar.showMessage("Plots cleared")
    
    def save_data(self):
        """Save current data to file"""
        if not self.data_buffer:
            QMessageBox.information(self, "Info", "No data to save")
            return
            
        try:
            # Combine all data
            all_data = np.vstack(self.data_buffer)
            
            # Save to file
            filename = f"ec14_data_{int(time.time())}.csv"
            np.savetxt(filename, all_data, delimiter=',', 
                      header='Ch0,Ch1,Ch2,Ch3', comments='')
            
            self.status_bar.showMessage(f"Data saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {e}")
    
    def on_sample_rate_changed(self, text):
        """Handle sample rate change"""
        rate = int(text.split()[0])
        self.device_manager.set_sample_rate(rate)
    
    def on_ad_range_changed(self, range_name):
        """Handle A/D range change"""
        self.device_manager.set_ad_range(range_name)
    
    def handle_error(self, error_msg):
        """Handle acquisition errors"""
        print(f"✗ Acquisition Error: {error_msg}")
        QMessageBox.critical(self, "Acquisition Error", error_msg)
        self.stop_scanning()
    
    def closeEvent(self, event):
        """Handle application close"""
        self.stop_scanning()
        self.device_manager.cleanup()
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
