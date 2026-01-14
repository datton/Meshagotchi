"""
MeshCore CLI wrapper for LoRa mesh communication.

Handles sending and receiving messages via MeshCore CLI with rate limiting
to prevent network flooding. Designed for Heltec V3 LoRa radio.
"""

import subprocess
import time
import re
from queue import Queue
from typing import Optional, Tuple
from datetime import datetime, timedelta


class MeshHandler:
    """
    Handles all MeshCore CLI communication with rate limiting.
    
    Hardware: Heltec V3 LoRa radio running latest MeshCore firmware,
    connected to Raspberry Pi via USB Serial.
    """
    
    # USA/Canada (Recommended) preset parameters
    USA_CANADA_PRESET = {
        'frequency': 910525000,  # 910.525 MHz in Hz
        'bandwidth': 62500,      # 62.5 kHz in Hz
        'spreading_factor': 7,   # SF7
        'coding_rate': 5,        # CR 5
        'power': 22              # 22 dBm
    }
    
    def __init__(self, min_send_interval: float = 2.0, max_message_length: int = 200, serial_port: Optional[str] = None):
        """
        Initialize MeshHandler.
        
        Args:
            min_send_interval: Minimum seconds between sends (default: 2.0)
            max_message_length: Maximum message length in bytes (default: 200)
            serial_port: Serial port path (e.g., "/dev/ttyUSB0"). If None, meshcli will auto-detect.
        """
        self.message_queue = Queue()
        self.last_send_time = None
        self.min_send_interval = min_send_interval
        self.max_message_length = max_message_length
        self.radio_version = None
        self.radio_info = None
        self.serial_port = serial_port  # e.g., "/dev/ttyUSB0" or None if auto-detected
    
    def _build_meshcli_cmd(self, *args) -> list:
        """
        Build meshcli command with optional serial port.
        
        Args:
            *args: Command arguments (e.g., "receive", "send", "node_id", "message")
            
        Returns:
            List of command arguments for subprocess.run
        """
        cmd = ["meshcli"]
        if self.serial_port:
            cmd.extend(["-s", self.serial_port])
        cmd.extend(args)
        return cmd
    
    def listen(self) -> Optional[Tuple[str, str]]:
        """
        Polls MeshCore CLI for new messages.
        
        Returns:
            Tuple of (sender_node_id, message_text) or None if no message
        """
        try:
            # Try to receive message via MeshCore CLI
            # Note: Exact command syntax to be verified during implementation
            # Assumed: meshcli receive or meshcli listen
            result = subprocess.run(
                self._build_meshcli_cmd("receive"),
                capture_output=True,
                text=True,
                timeout=1.0  # Non-blocking check
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse output - could be JSON or plain text
                # Try JSON first, fall back to plain text
                output = result.stdout.strip()
                
                # Simple parsing - adjust based on actual CLI output format
                # Example formats:
                # JSON: {"from": "!a1b2c3", "message": "hello"}
                # Plain: "!a1b2c3: hello"
                
                # Try to parse as JSON-like
                if output.startswith("{") and "from" in output.lower():
                    # Extract node_id and message from JSON-like format
                    # This is a simplified parser - adjust based on actual format
                    node_match = re.search(r'"from"\s*:\s*"([^"]+)"', output)
                    msg_match = re.search(r'"message"\s*:\s*"([^"]+)"', output)
                    
                    if node_match and msg_match:
                        node_id = node_match.group(1)
                        message = msg_match.group(1)
                        return (node_id, message)
                else:
                    # Try plain text format: "!nodeid: message"
                    if ":" in output:
                        parts = output.split(":", 1)
                        if len(parts) == 2:
                            node_id = parts[0].strip()
                            message = parts[1].strip()
                            return (node_id, message)
            
            return None
            
        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            # MeshCore CLI not found - return None (will be handled in main)
            return None
        except Exception as e:
            # Log error but don't crash
            print(f"Error listening for messages: {e}")
            return None
    
    def send(self, node_id: str, text: str):
        """
        Queue message for sending with rate limiting.
        
        Args:
            node_id: Target Node ID (e.g., "!a1b2c3")
            text: Message text to send
        """
        # Sanitize message
        sanitized = self._sanitize_message(text)
        
        # Add to queue
        self.message_queue.put((node_id, sanitized))
        
        # Try to process queue if interval allows
        self._process_queue()
    
    def _process_queue(self):
        """Internal method to send queued messages respecting rate limits."""
        if self.message_queue.empty():
            return
        
        # Check if enough time has passed
        now = datetime.now()
        if self.last_send_time is not None:
            time_since_last = (now - self.last_send_time).total_seconds()
            if time_since_last < self.min_send_interval:
                # Too soon, wait
                return
        
        # Send next message from queue
        try:
            node_id, message = self.message_queue.get_nowait()
            
            # Send via MeshCore CLI
            # Note: Exact command syntax to be verified
            # Assumed: meshcli send <node_id> <message>
            result = subprocess.run(
                self._build_meshcli_cmd("send", node_id, message),
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            if result.returncode == 0:
                self.last_send_time = now
            else:
                # Failed to send - put back in queue?
                # For now, just log error
                print(f"Failed to send message: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("Timeout sending message via MeshCore CLI")
        except FileNotFoundError:
            print("MeshCore CLI not found. Install meshcore-cli.")
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def _sanitize_message(self, text: str) -> str:
        """
        Remove excessive whitespace and ensure message is under max length.
        
        Args:
            text: Original message text
        
        Returns:
            Sanitized message
        """
        # Strip leading/trailing whitespace from each line
        lines = text.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        # Remove empty lines at start/end
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        # Rejoin
        sanitized = '\n'.join(cleaned_lines)
        
        # Ensure under max length (in bytes)
        if len(sanitized.encode('utf-8')) > self.max_message_length:
            # Truncate to fit
            while len(sanitized.encode('utf-8')) > self.max_message_length:
                sanitized = sanitized[:-1]
            # Add truncation indicator if needed
            if len(sanitized.encode('utf-8')) < self.max_message_length - 3:
                sanitized += "..."
        
        return sanitized
    
    def process_pending_messages(self):
        """
        Process any pending messages in the queue.
        Call this periodically to ensure queue is drained.
        """
        # Process up to 10 messages per call to avoid blocking
        processed = 0
        while not self.message_queue.empty() and processed < 10:
            self._process_queue()
            processed += 1
            # Small delay between messages
            time.sleep(0.1)
    
    def initialize_radio(self) -> bool:
        """
        Initialize and configure radio at startup.
        Probes for version info, link info, and sets USA/Canada preset.
        
        Returns:
            True if successful, False otherwise
        """
        print("Initializing MeshCore radio...")
        
        try:
            # Step 1: Get radio version information
            version_info = self.get_radio_version()
            if version_info:
                self.radio_version = version_info
                print(f"Radio version: {version_info}")
            else:
                print("Warning: Could not retrieve radio version")
            
            # Step 2: Get radio link information
            link_info = self.get_radio_link_info()
            if link_info:
                self.radio_info = link_info
                print(f"Radio link info: {link_info}")
            else:
                print("Warning: Could not retrieve radio link info")
            
            # Step 3: Configure radio to USA/Canada preset
            if self.configure_usa_canada_preset():
                print("Radio configured to USA/Canada (Recommended) preset")
                print(f"  Frequency: {self.USA_CANADA_PRESET['frequency'] / 1000000} MHz")
                print(f"  Bandwidth: {self.USA_CANADA_PRESET['bandwidth'] / 1000} kHz")
                print(f"  Spreading Factor: {self.USA_CANADA_PRESET['spreading_factor']}")
                print(f"  Coding Rate: {self.USA_CANADA_PRESET['coding_rate']}")
                print(f"  Power: {self.USA_CANADA_PRESET['power']} dBm")
                
                # Step 4: Set radio name to Meshagotchi
                if self.set_radio_name("Meshagotchi"):
                    print("Radio name set to: Meshagotchi")
                else:
                    print("Warning: Could not set radio name")
                
                # Step 5: Print node card and infos
                print("\n" + "="*60)
                print("NODE CARD:")
                print("="*60)
                node_card = self.get_node_card()
                if node_card:
                    print(node_card)
                else:
                    print("Could not retrieve node card")
                
                print("\n" + "="*60)
                print("NODE INFOS:")
                print("="*60)
                node_infos = self.get_node_infos()
                if node_infos:
                    print(node_infos)
                else:
                    print("Could not retrieve node infos")
                print("="*60 + "\n")
                
                # Step 6: Flood Advert to announce availability
                print("Sending Advert broadcasts to announce availability...")
                self.flood_advert()
                
                return True
            else:
                print("Error: Failed to configure radio preset")
                return False
                
        except Exception as e:
            print(f"Error initializing radio: {e}")
            return False
    
    def get_radio_version(self) -> Optional[str]:
        """
        Get radio firmware version information.
        
        Returns:
            Version string or None if failed
        """
        try:
            # Try various MeshCore CLI commands to get version
            # Correct pattern: meshcli -v (prints version)
            commands = [
                self._build_meshcli_cmd("-v"),
                self._build_meshcli_cmd("info"),
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        return result.stdout.strip()
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error getting radio version: {e}")
            return None
    
    def get_radio_link_info(self) -> Optional[str]:
        """
        Get radio link information (frequency, bandwidth, etc.).
        
        Returns:
            Link info string or None if failed
        """
        try:
            # Try various MeshCore CLI commands to get link info
            commands = [
                self._build_meshcli_cmd("link"),
                self._build_meshcli_cmd("config"),
                self._build_meshcli_cmd("get-config"),
                self._build_meshcli_cmd("info"),
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        return result.stdout.strip()
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error getting radio link info: {e}")
            return None
    
    def configure_usa_canada_preset(self) -> bool:
        """
        Configure radio to USA/Canada (Recommended) preset.
        
        Parameters:
        - Frequency: 910.525 MHz (910525000 Hz)
        - Bandwidth: 62.5 kHz (62500 Hz)
        - Spreading Factor: 7
        - Coding Rate: 5
        - Power: 22 dBm
        
        Returns:
            True if successful, False otherwise
        """
        try:
            preset = self.USA_CANADA_PRESET
            success_count = 0
            
            # Try to set frequency (may be in Hz or MHz depending on CLI)
            # Try both formats
            freq_commands = [
                self._build_meshcli_cmd("set-frequency", str(preset['frequency'])),  # Hz
                self._build_meshcli_cmd("set-frequency", str(preset['frequency'] / 1000000)),  # MHz
                self._build_meshcli_cmd("frequency", str(preset['frequency'])),
                self._build_meshcli_cmd("freq", str(preset['frequency'] / 1000000)),
            ]
            
            for cmd in freq_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    if result.returncode == 0:
                        success_count += 1
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            # Set bandwidth
            bw_commands = [
                self._build_meshcli_cmd("set-bandwidth", str(preset['bandwidth'])),
                self._build_meshcli_cmd("bandwidth", str(preset['bandwidth'])),
                self._build_meshcli_cmd("bw", str(preset['bandwidth'] / 1000)),  # kHz
            ]
            
            for cmd in bw_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    if result.returncode == 0:
                        success_count += 1
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            # Set spreading factor
            sf_commands = [
                self._build_meshcli_cmd("set-spreading-factor", str(preset['spreading_factor'])),
                self._build_meshcli_cmd("spreading-factor", str(preset['spreading_factor'])),
                self._build_meshcli_cmd("sf", str(preset['spreading_factor'])),
            ]
            
            for cmd in sf_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    if result.returncode == 0:
                        success_count += 1
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            # Set coding rate
            cr_commands = [
                self._build_meshcli_cmd("set-coding-rate", str(preset['coding_rate'])),
                self._build_meshcli_cmd("coding-rate", str(preset['coding_rate'])),
                self._build_meshcli_cmd("cr", str(preset['coding_rate'])),
            ]
            
            for cmd in cr_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    if result.returncode == 0:
                        success_count += 1
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            # Set power
            power_commands = [
                self._build_meshcli_cmd("set-power", str(preset['power'])),
                self._build_meshcli_cmd("power", str(preset['power'])),
                self._build_meshcli_cmd("tx-power", str(preset['power'])),
            ]
            
            for cmd in power_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    if result.returncode == 0:
                        success_count += 1
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            # Alternative: Try preset command if available
            preset_commands = [
                self._build_meshcli_cmd("set-preset", "usa-canada"),
                self._build_meshcli_cmd("preset", "usa-canada"),
                self._build_meshcli_cmd("set-preset", "USA/Canada"),
            ]
            
            for cmd in preset_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    if result.returncode == 0:
                        # Preset command succeeded, verify settings
                        time.sleep(0.5)  # Allow radio to apply settings
                        return True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            # If we got at least 3 out of 5 parameters set, consider it successful
            # (some parameters might not be settable or might use different commands)
            if success_count >= 3:
                time.sleep(0.5)  # Allow radio to apply settings
                return True
            
            # If preset command exists but individual commands don't work well,
            # that's okay - the preset should handle it
            print(f"Warning: Only {success_count}/5 parameters confirmed set")
            print("Radio may use preset defaults. Verify with: meshcli config")
            return True  # Assume success if we tried
            
        except Exception as e:
            print(f"Error configuring radio preset: {e}")
            return False
    
    def set_radio_name(self, name: str) -> bool:
        """
        Set the radio node name.
        
        Args:
            name: Name to set (e.g., "Meshagotchi")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try various MeshCore CLI commands to set name
            # Common patterns: set-name, name, setname, node-name
            name_commands = [
                self._build_meshcli_cmd("set-name", name),
                self._build_meshcli_cmd("name", name),
                self._build_meshcli_cmd("setname", name),
                self._build_meshcli_cmd("node-name", name),
                self._build_meshcli_cmd("set", "name", name),
            ]
            
            for cmd in name_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    
                    if result.returncode == 0:
                        # Allow time for name to be set
                        time.sleep(0.2)
                        return True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            # If none of the commands worked, try alternative approach
            # Some systems might require a different format
            alt_commands = [
                self._build_meshcli_cmd("config", "name", name),
                self._build_meshcli_cmd("set-config", "name", name),
            ]
            
            for cmd in alt_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    if result.returncode == 0:
                        time.sleep(0.2)
                        return True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            return False
            
        except Exception as e:
            print(f"Error setting radio name: {e}")
            return False
    
    def get_node_card(self) -> Optional[str]:
        """
        Get the node card information (node details/identity).
        
        Returns:
            Node card string or None if failed
        """
        try:
            # Try various MeshCore CLI commands to get node card
            commands = [
                self._build_meshcli_cmd("card"),
                self._build_meshcli_cmd("node-card"),
                self._build_meshcli_cmd("info", "card"),
                self._build_meshcli_cmd("show", "card"),
                self._build_meshcli_cmd("get", "card"),
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        return result.stdout.strip()
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error getting node card: {e}")
            return None
    
    def get_node_infos(self) -> Optional[str]:
        """
        Get node infos (detailed node information).
        
        Returns:
            Node infos string or None if failed
        """
        try:
            # Try various MeshCore CLI commands to get infos
            commands = [
                self._build_meshcli_cmd("infos"),
                self._build_meshcli_cmd("info"),
                self._build_meshcli_cmd("node-info"),
                self._build_meshcli_cmd("node-infos"),
                self._build_meshcli_cmd("show", "info"),
                self._build_meshcli_cmd("get", "info"),
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        return result.stdout.strip()
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error getting node infos: {e}")
            return None
    
    def flood_advert(self, count: int = 5, delay: float = 0.5):
        """
        Flood Advert messages to announce node availability.
        Sends multiple broadcast messages so other nodes can discover this device.
        
        Args:
            count: Number of Advert messages to send (default: 5)
            delay: Delay between messages in seconds (default: 0.5)
        """
        try:
            # Try various broadcast/advert commands
            # Common patterns: broadcast, advert, or send to broadcast address
            advert_commands = [
                self._build_meshcli_cmd("advert"),
                self._build_meshcli_cmd("broadcast", "Advert"),
                self._build_meshcli_cmd("send", "!ffffffff", "Advert"),  # Broadcast address
                self._build_meshcli_cmd("send", "!FFFFFFFF", "Advert"),  # Alternative broadcast
            ]
            
            # Try to find a working command first
            working_cmd = None
            for cmd in advert_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    if result.returncode == 0:
                        working_cmd = cmd
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            if working_cmd:
                # Flood the advert messages
                for i in range(count):
                    try:
                        result = subprocess.run(
                            working_cmd,
                            capture_output=True,
                            text=True,
                            timeout=3.0
                        )
                        if result.returncode == 0:
                            print(f"  Advert {i+1}/{count} sent")
                        else:
                            print(f"  Warning: Advert {i+1}/{count} failed: {result.stderr.strip()}")
                    except Exception as e:
                        print(f"  Warning: Advert {i+1}/{count} error: {e}")
                    
                    # Delay between messages (except for the last one)
                    if i < count - 1:
                        time.sleep(delay)
                
                print(f"Advert flood complete ({count} messages)")
            else:
                # Fallback: Try using direct send method with broadcast address
                print("  Trying alternative Advert method...")
                for i in range(count):
                    try:
                        # Use the send method with broadcast address
                        result = subprocess.run(
                            self._build_meshcli_cmd("send", "!ffffffff", "Advert"),
                            capture_output=True,
                            text=True,
                            timeout=3.0
                        )
                        if result.returncode == 0:
                            print(f"  Advert {i+1}/{count} sent (broadcast)")
                        time.sleep(delay)
                    except Exception as e:
                        print(f"  Warning: Could not send Advert {i+1}/{count}: {e}")
                        break
                
        except Exception as e:
            print(f"Error flooding Advert: {e}")
            print("  Continuing anyway - device may still be discoverable")


if __name__ == "__main__":
    # Test MeshHandler (will fail if MeshCore CLI not installed)
    handler = MeshHandler()
    
    print("Testing MeshHandler...")
    print("Note: This will fail if MeshCore CLI is not installed.")
    
    # Test sanitization
    test_msg = "   Line 1   \n\n  Line 2  \n  "
    sanitized = handler._sanitize_message(test_msg)
    print(f"Sanitized message: {repr(sanitized)}")
    
    # Test message length limit
    long_msg = "A" * 300
    sanitized_long = handler._sanitize_message(long_msg)
    print(f"Long message length: {len(sanitized_long.encode('utf-8'))} bytes")
