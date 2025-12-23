"""
Game Speed Controller Wrapper for xspeedhack
"""
import psutil
import logging
import xspeedhack as xsh
from typing import Optional

class GameSpeedController:
    def __init__(self, process_name: str, arch: str = "x64"):
        self.process_name = process_name
        self.arch = arch
        self.client: Optional[xsh.Client] = None
        self.current_speed = 1.0
        self.is_connected = False
        
    def connect(self) -> bool:
        """Attempt to find and connect to the game process"""
        try:
            # Method 1: Direct name connection
            self.client = xsh.Client(self.process_name, arch=self.arch)
            self.is_connected = True
            print(f"[SpeedHack] Connected to process: {self.process_name}")
            return True
            
        except Exception:
            # Method 2: PID lookup
            try:
                pid = self._find_process_pid()
                if pid:
                    self.client = xsh.Client(process_id=pid, arch=self.arch)
                    self.is_connected = True
                    print(f"[SpeedHack] Connected to PID: {pid}")
                    return True
            except Exception as e2:
                print(f"[SpeedHack] Connection failed: {e2}")
                
        self.is_connected = False
        return False
    
    def _find_process_pid(self) -> Optional[int]:
        """Helper to find PID by name"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == self.process_name.lower():
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def apply_speed(self, speed: float) -> bool:
        """Apply speed setting, handling reconnection if needed"""
        if speed == self.current_speed and self.is_connected:
            return True

        if not self.is_connected:
            if not self.connect():
                return False
        
        try:
            if self.client:
                self.client.set_speed(speed)
                self.current_speed = speed
                print(f"[SpeedHack] Speed set to: {speed}x")
                return True
        except Exception as e:
            print(f"[SpeedHack] Error setting speed: {e}")
            self.is_connected = False
            # Try once to reconnect and set
            if self.connect():
                try:
                    self.client.set_speed(speed)
                    self.current_speed = speed
                    print(f"[SpeedHack] Reconnected and speed set to: {speed}x")
                    return True
                except:
                    pass
            return False

    def reset(self):
        """Reset to 1.0x"""
        self.apply_speed(1.0)