"""
MeshCore CLI wrapper for LoRa mesh communication.

Handles sending and receiving messages via MeshCore CLI with rate limiting
to prevent network flooding. Designed for Heltec V3 LoRa radio.
"""

import subprocess
import time
import re
import json
import unicodedata
import os
from queue import Queue
from typing import Optional, Tuple, Dict
from datetime import datetime, timedelta

def _is_running_as_root() -> bool:
    """Check if the current process is running as root."""
    try:
        return os.geteuid() == 0
    except AttributeError:
        # Windows or other platform without geteuid
        return False


def _normalize_meshcli_text(value: str) -> str:
    """
    Normalize MeshCLI output / names for robust matching.
    MeshCLI output can contain odd spacing (including NBSP), so collapse all
    whitespace to single spaces and trim.
    """
    if value is None:
        return ""
    # Normalize a wide set of unicode whitespace / zero-width chars that can appear
    # in meshcli outputs (and that may survive naive .strip()).
    value = str(value)
    value = value.replace("\ufeff", "")  # BOM / zero-width no-break space
    value = value.replace("\u200b", "")  # zero-width space
    value = value.replace("\u200c", "")  # zero-width non-joiner
    value = value.replace("\u200d", "")  # zero-width joiner
    # Convert any whitespace to normal spaces so collapse works consistently.
    value = "".join((" " if ch.isspace() else ch) for ch in value)
    return re.sub(r"[ ]+", " ", value).strip()


def _normalize_contact_name(value: str) -> str:
    """
    Normalize a MeshCore contact name into a stable lookup key.

    The `recv` output can include invisible format chars (Unicode category Cf) that are
    NOT whitespace and therefore survive naive `.strip()`, causing lookups like:
      'Mattd-t1000-002<ZWSP>' != 'Mattd-t1000-002'
    
    CRITICAL: This function MUST preserve the actual name and only remove invisible/format characters.
    It should NOT remove visible characters that are part of the name.
    """
    if not value:
        return ""
    
    # First normalize whitespace (this handles NBSP and other whitespace issues)
    text = _normalize_meshcli_text(value)
    if not text:
        return ""

    # Remove all control/format characters (Cc/Cf) defensively - these are invisible
    # but preserve all visible characters including alphanumeric, underscore, dot, dash
    # CRITICAL: Only remove characters that are truly invisible (Cc/Cf categories)
    # Do NOT remove printable characters
    cleaned = []
    for ch in text:
        cat = unicodedata.category(ch)
        # Keep printable characters (letters, numbers, punctuation like dash, dot, underscore)
        if cat[0] in ('L', 'N', 'P', 'S'):  # Letter, Number, Punctuation, Symbol
            cleaned.append(ch)
        elif cat in ('Cc', 'Cf'):  # Control and Format characters - skip these
            continue
        # For any other category, be conservative and keep it
        else:
            cleaned.append(ch)
    
    text = "".join(cleaned)

    # Keep only characters we expect in mesh names (alnum + _ . -).
    # This removes any remaining special characters but preserves the core name
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "", text)
    
    return normalized


