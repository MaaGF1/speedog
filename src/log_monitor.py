"""
Log monitoring system for Speedog
"""
import re
import threading
import os
import sys
import time
from typing import List, Optional, TextIO

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from config import SpeedogConfig
from speed_controller import GameSpeedController

class LogMonitor:
    """Log monitor that triggers speed changes"""
    
    def __init__(self, config: SpeedogConfig, controller: GameSpeedController):
        self.config = config
        self.controller = controller
        
        # Monitoring state
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Log patterns
        self.node_patterns = {
            'start': re.compile(r'[pipeline_data\.name=(.*?)]\s*\|\s*enter', re.IGNORECASE),
            'complete': re.compile(r'[pipeline_data\.name=(.*?)]\s*\|\s*complete', re.IGNORECASE),
            'general': re.compile(r'[(?:node_name|pipeline_data\.name)=(.*?)](?!.*(?:list=|result\.name=))', re.IGNORECASE)
        }
        
        self.log_file: Optional[TextIO] = None
    
    def start_monitoring(self) -> bool:
        if self.is_running:
            return False
        
        if not self._prepare_log_source():
            return False
        
        self.stop_event.clear()
        self.is_running = True
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="SpeedogLogMonitor"
        )
        self.monitor_thread.start()
        return True
    
    def stop_monitoring(self) -> bool:
        if not self.is_running:
            return False
        
        self.stop_event.set()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        self._cleanup_log_source()
        self.is_running = False
        return True
    
    def _prepare_log_source(self) -> bool:
        if self.config.log_file_path:
            try:
                if os.path.exists(self.config.log_file_path):
                    self.log_file = open(self.config.log_file_path, 'r', encoding='utf-8', errors='ignore')
                    self.log_file.seek(0, os.SEEK_END)
                    print(f"Monitoring log file: {self.config.log_file_path}")
                    return True
                else:
                    print(f"Log file does not exist: {self.config.log_file_path}")
                    return False
            except Exception as e:
                print(f"Failed to open log file: {e}")
                return False
        return False
    
    def _cleanup_log_source(self):
        if self.log_file:
            try:
                self.log_file.close()
            except:
                pass
            self.log_file = None
    
    def _monitor_loop(self):
        print("Starting Speedog monitor loop...")
        while not self.stop_event.wait(self.config.monitor_interval):
            try:
                new_lines = self._read_new_log_lines()
                if new_lines:
                    for line in new_lines:
                        self._process_log_line(line.strip())
            except Exception as e:
                print(f"Monitor loop error: {e}")
    
    def _read_new_log_lines(self) -> List[str]:
        if not self.log_file:
            return []
        
        lines = []
        try:
            current_pos = self.log_file.tell()
            current_size = os.fstat(self.log_file.fileno()).st_size
            
            if current_size < current_pos:
                print("[WARNING] Log file truncated, resetting pointer.")
                self.log_file.seek(0)
            
            content = self.log_file.read()
            if content:
                # Handle incomplete lines at the end
                if not content.endswith('\n'):
                    last_newline = content.rfind('\n')
                    if last_newline != -1:
                        self.log_file.seek(self.log_file.tell() - (len(content) - (last_newline + 1)))
                        content = content[:last_newline + 1]
                    else:
                        self.log_file.seek(self.log_file.tell() - len(content))
                        return []
                lines = [line for line in content.split('\n') if line.strip()]
        except Exception as e:
            print(f"Error reading log: {e}")
            self._cleanup_log_source()
            self._prepare_log_source()
        
        return lines
    
    def _process_log_line(self, line: str):
        if not line:
            return
        if 'pipeline_data.name' not in line and 'node_name' not in line:
            return

        node_name = None
        # Try matching start, then complete, then general
        for pattern in [self.node_patterns['start'], self.node_patterns['complete'], self.node_patterns['general']]:
            match = pattern.search(line)
            if match:
                node_name = match.group(1).strip()
                break
        
        if not node_name:
            return
            
        # Check if this node has a speed rule
        rule = self.config.get_speed_rule(node_name)
        if rule:
            print(f"[DETECT] Node '{node_name}' matched rule '{rule.name}'. Target Speed: {rule.speed}x")
            self.controller.apply_speed(rule.speed)