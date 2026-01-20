# MeshAgotchi Installation Guide

Complete installation instructions for MeshAgotchi on a fresh Raspberry Pi.

## Hardware Requirements

- **Raspberry Pi**: Any model (Pi 3, Pi 4, Pi Zero 2W, or newer recommended)
- **MicroSD Card**: Minimum 8GB (16GB+ recommended)
- **Power Supply**: Official Raspberry Pi power adapter (5V, 2.5A+ for Pi 4)
- **Heltec V3 LoRa Radio**: Connected via USB Serial (ttyUSB)
- **USB Cable**: USB cable to connect Heltec V3 radio to Raspberry Pi
- **Network**: Ethernet cable or Wi-Fi for initial setup

## Step 1: Install Raspberry Pi OS

### Recommended Version

**Raspberry Pi OS (64-bit) - Bookworm or newer**

As of 2025, use **Raspberry Pi OS (64-bit)** based on Debian Bookworm or Trixie. This provides:
- Python 3.11+ support
- Better USB Serial support
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

## Step 3: Install MeshAgotchi

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

MeshAgotchi requires the `meshcore` Python package for MeshCore communication.

#### Option 1: Install with Virtual Environment (Recommended)

```bash
# Step 1: Navigate to MeshAgotchi directory (IMPORTANT: must be in this directory)
cd ~/Meshagotchi

# Step 2: Create a virtual environment in the MeshAgotchi directory
python3 -m venv venv

# Step 3: Activate the virtual environment
source venv/bin/activate

# You should now see (venv) in your prompt:
# (venv) meshagotchi@meshagotchi:~/Meshagotchi $

# Step 4: Verify you're using the venv's pip (should show path to venv/bin/pip)
which pip
# Should output: /home/meshagotchi/Meshagotchi/venv/bin/pip

which python3
# Should output: /home/meshagotchi/Meshagotchi/venv/bin/python3

# If either shows /usr/bin/, the venv isn't activated properly
# Make sure you're in ~/Meshagotchi directory and run: source venv/bin/activate

# Step 5: Upgrade pip (recommended)
python3 -m pip install --upgrade pip

# Step 6: Install dependencies from requirements file
python3 -m pip install -r requirements.txt

# Step 7: Verify installation
python3 -c "import meshcore; print('meshcore installed successfully')"

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
python3 -m pip install -r requirements.txt
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
# Install meshcore system-wide (requires sudo)
sudo pip3 install -r requirements.txt
```

**For systemd service**: If running as a systemd service, you'll need to either:
- Install meshcore system-wide (Option 2), or
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

## Step 4: Configure USB Serial Access

### Add User to dialout Group

To access USB serial ports, you need to add your user to the `dialout` group:

```bash
# Add your user to the dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in for changes to take effect
# Or use: newgrp dialout (for current session only)

# Verify you're in the dialout group
groups
# Should show 'dialout' in the list
```

### Verify Serial Port Detection

```bash
# Check if USB serial devices are detected
ls -l /dev/ttyUSB*

# Or check for USB CDC devices
ls -l /dev/ttyACM*

# If your Heltec V3 radio is connected, you should see a device like:
# /dev/ttyUSB0 or /dev/ttyACM0

# Check recent USB device connections
dmesg | tail
# Should show USB device connection messages
```

**Note**: MeshAgotchi will automatically detect and connect to USB serial devices on first run.

## Step 5: Run MeshAgotchi

### Manual Start (Testing)

```bash
cd ~/Meshagotchi

# If using virtual environment, activate it first
source venv/bin/activate

# Run MeshAgotchi (will auto-detect USB serial port on first run)
python3 main.py
```

**First Run**: On first run, MeshAgotchi will:
1. Check for a previously connected serial port in the database
2. If not found, automatically scan for USB serial devices (ttyUSB0, ttyUSB1, etc.)
3. If multiple devices are found, display a numbered list for you to select
4. If only one device is found, it will be auto-selected
5. Connect to the selected serial port and store it for future use

**Subsequent Runs**: Will automatically connect to the stored serial port.

You should see:
```
Initializing MeshAgotchi...
Scanning for serial devices...
Auto-selected serial port: /dev/ttyUSB0
Connecting to serial port: /dev/ttyUSB0...
Successfully connected to serial port: /dev/ttyUSB0
Database initialized.
MeshHandler initialized.
GameEngine initialized.
Radio initialization complete
MeshAgotchi daemon ready!
Listening for messages via MeshCore...
Press Ctrl+C to stop.
```

### Test Commands

From another device with MeshCore Mobile App:
- Send `/help` to the Raspberry Pi's Node ID
- You should receive a response with available commands

## Step 6: Set Up as System Service (Optional but Recommended)

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

## Step 7: Verify Installation

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

### Permission Denied Accessing Serial Port

```bash
# Check if you're in the dialout group
groups

# If dialout is not listed, add yourself:
sudo usermod -a -G dialout $USER

# Log out and log back in, or use:
newgrp dialout

# Verify serial port permissions
ls -l /dev/ttyUSB0
# Should show read/write permissions for dialout group
```

### Serial Port Not Found

```bash
# Check if USB serial devices are detected
ls -l /dev/ttyUSB* /dev/ttyACM*

# If no devices found:
# 1. Ensure Heltec V3 radio is powered on and connected via USB
# 2. Try unplugging and reconnecting the USB cable
# 3. Check USB connection: dmesg | tail
# 4. Try a different USB port or cable

# Check if device is detected by system
dmesg | grep -i usb
# Should show USB device connection messages
```

### Connection Issues

```bash
# Check if another program is using the serial port
lsof /dev/ttyUSB0

# If another process is using it, stop that process first

# Verify the port exists and is accessible
ls -l /dev/ttyUSB0

# Test serial port access
sudo chmod 666 /dev/ttyUSB0  # Temporary fix, but proper solution is dialout group
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

1. Verify serial port connection:
   ```bash
   # Check if port is accessible
   ls -l /dev/ttyUSB0
   
   # Check if MeshAgotchi is running
   ps aux | grep main.py
   ```

2. Check MeshAgotchi logs:
   ```bash
   # If running as service
   sudo journalctl -u meshagotchi.service -f
   
   # If running manually, check terminal output
   ```

3. Verify Node IDs match between devices

4. Check radio configuration:
   - Ensure radio is on USA/Canada preset (910.525 MHz)
   - Verify both nodes are on the same frequency/preset

## Additional Resources

- **meshcore Python Package**: https://pypi.org/project/meshcore/
- **MeshCore Documentation**: https://github.com/meshcore-dev/MeshCore
- **Raspberry Pi Documentation**: https://www.raspberrypi.com/documentation/
- **MeshAgotchi Repository**: https://github.com/datton/Meshagotchi

## Summary

After completing these steps, you should have:
- ✅ Raspberry Pi OS (64-bit) installed and updated
- ✅ Python 3.10+ installed
- ✅ meshcore Python package installed
- ✅ User added to dialout group for serial port access
- ✅ MeshAgotchi cloned and ready
- ✅ Heltec V3 LoRa radio connected via USB Serial
- ✅ MeshAgotchi running (manually or as service)
- ✅ Game responding to commands via LoRa mesh

Your MeshAgotchi virtual pet game is now ready to play!
