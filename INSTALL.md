# MeshAgotchi Installation Guide

Complete installation instructions for MeshAgotchi on a fresh Raspberry Pi.

## Hardware Requirements

- **Raspberry Pi**: Any model (Pi 3, Pi 4, Pi Zero 2W, or newer recommended)
- **MicroSD Card**: Minimum 8GB (16GB+ recommended)
- **Power Supply**: Official Raspberry Pi power adapter (5V, 2.5A+ for Pi 4)
- **Heltec V3 LoRa Radio**: Connected via BLE (Bluetooth Low Energy)
- **Network**: Ethernet cable or Wi-Fi for initial setup

## Step 1: Install Raspberry Pi OS

### Recommended Version

**Raspberry Pi OS (64-bit) - Bookworm or newer**

As of 2025, use **Raspberry Pi OS (64-bit)** based on Debian Bookworm or Trixie. This provides:
- Python 3.11+ support
- Better BLE (Bluetooth Low Energy) support
- Improved performance

### Installation Steps

1. **Download Raspberry Pi Imager**
   - Visit: https://www.raspberrypi.com/software/
   - Download Raspberry Pi Imager for your computer (Windows/Mac/Linux)

2. **Flash Raspberry Pi OS**
   - Insert microSD card into your computer
   - Open Raspberry Pi Imager
   - Click "Choose OS" → Select "Raspberry Pi OS (64-bit)"
   - Click "Choose Storage" → Select your microSD card
   - **Important**: Click the gear icon (⚙️) or press `Ctrl+Shift+X` for advanced options:
     - ✅ Enable SSH
     - ✅ Set username and password (remember these!)
     - ✅ Configure Wi-Fi (if using wireless)
     - ✅ Set locale settings
   - Click "Write" and wait for completion

3. **Boot Raspberry Pi**
   - Insert microSD card into Raspberry Pi
   - Connect power supply
   - Wait for boot (LED should stop blinking)
   - If using SSH, note the IP address (check router or use `hostname -I`)

## Step 2: Initial System Setup

### Connect to Raspberry Pi

**Option A: Direct Connection**
- Connect monitor, keyboard, and mouse
- Log in with your username and password

**Option B: SSH (Recommended)**
```bash
ssh meshagotchi@raspberry-pi-ip-address
# Replace 'raspberry-pi-ip-address' with your Pi's IP
```

### Update System

```bash
# Update package lists
sudo apt update

# Upgrade all packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y git python3 python3-pip python3-venv

# Reboot to ensure all updates are applied
sudo reboot
```

Wait for reboot, then reconnect via SSH or direct connection.

## Step 3: Install MeshCore CLI

MeshAgotchi requires the MeshCore CLI to communicate via LoRa radio.

### Install MeshCore CLI

```bash
# Clone MeshCore CLI repository
cd ~
git clone https://github.com/meshcore-dev/meshcore-cli.git
cd meshcore-cli

# Create a virtual environment (required for modern Raspberry Pi OS)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies and meshcore-cli
pip install meshcore
pip install .

# Verify installation
which meshcli
meshcli -v
```

### Make meshcli Available System-Wide

To make the `meshcli` command available without activating the virtual environment:

```bash
# Create ~/.local/bin directory if it doesn't exist
mkdir -p ~/.local/bin

# Add ~/.local/bin to PATH (if not already there)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Create symlink from venv to ~/.local/bin
ln -s ~/meshcore-cli/venv/bin/meshcli ~/.local/bin/meshcli

# Verify it works
which meshcli
meshcli -v
```

**Note**: The MeshCore CLI command is `meshcli` (not `meshcore`). If installation instructions differ, follow the official documentation at https://github.com/meshcore-dev/meshcore-cli

### Verify Bluetooth Support

```bash
# Check if Bluetooth is available
bluetoothctl show

# If Bluetooth is not available, install Bluetooth packages:
sudo apt install -y bluez bluez-tools

# Enable Bluetooth service
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Verify Bluetooth is running
sudo systemctl status bluetooth
```

## Step 4: Install MeshAgotchi

### Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone MeshAgotchi repository
git clone https://github.com/datton/Meshagotchi.git
cd Meshagotchi
```

### Verify Python Version

```bash
# Check Python version (should be 3.10+)
python3 --version

