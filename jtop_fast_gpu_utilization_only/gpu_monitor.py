import os
import time
import threading
import statistics
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FastGPUMonitor:
    """
    A class to monitor GPU utilization by reading from /sys/class/devfreq/17000000.gpu/device/load
    at high frequency (up to 100 Hz or more) in a separate thread.

    Attributes:
        interval (float): Time interval (in seconds) between GPU utilization readings.
        utilization_data (list): List of tuples (timestamp, utilization value 0-1000).
        stop_event (threading.Event): Event to signal the thread to stop.
        gpu_load_path (str): Path to the GPU load file in sysfs.
    """
    def __init__(self, interval=0.01):
        """
        Initialize the Fast GPU Monitor.

        Args:
            interval (float): Sampling interval in seconds (default: 0.01 for 100 Hz).
                              Minimum practical value is ~0.001 (1 kHz), though system limits may apply.
        """
        if interval <= 0:
            raise ValueError("Interval must be positive")
        self.interval = interval
        self.utilization_data = []  # Stores (timestamp, utilization) tuples
        self.stop_event = threading.Event()
        self.start_time = None
        self.gpu_load_path = "/sys/class/devfreq/17000000.gpu/device/load"
        self.thread = None
        
        # Verify GPU load file exists
        if not os.path.exists(self.gpu_load_path):
            logger.warning(f"GPU load file {self.gpu_load_path} not found. Monitoring will fail.")
        
    def _monitor(self):
        """
        Internal method to continuously collect GPU utilization data in a separate thread.
        Utilization values are in the range 0-1000.
        """
        self.start_time = time.time()
        try:
            while not self.stop_event.is_set():
                with open(self.gpu_load_path, 'r') as f:
                    # Value is 0-1000 as per sysfs specification
                    gpu_util = int(f.read().strip())
                timestamp = time.time() - self.start_time
                self.utilization_data.append((timestamp, gpu_util))
                time.sleep(self.interval)
        except Exception as e:
            logger.error(f"Error in GPU monitoring thread: {e}")
            self.utilization_data.append((timestamp, 0))  # Append 0 on error

    def start(self):
        """
        Start the GPU utilization monitoring in a separate thread.
        
        Raises:
            RuntimeError: If monitoring is already running.
        """
        if self.thread is not None and self.thread.is_alive():
            raise RuntimeError("Monitoring is already running")
        self.utilization_data.clear()
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
        logger.debug(f"Started GPU monitoring at {1/self.interval:.1f} Hz")

    def stop(self):
        """
        Stop the GPU utilization monitoring thread and wait for it to finish.
        
        Raises:
            RuntimeError: If monitoring is not running.
        """
        if self.thread is None or not self.thread.is_alive():
            raise RuntimeError("Monitoring is not running")
        self.stop_event.set()
        self.thread.join()
        logger.debug("Stopped GPU monitoring")

    def get_current_utilization(self):
        """
        Get the current GPU utilization value without affecting the monitoring thread.

        Returns:
            int: Current GPU utilization (0-1000), or 0 if reading fails or file is unavailable.
        """
        try:
            with open(self.gpu_load_path, 'r') as f:
                return int(f.read().strip())
        except Exception as e:
            logger.error(f"Error reading current GPU utilization: {e}")
            return 0

    def get_stats(self):
        """
        Get statistical analysis of collected GPU utilization data.

        Returns:
            tuple: (average utilization, max utilization, std deviation, number of samples)
                   All utilization values are in range 0-1000. Returns (0, 0, 0, 0) if no data.
        """
        if not self.utilization_data:
            return 0, 0, 0, 0
        util_values = [util for _, util in self.utilization_data]
        avg_util = statistics.mean(util_values)
        max_util = max(util_values)
        std_dev = statistics.stdev(util_values) if len(util_values) > 1 else 0
        num_samples = len(util_values)
        return avg_util, max_util, std_dev, num_samples

    def get_data(self):
        """
        Get the raw utilization data collected so far.

        Returns:
            list: List of tuples (timestamp, utilization), where utilization is 0-1000.
        """
        return self.utilization_data.copy()

    def is_running(self):
        """
        Check if the monitoring thread is currently running.

        Returns:
            bool: True if monitoring is active, False otherwise.
        """
        return self.thread is not None and self.thread.is_alive()