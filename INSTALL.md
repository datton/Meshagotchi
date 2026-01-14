# MeshAgotchi Installation Guide

Complete installation instructions for MeshAgotchi on a fresh Raspberry Pi.

## Hardware Requirements

- **Raspberry Pi**: Any model (Pi 3, Pi 4, Pi Zero 2W, or newer recommended)
- **MicroSD Card**: Minimum 8GB (16GB+ recommended)
- **Power Supply**: Official Raspberry Pi power adapter (5V, 2.5A+ for Pi 4)
- **Heltec V3 LoRa Radio**: Connected via USB Serial
- **Network**: Ethernet cable or Wi-Fi for initial setup

## Step 1: Install Raspberry Pi OS

### Recommended Version

**Raspberry Pi OS (64-bit) - Bookworm or newer**

As of 2025, use **Raspberry Pi OS (64-bit)** based on Debian Bookworm or Trixie. This provides:
- Python 3.11+ support
- Better USB serial support
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

### Verify USB Serial Access

```bash
# Check if Heltec V3 is connected
# Note: It may appear as /dev/ttyUSB0 or /dev/ttyACM0 depending on device
ls -l /dev/ttyUSB* 2>/dev/null || echo "No ttyUSB devices found"
ls -l /dev/ttyACM* 2>/dev/null || echo "No ttyACM devices found"

# You should see something like:
# crw-rw---- 1 root dialout 188, 0 Jan 13 18:22 /dev/ttyUSB0

# Add your user to dialout group (for USB serial access)
sudo usermod -a -G dialout $USER

# Log out and log back in for group change to take effect
# Or run: newgrp dialout

# Verify you're in the dialout group
groups | grep dialout
```

## Step 4: Install MeshAgotchi

### Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone MeshAgotchi repository
git clone https://github.com/datton/Meshagotchi.git
cd Meshogotchi
```

### Verify Python Version

```bash
# Check Python version (should be 3.10+)
python3 --version

# Should output: Python 3.10.x or higher
```

### Install Dependencies

MeshAgotchi uses only Python standard library modules, so no additional packages are required:
- `sqlite3` (standard library)
- `subprocess` (standard library)
- `queue` (standard library)
- `hashlib` (standard library)
- `datetime` (standard library)

**No pip install required!**

### Test Installation

```bash
# Test genetics demo
python3 genetics.py

# Test database initialization
python3 database.py

# Verify all modules import correctly
python3 -c "import genetics; import database; import mesh_interface; import game_engine; import main; print('All imports successful!')"
```

## Step 5: Configure MeshCore CLI

### Verify Heltec V3 Connection

```bash
# Check USB device
lsusb | grep -i heltec

# Check serial port (should show /dev/ttyUSB0 or /dev/ttyACM0)
dmesg | tail -20 | grep -i tty

# Find your device path
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null

# Test MeshCore CLI with serial port
# Replace /dev/ttyUSB0 with your actual device path
meshcli -s /dev/ttyUSB0 -h
# or try listing devices
meshcli -l
```

**Note**: The `-s` flag specifies the serial port. If your device is at `/dev/ttyUSB0`, use `meshcli -s /dev/ttyUSB0` for all commands.

### Configure MeshCore CLI Serial Port

MeshCore CLI needs to know which serial port to use. Based on the help output, use the `-s` flag:

```bash
# Connect to device at /dev/ttyUSB0
meshcli -s /dev/ttyUSB0 <command>

# Example: Get version
meshcli -s /dev/ttyUSB0 -v

# Example: Get status/info
meshcli -s /dev/ttyUSB0 status
```

**Note**: You may need to specify the serial port (`-s /dev/ttyUSB0`) for all meshcli commands, or meshcli may remember it after first use. Check meshcli documentation for details.

## Step 6: Run MeshAgotchi

### Manual Start (Testing)

```bash
cd ~/Meshagotchi

# If your device is at /dev/ttyUSB0, set environment variable:
export MESHCLI_SERIAL_PORT=/dev/ttyUSB0

# Or run without (meshcli may auto-detect):
python3 main.py
```

**Note**: If meshcli requires the serial port to be specified, set `MESHCLI_SERIAL_PORT` environment variable to your device path (e.g., `/dev/ttyUSB0`).

You should see:
```
Initializing MeshAgotchi...
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

### Permission Denied on USB Serial

```bash
# Ensure user is in dialout group
groups | grep dialout

# If not present:
sudo usermod -a -G dialout $USER
# Log out and log back in
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

2. Check USB connection:
   ```bash
   lsusb | grep -i heltec
   dmesg | grep -i tty
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
- ✅ Heltec V3 LoRa radio connected and accessible
- ✅ MeshAgotchi running (manually or as service)
- ✅ Game responding to commands via LoRa mesh

Your MeshAgotchi virtual pet game is now ready to play!