# Should output: Python 3.10.x or higher
```

### Install Dependencies

MeshAgotchi requires one external package for BLE scanning: **Bleak**

#### Option 1: Install with Virtual Environment (Recommended)

```bash
# Navigate to MeshAgotchi directory
cd ~/Meshagotchi

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Verify you're using the venv's pip (should show path to venv/bin/pip)
which pip
# Should output: /home/meshagotchi/Meshagotchi/venv/bin/pip

# If it shows /usr/bin/pip, the venv isn't activated properly
# Try: source venv/bin/activate again

# Upgrade pip (recommended)
python3 -m pip install --upgrade pip

# Install Bleak using python3 -m pip (more reliable)
python3 -m pip install bleak

# Or install from requirements file
python3 -m pip install -r requirements.txt

# Verify installation
python3 -c "import bleak; print('Bleak installed successfully')"

# Deactivate virtual environment when done (optional)
# deactivate
```

**Troubleshooting venv activation:**
If you get "externally-managed-environment" error even in venv:
```bash
# Make sure venv is activated (you should see (venv) in prompt)
source venv/bin/activate

# Verify which pip you're using
which pip
which python3

# Both should point to venv/bin/ directory

# Use python3 -m pip instead of just pip
python3 -m pip install bleak
```

**To run MeshAgotchi with the virtual environment:**
```bash
# Activate the virtual environment first
source venv/bin/activate

# Then run MeshAgotchi
python3 main.py

# The virtual environment will remain active in your current terminal session
```

#### Option 2: Install System-Wide (Alternative)

```bash
# Install Bleak system-wide (requires sudo)
sudo pip3 install bleak

# Or install from requirements file
sudo pip3 install -r requirements.txt
```

**Note**: Bleak is the modern standard for BLE operations on Linux/Raspberry Pi. If Bleak is not installed, MeshAgotchi will fall back to using `meshcli -l` or `bluetoothctl` for device scanning, but Bleak is recommended for better reliability.

**For systemd service**: If running as a systemd service, you'll need to either:
- Install Bleak system-wide (Option 2), or
- Modify the service file to activate the virtual environment before running

### Test Installation

```bash
# Test genetics demo
python3 genetics.py

# Test database initialization
python3 database.py

# Verify all modules import correctly
python3 -c "import genetics; import database; import mesh_interface; import game_engine; import main; print('All imports successful')"
```

## Step 5: Configure MeshCore CLI

### Verify Heltec V3 Connection

```bash
# Scan for BLE MeshCore devices
meshcli -l

# This will list available BLE devices with their addresses and names
# Example output:
# C2:2B:A1:D5:3E:B6  MeshCore-Device-Name

# Test connection to a specific BLE device
# Replace C2:2B:A1:D5:3E:B6 with your device's BLE address
meshcli -a C2:2B:A1:D5:3E:B6 infos

# Get version info
meshcli -a C2:2B:A1:D5:3E:B6 -v
```

**Note**: The `-a` flag specifies the BLE address. MeshAgotchi will handle device selection and connection automatically on first run.

## Step 6: Run MeshAgotchi

### Manual Start (Testing)

```bash
cd ~/Meshagotchi

# Run MeshAgotchi (will prompt for BLE device selection on first run)
python3 main.py
```

**First Run**: On first run, MeshAgotchi will:
1. Scan for available BLE MeshCore devices
2. Display a numbered list for you to select your device
3. Prompt for the BLE pairing code
4. Connect and store the device info for future use

**Subsequent Runs**: Will automatically connect to the stored BLE device.

You should see:
```
Initializing MeshAgotchi...
Scanning for BLE devices...
Available BLE devices:
  1 - MeshCore-Device-Name (C2:2B:A1:D5:3E:B6)

Select device number (or 'q' to quit): 1

Selected device: MeshCore-Device-Name (C2:2B:A1:D5:3E:B6)
Enter BLE pairing code (or press Enter if not required): 123456
Successfully connected to BLE device: MeshCore-Device-Name (C2:2B:A1:D5:3E:B6)
Database initialized.
MeshHandler initialized.
GameEngine initialized.
MeshAgotchi daemon ready!
Listening for messages via MeshCore CLI...
Press Ctrl+C to stop.
```

### Test Commands

From another device with MeshCore Mobile App:
- Send `/help` to the Raspberry Pi's Node ID
- You should receive a response with available commands

## Step 7: Set Up as System Service (Optional but Recommended)

To run MeshAgotchi automatically on boot:

### Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/meshagotchi.service
```

