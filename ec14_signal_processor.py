"""
EC14 Signal Processing Module
Advanced signal processing for eddy current analysis including filtering, 
defect detection, and frequency analysis
"""

import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.stats import linregress
from typing import Dict, List, Tuple, Optional
from collections import deque

class SignalProcessor:
    """Advanced signal processing for eddy current analysis"""
    
    def __init__(self, config):
        self.config = config
        self.setup_filters()
        self.defect_history = deque(maxlen=100)
        
    def setup_filters(self):
        """Setup digital filters for signal processing"""
        # Low-pass filter
        self.low_pass_b, self.low_pass_a = signal.butter(
            self.config.filters['filter_order'],
            self.config.filters['low_pass_freq'] / (self.config.sample_rate / 2),
            btype='low'
        )
        
        # High-pass filter
        self.high_pass_b, self.high_pass_a = signal.butter(
            self.config.filters['filter_order'],
            self.config.filters['high_pass_freq'] / (self.config.sample_rate / 2),
            btype='high'
        )
        
        # Notch filter for power line interference
        self.notch_b, self.notch_a = signal.iirnotch(
            self.config.filters['notch_freq'],
            30,  # Q factor
            self.config.sample_rate
        )
        
        # Moving average filter
        self.moving_avg_window = self.config.analysis['smoothing_window']
    
    def apply_filters(self, data: np.ndarray) -> np.ndarray:
        """Apply all filters to the signal"""
        if len(data) == 0:
            return data
        
        filtered_data = data.copy()
        
        # Apply notch filter
        filtered_data = signal.filtfilt(self.notch_b, self.notch_a, filtered_data)
        
        # Apply high-pass filter
        filtered_data = signal.filtfilt(self.high_pass_b, self.high_pass_a, filtered_data)
        
        # Apply low-pass filter
        filtered_data = signal.filtfilt(self.low_pass_b, self.low_pass_a, filtered_data)
        
        # Apply moving average smoothing
        if len(filtered_data) >= self.moving_avg_window:
            filtered_data = signal.convolve(
                filtered_data, 
                np.ones(self.moving_avg_window) / self.moving_avg_window, 
                mode='same'
            )
        
        return filtered_data
    
    def detect_defects(self, x_data: np.ndarray, y_data: np.ndarray, 
                      threshold: Optional[float] = None) -> List[Dict]:
        """Detect defects using amplitude and phase analysis"""
        if threshold is None:
            threshold = self.config.analysis['defect_threshold']
        
        if len(x_data) != len(y_data) or len(x_data) == 0:
            return []
        
        # Calculate signal magnitude
        magnitude = np.sqrt(x_data**2 + y_data**2)
        
        # Find peaks above threshold
        peaks, properties = signal.find_peaks(
            magnitude, 
            height=threshold,
            distance=10,  # Minimum distance between peaks
            prominence=threshold * 0.5  # Minimum prominence
        )
        
        defects = []
        for i, peak_idx in enumerate(peaks):
            # Calculate additional defect properties
            defect = {
                'index': peak_idx,
                'magnitude': magnitude[peak_idx],
                'x_value': x_data[peak_idx],
                'y_value': y_data[peak_idx],
                'phase': np.arctan2(y_data[peak_idx], x_data[peak_idx]),
                'timestamp': peak_idx / self.config.sample_rate,
                'prominence': properties['prominences'][i] if 'prominences' in properties else 0,
                'width': properties['widths'][i] if 'widths' in properties else 0,
                'severity': self.calculate_defect_severity(magnitude[peak_idx], threshold)
            }
            defects.append(defect)
        
        return defects
    
    def calculate_defect_severity(self, magnitude: float, threshold: float) -> str:
        """Calculate defect severity based on magnitude"""
        ratio = magnitude / threshold
        if ratio < 1.5:
            return "Minor"
        elif ratio < 3.0:
            return "Moderate"
        elif ratio < 5.0:
            return "Major"
        else:
            return "Critical"
    
    def calculate_phase_amplitude(self, x_data: np.ndarray, y_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate phase and amplitude from X-Y data"""
        if len(x_data) != len(y_data):
            return np.array([]), np.array([])
        
        amplitude = np.sqrt(x_data**2 + y_data**2)
        phase = np.arctan2(y_data, x_data)
        return amplitude, phase
    
    def fft_analysis(self, data: np.ndarray, sample_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Perform FFT analysis on signal"""
        if len(data) == 0:
            return np.array([]), np.array([])
        
        n = len(data)
        fft_data = fft(data)
        freqs = fftfreq(n, 1/sample_rate)
        
        # Get positive frequencies only
        positive_freqs = freqs[:n//2]
        magnitude = np.abs(fft_data[:n//2])
        
        return positive_freqs, magnitude
    
    def calculate_snr(self, signal_data: np.ndarray, noise_floor: Optional[float] = None) -> float:
        """Calculate Signal-to-Noise Ratio"""
        if len(signal_data) == 0:
            return 0.0
        
        if noise_floor is None:
            noise_floor = self.config.analysis['noise_threshold']
        
        signal_power = np.mean(signal_data**2)
        noise_power = noise_floor**2
        
        if noise_power == 0:
            return float('inf')
        
        snr = 10 * np.log10(signal_power / noise_power)
        return snr
    
    def detect_trends(self, data: np.ndarray, window_size: int = 100) -> Dict:
        """Detect trends in the signal"""
        if len(data) < window_size:
            return {'trend': 'insufficient_data', 'slope': 0, 'correlation': 0}
        
        # Use the last window_size points
        recent_data = data[-window_size:]
        x = np.arange(len(recent_data))
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = linregress(x, recent_data)
        
        # Determine trend
        if abs(slope) < 0.001:
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        
        return {
            'trend': trend,
            'slope': slope,
            'correlation': r_value,
            'p_value': p_value,
            'std_error': std_err
        }
    
    def calculate_statistics(self, data: np.ndarray) -> Dict:
        """Calculate comprehensive statistics for the signal"""
        if len(data) == 0:
            return {}
        
        return {
            'mean': np.mean(data),
            'std': np.std(data),
            'min': np.min(data),
            'max': np.max(data),
            'rms': np.sqrt(np.mean(data**2)),
            'peak_to_peak': np.max(data) - np.min(data),
            'crest_factor': np.max(np.abs(data)) / np.sqrt(np.mean(data**2)),
            'kurtosis': self.calculate_kurtosis(data),
            'skewness': self.calculate_skewness(data)
        }
    
    def calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of the signal"""
        if len(data) < 4:
            return 0.0
        
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        
        n = len(data)
        kurtosis = (n * (n + 1) * np.sum(((data - mean) / std) ** 4) - 
                   3 * (n - 1) ** 2) / ((n - 1) * (n - 2) * (n - 3))
        return kurtosis
    
    def calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of the signal"""
        if len(data) < 3:
            return 0.0
        
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        
        n = len(data)
        skewness = (n * np.sum(((data - mean) / std) ** 3)) / ((n - 1) * (n - 2))
        return skewness
    
    def apply_calibration(self, data: np.ndarray, calibration_factor: float) -> np.ndarray:
        """Apply calibration factor to the data"""
        return data * calibration_factor
    
    def remove_dc_offset(self, data: np.ndarray) -> np.ndarray:
        """Remove DC offset from the signal"""
        return data - np.mean(data)
    
    def normalize_signal(self, data: np.ndarray) -> np.ndarray:
        """Normalize signal to range [-1, 1]"""
        if len(data) == 0:
            return data
        
        max_val = np.max(np.abs(data))
        if max_val == 0:
            return data
        
        return data / max_val
    
    def detect_anomalies(self, data: np.ndarray, method: str = 'zscore', 
                        threshold: float = 3.0) -> List[int]:
        """Detect anomalies in the signal using various methods"""
        if len(data) == 0:
            return []
        
        if method == 'zscore':
            return self.detect_anomalies_zscore(data, threshold)
        elif method == 'iqr':
            return self.detect_anomalies_iqr(data, threshold)
        elif method == 'isolation_forest':
            return self.detect_anomalies_isolation_forest(data)
        else:
            return []
    
    def detect_anomalies_zscore(self, data: np.ndarray, threshold: float = 3.0) -> List[int]:
        """Detect anomalies using Z-score method"""
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return []
        
        z_scores = np.abs((data - mean) / std)
        anomalies = np.where(z_scores > threshold)[0]
        
        return anomalies.tolist()
    
    def detect_anomalies_iqr(self, data: np.ndarray, threshold: float = 1.5) -> List[int]:
        """Detect anomalies using Interquartile Range method"""
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        anomalies = np.where((data < lower_bound) | (data > upper_bound))[0]
        
        return anomalies.tolist()
    
    def detect_anomalies_isolation_forest(self, data: np.ndarray) -> List[int]:
        """Detect anomalies using Isolation Forest (simplified implementation)"""
        # Simplified implementation - in practice, you'd use sklearn.ensemble.IsolationForest
        # This is a basic approximation
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return []
        
        # Calculate distance from mean
        distances = np.abs(data - mean)
        
        # Find points that are far from the mean
        threshold = np.percentile(distances, 95)  # Top 5% as anomalies
        anomalies = np.where(distances > threshold)[0]
        
        return anomalies.tolist()
    
    def update_config(self, new_config):
        """Update configuration and reinitialize filters"""
        self.config = new_config
        self.setup_filters() 