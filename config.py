"""
Configuration management for MeshAgotchi.

Reads configuration from config.ini file and provides access to all settings.
"""

import configparser
import os
from typing import Dict, Optional


class Config:
    """Configuration manager for MeshAgotchi."""
    
    _instance: Optional['Config'] = None
    _config: Optional[configparser.ConfigParser] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """Load configuration from config.ini file."""
        self._config = configparser.ConfigParser()
        
        # Get the directory where this script is located
        config_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(config_dir, 'config.ini')
        
        # Read config file, create with defaults if it doesn't exist
        if os.path.exists(config_path):
            self._config.read(config_path)
        else:
            # Create default config if file doesn't exist
            self._create_default_config(config_path)
            self._config.read(config_path)
    
    def _create_default_config(self, config_path: str):
        """Create default config.ini file if it doesn't exist."""
        default_config = """[ollama]
# Ollama API endpoint configuration
host = 192.168.1.230
port = 11434
model = gemma3:1b
timeout = 30

[radio]
# Radio name displayed on the mesh network
name = MeshAgotchi

# Radio frequency and modulation settings
# Frequency in Hz (910.525 MHz = 910525000 Hz)
frequency = 910525000

# Bandwidth in Hz (62.5 kHz = 62500 Hz)
bandwidth = 62500

# Spreading Factor (SF7 = 7)
spreading_factor = 7

# Coding Rate (CR 5 = 5)
coding_rate = 5

# Transmit Power in dBm
power = 22
"""
        with open(config_path, 'w') as f:
            f.write(default_config)
        print(f"Created default config.ini at {config_path}")
    
    def get_ollama_config(self) -> Dict[str, any]:
        """Get Ollama configuration."""
        section = 'ollama'
        return {
            'host': self._config.get(section, 'host', fallback='192.168.1.230'),
            'port': self._config.getint(section, 'port', fallback=11434),
            'model': self._config.get(section, 'model', fallback='gemma3:1b'),
            'timeout': self._config.getint(section, 'timeout', fallback=30)
        }
    
    def get_ollama_url(self) -> str:
        """Get full Ollama API URL."""
        config = self.get_ollama_config()
        return f"http://{config['host']}:{config['port']}/api/chat"
    
    def get_radio_config(self) -> Dict[str, any]:
        """Get radio configuration."""
        section = 'radio'
        return {
            'name': self._config.get(section, 'name', fallback='Meshagotchi'),
            'frequency': self._config.getint(section, 'frequency', fallback=910525000),
            'bandwidth': self._config.getint(section, 'bandwidth', fallback=62500),
            'spreading_factor': self._config.getint(section, 'spreading_factor', fallback=7),
            'coding_rate': self._config.getint(section, 'coding_rate', fallback=5),
            'power': self._config.getint(section, 'power', fallback=22)
        }
    
    def get_radio_name(self) -> str:
        """Get radio name."""
        return self.get_radio_config()['name']


# Global config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