Add the following content (adjust paths as needed):

**If using virtual environment**, use this service file:

```ini
[Unit]
Description=MeshAgotchi Virtual Pet Game Daemon
After=network.target

[Service]
Type=simple
User=meshogotchi
WorkingDirectory=/home/meshagotchi/Meshagotchi
ExecStart=/home/meshagotchi/Meshagotchi/venv/bin/python3 /home/meshagotchi/Meshagotchi/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**If using system-wide installation**, use this service file:

```ini
[Unit]
Description=MeshAgotchi Virtual Pet Game Daemon
After=network.target

[Service]
Type=simple
User=meshogotchi
WorkingDirectory=/home/meshagotchi/Meshagotchi
ExecStart=/usr/bin/python3 /home/meshagotchi/Meshagotchi/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable meshagotchi.service

# Start service now
sudo systemctl start meshagotchi.service

# Check status
sudo systemctl status meshagotchi.service
```

### Service Management Commands

```bash
# View logs
sudo journalctl -u meshagotchi.service -f

# Stop service
sudo systemctl stop meshagotchi.service

# Restart service
sudo systemctl restart meshagotchi.service

# Disable auto-start on boot
sudo systemctl disable meshagotchi.service
```

## Step 8: Verify Installation

### Check Database

```bash
cd ~/Meshagotchi
ls -lh meshogotchi.db
# Should show database file exists
```

### Test Game Commands

Using MeshCore Mobile App, send commands to your Pi's Node ID:
- `/help` - Should return command list
- `/hatch` - Should create a new pet
- `/stats` - Should show pet status and ASCII art

### Monitor Logs

```bash
# If running as service
sudo journalctl -u meshagotchi.service -f

# If running manually, output appears in terminal
```

## Troubleshooting

### MeshCore CLI Not Found

```bash
# Check if meshcli is in PATH
which meshcli

# If not found, check installation
cd ~/meshcore-cli
source venv/bin/activate
which meshcli

# If found in venv but not in PATH, create symlink:
mkdir -p ~/.local/bin
ln -s ~/meshcore-cli/venv/bin/meshcli ~/.local/bin/meshcli
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### BLE Connection Issues

```bash
# Check Bluetooth is enabled
bluetoothctl show

# Scan for devices manually
meshcli -l

# If device not found:
# 1. Ensure MeshCore radio is powered on
# 2. Check radio is in pairing/discoverable mode
# 3. Verify radio is in range

# If connection fails:
# 1. Verify pairing code is correct
# 2. Check device is not connected to another system
# 3. Try removing and re-pairing:
bluetoothctl remove <BLE_ADDRESS>
# Then reconnect via MeshAgotchi
```

### Database Errors

```bash
# Check database file permissions
ls -l ~/Meshagotchi/meshogotchi.db

# If permission issues:
chmod 644 ~/Meshagotchi/meshogotchi.db
```

### Service Won't Start

```bash
# Check service status for errors
sudo systemctl status meshagotchi.service

# Check logs
sudo journalctl -u meshagotchi.service -n 50

# Verify paths in service file are correct
sudo cat /etc/systemd/system/meshagotchi.service
```

### Messages Not Received

1. Verify MeshCore CLI is working:
   ```bash
   meshcli receive
   # or
   meshcli listen
   ```

2. Check BLE connection:
   ```bash
   # Verify device is connected
   bluetoothctl devices
   
   # Test connection manually
   meshcli -a <BLE_ADDRESS> infos
   ```

3. Verify Node IDs match between devices

## Additional Resources

- **MeshCore CLI Documentation**: https://github.com/meshcore-dev/meshcore-cli
- **Raspberry Pi Documentation**: https://www.raspberrypi.com/documentation/
- **MeshAgotchi Repository**: https://github.com/datton/Meshagotchi

## Summary

After completing these steps, you should have:
- ✅ Raspberry Pi OS (64-bit) installed and updated
- ✅ Python 3.10+ installed
- ✅ MeshCore CLI installed and configured
- ✅ MeshAgotchi cloned and ready
- ✅ Heltec V3 LoRa radio connected via BLE
- ✅ MeshAgotchi running (manually or as service)
- ✅ Game responding to commands via LoRa mesh

Your MeshAgotchi virtual pet game is now ready to play!
