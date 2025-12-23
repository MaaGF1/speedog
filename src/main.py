"""
Speedog - Log-based SpeedHack Controller
"""
import os
import sys
import time
import signal
import argparse
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from config import load_speedog_config, get_speedog_config
from log_monitor import LogMonitor
from speed_controller import GameSpeedController

class SpeedogService:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._get_default_config_path()
        self.monitor: LogMonitor = None
        self.controller: GameSpeedController = None
        self.running = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _get_default_config_path(self) -> str:
        return os.path.join(current_dir, 'speedog.conf')
    
    def _signal_handler(self, signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        self.shutdown()
    
    def initialize(self) -> bool:
        print("Initializing Speedog Service...")
        print(f"Config file: {self.config_path}")
        
        if not load_speedog_config(self.config_path):
            print("Failed to load configuration")
            return False
        
        config = get_speedog_config()
        
        # Initialize Controller
        self.controller = GameSpeedController(config.process_name, config.process_arch)
        
        # Initialize Monitor
        self.monitor = LogMonitor(config, self.controller)
        
        print("Service initialized successfully")
        return True
    
    def start(self) -> bool:
        if not self.monitor:
            return False
        
        print("Starting service...")
        
        # Try initial connection
        self.controller.connect()
        
        if not self.monitor.start_monitoring():
            print("Failed to start log monitoring")
            return False
        
        self.running = True
        print(f"Speedog started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    
    def shutdown(self):
        if not self.running:
            return
        
        print("Shutting down...")
        if self.monitor:
            self.monitor.stop_monitoring()
        
        if self.controller:
            print("Resetting game speed...")
            self.controller.reset()
        
        self.running = False
        print("Service stopped")
    
    def run(self):
        if not self.start():
            return False
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
        return True

def print_logo():
    logo = r"""
              .=====================.
             /|                     |\
            | |  Dandelion Service  | |
            | |                     | |
            |  \___________________/  |
             \_______________________/
                     \      /
                      \    /
                 .-----`--'-----.
                / .------------. \
               / /    .----.    \ \
              | |    /  ()  \    | |
              | |   |   __   |   | |
               \ \   \      /   / /
                \ '------------' /
                 \              /
                 /`.__________.'\
                /   /        \   \
               ^   ^          ^   ^
    """
    print(logo)

def main():
    parser = argparse.ArgumentParser(description='Speedog Service')
    parser.add_argument('--config', '-c', type=str, help='Path to configuration file')
    args = parser.parse_args()
    
    print_logo()
    
    service = SpeedogService(args.config)
    if not service.initialize():
        sys.exit(1)
        
    success = service.run()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()