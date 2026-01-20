# MeshAgotchi

A virtual pet game that runs on LoRa mesh networks, allowing players to hatch, raise, and care for procedurally generated pets using MeshCore-compatible radios.

## Overview

MeshAgotchi is a Tamagotchi-inspired virtual pet game designed for decentralized, off-grid communication. Players interact with their pets through LoRa mesh networks using MeshCore-compatible devices, creating a unique gaming experience that doesn't require internet connectivity.

## Features

### Game Features

- **Procedural Pet Generation**: Each pet is uniquely generated using a genetics system
  - Family Trait: Eye style inherited from your Node ID (persistent across generations)
  - Individual Trait: Body shape determined by generation seed
  - ASCII art rendering for visual representation

- **Pet Care System**:
  - Health, Hunger, Hygiene, Happiness, and Energy stats
  - Age stages: Egg → Child → Teen → Adult → Elder
  - Pet decay over time requiring regular care
  - Death and rebirth system with generational tracking

- **Game Commands**:
  - `/hatch` - Create a new pet
  - `/pet` - Display your pet's ASCII art
  - `/status` - View pet stats and info
  - `/feed` - Feed your pet (reduces hunger)
  - `/clean` - Clean your pet (improves hygiene)
  - `/play` - Play with your pet (increases happiness, uses 20 energy)
  - `/name <name>` - Name your pet (max 20 chars)
  - `/quiet` - Enable quiet mode (pet only messages when in trouble)
  - `/talk` - Disable quiet mode (pet messages regularly)
  - `/help` - List all commands
  - `/howto` - Detailed game guide

### Technical Features

- **MeshCore Integration**: Full compatibility with MeshCore CLI and mesh networking
- **Auto-Discovery**: Automatically discovers and connects with other nodes
- **Zero-Hop Advertising**: Floods adverts for direct discoverability
- **Contact Management**: Auto-adds contacts from received adverts
- **Persistent Storage**: SQLite database for pet data persistence
- **Systemd Service**: Can run as a background daemon
- **Rate Limiting**: Built-in message rate limiting to prevent network flooding

## Hardware Requirements

- **Raspberry Pi**: Any model (Pi 3, Pi 4, Pi Zero 2W, or newer recommended)
- **Heltec V3 LoRa Radio**: Connected via USB Serial (ttyUSB)
- **MicroSD Card**: Minimum 8GB (16GB+ recommended)
- **Power Supply**: Official Raspberry Pi power adapter
- **USB Cable**: USB cable to connect Heltec V3 radio to Raspberry Pi

## Software Requirements

- Raspberry Pi OS (64-bit) - Bookworm or newer
- Python 3.10 or higher
- meshcore Python package - `pip install meshcore`
- MeshCore-compatible firmware on Heltec V3 radio

## Quick Start

### Installation

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

**Quick setup:**

```bash
# Clone the repository
git clone https://github.com/datton/Meshagotchi.git
cd Meshogotchi

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run MeshAgotchi
python3 main.py
```

### Running as a Service

