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
            serial_port: Serial port path (e.g., "/dev/ttyUSB0"). If None, will auto-detect /dev/ttyUSB0.
        """
        self.message_queue = Queue()
        self.last_send_time = None
        self.min_send_interval = min_send_interval
        self.max_message_length = max_message_length
        self.radio_version = None
        self.radio_info = None
        
        # Auto-detect serial port if not specified
        if serial_port is None:
            import os
            # Check environment variable first
            serial_port = os.environ.get("MESHCLI_SERIAL_PORT")
            
            # If still None, try to auto-detect /dev/ttyUSB0
            if serial_port is None:
                import os.path
                if os.path.exists("/dev/ttyUSB0"):
                    serial_port = "/dev/ttyUSB0"
                    print(f"[DEBUG] Auto-detected serial port: {serial_port}")
                elif os.path.exists("/dev/ttyACM0"):
                    serial_port = "/dev/ttyACM0"
                    print(f"[DEBUG] Auto-detected serial port: {serial_port}")
        
        self.serial_port = serial_port  # e.g., "/dev/ttyUSB0" or None if auto-detected
        if self.serial_port:
            print(f"[DEBUG] Using serial port: {self.serial_port}")
        else:
            print("[DEBUG] Warning: No serial port specified, meshcli may default to BLE")
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
            cmd = self._build_meshcli_cmd("recv")
            print(f"[DEBUG] Listening for messages: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2.0  # Increased timeout to catch messages
            )
            
            stdout_text = result.stdout.strip() if result.stdout else ""
            stderr_text = result.stderr.strip() if result.stderr else ""
            
            print(f"[DEBUG] recv exit code: {result.returncode}")
            if stdout_text:
                print(f"[DEBUG] recv stdout: {stdout_text}")
            if stderr_text:
                print(f"[DEBUG] recv stderr: {stderr_text}")
            
            if result.returncode == 0 and stdout_text:
                output = stdout_text
                
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
                        print(f"[DEBUG] Parsed JSON format: node_id={node_id}, message={message}")
                else:
                    # Parse MeshCore format: name(hop): message
                    # Match pattern like "name(hop): message" or "name: message"
                    match = re.match(r'^([^(]+)(?:\([^)]+\))?:\s*(.+)$', output)
                    if match:
                        node_id = match.group(1).strip()
                        message = match.group(2).strip()
                        print(f"[DEBUG] Parsed regex format: node_id={node_id}, message={message}")
                    elif ":" in output:
                        # Fallback: simple split on colon
                        parts = output.split(":", 1)
                        if len(parts) == 2:
                            node_id = parts[0].strip()
                            # Remove hop indicator if present: "name(hop)" -> "name"
                            node_id = re.sub(r'\([^)]+\)', '', node_id).strip()
                            # Strip any remaining whitespace
                            node_id = node_id.strip()
                            message = parts[1].strip()
                        print(f"[DEBUG] Parsed split format: node_id='{node_id}', message='{message}'")
                
                # Track sender locally (MeshCore auto-adds contacts from adverts)
                if node_id and message:
                    # Strip whitespace from node_id
                    node_id = node_id.strip()
                    
                    # Get the actual node ID from contacts list for this name
                    # We need to use node ID for sending, not the name
                    node_id_actual = self._get_node_id_from_name(node_id)
                    if node_id_actual:
                        print(f"[DEBUG] Mapped name '{node_id}' to node ID '{node_id_actual}'")
                        # Store both name and node ID
                        if node_id not in self.friends:
                            self.friends.add(node_id)
                        # Use node ID for sending, but keep name for display
                        return (node_id_actual, message)
                    else:
                        # If we can't find node ID, still track the name
                        if node_id not in self.friends:
                            print(f"[DEBUG] Adding new friend: '{node_id}' (node ID not found in contacts)")
                            self.friends.add(node_id)
                        print(f"[MESSAGE RECEIVED] From: '{node_id}', Message: '{message}'")
                        return (node_id, message)
                else:
                    print(f"[DEBUG] Could not parse message from output: {output}")
            
            return None
            
        except subprocess.TimeoutExpired:
            # Timeout is normal when no messages are available
            return None
        except FileNotFoundError:
            # MeshCore CLI not found - return None (will be handled in main)
            print("[DEBUG] MeshCore CLI not found")
            return None
        except Exception as e:
            # Log error but don't crash
            print(f"[ERROR] Error listening for messages: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def send(self, node_id: str, text: str):
        """
        Queue message for sending with rate limiting.
        
        Args:
            node_id: Target Node ID (e.g., "!a1b2c3")
            text: Message text to send
        """
        # Strip whitespace from node_id immediately
        node_id = node_id.strip()
        print(f"[DEBUG] send() called: node_id='{node_id}', text length={len(text)}")
        
        # ALWAYS use node ID for sending, not the name
        # If node_id looks like a name (not a hex string), look up the node ID
        # Node IDs are typically hex strings (8+ chars) or start with !
        if not re.match(r'^!?[a-fA-F0-9]{8,}$', node_id):
            print(f"[DEBUG] '{node_id}' looks like a name, looking up node ID from contacts...")
            node_id_actual = self._get_node_id_from_name(node_id)
            if node_id_actual:
                print(f"[DEBUG] Using node ID '{node_id_actual}' instead of name '{node_id}'")
                node_id = node_id_actual
            else:
                print(f"[DEBUG] ERROR: Could not find node ID for '{node_id}' - message may fail!")
        
        # Sanitize message
        sanitized = self._sanitize_message(text)
        print(f"[DEBUG] Sanitized message: {sanitized[:100]}...")
        
        # Add to queue (with node_id - should be actual node ID now)
        self.message_queue.put((node_id, sanitized))
        print(f"[DEBUG] Message queued with node_id='{node_id}'. Queue size: {self.message_queue.qsize()}")
        
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
                print(f"[DEBUG] Rate limiting: {time_since_last:.2f}s since last send, need {self.min_send_interval}s")
                return
        
        # Send next message from queue
        try:
            node_id, message = self.message_queue.get_nowait()
            # Strip any whitespace from node_id
            node_id = node_id.strip()
            print(f"[DEBUG] Processing queue: sending to '{node_id}', message: {message[:100]}...")
            
            # ALWAYS use node ID, not name - look it up if needed
            # If node_id looks like a name (not a hex string), look up the node ID
            if not re.match(r'^!?[a-fA-F0-9]{8,}$', node_id):
                print(f"[DEBUG] '{node_id}' in queue looks like a name, looking up node ID...")
                node_id_actual = self._get_node_id_from_name(node_id)
                if node_id_actual:
                    print(f"[DEBUG] Found node ID '{node_id_actual}' for name '{node_id}', using node ID")
                    node_id = node_id_actual
                else:
                    print(f"[DEBUG] ERROR: Could not find node ID for '{node_id}' - will try anyway but may fail")
            
            # Ensure the contact is added before sending
            if node_id not in self.friends:
                print(f"[DEBUG] Node '{node_id}' not in friends list, adding as contact...")
                self._ensure_contact(node_id)
            
            # Send via MeshCore CLI using msg command
            # Format: msg <node_id> <message>
            # MUST use node ID, not name
            cmd = self._build_meshcli_cmd("msg", node_id, message)
            print(f"[DEBUG] Sending command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            stdout_text = result.stdout.strip() if result.stdout else ""
            stderr_text = result.stderr.strip() if result.stderr else ""
            
            print(f"[DEBUG] msg exit code: {result.returncode}")
            if stdout_text:
                print(f"[DEBUG] msg stdout: {stdout_text}")
            if stderr_text:
                print(f"[DEBUG] msg stderr: {stderr_text}")
            
            # Check if stdout indicates failure (like "Unknown destination")
            if result.returncode == 0 and ("unknown" in stdout_text.lower() or "not found" in stdout_text.lower()):
                print(f"[ERROR] Destination '{node_id}' not recognized by meshcli")
                print(f"[DEBUG] Attempting to get node ID from contacts list...")
                
                # Try to get the actual node ID from the contacts list
                node_id_actual = self._get_node_id_from_name(node_id)
                if node_id_actual and node_id_actual != node_id:
                    print(f"[DEBUG] Found node ID '{node_id_actual}' for name '{node_id}', retrying with node ID...")
                    # Retry with the actual node ID (try both with and without ! prefix)
                    for try_id in [node_id_actual, f"!{node_id_actual}"]:
                        print(f"[DEBUG] Trying to send with node ID: '{try_id}'")
                        cmd = self._build_meshcli_cmd("msg", try_id, message)
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=5.0
                        )
                        stdout_text = result.stdout.strip() if result.stdout else ""
                        stderr_text = result.stderr.strip() if result.stderr else ""
                        print(f"[DEBUG] Retry with node ID '{try_id}' - exit code: {result.returncode}")
                        if stdout_text:
                            print(f"[DEBUG] Retry msg stdout: {stdout_text}")
                        if stderr_text:
                            print(f"[DEBUG] Retry msg stderr: {stderr_text}")
                        
                        # If this worked, break out of the loop
                        if result.returncode == 0 and not ("unknown" in stdout_text.lower() or "not found" in stdout_text.lower()):
                            print(f"[DEBUG] Successfully sent with node ID '{try_id}'!")
                            break
                else:
                    # Try to add contact and retry
                    print(f"[DEBUG] Attempting to add contact and retry...")
                    if self._ensure_contact(node_id):
                        # Retry sending
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=5.0
                        )
                        stdout_text = result.stdout.strip() if result.stdout else ""
                        stderr_text = result.stderr.strip() if result.stderr else ""
                        print(f"[DEBUG] Retry msg exit code: {result.returncode}")
                        if stdout_text:
                            print(f"[DEBUG] Retry msg stdout: {stdout_text}")
                        if stderr_text:
                            print(f"[DEBUG] Retry msg stderr: {stderr_text}")
            
            if result.returncode == 0 and not ("unknown" in stdout_text.lower() or "not found" in stdout_text.lower()):
                self.last_send_time = now
                print(f"[MESSAGE SENT] To: '{node_id}', Message: {message[:100]}...")
            else:
                print(f"[ERROR] Failed to send message to '{node_id}': {stdout_text or stderr_text}")
                # Put message back in queue to retry
                self.message_queue.put((node_id, message))
                
        except subprocess.TimeoutExpired:
            print("[ERROR] Timeout sending message via MeshCore CLI")
            # Put message back in queue to retry
            if 'node_id' in locals() and 'message' in locals():
                self.message_queue.put((node_id, message))
        except FileNotFoundError:
            print("[ERROR] MeshCore CLI not found. Install meshcore-cli.")
        except Exception as e:
            print(f"[ERROR] Error sending message: {e}")
            import traceback
            traceback.print_exc()
            # Put message back in queue to retry
            if 'node_id' in locals() and 'message' in locals():
                self.message_queue.put((node_id, message))
    
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
            print("[DEBUG] Getting radio version...")
            version_info = self.get_radio_version()
            if version_info:
                self.radio_version = version_info
                print(f"Radio version: {version_info}")
            else:
                print("Warning: Could not retrieve radio version")
            
            # Step 2: Get radio link information
            print("[DEBUG] Getting radio link info...")
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
                print("[DEBUG] Setting radio name to 'Meshagotchi'...")
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
            # Try without JSON first (faster, more reliable)
            result = subprocess.run(
                self._build_meshcli_cmd("infos"),
                capture_output=True,
                text=True,
                timeout=5.0  # Increased timeout
            )
            
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                return output
            
            # Fallback to JSON output if non-JSON didn't work
            try:
                result = subprocess.run(
                    self._build_meshcli_cmd("infos", json_output=True),
                    capture_output=True,
                    text=True,
                    timeout=5.0  # Increased timeout
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    output = result.stdout.strip()
                    return output
            except subprocess.TimeoutExpired:
                # JSON output timed out, that's okay - we'll use non-JSON
                pass
            except Exception:
                # JSON output failed, that's okay - we'll use non-JSON
                pass
            
            return None
            
        except subprocess.TimeoutExpired:
            # Timeout is okay, just return None
            return None
        except Exception as e:
            # Only print error if it's not a timeout (timeouts are expected sometimes)
            if "timeout" not in str(e).lower():
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
            print(f"  [DEBUG] Trying combined radio command format: {combined_radio_command}")
            combined_commands = [
                ("set radio", self._build_meshcli_cmd("set", "radio", combined_radio_command)),
                ("set-radio", self._build_meshcli_cmd("set-radio", combined_radio_command)),
                ("radio", self._build_meshcli_cmd("radio", combined_radio_command)),
            ]
            
            combined_success = False
            for cmd_name, cmd in combined_commands:
                try:
                    print(f"  [DEBUG] Trying command: {' '.join(cmd)}")
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5.0
                    )
                    stdout_text = result.stdout.strip() if result.stdout else ""
                    stderr_text = result.stderr.strip() if result.stderr else ""
                    print(f"  [DEBUG] Command exit code: {result.returncode}")
                    if stdout_text:
                        print(f"  [DEBUG] stdout: {stdout_text[:200]}")  # First 200 chars
                    if stderr_text:
                        print(f"  [DEBUG] stderr: {stderr_text[:200]}")  # First 200 chars
                    
                    # Check for error events
                    output = stdout_text + stderr_text
                    if "EventType.ERROR" in output or "command_error" in output:
                        print(f"  [DEBUG] Error event detected in output, trying next command...")
                        continue
                    if result.returncode == 0:
                        if not (stderr_text and ("error" in stderr_text.lower() or "unknown" in stderr_text.lower())):
                            print(f"  ✓ Applied radio settings using '{cmd_name}' command: {combined_radio_command}")
                            combined_success = True
                            time.sleep(1.5)  # Wait for settings to apply
                            break
                        else:
                            print(f"  [DEBUG] Command returned 0 but stderr contains error, trying next...")
                    else:
                        print(f"  [DEBUG] Command failed with exit code {result.returncode}")
                except Exception as e:
                    print(f"  [DEBUG] Exception running command: {e}")
                    continue
            
            # If combined command worked, verify it applied correctly
            if combined_success:
                print("  [DEBUG] Combined command succeeded, verifying settings...")
                time.sleep(1.0)
                current_info = self.get_radio_link_info()
                if current_info:
                    import json
                    try:
                        config = json.loads(current_info)
                        print(f"  [DEBUG] Current config: freq={config.get('radio_freq')}, bw={config.get('radio_bw')}, sf={config.get('radio_sf')}")
                        freq_ok = abs(config.get('radio_freq', 0) - freq_mhz) < 0.1
                        bw_ok = abs(config.get('radio_bw', 0) - bw_khz) < 1.0
                        sf_ok = config.get('radio_sf', 0) == preset['spreading_factor']
                        print(f"  [DEBUG] Verification: freq_ok={freq_ok}, bw_ok={bw_ok}, sf_ok={sf_ok}")
                        if freq_ok and bw_ok and sf_ok:
                            print("  Radio settings verified successfully!")
                            return True
                        else:
                            print("  [DEBUG] Settings not verified correctly, continuing with individual settings...")
                    except Exception as e:
                        print(f"  [DEBUG] Error parsing config for verification: {e}")
                else:
                    print("  [DEBUG] Could not get radio info for verification")
            
            # Try preset/region commands if combined command didn't work
            preset_commands = [
                ("preset", self._build_meshcli_cmd("preset", "usa")),
                ("preset", self._build_meshcli_cmd("preset", "usa-canada")),
                ("preset", self._build_meshcli_cmd("preset", "US")),
                ("region", self._build_meshcli_cmd("region", "usa")),
                ("region", self._build_meshcli_cmd("region", "US")),
                ("set-preset", self._build_meshcli_cmd("set-preset", "usa")),
            ]
            
            if not combined_success:
                print("  [DEBUG] Trying preset/region commands...")
            preset_success = False
            for preset_name, preset_cmd in preset_commands:
                try:
                    print(f"  [DEBUG] Trying preset command: {' '.join(preset_cmd)}")
                    result = subprocess.run(
                        preset_cmd,
                        capture_output=True,
                        text=True,
                        timeout=5.0
                    )
                    stdout_text = result.stdout.strip() if result.stdout else ""
                    stderr_text = result.stderr.strip() if result.stderr else ""
                    print(f"  [DEBUG] Preset command exit code: {result.returncode}")
                    if stdout_text:
                        print(f"  [DEBUG] Preset stdout: {stdout_text[:150]}")
                    if stderr_text:
                        print(f"  [DEBUG] Preset stderr: {stderr_text[:150]}")
                    if result.returncode == 0:
                        # Check for error events
                        output = stdout_text + stderr_text
                        if "EventType.ERROR" in output or "command_error" in output:
                            print(f"  [DEBUG] Error event in preset command, trying next...")
                            continue
                        if not (stderr_text and ("error" in stderr_text.lower() or "unknown" in stderr_text.lower())):
                            print(f"  ✓ Applied preset using '{preset_name}' command")
                            preset_success = True
                            time.sleep(1.0)  # Wait for preset to apply
                            break
                except Exception as e:
                    print(f"  [DEBUG] Exception in preset command: {e}")
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
                            print(f"    [DEBUG] Trying: {' '.join(cmd)}")
                            result = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                timeout=5.0
                            )
                            
                            # Debug: Check actual command output to see if it's working
                            stdout_text = result.stdout.strip() if result.stdout else ""
                            stderr_text = result.stderr.strip() if result.stderr else ""
                            print(f"    [DEBUG] Exit code: {result.returncode}")
                            if stdout_text:
                                print(f"    [DEBUG] stdout: {stdout_text[:150]}")
                            if stderr_text:
                                print(f"    [DEBUG] stderr: {stderr_text[:150]}")
                            
                            # Check for error events in output (meshcli may output error events)
                            # Error format: "Error : Event(type=<EventType.ERROR: 'command_error'>, payload={'error_code': 6}, ...)"
                            if "EventType.ERROR" in stdout_text or "EventType.ERROR" in stderr_text:
                                print(f"    [DEBUG] Error event detected!")
                                # Extract error code if present
                                error_match = re.search(r"error_code['\"]?\s*:\s*(\d+)", stdout_text + stderr_text)
                                if error_match:
                                    error_code = error_match.group(1)
                                    last_error = f"Command rejected by radio (error_code: {error_code})"
                                    print(f"    [DEBUG] Error code: {error_code}")
                                    # If error_code 6, commands are not supported
                                    if error_code == "6":
                                        commands_not_supported = True
                                        print(f"    [DEBUG] error_code 6 detected - commands not supported")
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
    
    def _ensure_contact(self, node_id: str) -> bool:
        """
        Ensure a node is added as a contact so we can send messages to it.
        
        Args:
            node_id: Node ID or name to add as contact
            
        Returns:
            True if contact was added or already exists, False otherwise
        """
        node_id = node_id.strip()
        if not node_id:
            return False
        
        try:
            # Try to add contact using various commands
            add_commands = [
                self._build_meshcli_cmd("add", node_id),
                self._build_meshcli_cmd("contact", "add", node_id),
                self._build_meshcli_cmd("friend", "add", node_id),
            ]
            
            for cmd in add_commands:
                try:
                    print(f"[DEBUG] Trying to add contact with: {' '.join(cmd)}")
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    stdout_text = result.stdout.strip() if result.stdout else ""
                    stderr_text = result.stderr.strip() if result.stderr else ""
                    print(f"[DEBUG] Add contact exit code: {result.returncode}, stdout: {stdout_text}, stderr: {stderr_text}")
                    if result.returncode == 0:
                        if node_id not in self.friends:
                            self.friends.add(node_id)
                        print(f"[DEBUG] Contact '{node_id}' added successfully")
                        return True
                except Exception as e:
                    print(f"[DEBUG] Exception adding contact: {e}")
                    continue
            
            # If add commands don't work, just track locally
            if node_id not in self.friends:
                self.friends.add(node_id)
            return True
            
        except Exception as e:
            print(f"[DEBUG] Error ensuring contact '{node_id}': {e}")
            return False
    
    def _get_node_id_from_name(self, name: str) -> Optional[str]:
        """
        Try to get the actual node ID from a name.
        First checks database, then queries meshcli contacts list if not found.
        
        Args:
            name: Node name to look up
            
        Returns:
            Node ID if found, None otherwise
        """
        name = name.strip()
        if not name:
            print(f"[DEBUG] _get_node_id_from_name: Empty name provided")
            return None
        
        print(f"[DEBUG] _get_node_id_from_name: Looking up node ID for name '{name}'")
        
        # First, try to get from database
        try:
            import database
            node_id = database.get_node_id_by_name(name)
            if node_id:
                print(f"[DEBUG] Found node ID '{node_id}' for name '{name}' in database")
                return node_id
        except Exception as e:
            print(f"[DEBUG] Error checking database: {e}")
        
        # If not in database, query meshcli contacts list
        try:
            # Get contacts list
            result = subprocess.run(
                self._build_meshcli_cmd("contacts"),
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            if result.returncode == 0 and result.stdout:
                output = result.stdout.strip()
                print(f"[DEBUG] Contacts list: {output[:200]}...")
                
                # Parse contacts list format:
                # Format appears to be: "name <spaces> type <spaces> node_id <spaces> hop_count"
                # Example: "Mattd-t1000-002                CLI   0b2c2328618f  0 hop"
                lines = output.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('>') or 'contacts in device' in line.lower():
                        continue
                    
                    # Check if this line contains the name we're looking for
                    # Strip the line and compare - name might be at the start
                    line_stripped = line.strip()
                    name_stripped = name.strip()
                    
                    print(f"[DEBUG] Checking if name '{name_stripped}' is in line: '{line_stripped[:50]}...'")
                    
                    # Check if name appears in the line (could be at start or anywhere)
                    # Also check if the line starts with the name (most common case)
                    if name_stripped in line_stripped or line_stripped.startswith(name_stripped):
                        print(f"[DEBUG] ✓ Found line with name '{name_stripped}': {line_stripped}")
                        # Try to extract node ID - it's usually a hex string (8+ chars)
                        # Look for hex strings that are likely node IDs
                        # Pattern: name, then spaces, then type, then spaces, then node_id
                        # The node_id is typically 8-16 hex characters
                        # Split by whitespace - filter out empty strings
                        parts = [p.strip() for p in line.split() if p.strip()]
                        print(f"[DEBUG] Line parts: {parts}")
                        
                        # Look for the type (CLI, REP, etc.) and get the node ID after it
                        for i, part in enumerate(parts):
                            # Node ID is usually after the type (CLI, REP, etc.)
                            # and is a hex string
                            if part.upper() in ['CLI', 'REP', 'CLIENT', 'REPEATER'] and i + 1 < len(parts):
                                node_id_candidate = parts[i + 1].strip()
                                print(f"[DEBUG] Checking candidate '{node_id_candidate}' after type '{part}'")
                                # Check if it looks like a node ID (hex string, 8+ chars)
                                if re.match(r'^[a-fA-F0-9]{8,}$', node_id_candidate):
                                    node_id = node_id_candidate
                                    print(f"[DEBUG] ✓✓✓ Found node ID '{node_id}' after type '{part}'")
                                    # Store in database for future lookups
                                    try:
                                        import database
                                        database.store_contact(name_stripped, node_id)
                                        print(f"[DEBUG] Stored contact mapping '{name_stripped}' -> '{node_id}' in database")
                                    except Exception as e:
                                        print(f"[DEBUG] Error storing contact in database: {e}")
                                    return node_id
                                else:
                                    print(f"[DEBUG] Candidate '{node_id_candidate}' doesn't match hex pattern")
                        
                        # Fallback: try to find any hex string in the line (8+ chars)
                        # Use word boundary to avoid partial matches
                        print(f"[DEBUG] Trying fallback regex to find hex string...")
                        node_id_match = re.search(r'\b([a-fA-F0-9]{8,})\b', line)
                        if node_id_match:
                            node_id = node_id_match.group(1)
                            print(f"[DEBUG] ✓ Found node ID '{node_id}' using fallback regex")
                            # Store in database for future lookups
                            try:
                                import database
                                database.store_contact(name_stripped, node_id)
                                print(f"[DEBUG] Stored contact mapping '{name_stripped}' -> '{node_id}' in database")
                            except Exception as e:
                                print(f"[DEBUG] Error storing contact in database: {e}")
                            return node_id
                        
                        print(f"[DEBUG] ✗✗✗ WARNING: Could not extract node ID from line: {line}")
                        print(f"[DEBUG] Parts were: {parts}")
                    else:
                        print(f"[DEBUG] Name '{name_stripped}' not found in line (checked: '{line_stripped[:50]}...')")
                        # Try a more flexible match - check if name starts the line (after stripping)
                        if line_stripped.startswith(name_stripped):
                            print(f"[DEBUG] Line starts with name, trying extraction anyway...")
                            parts = [p.strip() for p in line.split() if p.strip()]
                            print(f"[DEBUG] Line parts: {parts}")
                            for i, part in enumerate(parts):
                                if part.upper() in ['CLI', 'REP', 'CLIENT', 'REPEATER'] and i + 1 < len(parts):
                                    node_id_candidate = parts[i + 1].strip()
                                    if re.match(r'^[a-fA-F0-9]{8,}$', node_id_candidate):
                                        node_id = node_id_candidate
                                        print(f"[DEBUG] ✓✓✓ Found node ID '{node_id}' after type '{part}' (flexible match)")
                                        return node_id
                
                # If not found, try parsing as JSON
                try:
                    import json
                    contacts = json.loads(output)
                    if isinstance(contacts, list):
                        for contact in contacts:
                            if isinstance(contact, dict):
                                contact_name = contact.get('name', '').strip()
                                contact_id = contact.get('id', '') or contact.get('node_id', '')
                                if contact_name == name and contact_id:
                                    print(f"[DEBUG] Found node ID '{contact_id}' for name '{name}' in JSON")
                                    return contact_id
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"[DEBUG] Error getting node ID from name: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def add_friend(self, node_id: str) -> bool:
        """
        Track a node locally. MeshCore auto-adds contacts when adverts are received,
        so we mainly track them locally for reference.
        
        Args:
            node_id: Node ID or name to track (e.g., "!a1b2c3" or "Meshagotchi")
            
        Returns:
            True (always succeeds for local tracking)
        """
        node_id = node_id.strip()
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
            # This is the PRIMARY source for name -> node_id mappings
            try:
                result = subprocess.run(
                    self._build_meshcli_cmd("contacts"),
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    output = result.stdout.strip()
                    lines = output.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith('>') or 'contacts in device' in line.lower():
                            continue
                        
                        # Parse: "name <spaces> type <spaces> node_id <spaces> hop_count"
                        # Example: "Mattd-t1000-002                CLI   0b2c2328618f  0 hop"
                        parts = [p.strip() for p in line.split() if p.strip()]
                        
                        if len(parts) >= 3:
                            # parts[0] = name, parts[1] = type, parts[2] = node_id
                            name = parts[0]
                            node_id_candidate = parts[2] if len(parts) > 2 else None
                            
                            # Check if node_id_candidate looks like a node ID
                            if node_id_candidate and re.match(r'^[a-fA-F0-9]{8,}$', node_id_candidate):
                                try:
                                    import database
                                    database.store_contact(name, node_id_candidate)
                                    print(f"[DEBUG] Stored contact: '{name}' -> '{node_id_candidate}'")
                                    # Also add to friends set (use node ID, not name)
                                    if node_id_candidate not in self.friends:
                                        self.friends.add(node_id_candidate)
                                except Exception as e:
                                    print(f"[DEBUG] Error storing contact: {e}")
                    
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