def _check_rfkill_status() -> bool:
    """
    Check if Bluetooth is blocked by rfkill and unblock if needed.
    
    Returns:
        True if Bluetooth is unblocked, False otherwise
    """
    try:
        # Check rfkill status
        cmd = ["rfkill", "list", "bluetooth"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5.0
        )
        
        if result.returncode == 0:
            output = result.stdout
            # Check if any Bluetooth device is blocked
            if " blocked" in output.lower() or ": yes" in output:
                print("Bluetooth is blocked by rfkill. Attempting to unblock...")
                is_root = _is_running_as_root()
                
                unblock_cmd = ["rfkill", "unblock", "bluetooth"]
                if not is_root:
                    unblock_cmd = ["sudo", "-n"] + unblock_cmd
                
                unblock_result = subprocess.run(
                    unblock_cmd,
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                
                if unblock_result.returncode == 0:
                    print("Bluetooth unblocked successfully")
                    time.sleep(2)  # Wait for unblock to take effect
                    return True
                else:
                    print("Failed to unblock Bluetooth with rfkill")
                    if unblock_result.stderr:
                        print(f"Error: {unblock_result.stderr.strip()}")
                    return False
        return True  # Not blocked or couldn't check
    except FileNotFoundError:
        print("rfkill command not found, skipping rfkill check")
        return True  # Assume not blocked if we can't check
    except Exception as e:
        print(f"Error checking rfkill: {e}")
        return True  # Continue anyway


def _ensure_bluetooth_enabled() -> bool:
    """
    Ensure Bluetooth is powered on and ready for BLE scanning.
    
    Returns:
        True if Bluetooth is enabled, False otherwise
    """
    try:
        # First check and unblock rfkill if needed
        if not _check_rfkill_status():
            print("Could not unblock Bluetooth. Please run manually:")
            print("  sudo rfkill unblock bluetooth")
            return False
        
        # Check Bluetooth service status
        is_root = _is_running_as_root()
        service_cmd = ["systemctl", "is-active", "bluetooth"]
        if not is_root:
            service_cmd = ["sudo", "-n"] + service_cmd
        
        service_result = subprocess.run(
            service_cmd,
            capture_output=True,
            text=True,
            timeout=5.0
        )
        
        if service_result.returncode != 0 or "active" not in service_result.stdout:
            print("Bluetooth service is not active. Attempting to start...")
            start_cmd = ["systemctl", "start", "bluetooth"]
            if not is_root:
                start_cmd = ["sudo", "-n"] + start_cmd
            
            start_result = subprocess.run(
                start_cmd,
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            if start_result.returncode == 0:
                print("Bluetooth service started")
                time.sleep(2)  # Wait for service to initialize
            else:
                print("Failed to start Bluetooth service")
                if start_result.stderr:
                    print(f"Error: {start_result.stderr.strip()}")
                print("Please run manually: sudo systemctl start bluetooth")
                return False
        
        # Check Bluetooth power state
        cmd = ["bluetoothctl", "show"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5.0
        )
        
        if result.returncode != 0:
            print("Warning: Could not check Bluetooth status")
            return False
        
        output = result.stdout
        
        # Check if powered is off
        if "Powered: no" in output or "PowerState: off" in output:
            print("Bluetooth is powered off. Attempting to power on...")
            
            # Check if we're already running as root
            is_root = _is_running_as_root()
            
            # Try to power on Bluetooth
            if is_root:
                # Already running as root, don't use sudo
                power_cmd = ["bluetoothctl", "power", "on"]
            else:
                # Try without sudo first
                power_cmd = ["bluetoothctl", "power", "on"]
            
            power_result = subprocess.run(
                power_cmd,
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            if power_result.returncode == 0:
                print("Bluetooth powered on successfully")
                time.sleep(2)  # Wait for Bluetooth to initialize
            else:
                # If not root and regular command failed, try with sudo
                if not is_root:
                    print("Regular command failed, trying with sudo...")
                    sudo_power_cmd = ["sudo", "-n", "bluetoothctl", "power", "on"]  # -n = non-interactive
                    sudo_power_result = subprocess.run(
                        sudo_power_cmd,
                        capture_output=True,
                        text=True,
                        timeout=5.0
                    )
                    
                    if sudo_power_result.returncode == 0:
                        print("Bluetooth powered on successfully (with sudo)")
                        time.sleep(2)  # Wait for Bluetooth to initialize
                    else:
                        # Show what went wrong
                        if sudo_power_result.stderr:
                            print(f"Error: {sudo_power_result.stderr.strip()}")
                        print("Failed to power on Bluetooth automatically.")
                        print("Please run manually: sudo bluetoothctl power on")
                        return False
                else:
                    # We're root but it still failed - show detailed error
                    print(f"Command failed with return code: {power_result.returncode}")
                    if power_result.stdout:
                        print(f"stdout: {power_result.stdout.strip()}")
                    if power_result.stderr:
                        print(f"stderr: {power_result.stderr.strip()}")
                    print("Failed to power on Bluetooth (running as root).")
                    print("Trying alternative method...")
                    
                    # Try using systemctl to restart bluetooth service
                    try:
                        restart_cmd = ["systemctl", "restart", "bluetooth"]
                        restart_result = subprocess.run(
                            restart_cmd,
                            capture_output=True,
                            text=True,
                            timeout=5.0
                        )
                        if restart_result.returncode == 0:
                            print("Bluetooth service restarted, waiting...")
                            time.sleep(3)
                            # Try power on again
                            power_result2 = subprocess.run(
                                ["bluetoothctl", "power", "on"],
                                capture_output=True,
                                text=True,
                                timeout=5.0
                            )
                            if power_result2.returncode == 0:
                                print("Bluetooth powered on successfully after restart")
                                time.sleep(2)
                            else:
                                # Check for specific error messages
                                error_output = (power_result2.stderr or power_result2.stdout or "").strip()
                                if "org.bluez.Error.Failed" in error_output:
                                    print("Got org.bluez.Error.Failed - Bluetooth may be blocked or hardware issue")
                                    print("Checking rfkill status...")
                                    # Check rfkill again
                                    rfkill_cmd = ["rfkill", "list", "bluetooth"]
                                    rfkill_result = subprocess.run(
                                        rfkill_cmd,
                                        capture_output=True,
                                        text=True,
                                        timeout=5.0
                                    )
                                    if rfkill_result.returncode == 0:
                                        print(rfkill_result.stdout)
                                
                                print("Still failed after restart.")
                                print("\nTroubleshooting steps:")
                                print("  1. Check Bluetooth service: sudo systemctl status bluetooth")
                                print("  2. Check if hardware is blocked: rfkill list bluetooth")
                                print("  3. Unblock if needed: sudo rfkill unblock bluetooth")
                                print("  4. Restart service: sudo systemctl restart bluetooth")
                                print("  5. Try power on: sudo bluetoothctl power on")
                                return False
                        else:
                            print("Could not restart Bluetooth service")
                            return False
                    except Exception as e:
                        print(f"Error restarting service: {e}")
                        return False
        
        # Check if it's blocked (may need to unblock with rfkill)
        if "PowerState: off-blocked" in output:
            print("Bluetooth is blocked. Attempting to unblock with rfkill...")
            try:
                is_root = _is_running_as_root()
                
                # Try to unblock with rfkill
                unblock_cmd = ["rfkill", "unblock", "bluetooth"]
                unblock_result = subprocess.run(
                    unblock_cmd,
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                if unblock_result.returncode == 0:
                    print("Bluetooth unblocked successfully")
                    time.sleep(1)
                elif not is_root:
                    # Try with sudo
                    print("Regular command failed, trying with sudo...")
                    sudo_unblock_cmd = ["sudo", "-n", "rfkill", "unblock", "bluetooth"]
                    sudo_unblock_result = subprocess.run(
                        sudo_unblock_cmd,
                        capture_output=True,
                        text=True,
                        timeout=5.0
                    )
                    if sudo_unblock_result.returncode == 0:
                        print("Bluetooth unblocked successfully (with sudo)")
                        time.sleep(1)
                    else:
                        print("Could not unblock Bluetooth automatically")
                        print("Please run manually: sudo rfkill unblock bluetooth")
                
                # Now try to power on
                if is_root:
                    power_cmd = ["bluetoothctl", "power", "on"]
                else:
                    power_cmd = ["bluetoothctl", "power", "on"]
                
                power_result = subprocess.run(power_cmd, capture_output=True, text=True, timeout=5.0)
                if power_result.returncode != 0 and not is_root:
                    sudo_power_cmd = ["sudo", "-n", "bluetoothctl", "power", "on"]
                    subprocess.run(sudo_power_cmd, capture_output=True, text=True, timeout=5.0)
                time.sleep(2)
            except FileNotFoundError:
                print("rfkill command not found. Please install rfkill or run manually:")
                print("  sudo rfkill unblock bluetooth")
                print("  sudo bluetoothctl power on")
        
        # Verify it's now powered on
        verify_result = subprocess.run(
            ["bluetoothctl", "show"],
            capture_output=True,
            text=True,
            timeout=5.0
        )
        
        if "Powered: yes" in verify_result.stdout:
            return True
        else:
            print("Bluetooth is still not powered on.")
            print("You may need to run: sudo bluetoothctl power on")
            return False
            
    except subprocess.TimeoutExpired:
        print("Timeout checking Bluetooth status")
        return False
    except FileNotFoundError:
        print("bluetoothctl command not found. Please install bluez package.")
        return False
    except Exception as e:
        print(f"Error checking Bluetooth status: {e}")
        return False


def _scan_ble_devices() -> list:
    """
    Scan for available BLE MeshCore devices.
    
    Uses meshcli -l to list BLE devices. Falls back to bluetoothctl if needed.
    
    Returns:
        List of dictionaries with 'address' and 'name' keys, or empty list if none found
    """
    devices = []
    
    # First, try meshcli -l
    try:
        cmd = ["meshcli", "-l"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15.0  # Allow more time for BLE scan
        )
        
        # Debug: show what meshcli returned
        if result.stdout:
            print(f"meshcli -l output: {result.stdout[:200]}...")  # Show first 200 chars
        if result.stderr:
            print(f"meshcli -l stderr: {result.stderr[:200]}...")
        if result.returncode != 0:
            print(f"meshcli -l returned exit code: {result.returncode}")
        
        if result.returncode == 0 and result.stdout.strip():
            output = result.stdout.strip()
            lines = output.split('\n')
            
            # Parse output - format may vary, but typically shows address and name
            # Example formats:
            # "C2:2B:A1:D5:3E:B6  DeviceName"
            # or JSON format
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Try to parse as JSON first
                if line.startswith('{'):
                    try:
                        parsed = json.loads(line)
                        if 'address' in parsed:
                            devices.append({
                                'address': parsed['address'],
                                'name': parsed.get('name', 'Unknown')
                            })
                        continue
                    except json.JSONDecodeError:
                        pass
                
                # Parse text format - look for MAC address pattern (XX:XX:XX:XX:XX:XX)
                mac_pattern = r'([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})'
                match = re.search(mac_pattern, line)
                if match:
                    address = match.group(1).upper()
                    # Extract name (everything after the address)
                    name_part = line[match.end():].strip()
                    # Remove any extra whitespace or separators
                    name = re.sub(r'^\s*[-:]\s*', '', name_part).strip() or 'Unknown'
                    devices.append({
                        'address': address,
                        'name': name
                    })
        
    except subprocess.TimeoutExpired:
        print("BLE scan timed out (meshcli -l)")
    except FileNotFoundError:
        print("meshcli command not found. Please ensure MeshCore CLI is installed.")
    except Exception as e:
        print(f"Error scanning with meshcli: {e}")
    
    # If meshcli didn't find devices, try bluetoothctl as fallback
    if not devices:
        try:
            print("Trying bluetoothctl to scan for BLE devices...")
            # Start bluetoothctl scan
            scan_cmd = ["bluetoothctl", "scan", "on"]
            subprocess.run(scan_cmd, capture_output=True, timeout=2.0)
            time.sleep(5)  # Wait for scan
            
            # Get devices
            devices_cmd = ["bluetoothctl", "devices"]
            result = subprocess.run(
                devices_cmd,
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    # bluetoothctl format: "Device C2:2B:A1:D5:3E:B6 DeviceName"
                    mac_pattern = r'([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})'
                    match = re.search(mac_pattern, line)
                    if match:
                        address = match.group(1).upper()
                        # Extract name (everything after the MAC address)
                        name_part = line[match.end():].strip()
                        name = name_part or 'Unknown'
                        devices.append({
                            'address': address,
                            'name': name
                        })
        except Exception as e:
            print(f"Error scanning with bluetoothctl: {e}")
    
    return devices


def _select_ble_device_interactive(devices: list) -> Optional[Dict]:
    """
    Display numbered list of BLE devices and prompt user for selection.
    
    Args:
        devices: List of device dicts with 'address' and 'name' keys
    
    Returns:
        Selected device dict or None if cancelled
    """
    if not devices:
        print("No BLE devices found. Please ensure your MeshCore radio is powered on and in range.")
        return None
    
    print("\nAvailable BLE devices:")
    for i, device in enumerate(devices, 1):
        name = device.get('name', 'Unknown')
        address = device.get('address', 'Unknown')
        print(f"  {i} - {name} ({address})")
    
    while True:
        try:
            choice = input("\nSelect device number (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(devices):
                return devices[index]
            else:
                print(f"Invalid selection. Please enter a number between 1 and {len(devices)}")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
        except KeyboardInterrupt:
            print("\nCancelled.")
            return None


class MeshHandler:
    """
    Handles all MeshCore CLI communication with rate limiting.
    
    Hardware: Heltec V3 LoRa radio running latest MeshCore firmware,
    connected to Raspberry Pi via BLE (Bluetooth Low Energy).
    """
    
    # USA/Canada (Recommended) preset parameters
    USA_CANADA_PRESET = {
        'frequency': 910525000,  # 910.525 MHz in Hz
        'bandwidth': 62500,      # 62.5 kHz in Hz
        'spreading_factor': 7,   # SF7
        'coding_rate': 5,        # CR 5
        'power': 22              # 22 dBm
    }
    
    def __init__(self, min_send_interval: float = 2.0, max_message_length: int = 200):
        """
        Initialize MeshHandler with BLE connection.
        
        Args:
            min_send_interval: Minimum seconds between sends (default: 2.0)
            max_message_length: Maximum message length in bytes (default: 200)
        """
        self.message_queue = Queue()
        self.last_send_time = None
        self.min_send_interval = min_send_interval
        self.max_message_length = max_message_length
        self.radio_version = None
        self.radio_info = None
        
        # BLE connection info
        self.ble_address = None
        self.ble_name = None
        self.ble_pairing_code = None
        
        # Connect via BLE
        self._connect_ble()
        
        self.friends = set()  # Track discovered nodes as friends

        # Cache for contacts mapping (adv_name -> public_key). Avoid shelling out to meshcli
        # on every recv/send. TTL is short because contacts can change.
        self._contacts_cache_ts = 0.0
        self._contacts_cache_ttl_s = 10.0
        self._contacts_cache_name_to_pubkey: Dict[str, str] = {}

    def _connect_ble(self):
        """
        Establish BLE connection to MeshCore radio.
        
        Flow:
        1. Check database for stored BLE device
        2. If found, attempt connection with stored info
        3. If not found or connection fails, scan and prompt user
        4. Store successful connection in database
        """
        import database
        
        # Step 1: Check for stored BLE device
        stored_device = database.get_stored_ble_device()
        
        if stored_device:
            address = stored_device['address']
            name = stored_device.get('name', 'Unknown')
            pairing_code = stored_device.get('pairing_code')
            
            print(f"Found stored BLE device: {name} ({address})")
            
            # Attempt connection with stored device
            if self._test_ble_connection(address, pairing_code):
                self.ble_address = address
                self.ble_name = name
                self.ble_pairing_code = pairing_code
                database.update_ble_device_connection(address)
                print(f"Connected to BLE device: {name} ({address})")
                return
        
        # Step 2: No stored device or connection failed - scan and prompt
        # First ensure Bluetooth is enabled
        print("Checking Bluetooth status...")
        if not _ensure_bluetooth_enabled():
            print("\nBluetooth is not enabled. Please enable Bluetooth first:")
            print("  sudo bluetoothctl power on")
            print("Or if blocked, you may need to:")
            print("  sudo rfkill unblock bluetooth")
            print("  sudo bluetoothctl power on")
            raise RuntimeError("Bluetooth is not enabled")
        
        print("Scanning for BLE devices...")
        devices = _scan_ble_devices()
        
        if not devices:
            print("\nNo BLE devices found via automatic scan.")
            print("Troubleshooting steps:")
            print("  1. Ensure your MeshCore radio is powered on")
            print("  2. Check Bluetooth is enabled: bluetoothctl show")
            print("  3. Try manual scan: meshcli -l")
            print("  4. If you know the BLE address, you can enter it manually")
            
            # Offer manual entry as fallback
            while True:
                try:
                    manual_input = input("\nEnter BLE address manually (format: XX:XX:XX:XX:XX:XX) or 'q' to quit: ").strip()
                    if manual_input.lower() == 'q':
                        raise RuntimeError("No BLE device selected")
                    
                    # Validate MAC address format
                    mac_pattern = r'^([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})$'
                    if re.match(mac_pattern, manual_input):
                        address = manual_input.upper()
                        name = input("Enter device name (or press Enter for 'Unknown'): ").strip() or 'Unknown'
                        devices = [{'address': address, 'name': name}]
                        break
                    else:
                        print("Invalid MAC address format. Please use format: XX:XX:XX:XX:XX:XX")
                except KeyboardInterrupt:
                    raise RuntimeError("Connection cancelled by user")
            
            if not devices:
                raise RuntimeError("No BLE devices available")
        
        # Step 3: User selects device
        selected_device = _select_ble_device_interactive(devices)
        if not selected_device:
            raise RuntimeError("No BLE device selected")
        
        address = selected_device['address']
        name = selected_device.get('name', 'Unknown')
        
        # Step 4: Prompt for pairing code
        print(f"\nSelected device: {name} ({address})")
        pairing_code = None
        while True:
            try:
                code_input = input("Enter BLE pairing code (or press Enter if not required): ").strip()
                if code_input:
                    pairing_code = code_input
                break
            except KeyboardInterrupt:
                raise RuntimeError("Connection cancelled by user")
        
        # Step 5: Attempt connection
        if not self._test_ble_connection(address, pairing_code):
            print("Failed to connect to BLE device. Please check:")
            print("  - Device is powered on and in range")
            print("  - Pairing code is correct")
            print("  - Device is not already connected to another system")
            raise RuntimeError(f"Failed to connect to BLE device {address}")
        
        # Step 6: Store successful connection
        self.ble_address = address
        self.ble_name = name
        self.ble_pairing_code = pairing_code
        database.store_ble_device(address, name, pairing_code)
        print(f"Successfully connected to BLE device: {name} ({address})")
    
    def _test_ble_connection(self, address: str, pairing_code: Optional[str] = None) -> bool:
        """
        Test BLE connection to a device.
        
        Args:
            address: BLE MAC address
            pairing_code: Optional pairing code
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # If pairing code is provided, attempt OS-level pairing first
            if pairing_code:
                try:
                    # Use bluetoothctl to pair the device
                    # Note: This may require user interaction, but we'll try automated pairing
                    pair_cmd = ["bluetoothctl", "pair", address]
                    pair_result = subprocess.run(
                        pair_cmd,
                        capture_output=True,
                        text=True,
                        timeout=10.0
                    )
                    # If pairing requires PIN, it will prompt - we can't easily automate this
                    # The user may need to pair manually via bluetoothctl if this fails
                    time.sleep(1)  # Brief pause after pairing attempt
                except Exception as e:
                    print(f"Note: Automatic pairing may have failed: {e}")
                    print("You may need to pair manually: bluetoothctl pair " + address)
            
            # Try a simple command to test connection
            # Use meshcli -a <address> with a lightweight command
            cmd = ["meshcli", "-a", address, "infos", "-j"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            if result.returncode == 0:
                # Connection successful - verify we got valid output
                output = result.stdout.strip()
                if output:
                    # Check if output contains expected MeshCore data
                    if "{" in output or any(keyword in output.lower() for keyword in ["radio", "frequency", "meshcore", "node"]):
                        return True
            
            return False
            
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            print(f"Error testing BLE connection: {e}")
            return False

    def _get_contacts_name_to_pubkey_map(self, force_refresh: bool = False) -> Dict[str, str]:
        """
        Query MeshCore contacts via JSON (`meshcli -j contacts`) and build a mapping:
        normalized adv_name -> destination hex id.

        We prefer this over parsing the text table because the JSON output is stable and
        includes the true public key (hex destination) directly.
        """
        now = time.time()
        if (
            not force_refresh
            and self._contacts_cache_name_to_pubkey
            and (now - self._contacts_cache_ts) < self._contacts_cache_ttl_s
        ):
            return self._contacts_cache_name_to_pubkey

        try:
            result = subprocess.run(
                self._build_meshcli_cmd("contacts", json_output=True),
                capture_output=True,
                text=True,
                timeout=5.0,
            )
            if result.returncode != 0 or not result.stdout:
                return {}

            raw = result.stdout.strip()
            # Some meshcli builds may print non-JSON preamble; extract the JSON object if needed.
            if not raw.startswith("{"):
                start = raw.find("{")
                end = raw.rfind("}")
                if start != -1 and end != -1 and end > start:
                    raw = raw[start : end + 1]
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                return {}

            mapping: Dict[str, str] = {}
            for public_key, info in payload.items():
                if not isinstance(public_key, str) or not isinstance(info, dict):
                    continue

                # JSON shows adv_name (human name) and public_key (hex id). Key is also public key.
                # Use names as-is from JSON - they're already clean and don't need normalization
                adv_name = info.get("adv_name") or info.get("name")
                if not isinstance(adv_name, str) or not adv_name.strip():
                    continue

                # Use the name as-is from JSON (just strip whitespace)
                name_clean = adv_name.strip()
                
                # Extract hex ID from public_key - clean it but keep it as hex
                pub_norm = public_key.lstrip("!").lower().strip()
                if not re.fullmatch(r"[a-f0-9]{8,}", pub_norm):
                    continue

                # MeshCore CLI text table displays a short hex node id (e.g., 0b2c2328618f).
                # Your radios accept both the short and full public_key, but we prefer the short
                # to match the device's own displayed destination format.
                dest = pub_norm[:12] if len(pub_norm) >= 12 else pub_norm
                mapping[name_clean] = dest

            # Cache
            self._contacts_cache_ts = now
            self._contacts_cache_name_to_pubkey = mapping

            # Store in DB for persistence across restarts (best effort)
            if mapping:
                try:
                    import database
                    for n, k in mapping.items():
                        database.store_contact(n, k)
                except Exception:
                    pass

            return mapping

        except Exception as e:
            return {}
    
    def _build_meshcli_cmd(self, *args, json_output: bool = False) -> list:
        """
        Build meshcli command with BLE address.
        
        Args:
            *args: Command arguments (e.g., "receive", "send", "node_id", "message")
            json_output: If True, add -j flag for JSON output
            
        Returns:
            List of command arguments for subprocess.run
        """
        if not self.ble_address:
            raise RuntimeError("BLE device not connected. Cannot build meshcli command.")
        
        cmd = ["meshcli", "-a", self.ble_address]
        if json_output:
            cmd.append("-j")
        cmd.extend(args)
        return cmd
    
    def _extract_json_from_output(self, output: str) -> str:
        """
        Extract JSON object from output that may contain non-JSON preamble.
        
        Some meshcli builds may print non-JSON text before the JSON object.
        This method extracts the JSON portion from mixed output.
        
        Args:
            output: Raw output string that may contain JSON
            
        Returns:
            Extracted JSON string, or empty string if no JSON found
        """
        if not output:
            return ""
        
        output = output.strip()
        
        # If already starts with JSON, return as-is
        if output.startswith("{") or output.startswith("["):
            return output
        
        # Try to find JSON object boundaries
        start = output.find("{")
        if start == -1:
            start = output.find("[")
        if start == -1:
            return ""
        
        # Find matching closing brace/bracket
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start, len(output)):
            char = output[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if not in_string:
                if char in ('{', '['):
                    depth += 1
                elif char in ('}', ']'):
                    depth -= 1
                    if depth == 0:
                        return output[start:i+1]
        
        # If we didn't find a complete JSON, try simple approach
        end = output.rfind("}")
        if end == -1:
            end = output.rfind("]")
        if end != -1 and end > start:
            return output[start:end+1]
        
        return ""
    
    def _parse_json_response(self, output: str) -> Optional[Dict]:
        """
        Parse JSON response from meshcli output.
        
        Handles JSON extraction from output (removes preamble if present),
        parses JSON, and returns parsed dict or None on error.
        
        Args:
            output: Raw output string from meshcli command
            
        Returns:
            Parsed JSON dict/list, or None if parsing fails
        """
        if not output:
            return None
        
        try:
            # Extract JSON from output
            json_str = self._extract_json_from_output(output)
            if not json_str:
                # Try parsing the whole output as JSON
                json_str = output.strip()
            
            # Parse JSON
            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError as e:
            return None
        except Exception as e:
            return None
    
    def listen(self) -> Optional[Tuple[str, str]]:
        """
        Polls MeshCore CLI for new messages using recv command with JSON output.
        
        Expected JSON format: {"type": "PRIV", "pubkey_prefix": "0b2c2328618f", "text": "Hi", ...}
        The pubkey_prefix is the hex node ID that should be used as the destination for replies.
        Falls back to text parsing for backward compatibility with older firmware.
        
        Returns:
            Tuple of (sender_node_id, message_text) or None if no message
        """
        try:
            # Use recv command with JSON output
            cmd = self._build_meshcli_cmd("recv", json_output=True)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2.0  # Increased timeout to catch messages
            )
            
            stdout_text = result.stdout.strip() if result.stdout else ""
            stderr_text = result.stderr.strip() if result.stderr else ""
            
            if result.returncode == 0 and stdout_text:
                output = stdout_text
                
                node_id = None
                message = None
                
                # Try JSON format first
                json_response = self._parse_json_response(output)
                if json_response and isinstance(json_response, dict):
                    # Extract pubkey_prefix (hex node ID) and text (message) from JSON
                    # pubkey_prefix is the destination address for replies
                    node_id = json_response.get("pubkey_prefix")
                    message = json_response.get("text")
                    
                    if node_id and message:
                        # pubkey_prefix is already a hex node ID, no lookup needed
                        # Clean it up (remove any ! prefix, ensure lowercase)
                        node_id = node_id.lstrip("!").lower().strip()
                        # Verify it's a valid hex string
                        if re.fullmatch(r'^[a-f0-9]{8,}$', node_id):
                            # Store node ID in friends (use hex node ID)
                            if node_id not in self.friends:
                                self.friends.add(node_id)
                            return (node_id, message)
                        else:
                            node_id = None
                            message = None
                    else:
                        json_response = None
                
                # Fallback to text parsing if JSON parsing failed
                if not node_id or not message:
                    # Parse MeshCore text format: name(hop): message
                    # Example: "Meshagotchi(0): /help" or "t114_fdl(D): Hello"
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
                            # Strip any remaining whitespace
                            node_id = node_id.strip()
                            message = parts[1].strip()
                
                # Track sender locally (MeshCore auto-adds contacts from adverts)
                if node_id and message:
                    # CRITICAL: The node_id extracted from the message is the ADVERT NAME, not the hex node ID
                    # We MUST look up the hex node ID immediately - NEVER use the advert name as a node ID
                    # First, extract the visible name pattern (alphanumeric, dash, underscore, dot)
                    # This avoids corruption from invisible characters
                    name_raw = node_id.strip()
                    # Remove hop indicator if present: "name(hop)" -> "name"
                    name_raw = re.sub(r'\([^)]+\)', '', name_raw).strip()
                    
                    # Extract the actual name using regex - match the pattern of mesh names
                    # This avoids issues with invisible characters corrupting the name
                    name_match = re.search(r'([A-Za-z0-9][A-Za-z0-9_.-]*)', name_raw)
                    if name_match:
                        name_extracted = name_match.group(1)
                    else:
                        # Fallback: just use the raw name
                        name_extracted = name_raw
                    
                    # CRITICAL: Use JSON contacts ONLY - it's clean, structured, and reliable
                    hex_node_id = None
                    
                    try:
                        # Get JSON contacts mapping (clean data from JSON, no text parsing)
                        name_to_pub = self._get_contacts_name_to_pubkey_map(force_refresh=True)  # Force refresh to get latest
                        
                        # Try exact match first (using extracted name)
                        hex_node_id = name_to_pub.get(name_extracted)
                        if not hex_node_id:
                            # Try case-insensitive match
                            for json_name, json_hex in name_to_pub.items():
                                if json_name.lower() == name_extracted.lower():
                                    hex_node_id = json_hex
                                    break
                            
                            # Try partial match (name starts with or contains the extracted name)
                            if not hex_node_id:
                                for json_name, json_hex in name_to_pub.items():
                                    if name_extracted.lower() in json_name.lower() or json_name.lower() in name_extracted.lower():
                                        hex_node_id = json_hex
                                        break
                    except Exception:
                        pass
                    
                    # Final verification and return
                    if hex_node_id and re.fullmatch(r'^[a-fA-F0-9]{8,}$', hex_node_id):
                        # Store node ID in friends (use hex node ID, not name)
                        if hex_node_id not in self.friends:
                            self.friends.add(hex_node_id)
                        # ALWAYS return the hex node ID, never the name
                        return (hex_node_id, message)
                    else:
                        # Return None for node_id to indicate we can't reply
                        return (None, message)
            
            return None
            
        except subprocess.TimeoutExpired:
            # Timeout is normal when no messages are available
            return None
        except FileNotFoundError:
            # MeshCore CLI not found - return None (will be handled in main)
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
        
        # CRITICAL: ALWAYS use hex node ID for sending, NEVER use the advert name
        # If node_id looks like a name (not a hex string), look up the hex node ID
        # Node IDs are hex strings (8+ chars), optionally prefixed with !
        if not re.match(r'^!?[a-fA-F0-9]{8,}$', node_id):
            node_id_actual = self._get_node_id_from_name(node_id)
            if node_id_actual:
                # Verify it's actually a hex node ID
                if re.fullmatch(r'^[a-fA-F0-9]{8,}$', node_id_actual):
                    node_id = node_id_actual
                else:
                    node_id_actual = None
            
            if not node_id_actual:
                # Try direct extraction from contacts list
                node_id_actual = self._extract_node_id_from_contacts_list(node_id)
                if node_id_actual:
                    # Verify it's actually a hex node ID
                    if re.fullmatch(r'^[a-fA-F0-9]{8,}$', node_id_actual):
                        node_id = node_id_actual
                    else:
                        node_id_actual = None
            
            if not node_id_actual:
                return  # Don't queue the message if we can't find hex node ID
        
        # Final verification: ensure node_id is a valid hex string (remove ! prefix if present)
        node_id_clean = node_id.lstrip("!")
        if not re.fullmatch(r'^[a-fA-F0-9]{8,}$', node_id_clean):
            return
        
        # Sanitize message
        sanitized = self._sanitize_message(text)
        
        # Add to queue (with node_id - should be actual node ID now)
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
            # Strip any whitespace from node_id
            node_id = node_id.strip()
            
            # CRITICAL: ALWAYS use hex node ID, not name - look it up if needed
            # If node_id looks like a name (not a hex string), look up the hex node ID
            if not re.match(r'^!?[a-fA-F0-9]{8,}$', node_id):
                node_id_actual = self._get_node_id_from_name(node_id)
                if node_id_actual:
                    # Verify it's actually a hex node ID
                    if not re.fullmatch(r'^[a-fA-F0-9]{8,}$', node_id_actual):
                        node_id_actual = None
                
                if not node_id_actual:
                    # Try direct extraction from contacts list
                    node_id_actual = self._extract_node_id_from_contacts_list(node_id)
                    if node_id_actual:
                        # Verify it's actually a hex node ID
                        if not re.fullmatch(r'^[a-fA-F0-9]{8,}$', node_id_actual):
                            node_id_actual = None
                
                if node_id_actual:
                    node_id = node_id_actual
                else:
                    return  # Skip this message - don't try to send with a name
            
            # Final verification: ensure node_id is a valid hex string (remove ! prefix if present)
            node_id_clean = node_id.lstrip("!")
            if not re.fullmatch(r'^[a-fA-F0-9]{8,}$', node_id_clean):
                return
            
            # Ensure the contact is added before sending
            if node_id not in self.friends:
                self._ensure_contact(node_id)
            
            # Send via MeshCore CLI using msg command with JSON output
            # Format: msg <node_id> <message>
            # CRITICAL: MUST use hex node ID, NEVER use name
            # node_id has already been verified as a valid hex string above
            cmd = self._build_meshcli_cmd("msg", node_id, message, json_output=True)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            stdout_text = result.stdout.strip() if result.stdout else ""
            stderr_text = result.stderr.strip() if result.stderr else ""
            
            # Parse JSON response
            json_response = self._parse_json_response(stdout_text)
            send_success = False
            error_message = None
            
            if json_response:
                # Check for error in JSON response
                if isinstance(json_response, dict):
                    error = json_response.get("error")
                    error_code = json_response.get("error_code")
                    if error or error_code:
                        error_message = error or f"Error code: {error_code}"
                        print(f"[ERROR] JSON error response: {error_message}")
                    elif json_response.get("ok") or "ok" in str(json_response).lower():
                        send_success = True
                    elif "expected_ack" in json_response or "suggested_timeout" in json_response:
                        # Response format: {"type": 0, "expected_ack": "...", "suggested_timeout": ...}
                        # This indicates the message was successfully sent and is waiting for ACK
                        send_success = True
                elif isinstance(json_response, list):
                    # Array response like [{"type":0,"expected_ack":"..."},{"code":"..."}]
                    # This typically indicates success
                    send_success = True
            else:
                # Fallback to text-based error detection if JSON parsing failed
                if result.returncode == 0 and ("unknown" in stdout_text.lower() or "not found" in stdout_text.lower()):
                    error_message = "Unknown destination"
                elif result.returncode == 0 and not ("error" in stdout_text.lower() or "unknown" in stdout_text.lower()):
                    send_success = True
            
            # If failed, try to get node ID from contacts and retry
            if not send_success and error_message:
                # Try to get the actual node ID from the contacts list
                node_id_actual = self._get_node_id_from_name(node_id)
                if node_id_actual and node_id_actual != node_id:
                    # Retry with the actual node ID (try both with and without ! prefix)
                    for try_id in [node_id_actual, f"!{node_id_actual}"]:
                        cmd = self._build_meshcli_cmd("msg", try_id, message, json_output=True)
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=5.0
                        )
                        stdout_text = result.stdout.strip() if result.stdout else ""
                        
                        # Check JSON response for success
                        json_response = self._parse_json_response(stdout_text)
                        if json_response:
                            if isinstance(json_response, dict):
                                if json_response.get("error") or json_response.get("error_code"):
                                    continue  # Still an error, try next
                                elif "expected_ack" in json_response or "suggested_timeout" in json_response:
                                    send_success = True
                                    break
                                else:
                                    send_success = True
                                    break
                            elif isinstance(json_response, list):
                                send_success = True
                                break
                        elif result.returncode == 0 and not ("unknown" in stdout_text.lower() or "not found" in stdout_text.lower()):
                            send_success = True
                            break
                else:
                    # Try to add contact and retry
                    if self._ensure_contact(node_id):
                        # Retry sending
                        cmd = self._build_meshcli_cmd("msg", node_id, message, json_output=True)
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=5.0
                        )
                        stdout_text = result.stdout.strip() if result.stdout else ""
                        
                        # Check JSON response
                        json_response = self._parse_json_response(stdout_text)
                        if json_response:
                            if isinstance(json_response, dict):
                                if json_response.get("error") or json_response.get("error_code"):
                                    # Still an error
                                    pass
                                elif "expected_ack" in json_response or "suggested_timeout" in json_response:
                                    send_success = True
                                elif not (json_response.get("error") or json_response.get("error_code")):
                                    send_success = True
                            elif isinstance(json_response, list):
                                send_success = True
            
            if send_success:
                self.last_send_time = now
                print(f"[MESSAGE SENT] To: '{node_id}', Message: {message[:100]}...")
            else:
                print(f"[ERROR] Failed to send message to '{node_id}': {error_message or stdout_text or stderr_text}")
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
    
    def _format_ascii_art_for_mobile(self, text: str) -> str:
        """
        Format ASCII art for better mobile display.
        Left-aligns the art to work with mobile apps that strip leading spaces
        or use proportional fonts, while preserving internal spacing for alignment.
        
        Args:
            text: ASCII art text with potential leading spaces
        
        Returns:
            Formatted ASCII art optimized for mobile display
        """
        lines = text.split('\n')
        
        # Remove completely empty lines at start/end only
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        
        if not lines:
            return text
        
        # Find minimum leading spaces across all non-empty lines
        # This allows us to left-align while preserving relative positioning
        non_empty_lines = [line for line in lines if line.strip()]
        if not non_empty_lines:
            return '\n'.join(lines)
        
        min_leading = min(len(line) - len(line.lstrip()) for line in non_empty_lines)
        
        # Left-align by removing the minimum leading spaces from all lines
        # This preserves the relative alignment between lines
        formatted_lines = []
        for line in lines:
            if line.strip():
                # Remove minimum leading spaces to left-align
                # Preserve trailing spaces for internal alignment
                formatted_line = line[min_leading:] if min_leading > 0 else line
                formatted_lines.append(formatted_line)
            else:
                # Keep empty lines as-is
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _sanitize_message(self, text: str) -> str:
        """
        Remove excessive whitespace and ensure message is under max length.
        Formats ASCII art for mobile display compatibility.
        
        Args:
            text: Original message text
        
        Returns:
            Sanitized message
        """
        # Detect if this is ASCII art (contains ASCII art patterns and multiple lines)
        lines = text.split('\n')
        is_ascii_art = False
        
        if len(lines) >= 3:  # ASCII art typically has multiple lines
            # Check for ASCII art patterns: brackets, pipes, slashes, etc.
            ascii_art_chars = set('|[](){}<>/\\=+-*#@$%&~^')
            ascii_line_count = 0
            for line in lines:
                if any(c in ascii_art_chars for c in line):
                    ascii_line_count += 1
            
            # If most lines contain ASCII art characters, treat as ASCII art
            if ascii_line_count >= len(lines) * 0.5:  # At least 50% of lines have ASCII chars
                is_ascii_art = True
        
        if is_ascii_art:
            # For ASCII art: format for mobile display (left-align, preserve relative spacing)
            sanitized = self._format_ascii_art_for_mobile(text)
        else:
            # For regular text: strip trailing whitespace from each line
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
        try:
            # Step 1: Get radio version information
            version_info = self.get_radio_version()
            if version_info:
                self.radio_version = version_info
            
            # Step 2: Get radio link information
            link_info = self.get_radio_link_info()
            if link_info:
                self.radio_info = link_info
            
            # Step 3: Configure radio to USA/Canada preset
            if self.configure_usa_canada_preset():
                # Step 4: Set radio name to Meshagotchi
                self.set_radio_name("Meshagotchi")
                
                # Step 5: Flood Advert to announce availability
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
        Get radio firmware version information using JSON output.
        
        Expected JSON format: {"version": "1.3.2"} or similar
        
        Returns:
            Version string or None if failed
        """
        try:
            # Try various MeshCore CLI commands to get version with JSON
            commands = [
                self._build_meshcli_cmd("-v", json_output=True),
                self._build_meshcli_cmd("info", json_output=True),
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
                        output = result.stdout.strip()
                        # Try JSON parsing first
                        json_response = self._parse_json_response(output)
                        if json_response and isinstance(json_response, dict):
                            version = json_response.get("version") or json_response.get("ver")
                            if version:
                                return str(version)
                        # Fallback to raw output if JSON parsing failed
                        return output
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            # Fallback to non-JSON commands
            commands_text = [
                self._build_meshcli_cmd("-v"),
                self._build_meshcli_cmd("info"),
            ]
            
            for cmd in commands_text:
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
    
    def get_radio_link_info(self) -> Optional[Dict]:
        """
        Get radio link information (frequency, bandwidth, etc.) using JSON output.
        Uses infos command which returns all node information including radio settings.
        
        Expected JSON format: {"radio_freq": 910.525, "radio_bw": 62.5, "radio_sf": 7, "radio_cr": 5, "tx_power": 22, ...}
        
        Returns:
            Parsed JSON dict with radio settings, or None if failed
        """
        try:
            # Prioritize JSON output for structured data
            result = subprocess.run(
                self._build_meshcli_cmd("infos", json_output=True),
                capture_output=True,
                text=True,
                timeout=5.0  # Increased timeout
            )
            
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                json_response = self._parse_json_response(output)
                if json_response and isinstance(json_response, dict):
                    return json_response
                # If JSON parsing failed, return raw output for backward compatibility
                return output
            
            # Fallback to non-JSON output if JSON didn't work
            try:
                result = subprocess.run(
                    self._build_meshcli_cmd("infos"),
                    capture_output=True,
                    text=True,
                    timeout=5.0  # Increased timeout
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    output = result.stdout.strip()
                    # Try to parse as JSON even if -j wasn't used
                    json_response = self._parse_json_response(output)
                    if json_response and isinstance(json_response, dict):
                        return json_response
                    return output
            except subprocess.TimeoutExpired:
                # Timeout is okay
                pass
            except Exception:
                # Error is okay, we'll return None
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
            combined_commands = [
                ("set radio", self._build_meshcli_cmd("set", "radio", combined_radio_command, json_output=True)),
                ("set-radio", self._build_meshcli_cmd("set-radio", combined_radio_command, json_output=True)),
                ("radio", self._build_meshcli_cmd("radio", combined_radio_command, json_output=True)),
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
                    stdout_text = result.stdout.strip() if result.stdout else ""
                    stderr_text = result.stderr.strip() if result.stderr else ""
                    
                    # Parse JSON response for error detection
                    json_response = self._parse_json_response(stdout_text)
                    has_error = False
                    
                    if json_response and isinstance(json_response, dict):
                        # Check for error in JSON response
                        if json_response.get("error") or json_response.get("error_code"):
                            has_error = True
                            continue
                    
                    # Fallback to text-based error detection if JSON parsing failed
                    if not json_response:
                        output = stdout_text + stderr_text
                        if "EventType.ERROR" in output or "command_error" in output:
                            continue
                    
                    if result.returncode == 0:
                        if not has_error and not (stderr_text and ("error" in stderr_text.lower() or "unknown" in stderr_text.lower())):
                            combined_success = True
                            time.sleep(1.5)  # Wait for settings to apply
                            break
                except Exception:
                    continue
            
            # If combined command worked, verify it applied correctly
            if combined_success:
                time.sleep(1.0)
                current_info = self.get_radio_link_info()
                if current_info:
                    # Handle both dict (JSON) and string (fallback) return types
                    if isinstance(current_info, dict):
                        config = current_info
                    else:
                        # Fallback: try to parse as JSON string
                        import json
                        try:
                            config = json.loads(current_info) if isinstance(current_info, str) else current_info
                        except:
                            config = None
                    
                    if config and isinstance(config, dict):
                        freq_ok = abs(config.get('radio_freq', 0) - freq_mhz) < 0.1
                        bw_ok = abs(config.get('radio_bw', 0) - bw_khz) < 1.0
                        sf_ok = config.get('radio_sf', 0) == preset['spreading_factor']
                        if freq_ok and bw_ok and sf_ok:
                            return True
            
            # Try preset/region commands if combined command didn't work
            preset_commands = [
                ("preset", self._build_meshcli_cmd("preset", "usa", json_output=True)),
                ("preset", self._build_meshcli_cmd("preset", "usa-canada", json_output=True)),
                ("preset", self._build_meshcli_cmd("preset", "US", json_output=True)),
                ("region", self._build_meshcli_cmd("region", "usa", json_output=True)),
                ("region", self._build_meshcli_cmd("region", "US", json_output=True)),
                ("set-preset", self._build_meshcli_cmd("set-preset", "usa", json_output=True)),
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
                    stdout_text = result.stdout.strip() if result.stdout else ""
                    stderr_text = result.stderr.strip() if result.stderr else ""
                    
                    # Parse JSON response for error detection
                    json_response = self._parse_json_response(stdout_text)
                    has_error = False
                    
                    if json_response and isinstance(json_response, dict):
                        # Check for error in JSON response
                        if json_response.get("error") or json_response.get("error_code"):
                            has_error = True
                            continue
                    
                    # Fallback to text-based error detection if JSON parsing failed
                    if not json_response:
                        output = stdout_text + stderr_text
                        if "EventType.ERROR" in output or "command_error" in output:
                            continue
                    
                    if result.returncode == 0:
                        if not has_error and not (stderr_text and ("error" in stderr_text.lower() or "unknown" in stderr_text.lower())):
                            preset_success = True
                            time.sleep(1.0)  # Wait for preset to apply
                            break
                except Exception:
                    continue
            
            # If preset worked, verify it applied correctly
            if preset_success:
                time.sleep(1.0)
                current_info = self.get_radio_link_info()
                if current_info:
                    # Handle both dict (JSON) and string (fallback) return types
                    if isinstance(current_info, dict):
                        config = current_info
                    else:
                        import json
                        try:
                            config = json.loads(current_info) if isinstance(current_info, str) else current_info
                        except:
                            config = None
                    
                    if config and isinstance(config, dict):
                        freq_ok = abs(config.get('radio_freq', 0) - freq_mhz) < 0.1
                        bw_ok = abs(config.get('radio_bw', 0) - bw_khz) < 1.0
                        sf_ok = config.get('radio_sf', 0) == preset['spreading_factor']
                        if freq_ok and bw_ok and sf_ok:
                            print("  Preset applied successfully!")
                            return True
            
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
                    
                    # Try multiple command patterns with JSON output
                    commands_to_try = [
                        ("set", self._build_meshcli_cmd("set", param_name, param_value, json_output=True)),
                        ("config", self._build_meshcli_cmd("config", param_name, param_value, json_output=True)),
                        ("set-param", self._build_meshcli_cmd("set-" + param_name, param_value, json_output=True)),
                        ("direct", self._build_meshcli_cmd(param_name, param_value, json_output=True)),
                    ]
                    
                    for cmd_name, cmd in commands_to_try:
                        try:
                            result = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                timeout=5.0
                            )
                            
                            stdout_text = result.stdout.strip() if result.stdout else ""
                            stderr_text = result.stderr.strip() if result.stderr else ""
                            
                            # Parse JSON response for error detection
                            json_response = self._parse_json_response(stdout_text)
                            has_error = False
                            error_code = None
                            
                            if json_response and isinstance(json_response, dict):
                                # Check for error in JSON response
                                error = json_response.get("error")
                                error_code = json_response.get("error_code")
                                if error or error_code:
                                    has_error = True
                                    error_code_str = str(error_code) if error_code else "unknown"
                                    last_error = f"Command rejected by radio (error: {error}, error_code: {error_code_str})"
                                    # If error_code 6, commands are not supported
                                    if error_code == 6:
                                        commands_not_supported = True
                                    last_cmd_name = cmd_name
                                    last_value_used = f"{param_value} {value_unit}".strip()
                                    continue
                            else:
                                # Fallback to text-based error detection if JSON parsing failed
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
                                # Check for error messages in stderr (fallback)
                                if result.stderr and ("error" in result.stderr.lower() or "unknown" in result.stderr.lower() or "command_error" in result.stderr.lower()):
                                    last_error = result.stderr.strip()
                                    last_cmd_name = cmd_name
                                    last_value_used = f"{param_value} {value_unit}".strip()
                                    continue
                                
                                # Check if stdout indicates success or failure (fallback for non-JSON)
                                if not json_response and stdout_text and ("unknown" in stdout_text.lower() or "invalid" in stdout_text.lower() or "not found" in stdout_text.lower() or "command_error" in stdout_text.lower()):
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
                                        self._build_meshcli_cmd("save", json_output=True),
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
                    self._build_meshcli_cmd("save", json_output=True),
                    self._build_meshcli_cmd("commit", json_output=True),
                    self._build_meshcli_cmd("write", json_output=True),
                    self._build_meshcli_cmd("save-config", json_output=True),
                    self._build_meshcli_cmd("write-config", json_output=True),
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
                            stdout_text = result.stdout.strip() if result.stdout else ""
                            # Check JSON response for success
                            json_response = self._parse_json_response(stdout_text)
                            if json_response:
                                if isinstance(json_response, dict):
                                    if not (json_response.get("error") or json_response.get("error_code")):
                                        print("  Configuration saved")
                                        break
                                else:
                                    print("  Configuration saved")
                                    break
                            elif not (result.stderr and ("error" in result.stderr.lower() or "unknown" in result.stderr.lower())):
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
                # Handle both dict (JSON) and string (fallback) return types
                if isinstance(current_info, dict):
                    config = current_info
                else:
                    import json
                    try:
                        # Try to parse as JSON string
                        config = json.loads(current_info) if isinstance(current_info, str) else current_info
                    except:
                        config = None
                
                if config and isinstance(config, dict):
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
                else:
                    # If not dict, try to extract values from text output
                    if isinstance(current_info, str):
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
            # Try various MeshCore CLI commands to set name with JSON output
            # Common patterns: set-name, name, setname, node-name
            # Also try: set name <name> (similar to set radio format)
            name_commands = [
                ("set name", self._build_meshcli_cmd("set", "name", name, json_output=True)),
                ("set-name", self._build_meshcli_cmd("set-name", name, json_output=True)),
                ("name", self._build_meshcli_cmd("name", name, json_output=True)),
                ("setname", self._build_meshcli_cmd("setname", name, json_output=True)),
                ("node-name", self._build_meshcli_cmd("node-name", name, json_output=True)),
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
                    
                    # Parse JSON response for error detection
                    json_response = self._parse_json_response(stdout_text)
                    has_error = False
                    
                    if json_response and isinstance(json_response, dict):
                        # Check for error in JSON response
                        if json_response.get("error") or json_response.get("error_code"):
                            has_error = True
                            continue
                    
                    # Fallback to text-based error detection if JSON parsing failed
                    if not json_response:
                        if "EventType.ERROR" in stdout_text or "EventType.ERROR" in stderr_text:
                            continue
                    
                    if result.returncode == 0:
                        # Check for error messages (fallback)
                        if has_error or (stderr_text and ("error" in stderr_text.lower() or "unknown" in stderr_text.lower() or "command_error" in stderr_text.lower())):
                            continue
                        if not json_response and stdout_text and ("error" in stdout_text.lower() or "unknown" in stdout_text.lower() or "command_error" in stdout_text.lower()):
                            continue
                        
                        # Allow time for name to be set
                        time.sleep(0.5)
                        
                        # Verify the name was actually set
                        current_info = self.get_radio_link_info()
                        if current_info:
                            # Handle both dict (JSON) and string (fallback) return types
                            if isinstance(current_info, dict):
                                config = current_info
                            else:
                                import json
                                try:
                                    config = json.loads(current_info) if isinstance(current_info, str) else current_info
                                except:
                                    config = None
                            
                            if config and isinstance(config, dict):
                                current_name = config.get('name', '')
                                if current_name == name:
                                    print(f"  ✓ Radio name set to '{name}' using '{cmd_name}' command")
                                    return True
                                else:
                                    # Name command was accepted but didn't change the name
                                    continue
                            else:
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
                ("config name", self._build_meshcli_cmd("config", "name", name, json_output=True)),
                ("set-config name", self._build_meshcli_cmd("set-config", "name", name, json_output=True)),
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
                    
                    # Parse JSON response for error detection
                    json_response = self._parse_json_response(stdout_text)
                    has_error = False
                    
                    if json_response and isinstance(json_response, dict):
                        # Check for error in JSON response
                        if json_response.get("error") or json_response.get("error_code"):
                            has_error = True
                            continue
                    
                    # Fallback to text-based error detection if JSON parsing failed
                    if not json_response:
                        if "EventType.ERROR" in stdout_text or "EventType.ERROR" in stderr_text:
                            continue
                    
                    if result.returncode == 0:
                        if has_error or (stderr_text and ("error" in stderr_text.lower() or "unknown" in stderr_text.lower() or "command_error" in stderr_text.lower())):
                            continue
                        if not json_response and stdout_text and ("error" in stdout_text.lower() or "unknown" in stdout_text.lower() or "command_error" in stdout_text.lower()):
                            continue
                        
                        time.sleep(0.5)
                        
                        # Verify the name was actually set
                        current_info = self.get_radio_link_info()
                        if current_info:
                            # Handle both dict (JSON) and string (fallback) return types
                            if isinstance(current_info, dict):
                                config = current_info
                            else:
                                import json
                                try:
                                    config = json.loads(current_info) if isinstance(current_info, str) else current_info
                                except:
                                    config = None
                            
                            if config and isinstance(config, dict):
                                current_name = config.get('name', '')
                                if current_name == name:
                                    print(f"  ✓ Radio name set to '{name}' using '{cmd_name}' command")
                                    return True
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
    
    def get_node_card(self) -> Optional[Dict]:
        """
        Get the node card information (node URI/identity) using JSON output.
        Uses card command which exports the node URI.
        
        Expected JSON format: {"card": "meshcore://..."} or similar
        
        Returns:
            Parsed JSON dict with node card info, or None if failed
        """
        try:
            # Use card command with JSON output
            result = subprocess.run(
                self._build_meshcli_cmd("card", json_output=True),
                capture_output=True,
                text=True,
                timeout=3.0
            )
            
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                json_response = self._parse_json_response(output)
                if json_response and isinstance(json_response, dict):
                    return json_response
                # Fallback: return raw output if JSON parsing failed
                return output
            
            return None
            
        except Exception as e:
            print(f"Error getting node card: {e}")
            return None
    
    def get_node_infos(self) -> Optional[Dict]:
        """
        Get node infos (detailed node information) using JSON output.
        Uses infos command which returns all node information.
        
        Expected JSON format: {"radio_freq": 910.525, "radio_bw": 62.5, "name": "...", ...}
        
        Returns:
            Parsed JSON dict with node information, or None if failed
        """
        try:
            # Use infos command with JSON output
            result = subprocess.run(
                self._build_meshcli_cmd("infos", json_output=True),
                capture_output=True,
                text=True,
                timeout=3.0
            )
            
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                json_response = self._parse_json_response(output)
                if json_response and isinstance(json_response, dict):
                    return json_response
                # Fallback: return raw output if JSON parsing failed
                return output
            
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
            # First try floodadv command (most efficient) with JSON output
            try:
                result = subprocess.run(
                    self._build_meshcli_cmd("floodadv", json_output=True),
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                if result.returncode == 0:
                    stdout_text = result.stdout.strip() if result.stdout else ""
                    json_response = self._parse_json_response(stdout_text)
                    # Check JSON response for success
                    if json_response:
                        if isinstance(json_response, dict):
                            if not (json_response.get("error") or json_response.get("error_code")):
                                print(f"  Flood advert sent (using floodadv command)")
                                return
                        else:
                            print(f"  Flood advert sent (using floodadv command)")
                            return
                    else:
                        # Fallback: assume success if return code is 0
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
                        self._build_meshcli_cmd("scope", "", json_output=True),  # Empty scope might mean local/zero-hop
                        capture_output=True,
                        text=True,
                        timeout=2.0
                    )
                except:
                    pass  # Scope setting is optional
            
            # Send multiple adverts with JSON output
            success_count = 0
            for i in range(count):
                try:
                    result = subprocess.run(
                        self._build_meshcli_cmd("advert", json_output=True),
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    if result.returncode == 0:
                        stdout_text = result.stdout.strip() if result.stdout else ""
                        json_response = self._parse_json_response(stdout_text)
                        # Check JSON response for success
                        if json_response:
                            if isinstance(json_response, dict):
                                if not (json_response.get("error") or json_response.get("error_code")):
                                    success_count += 1
                                    print(f"  Advert {i+1}/{count} sent")
                            else:
                                success_count += 1
                                print(f"  Advert {i+1}/{count} sent")
                        else:
                            # Fallback: assume success if return code is 0
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
            # Try to add contact using various commands with JSON output
            add_commands = [
                self._build_meshcli_cmd("add", node_id, json_output=True),
                self._build_meshcli_cmd("contact", "add", node_id, json_output=True),
                self._build_meshcli_cmd("friend", "add", node_id, json_output=True),
            ]
            
            for cmd in add_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    stdout_text = result.stdout.strip() if result.stdout else ""
                    stderr_text = result.stderr.strip() if result.stderr else ""
                    
                    # Parse JSON response for success/failure
                    json_response = self._parse_json_response(stdout_text)
                    success = False
                    
                    if json_response:
                        if isinstance(json_response, dict):
                            if not (json_response.get("error") or json_response.get("error_code")):
                                success = True
                        else:
                            success = True
                    elif result.returncode == 0:
                        # Fallback: assume success if return code is 0 and no error in stderr
                        if not (stderr_text and ("error" in stderr_text.lower() or "unknown" in stderr_text.lower())):
                            success = True
                    
                    if success:
                        if node_id not in self.friends:
                            self.friends.add(node_id)
                        return True
                except Exception:
                    continue
            
            # If add commands don't work, just track locally
            if node_id not in self.friends:
                self.friends.add(node_id)
            return True
            
        except Exception:
            return False
    
    def _extract_node_id_from_contacts_list(self, name: str) -> Optional[str]:
        """
        Extract hex node ID from JSON contacts only.
        This uses JSON contacts command which provides clean, structured data.
        
        Args:
            name: Node name to look up
            
        Returns:
            Hex node ID if found, None otherwise
        """
        if not name:
            return None
        
        # Extract visible name pattern
        name_match = re.search(r'([A-Za-z0-9][A-Za-z0-9_.-]*)', name)
        name_extracted = name_match.group(1) if name_match else name.strip()
        
        # Use JSON contacts ONLY - clean and reliable
        try:
            name_to_pub = self._get_contacts_name_to_pubkey_map(force_refresh=False)
            
            # Try exact match
            if name_extracted in name_to_pub:
                node_id = name_to_pub[name_extracted]
                return node_id
            
            # Try case-insensitive match
            for json_name, json_hex in name_to_pub.items():
                if json_name.lower() == name_extracted.lower():
                    return json_hex
            
            # Try partial match
            for json_name, json_hex in name_to_pub.items():
                if name_extracted.lower() in json_name.lower() or json_name.lower() in name_extracted.lower():
                    return json_hex
        except Exception:
            pass
        
        return None
    
    def _get_node_id_from_name(self, name: str) -> Optional[str]:
        """
        Get the actual hex node ID from a name using JSON contacts only.
        
        Args:
            name: Node name to look up
            
        Returns:
            Hex node ID if found, None otherwise
        """
        if not name:
            return None

        # If it already looks like a hex node ID, just return it (cleaned)
        if re.fullmatch(r"!?[a-fA-F0-9]{8,}", name):
            return name.lstrip("!").lower()

        # Extract visible name pattern (alphanumeric, dash, underscore, dot)
        name_match = re.search(r'([A-Za-z0-9][A-Za-z0-9_.-]*)', name)
        name_extracted = name_match.group(1) if name_match else name.strip()

        # Use JSON contacts mapping ONLY - clean and reliable
        try:
            name_to_pub = self._get_contacts_name_to_pubkey_map(force_refresh=False)
            
            # Try exact match first
            mapped = name_to_pub.get(name_extracted)
            if mapped:
                return mapped
            
            # Try case-insensitive match
            for json_name, json_hex in name_to_pub.items():
                if json_name.lower() == name_extracted.lower():
                    return json_hex
            
            # Try partial match
            for json_name, json_hex in name_to_pub.items():
                if name_extracted.lower() in json_name.lower() or json_name.lower() in name_extracted.lower():
                    return json_hex
        except Exception:
            pass
        
        # Fallback: check database
        try:
            import database
            node_id = database.get_node_id_by_name(name_extracted)
            if node_id:
                node_id_clean = node_id.lstrip("!").lower().strip()
                if re.fullmatch(r'^[a-f0-9]{8,}$', node_id_clean):
                    return node_id_clean
        except Exception:
            pass
        
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
            # First, use node_discover to discover nodes with JSON output
            # Format: node_discover <filter> where filter can be type (1=client, 2=repeater, etc.)
            # Empty filter discovers all nodes
            discover_commands = [
                self._build_meshcli_cmd("node_discover", json_output=True),  # Discover all nodes
                self._build_meshcli_cmd("node_discover", "1", json_output=True),  # Discover clients only
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
                        
                        # Try to parse JSON response first
                        json_response = self._parse_json_response(output)
                        all_nodes = set()
                        
                        if json_response:
                            if isinstance(json_response, dict):
                                # Expected format: {"nodes": [{"name": "...", "public_key": "...", ...}]}
                                nodes_list = json_response.get("nodes", [])
                                if isinstance(nodes_list, list):
                                    for node_info in nodes_list:
                                        if isinstance(node_info, dict):
                                            # Extract name and public_key
                                            name = node_info.get("name") or node_info.get("adv_name")
                                            pub_key = node_info.get("public_key") or node_info.get("pub_key")
                                            if name:
                                                all_nodes.add(name)
                                            if pub_key:
                                                # Use short hex ID
                                                pub_clean = pub_key.lstrip("!").lower().strip()
                                                if re.fullmatch(r'[a-f0-9]{8,}', pub_clean):
                                                    hex_id = pub_clean[:12] if len(pub_clean) >= 12 else pub_clean
                                                    all_nodes.add(hex_id)
                            elif isinstance(json_response, list):
                                # If response is a list of nodes
                                for node_info in json_response:
                                    if isinstance(node_info, dict):
                                        name = node_info.get("name") or node_info.get("adv_name")
                                        pub_key = node_info.get("public_key") or node_info.get("pub_key")
                                        if name:
                                            all_nodes.add(name)
                                        if pub_key:
                                            pub_clean = pub_key.lstrip("!").lower().strip()
                                            if re.fullmatch(r'[a-f0-9]{8,}', pub_clean):
                                                hex_id = pub_clean[:12] if len(pub_clean) >= 12 else pub_clean
                                                all_nodes.add(hex_id)
                        
                        # Fallback to text parsing if JSON parsing failed
                        if not all_nodes:
                            # Parse discovered nodes from text output
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
            
            # Also sync with MeshCore's contact list using JSON
            # This ensures we're tracking nodes that MeshCore already knows about
            # This is the PRIMARY source for name -> node_id mappings
            try:
                # Use JSON contacts - clean and reliable
                name_to_pub = self._get_contacts_name_to_pubkey_map(force_refresh=True)
                
                for name, hex_id in name_to_pub.items():
                    try:
                        import database
                        database.store_contact(name, hex_id)
                        # Also add to friends set (use hex node ID, not name)
                        if hex_id not in self.friends:
                            self.friends.add(hex_id)
                    except Exception:
                        pass
                    
            except Exception:
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