MeshAgotchi can run as a systemd service for automatic startup. See [INSTALL.md](INSTALL.md#step-6-set-up-as-system-service-optional-but-recommended) for setup instructions.

## Usage

### Starting the Game

1. Ensure your Heltec V3 radio is powered on and connected via USB to your Raspberry Pi
2. Run the daemon:
   ```bash
   python3 main.py
   ```

### Playing the Game

Send commands to your MeshAgotchi node from another MeshCore-compatible device (mobile app, another radio, etc.):

```
/hatch          # Create your first pet
/pet            # Display your pet's ASCII art
/status         # View pet stats and info
/feed            # Feed your pet
/clean           # Clean your pet
/play            # Play with your pet
/name Fluffy     # Name your pet
/quiet           # Enable quiet mode
/talk            # Disable quiet mode
/help            # List all commands
/howto           # Detailed game guide
```

### How It Works

1. **Node Discovery**: MeshAgotchi automatically advertises itself on the mesh network using zero-hop floods
2. **Contact Management**: Other nodes that receive adverts are automatically added as contacts
3. **Message Handling**: Commands sent to the node are processed by the game engine
4. **Pet Management**: Pet stats decay over time and require regular interaction
5. **Persistence**: All pet data is stored in a local SQLite database

## Architecture

```
MeshAgotchi
├── main.py              # Main daemon entry point
├── game_engine.py       # Game logic and command processing
├── mesh_interface.py   # MeshCore CLI wrapper and communication
├── database.py          # SQLite database operations
├── genetics.py          # Procedural pet generation system
└── meshogotchi.db      # SQLite database (created on first run)
```

### Key Components

- **MeshHandler**: Manages all MeshCore communication via USB Serial, advertising, and message handling
- **GameEngine**: Processes game commands and manages pet state
- **Database**: Handles user and pet data persistence
- **Genetics**: Generates unique pets based on Node ID and generation

## Configuration

### USB Serial Connection

On first run, MeshAgotchi will:
1. Check for a previously connected serial port in the database
2. If not found, automatically detect available USB serial devices (ttyUSB0, ttyUSB1, etc.)
3. If multiple devices are found, display a numbered list for you to select
4. If only one device is found, it will be auto-selected
5. Connect to the selected serial port and store it for future use

Subsequent runs will automatically connect to the stored serial port.

**Common serial ports:**
- `/dev/ttyUSB0` - Most common USB serial adapter
- `/dev/ttyUSB1` - Second USB serial adapter
- `/dev/ttyACM0` - USB CDC device

**Note**: You may need to add your user to the `dialout` group to access serial ports:
```bash
sudo usermod -a -G dialout $USER
# Then log out and log back in
```

### Radio Configuration

MeshAgotchi automatically configures the radio with USA/Canada preset settings:
- Frequency: 910.525 MHz
- Bandwidth: 62.5 kHz
- Spreading Factor: 7
- Coding Rate: 5
- Power: 22 dBm

The radio name is automatically set to "Meshagotchi" at startup.

### Advertising Schedule

- Initial flood: 5 adverts at startup
- Periodic floods: Every 4 hours (6 times per day)
- Node discovery: Every 60 seconds

## Development

### Project Structure

- **Minimal Dependencies**: Only requires the `meshcore` Python package
- **Modular Design**: Clean separation of concerns between mesh communication, game logic, and data persistence
- **Extensible**: Easy to add new commands or game features

### Adding New Commands

1. Add command handler in `game_engine.py`:
   ```python
   elif command == '/newcommand':
       return self._handle_newcommand(node_id, pet, args)
   ```

2. Implement handler method:
   ```python
   def _handle_newcommand(self, node_id: str, pet: Optional[Dict], args: str) -> str:
       # Your command logic here
       return "Response message"
   ```

3. Update help text in `_handle_help()` method

## Troubleshooting

### Common Issues

**"Warning: Could not retrieve radio link info"**
- This is usually harmless. The node should still function correctly.
- Verify radio connection by checking if the serial port is accessible

**"Permission denied accessing /dev/ttyUSB0"**
- Add your user to the `dialout` group: `sudo usermod -a -G dialout $USER`
- Log out and log back in for changes to take effect
- Verify with: `groups` (should show `dialout`)

**"Serial port not found"**
- Ensure your Heltec V3 radio is powered on and connected via USB
- Check if device is detected: `ls -l /dev/ttyUSB*` or `ls -l /dev/ttyACM*`
- Try unplugging and reconnecting the USB cable
- Verify the device appears: `dmesg | tail` (should show USB device connection)

**"Failed to connect to serial port"**
- Check if another program is using the port: `lsof /dev/ttyUSB0`
- Verify the port exists: `ls -l /dev/ttyUSB0`
- Try a different USB port or cable
- Ensure the radio firmware is MeshCore-compatible

**Other nodes can't see MeshAgotchi**
- Verify radio is connected via USB Serial
- Check radio name is set (should be "Meshagotchi" automatically)
- Ensure adverts are being sent (check logs)
- Verify both nodes are on the same frequency/preset (USA/Canada preset: 910.525 MHz)

For more troubleshooting, see [INSTALL.md](INSTALL.md#troubleshooting).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Areas for Contribution

- Additional game features and commands
- Improved ASCII art generation
- Better error handling and recovery
- Documentation improvements
- Testing and bug fixes

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [MeshCore](https://github.com/meshcore-dev/MeshCore) - The mesh networking protocol
- [meshcore Python package](https://pypi.org/project/meshcore/) - Python library for MeshCore communication
- Inspired by Tamagotchi and other virtual pet games

## Links

- **Repository**: https://github.com/datton/Meshagotchi
- **Installation Guide**: [INSTALL.md](INSTALL.md)
- **MeshCore Documentation**: https://github.com/meshcore-dev/MeshCore
- **meshcore Python Package**: https://pypi.org/project/meshcore/

## Status

Active development. The project is functional and playable, with ongoing improvements and feature additions.

---

**Note**: MeshAgotchi requires MeshCore-compatible hardware and firmware. Ensure your Heltec V3 radio is running MeshCore firmware before use.
