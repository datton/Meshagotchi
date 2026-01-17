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
  - Age stages: Child → Teen → Adult
  - Pet decay over time requiring regular care
  - Death and rebirth system with generational tracking

- **Game Commands**:
  - `/hatch` - Create a new pet
  - `/stats` - View pet status and ASCII art
  - `/feed` - Feed your pet (reduces hunger)
  - `/clean` - Clean your pet (improves hygiene)
  - `/play` - Play with your pet (increases happiness)
  - `/status` - Quick status check
  - `/name <name>` - Name your pet
  - `/help` - List all commands

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
- **Heltec V3 LoRa Radio**: Connected via BLE (Bluetooth Low Energy)
- **MicroSD Card**: Minimum 8GB (16GB+ recommended)
- **Power Supply**: Official Raspberry Pi power adapter

## Software Requirements

- Raspberry Pi OS (64-bit) - Bookworm or newer
- Python 3.10 or higher
- MeshCore CLI (meshcore-cli)
- Bleak library (for BLE scanning) - `pip3 install bleak`
- MeshCore-compatible firmware on Heltec V3 radio

## Quick Start

### Installation

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

**Quick setup:**

```bash
# Clone the repository
git clone https://github.com/datton/Meshagotchi.git
cd Meshogotchi

# Install MeshCore CLI (see INSTALL.md for details)
cd ~
git clone https://github.com/meshcore-dev/meshcore-cli.git
cd meshcore-cli
python3 -m venv venv
source venv/bin/activate
pip install meshcore
pip install .

# Install Bleak for BLE scanning (recommended)
pip3 install bleak

# Run MeshAgotchi
cd ~/Meshagotchi
python3 main.py
```

### Running as a Service

MeshAgotchi can run as a systemd service for automatic startup. See [INSTALL.md](INSTALL.md#step-7-set-up-as-system-service-optional-but-recommended) for setup instructions.

## Usage

### Starting the Game

1. Ensure your Heltec V3 radio is powered on and Bluetooth is enabled on your Raspberry Pi
2. Run the daemon:
   ```bash
   python3 main.py
   ```

### Playing the Game

Send commands to your MeshAgotchi node from another MeshCore-compatible device (mobile app, another radio, etc.):

```
/hatch          # Create your first pet
/stats           # View your pet's status and ASCII art
/feed            # Feed your pet
/clean           # Clean your pet
/play            # Play with your pet
/name Fluffy     # Name your pet
/help            # Get help
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

- **MeshHandler**: Manages all MeshCore CLI communication, advertising, and message handling
- **GameEngine**: Processes game commands and manages pet state
- **Database**: Handles user and pet data persistence
- **Genetics**: Generates unique pets based on Node ID and generation

## Configuration

### BLE Connection

On first run, MeshAgotchi will:
1. Check for a previously connected BLE device
2. If not found, scan for available BLE MeshCore devices
3. Display a numbered list for you to select your device
4. Prompt for the BLE pairing code
5. Connect and store the device info for future use

Subsequent runs will automatically connect to the stored device.

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

- **Standard Library Only**: Uses only Python standard library modules (no external dependencies)
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
- Verify radio connection: `meshcli -a <BLE_ADDRESS> infos`

**"MeshCore CLI not found"**
- Ensure meshcore-cli is installed and in PATH
- Check: `which meshcli` or `which meshcore-cli`
- See [INSTALL.md](INSTALL.md#step-3-install-meshcore-cli) for installation

**"No BLE devices found"**
- Ensure your MeshCore radio is powered on and in range
- Check Bluetooth is enabled on Raspberry Pi: `bluetoothctl show`
- Try scanning manually: `meshcli -l`
- Ensure radio is in pairing/discoverable mode

**"Failed to connect to BLE device"**
- Verify pairing code is correct
- Check device is not already connected to another system
- Try removing and re-pairing: `bluetoothctl remove <ADDRESS>` then reconnect

**Other nodes can't see MeshAgotchi**
- Verify radio is connected via BLE
- Check radio name is set: `meshcli -a <BLE_ADDRESS> infos`
- Ensure adverts are being sent (check logs)
- Verify both nodes are on the same frequency/preset

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
- [meshcore-cli](https://github.com/meshcore-dev/meshcore-cli) - The CLI interface used for communication
- Inspired by Tamagotchi and other virtual pet games

## Links

- **Repository**: https://github.com/datton/Meshagotchi
- **Installation Guide**: [INSTALL.md](INSTALL.md)
- **MeshCore Documentation**: https://github.com/meshcore-dev/MeshCore
- **MeshCore CLI**: https://github.com/meshcore-dev/meshcore-cli

## Status

Active development. The project is functional and playable, with ongoing improvements and feature additions.

---

**Note**: MeshAgotchi requires MeshCore-compatible hardware and firmware. Ensure your Heltec V3 radio is running MeshCore firmware before use.
