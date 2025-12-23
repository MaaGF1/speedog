"""
Speedog Configuration Management
"""
import os
from typing import Dict, Optional

class SpeedNode:
    """Represents a configuration rule for a specific log node"""
    def __init__(self, name: str, node_name: str, speed: float):
        self.name = name
        self.node_name = node_name
        self.speed = speed
    
    def __str__(self):
        return f"SpeedNode({self.name}: {self.node_name} -> {self.speed}x)"

class SpeedogConfig:
    """Configuration manager for Speedog"""
    
    def __init__(self):
        # Game Settings
        self.process_name = "GrilsFrontLine.exe"
        self.process_arch = "x64"
        
        # Monitoring Settings
        self.log_file_path = None
        self.monitor_interval = 1.0
        
        # Node Rules: Map node_name (str) -> SpeedNode
        self.speed_rules: Dict[str, SpeedNode] = {}
        
        # Regex patterns for log parsing
        self.log_patterns = {
            'node_start': r'[pipeline_data\.name=(.*?)]\s*\|\s*enter',
            'node_complete': r'[pipeline_data\.name=(.*?)]\s*\|\s*complete',
        }
        
    def load_config(self, config_path: str) -> bool:
        if not os.path.exists(config_path):
            print(f"Config file not found: {config_path}")
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                current_section = None
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith(';'):
                        continue
                        
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1].lower()
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if current_section == 'game':
                            self._parse_game_config(key, value)
                        elif current_section == 'monitoring':
                            self._parse_monitoring_config(key, value)
                        elif current_section == 'nodes':
                            self._parse_node_config(key, value, line_num)
            
            print(f"Configuration loaded.")
            print(f"Target Process: {self.process_name} ({self.process_arch})")
            print(f"Loaded {len(self.speed_rules)} speed rules.")
            return True
            
        except Exception as e:
            print(f"Failed to load config: {e}")
            return False

    def _parse_game_config(self, key: str, value: str):
        if key == 'Process_Name':
            self.process_name = value
        elif key == 'Process_Arch':
            self.process_arch = value

    def _parse_monitoring_config(self, key: str, value: str):
        if key == 'Log_File_Path':
            self.log_file_path = value
        elif key == 'Monitor_Interval':
            try:
                self.monitor_interval = float(value)
                if self.monitor_interval <= 0:
                    self.monitor_interval = 1.0
            except ValueError:
                pass

    def _parse_node_config(self, key: str, value: str, line_num: int):
        # Format: RuleName={NodeName, Speed}
        try:
            if value.startswith('{') and value.endswith('}'):
                value = value[1:-1]
            
            parts = [part.strip() for part in value.split(',')]
            if len(parts) < 2:
                print(f"Warning: Invalid node config at line {line_num}")
                return
                
            node_name = parts[0]
            try:
                speed = float(parts[1])
            except ValueError:
                print(f"Warning: Invalid speed value at line {line_num}")
                return
                
            rule = SpeedNode(key, node_name, speed)
            # We map by node_name for O(1) lookup during monitoring
            self.speed_rules[node_name] = rule
            
        except Exception as e:
            print(f"Warning: Failed to parse node rule at line {line_num}: {e}")

    def get_speed_rule(self, node_name: str) -> Optional[SpeedNode]:
        return self.speed_rules.get(node_name)

# Global singleton
speedog_config = SpeedogConfig()

def load_speedog_config(config_path: str) -> bool:
    return speedog_config.load_config(config_path)

def get_speedog_config() -> SpeedogConfig:
    return speedog_config