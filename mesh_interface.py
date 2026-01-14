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
        self.friends = set()  # Track discovered nodes as friends
    
    def _build_meshcli_cmd(self, *args, json_output: bool = False) -> list:
        """
        Build meshcli command with optional serial port.
        
        Args:
            *args: Command arguments (e.g., "receive", "send", "node_id", "message")
            json_output: If True, add -j flag for JSON output
            
        Returns:
            List of command arguments for subprocess.run
        """
        cmd = ["meshcli"]
        if self.serial_port:
            cmd.extend(["-s", self.serial_port])
        if json_output:
            cmd.append("-j")
        cmd.extend(args)
        return cmd
    
    def listen(self) -> Optional[Tuple[str, str]]:
        """
        Polls MeshCore CLI for new messages using recv command.
        MeshCore format: name(hop): message
        
        Returns:
            Tuple of (sender_node_id, message_text) or None if no message
        """
        try:
            # Use recv command to get next message
            result = subprocess.run(
                self._build_meshcli_cmd("recv"),
                capture_output=True,
                text=True,
                timeout=1.0  # Non-blocking check
            )
            
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                
                # MeshCore CLI format: name(hop): message
                # Example: "Meshagotchi(0): /help" or "t114_fdl(D): Hello"
                # Also supports JSON format with -j flag
                
                node_id = None
                message = None
                
                # Try JSON format first (if -j was used or output is JSON)
                if output.startswith("{") and "from" in output.lower():
                    node_match = re.search(r'"from"\s*:\s*"([^"]+)"', output)
                    msg_match = re.search(r'"message"\s*:\s*"([^"]+)"', output)
                    
                    if node_match and msg_match:
                        node_id = node_match.group(1)
                        message = msg_match.group(1)
                else:
                    # Parse MeshCore format: name(hop): message
                    # Match pattern like "name(hop): message" or "name: message"
                    match = re.match(r'^([^(]+)(?:\([^)]+\))?:\s*(.+)$', output)
                    if match:
                        node_id = match.group(1).strip()
                        message = match.group(2).strip()
                    elif ":" in output:
                        # Fallback: simple split on colon
                        parts = output.split(":", 1)
                        if len(parts) == 2:
                            node_id = parts[0].strip()
                            # Remove hop indicator if present: "name(hop)" -> "name"
                            node_id = re.sub(r'\([^)]+\)', '', node_id).strip()
                            message = parts[1].strip()
                
                # Track sender locally (MeshCore auto-adds contacts from adverts)
                if node_id:
                    if node_id not in self.friends:
                        self.friends.add(node_id)
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
            
            # Send via MeshCore CLI using msg command
            # Format: msg <name> <message>
            # Note: node_id might be a name or node ID - meshcli handles both
            result = subprocess.run(
                self._build_meshcli_cmd("msg", node_id, message),
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
        Uses infos command which returns all node information including radio settings.
        
        Returns:
            Link info string (JSON or text) or None if failed
        """
        try:
            # Try with JSON output first for easier parsing
            result = subprocess.run(
                self._build_meshcli_cmd("infos", json_output=True),
                capture_output=True,
                text=True,
                timeout=3.0
            )
            
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                return output
            
            # Fallback to non-JSON output
            result = subprocess.run(
                self._build_meshcli_cmd("infos"),
                capture_output=True,
                text=True,
                timeout=3.0
            )
            
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                return output
            
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
            
        Note: If automatic configuration fails, you may need to manually configure
        the radio using meshcli commands or the MeshCore mobile app.
        
        WARNING: Some MeshCore firmware versions may not support changing radio
        parameters via CLI commands. If this method fails, you may need to:
        1. Configure the radio via the MeshCore mobile app
        2. Use a different firmware version that supports parameter changes
        3. Configure the radio at firmware compile time
        """
        try:
            preset = self.USA_CANADA_PRESET
            freq_mhz = preset['frequency'] / 1000000  # 910.525
            freq_hz = preset['frequency']  # 910525000
            bw_khz = preset['bandwidth'] / 1000  # 62.5
            bw_hz = preset['bandwidth']  # 62500
            
            print("Configuring radio to USA/Canada preset...")
            
            # Try different command patterns for setting radio parameters
            # MeshCore CLI typically uses: set <param> <value> or config <param> <value>
            # Try both MHz/kHz and Hz formats as different firmwares may expect different units
            settings_to_apply = [
                ("radio_freq", [
                    (str(freq_mhz), "MHz"),
                    (str(freq_hz), "Hz"),
                    (str(int(freq_hz)), "Hz (int)"),
                ], "Frequency"),
                ("radio_bw", [
                    (str(bw_khz), "kHz"),
                    (str(bw_hz), "Hz"),
                    (str(int(bw_hz)), "Hz (int)"),
                ], "Bandwidth"),
                ("radio_sf", [
                    (str(preset['spreading_factor']), ""),
                ], "Spreading Factor"),
                ("radio_cr", [
                    (str(preset['coding_rate']), ""),
                ], "Coding Rate"),
                ("tx_power", [
                    (str(preset['power']), ""),
                ], "TX Power (dBm)"),
            ]
            
            applied_settings = []
            
            # First, try the combined radio command format: set radio freq,bw,sf,cr
            # Format: set radio <freq_MHz>,<bw_kHz>,<spreading_factor>,<coding_rate>
            combined_radio_command = f"{freq_mhz},{bw_khz},{preset['spreading_factor']},{preset['coding_rate']}"
            combined_commands = [
                ("set radio", self._build_meshcli_cmd("set", "radio", combined_radio_command)),
                ("set-radio", self._build_meshcli_cmd("set-radio", combined_radio_command)),
                ("radio", self._build_meshcli_cmd("radio", combined_radio_command)),
            ]
            
            combined_success = False
            for cmd_name, cmd in combined_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5.0
                    )
                    # Check for error events
                    output = (result.stdout or "") + (result.stderr or "")
                    if "EventType.ERROR" in output or "command_error" in output:
                        continue
                    if result.returncode == 0:
                        if not (result.stderr and ("error" in result.stderr.lower() or "unknown" in result.stderr.lower())):
                            print(f"  ✓ Applied radio settings using '{cmd_name}' command: {combined_radio_command}")
                            combined_success = True
                            time.sleep(1.5)  # Wait for settings to apply
                            break
                except:
                    continue
            
            # If combined command worked, verify it applied correctly
            if combined_success:
                time.sleep(1.0)
                current_info = self.get_radio_link_info()
                if current_info:
                    import json
                    try:
                        config = json.loads(current_info)
                        freq_ok = abs(config.get('radio_freq', 0) - freq_mhz) < 0.1
                        bw_ok = abs(config.get('radio_bw', 0) - bw_khz) < 1.0
                        sf_ok = config.get('radio_sf', 0) == preset['spreading_factor']
                        if freq_ok and bw_ok and sf_ok:
                            print("  Radio settings verified successfully!")
                            return True
                    except:
                        pass
            
            # Try preset/region commands if combined command didn't work
            preset_commands = [
                ("preset", self._build_meshcli_cmd("preset", "usa")),
                ("preset", self._build_meshcli_cmd("preset", "usa-canada")),
                ("preset", self._build_meshcli_cmd("preset", "US")),
                ("region", self._build_meshcli_cmd("region", "usa")),
                ("region", self._build_meshcli_cmd("region", "US")),
                ("set-preset", self._build_meshcli_cmd("set-preset", "usa")),
            ]
            
            preset_success = False
            for preset_name, preset_cmd in preset_commands:
                try:
                    result = subprocess.run(
                        preset_cmd,
                        capture_output=True,
                        text=True,
                        timeout=5.0
                    )
                    if result.returncode == 0:
                        # Check for error events
                        output = (result.stdout or "") + (result.stderr or "")
                        if "EventType.ERROR" in output or "command_error" in output:
                            continue
                        if not (result.stderr and ("error" in result.stderr.lower() or "unknown" in result.stderr.lower())):
                            print(f"  ✓ Applied preset using '{preset_name}' command")
                            preset_success = True
                            time.sleep(1.0)  # Wait for preset to apply
                            break
                except:
                    continue
            
            # If preset worked, verify it applied correctly
            if preset_success:
                time.sleep(1.0)
                current_info = self.get_radio_link_info()
                if current_info:
                    import json
                    try:
                        config = json.loads(current_info)
                        freq_ok = abs(config.get('radio_freq', 0) - freq_mhz) < 0.1
                        bw_ok = abs(config.get('radio_bw', 0) - bw_khz) < 1.0
                        sf_ok = config.get('radio_sf', 0) == preset['spreading_factor']
                        if freq_ok and bw_ok and sf_ok:
                            print("  Preset applied successfully!")
                            return True
                    except:
                        pass
            
            # If preset didn't work or didn't apply correctly, try individual settings
            # Track if we're getting error_code 6 (command not supported)
            commands_not_supported = False
            
            for param_name, value_options, param_desc in settings_to_apply:
                success = False
                last_error = None
                last_cmd_name = None
                last_value_used = None
                
                # Try each value format (MHz, Hz, etc.)
                for param_value, value_unit in value_options:
                    if success:
                        break
                    
                    # Try multiple command patterns
                    commands_to_try = [
                        ("set", self._build_meshcli_cmd("set", param_name, param_value)),
                        ("config", self._build_meshcli_cmd("config", param_name, param_value)),
                        ("set-param", self._build_meshcli_cmd("set-" + param_name, param_value)),
                        ("direct", self._build_meshcli_cmd(param_name, param_value)),
                    ]
                    
                    for cmd_name, cmd in commands_to_try:
                        try:
                            result = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                timeout=5.0
                            )
                            
                            # Debug: Check actual command output to see if it's working
                            stdout_text = result.stdout.strip() if result.stdout else ""
                            stderr_text = result.stderr.strip() if result.stderr else ""
                            
                            # Check for error events in output (meshcli may output error events)
                            # Error format: "Error : Event(type=<EventType.ERROR: 'command_error'>, payload={'error_code': 6}, ...)"
                            if "EventType.ERROR" in stdout_text or "EventType.ERROR" in stderr_text:
                                # Extract error code if present
                                error_match = re.search(r"error_code['\"]?\s*:\s*(\d+)", stdout_text + stderr_text)
                                if error_match:
                                    error_code = error_match.group(1)
                                    last_error = f"Command rejected by radio (error_code: {error_code})"
                                    # If error_code 6, commands are not supported
                                    if error_code == "6":
                                        commands_not_supported = True
                                else:
                                    last_error = "Command rejected by radio (error event)"
                                last_cmd_name = cmd_name
                                last_value_used = f"{param_value} {value_unit}".strip()
                                continue
                            
                            # Check if command succeeded
                            if result.returncode == 0:
                                # Check for error messages in stderr
                                if result.stderr and ("error" in result.stderr.lower() or "unknown" in result.stderr.lower() or "command_error" in result.stderr.lower()):
                                    last_error = result.stderr.strip()
                                    last_cmd_name = cmd_name
                                    last_value_used = f"{param_value} {value_unit}".strip()
                                    continue
                                
                                # Check if stdout indicates success or failure
                                # Some CLIs return success but indicate the command wasn't recognized
                                if stdout_text and ("unknown" in stdout_text.lower() or "invalid" in stdout_text.lower() or "not found" in stdout_text.lower() or "command_error" in stdout_text.lower()):
                                    last_error = stdout_text
                                    last_cmd_name = cmd_name
                                    last_value_used = f"{param_value} {value_unit}".strip()
                                    continue
                                
                                # Success! But we'll verify it actually worked after all settings are applied
                                # However, we've seen that exit code 0 doesn't mean the value actually changed
                                # So we mark it as "attempted" but will verify later
                                value_display = f"{param_value} {value_unit}".strip()
                                print(f"  ✓ Command accepted for {param_desc} = {value_display} (will verify)")
                                success = True
                                applied_settings.append((param_name, param_desc))
                                # Save immediately after setting (some radios require this)
                                try:
                                    save_result = subprocess.run(
                                        self._build_meshcli_cmd("save"),
                                        capture_output=True,
                                        text=True,
                                        timeout=2.0
                                    )
                                except:
                                    pass
                                time.sleep(0.5)  # Small delay between settings
                                break
                            else:
                                last_error = result.stderr.strip() if result.stderr else f"Exit code: {result.returncode}"
                                last_cmd_name = cmd_name
                                last_value_used = f"{param_value} {value_unit}".strip()
                        except subprocess.TimeoutExpired:
                            last_error = "Command timed out"
                            last_cmd_name = cmd_name
                            last_value_used = f"{param_value} {value_unit}".strip()
                            continue
                        except FileNotFoundError:
                            last_error = "meshcli command not found"
                            last_cmd_name = cmd_name
                            last_value_used = f"{param_value} {value_unit}".strip()
                            continue
                        except Exception as e:
                            last_error = str(e)
                            last_cmd_name = cmd_name
                            last_value_used = f"{param_value} {value_unit}".strip()
                            continue
                
                if not success:
                    print(f"  ✗ Could not set {param_desc}")
                    if last_error:
                        print(f"    Last attempt: '{last_cmd_name}' with value '{last_value_used}'")
                        print(f"    Error: {last_error}")
            
            # If we detected that commands are not supported, skip the rest and show message
            if commands_not_supported:
                print()
                print("  ⚠ Radio firmware does not support runtime parameter changes (error_code: 6)")
                print("  Skipping remaining configuration attempts.")
                print("  Please configure radio via MeshCore mobile app or firmware settings.")
                print()
                # Still try to verify current settings
                time.sleep(1.0)
            else:
                # Try to save/commit configuration (some radios require this)
                # Also try writing config after each setting
                save_commands = [
                    self._build_meshcli_cmd("save"),
                    self._build_meshcli_cmd("commit"),
                    self._build_meshcli_cmd("write"),
                    self._build_meshcli_cmd("save-config"),
                    self._build_meshcli_cmd("write-config"),
                ]
                
                for cmd in save_commands:
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=3.0
                        )
                        if result.returncode == 0:
                            if not (result.stderr and ("error" in result.stderr.lower() or "unknown" in result.stderr.lower())):
                                print("  Configuration saved")
                                break
                    except:
                        continue
                
                # Wait for settings to apply and radio to process changes
                time.sleep(2.0)  # Increased wait time
            
            # Verify settings were actually applied by reading config back
            print("Verifying radio configuration...")
            current_info = self.get_radio_link_info()
            
            if current_info:
                import json
                try:
                    # Try to parse as JSON first
                    config = json.loads(current_info)
                    verified = []
                    issues = []
                    
                    # Check frequency (allow small tolerance)
                    current_freq = config.get('radio_freq', 0)
                    if abs(current_freq - freq_mhz) < 0.1:
                        verified.append(f"Frequency: {current_freq} MHz ✓")
                    else:
                        issues.append(f"Frequency: {current_freq} MHz (expected {freq_mhz} MHz)")
                    
                    # Check bandwidth (allow small tolerance)
                    current_bw = config.get('radio_bw', 0)
                    if abs(current_bw - bw_khz) < 1.0:
                        verified.append(f"Bandwidth: {current_bw} kHz ✓")
                    else:
                        issues.append(f"Bandwidth: {current_bw} kHz (expected {bw_khz} kHz)")
                    
                    # Check spreading factor
                    current_sf = config.get('radio_sf', 0)
                    if current_sf == preset['spreading_factor']:
                        verified.append(f"Spreading Factor: {current_sf} ✓")
                    else:
                        issues.append(f"Spreading Factor: {current_sf} (expected {preset['spreading_factor']})")
                    
                    # Check coding rate
                    current_cr = config.get('radio_cr', 0)
                    if current_cr == preset['coding_rate']:
                        verified.append(f"Coding Rate: {current_cr} ✓")
                    else:
                        issues.append(f"Coding Rate: {current_cr} (expected {preset['coding_rate']})")
                    
                    # Check power
                    current_power = config.get('tx_power', 0)
                    if current_power == preset['power']:
                        verified.append(f"TX Power: {current_power} dBm ✓")
                    else:
                        issues.append(f"TX Power: {current_power} dBm (expected {preset['power']} dBm)")
                    
                    if verified:
                        print("  Verified settings:")
                        for v in verified:
                            print(f"    {v}")
                    
                    if issues:
                        print("  Configuration issues:")
                        for issue in issues:
                            print(f"    ⚠ {issue}")
                        print("  Radio may not be discoverable by other nodes on different frequencies.")
                        print()
                        print("  ⚠ WARNING: Radio parameter configuration via CLI is not supported by this firmware.")
                        print("  The 'set' command is being rejected by the radio (error_code: 6).")
                        print()
                        print("  SOLUTION: Configure the radio using one of these methods:")
                        print("  1. Use the MeshCore mobile app to set radio parameters")
                        print("  2. Flash firmware compiled with USA/Canada preset settings")
                        print("  3. Check meshcore-cli documentation for alternative configuration methods")
                        print()
                        print("  Current radio settings:")
                        print(f"    Frequency: {config.get('radio_freq', 'unknown')} MHz")
                        print(f"    Bandwidth: {config.get('radio_bw', 'unknown')} kHz")
                        print(f"    Spreading Factor: {config.get('radio_sf', 'unknown')}")
                        print()
                        print("  MeshAgotchi will continue to run, but may not be discoverable by")
                        print("  other nodes if they are using different radio settings.")
                        return len(verified) >= 3  # At least 3 settings correct
                    
                    print("  All settings verified successfully!")
                    return True
                except json.JSONDecodeError:
                    # If not JSON, try to extract values from text output
                    print("  Warning: Config not in JSON format, attempting text parsing...")
                    # Try to extract key values from text
                    freq_match = re.search(r'"radio_freq":\s*([\d.]+)', current_info)
                    bw_match = re.search(r'"radio_bw":\s*([\d.]+)', current_info)
                    sf_match = re.search(r'"radio_sf":\s*(\d+)', current_info)
                    cr_match = re.search(r'"radio_cr":\s*(\d+)', current_info)
                    power_match = re.search(r'"tx_power":\s*(\d+)', current_info)
                    
                    config = {}
                    if freq_match:
                        config['radio_freq'] = float(freq_match.group(1))
                    if bw_match:
                        config['radio_bw'] = float(bw_match.group(1))
                    if sf_match:
                        config['radio_sf'] = int(sf_match.group(1))
                    if cr_match:
                        config['radio_cr'] = int(cr_match.group(1))
                    if power_match:
                        config['tx_power'] = int(power_match.group(1))
                    
                    if not config:
                        print("  Could not extract config values from output")
                        return len(applied_settings) > 0
            
            # If we applied at least some settings, consider it partially successful
            if applied_settings:
                print(f"  Applied {len(applied_settings)}/{len(settings_to_apply)} settings")
                return True
            
            print("  Error: Could not apply any radio settings")
            return False
            
        except Exception as e:
            print(f"Error configuring radio preset: {e}")
            import traceback
            traceback.print_exc()
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
            # Also try: set name <name> (similar to set radio format)
            name_commands = [
                ("set name", self._build_meshcli_cmd("set", "name", name)),
                ("set-name", self._build_meshcli_cmd("set-name", name)),
                ("name", self._build_meshcli_cmd("name", name)),
                ("setname", self._build_meshcli_cmd("setname", name)),
                ("node-name", self._build_meshcli_cmd("node-name", name)),
            ]
            
            for cmd_name, cmd in name_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5.0
                    )
                    
                    stdout_text = result.stdout.strip() if result.stdout else ""
                    stderr_text = result.stderr.strip() if result.stderr else ""
                    
                    # Check for error events (like error_code 6)
                    if "EventType.ERROR" in stdout_text or "EventType.ERROR" in stderr_text:
                        continue
                    
                    if result.returncode == 0:
                        # Check for error messages
                        if stderr_text and ("error" in stderr_text.lower() or "unknown" in stderr_text.lower() or "command_error" in stderr_text.lower()):
                            continue
                        if stdout_text and ("error" in stdout_text.lower() or "unknown" in stdout_text.lower() or "command_error" in stdout_text.lower()):
                            continue
                        
                        # Allow time for name to be set
                        time.sleep(0.5)
                        
                        # Verify the name was actually set
                        current_info = self.get_radio_link_info()
                        if current_info:
                            import json
                            try:
                                config = json.loads(current_info)
                                current_name = config.get('name', '')
                                if current_name == name:
                                    print(f"  ✓ Radio name set to '{name}' using '{cmd_name}' command")
                                    return True
                                else:
                                    # Name command was accepted but didn't change the name
                                    continue
                            except:
                                # If we can't verify, assume it worked
                                print(f"  ✓ Radio name command accepted using '{cmd_name}' command (could not verify)")
                                return True
                        else:
                            # If we can't verify, assume it worked
                            print(f"  ✓ Radio name command accepted using '{cmd_name}' command (could not verify)")
                            return True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
                except Exception as e:
                    continue
            
            # If none of the commands worked, try alternative approach
            # Some systems might require a different format
            alt_commands = [
                ("config name", self._build_meshcli_cmd("config", "name", name)),
                ("set-config name", self._build_meshcli_cmd("set-config", "name", name)),
            ]
            
            for cmd_name, cmd in alt_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5.0
                    )
                    
                    stdout_text = result.stdout.strip() if result.stdout else ""
                    stderr_text = result.stderr.strip() if result.stderr else ""
                    
                    # Check for error events
                    if "EventType.ERROR" in stdout_text or "EventType.ERROR" in stderr_text:
                        continue
                    
                    if result.returncode == 0:
                        if stderr_text and ("error" in stderr_text.lower() or "unknown" in stderr_text.lower() or "command_error" in stderr_text.lower()):
                            continue
                        if stdout_text and ("error" in stdout_text.lower() or "unknown" in stdout_text.lower() or "command_error" in stdout_text.lower()):
                            continue
                        
                        time.sleep(0.5)
                        
                        # Verify the name was actually set
                        current_info = self.get_radio_link_info()
                        if current_info:
                            import json
                            try:
                                config = json.loads(current_info)
                                current_name = config.get('name', '')
                                if current_name == name:
                                    print(f"  ✓ Radio name set to '{name}' using '{cmd_name}' command")
                                    return True
                            except:
                                pass
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
                except Exception:
                    continue
            
            print(f"  ✗ Could not set radio name to '{name}'")
            print("  All name setting commands were rejected or failed")
            return False
            
        except Exception as e:
            print(f"Error setting radio name: {e}")
            return False
    
    def get_node_card(self) -> Optional[str]:
        """
        Get the node card information (node URI/identity).
        Uses card command which exports the node URI.
        
        Returns:
            Node card string or None if failed
        """
        try:
            # Use card command (correct MeshCore CLI command)
            result = subprocess.run(
                self._build_meshcli_cmd("card"),
                capture_output=True,
                text=True,
                timeout=3.0
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            
            return None
            
            
        except Exception as e:
            print(f"Error getting node card: {e}")
            return None
    
    def get_node_infos(self) -> Optional[str]:
        """
        Get node infos (detailed node information).
        Uses infos command which returns all node information.
        
        Returns:
            Node infos string or None if failed
        """
        try:
            # Use infos command (correct MeshCore CLI command)
            result = subprocess.run(
                self._build_meshcli_cmd("infos"),
                capture_output=True,
                text=True,
                timeout=3.0
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            
            return None
            
        except Exception as e:
            print(f"Error getting node infos: {e}")
            return None
    
    def flood_advert(self, count: int = 5, delay: float = 0.5, zero_hop: bool = True):
        """
        Flood Advert messages to announce node availability.
        Uses floodadv command for efficient flooding, or advert for single sends.
        
        Args:
            count: Number of Advert messages to send (default: 5)
            delay: Delay between messages in seconds (default: 0.5) - only used if floodadv not available
            zero_hop: If True, set scope for zero-hop flooding (default: True)
        """
        try:
            # First try floodadv command (most efficient)
            try:
                result = subprocess.run(
                    self._build_meshcli_cmd("floodadv"),
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                if result.returncode == 0:
                    print(f"  Flood advert sent (using floodadv command)")
                    return
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # If floodadv doesn't work, use advert command in a loop
            # For zero-hop, we might need to set scope first
            if zero_hop:
                # Try to set scope for zero-hop (if supported)
                # Scope might control flooding behavior
                try:
                    subprocess.run(
                        self._build_meshcli_cmd("scope", ""),  # Empty scope might mean local/zero-hop
                        capture_output=True,
                        text=True,
                        timeout=2.0
                    )
                except:
                    pass  # Scope setting is optional
            
            # Send multiple adverts
            success_count = 0
            for i in range(count):
                try:
                    result = subprocess.run(
                        self._build_meshcli_cmd("advert"),
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    if result.returncode == 0:
                        success_count += 1
                        print(f"  Advert {i+1}/{count} sent")
                    else:
                        if result.stderr:
                            print(f"  Warning: Advert {i+1}/{count} failed: {result.stderr.strip()}")
                except Exception as e:
                    print(f"  Warning: Advert {i+1}/{count} error: {e}")
                
                # Delay between messages (except for the last one)
                if i < count - 1:
                    time.sleep(delay)
            
            if success_count > 0:
                print(f"Advert flood complete ({success_count}/{count} messages sent)")
            else:
                print("  Warning: No adverts were sent successfully")
                
        except Exception as e:
            print(f"Error flooding Advert: {e}")
            print("  Continuing anyway - device may still be discoverable")
    
    def add_friend(self, node_id: str) -> bool:
        """
        Track a node locally. MeshCore auto-adds contacts when adverts are received,
        so we mainly track them locally for reference.
        
        Args:
            node_id: Node ID or name to track (e.g., "!a1b2c3" or "Meshagotchi")
            
        Returns:
            True (always succeeds for local tracking)
        """
        # Skip if already tracked
        if node_id in self.friends:
            return True
        
        # Just track locally - MeshCore auto-adds contacts from adverts
        self.friends.add(node_id)
        
        # Only print if not in silent mode
        if not hasattr(self, '_silent_friend_add') or not self._silent_friend_add:
            print(f"  Tracking {node_id} (MeshCore will auto-add from adverts)")
        
        return True
    
    def get_friends_list(self) -> list:
        """
        Get list of current friends.
        
        Returns:
            List of node IDs that are friends
        """
        return list(self.friends)
    
    def discover_and_add_nodes(self):
        """
        Discover new nodes using node_discover command.
        MeshCore auto-adds contacts from adverts, so we mainly track them locally.
        Also use contacts command to sync with MeshCore's contact list.
        """
        try:
            # First, use node_discover to discover nodes
            # Format: node_discover <filter> where filter can be type (1=client, 2=repeater, etc.)
            # Empty filter discovers all nodes
            discover_commands = [
                self._build_meshcli_cmd("node_discover"),  # Discover all nodes
                self._build_meshcli_cmd("node_discover", "1"),  # Discover clients only
            ]
            
            nodes_discovered = 0
            
            for cmd in discover_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=10.0  # Discovery can take time
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        output = result.stdout.strip()
                        # Parse discovered nodes from output
                        # Format varies - could be names, node IDs, or structured data
                        # Extract any node identifiers
                        node_names = re.findall(r'\b[A-Za-z0-9_]+', output)
                        node_ids = re.findall(r'![\da-fA-F]+', output)
                        
                        all_nodes = set(node_names + node_ids)
                        nodes_discovered = len(all_nodes)
                        
                        # Track discovered nodes locally
                        self._silent_friend_add = True
                        for node in all_nodes:
                            if node and node not in self.friends:
                                self.add_friend(node)
                        self._silent_friend_add = False
                        
                        if nodes_discovered > 0:
                            break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            # Also sync with MeshCore's contact list
            # This ensures we're tracking nodes that MeshCore already knows about
            try:
                result = subprocess.run(
                    self._build_meshcli_cmd("contacts"),
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    output = result.stdout.strip()
                    # Parse contact list - format varies
                    # Extract contact names/IDs
                    contact_names = re.findall(r'\b[A-Za-z0-9_]+', output)
                    contact_ids = re.findall(r'![\da-fA-F]+', output)
                    
                    all_contacts = set(contact_names + contact_ids)
                    
                    # Track all contacts locally
                    self._silent_friend_add = True
                    for contact in all_contacts:
                        if contact and contact not in self.friends:
                            self.add_friend(contact)
                    self._silent_friend_add = False
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
                    
        except Exception as e:
            # Silently fail - discovery is optional
            pass


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
