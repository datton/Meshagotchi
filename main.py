"""
Main daemon entry point for MeshAgotchi.

Initializes database, starts MeshHandler listener loop, routes commands
to GameEngine, and handles periodic notifications.
"""

import signal
import sys
import asyncio
from datetime import datetime, timedelta
import database
import mesh_interface
import game_engine
import config


# Welcome message sent to public channel on startup and once per day
WELCOME_MESSAGE = (
    "Meshagotchi is live and your pet is ready to meet you! "
    "Message /help to this address to get started"
)


class MeshAgotchiDaemon:
    """Main daemon class for MeshAgotchi."""
    
    def __init__(self):
        """Initialize daemon."""
        self.running = True
        self.mesh_handler = None
        self.game_engine = None
        self.last_notification_check = None
        self.notification_interval = 300  # 5 minutes in seconds
        self.last_flood_advert = None
        self.flood_advert_interval = 20 * 60  # 20 minutes in seconds
        self.last_zero_hop_advert = None
        self.zero_hop_advert_interval = 5 * 60  # 5 minutes in seconds
        self.last_welcome_message = None
        self.welcome_message_interval = 24 * 3600  # 24 hours in seconds
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.running = False
    
    async def initialize(self):
        """Initialize database and components (async)."""
        print("Initializing MeshAgotchi...")
        
        # Initialize database
        database.init_database()
        
        # Create MeshHandler (will connect via BLE)
        self.mesh_handler = mesh_interface.MeshHandler(
            min_send_interval=2.0,
            max_message_length=200
        )
        
        # Initialize and connect (async)
        await self.mesh_handler.initialize()
        
        # Initialize and configure radio
        if not await self.mesh_handler.initialize_radio():
            print("Warning: Radio initialization failed. Continuing anyway...")
        
        # Create GameEngine
        self.game_engine = game_engine.GameEngine()
        
        # Initialize notification check time
        self.last_notification_check = datetime.now()
        
        # Initialize advert timers (next run will be after interval)
        self.last_flood_advert = datetime.now()
        self.last_zero_hop_advert = datetime.now()
        
        # Send welcome message to public channel on startup
        await self._send_welcome_message()
        self.last_welcome_message = datetime.now()
        
        print("MeshAgotchi ready. Listening for messages...")
    
    async def run(self):
        """Main event loop (async)."""
        if not self.mesh_handler or not self.game_engine:
            print("Error: Components not initialized!")
            return
        
        while self.running:
            try:
                # Check for incoming messages
                message = await self.mesh_handler.listen()
                
                if message:
                    sender_node_id, command_text = message
                    
                    # If we can't resolve sender to a node id, we cannot safely process commands
                    # (user/pet identity depends on node_id) and we definitely cannot reply.
                    if sender_node_id is None:
                        continue
                    
                    # Process command
                    response = self.game_engine.process_command(sender_node_id, command_text)
                    
                    # Send response (handle both single string and list of strings)
                    if response and sender_node_id:
                        if isinstance(response, list):
                            # Send each part separately
                            for part in response:
                                if part:
                                    self.mesh_handler.send(sender_node_id, part)
                                    # Small delay between parts to avoid overwhelming the radio
                                    await asyncio.sleep(0.5)
                        else:
                            # Single string response
                            self.mesh_handler.send(sender_node_id, response)
                
                # Process pending messages in queue
                await self.mesh_handler.process_pending_messages()
                
                # Periodically discover and add new nodes as friends
                # This ensures the node can receive messages from anyone
                if not hasattr(self, 'last_discovery_check'):
                    self.last_discovery_check = datetime.now()
                
                discovery_interval = 60  # Check every 60 seconds
                time_since_discovery = (datetime.now() - self.last_discovery_check).total_seconds()
                if time_since_discovery >= discovery_interval:
                    await self.mesh_handler.discover_and_add_nodes()
                    self.last_discovery_check = datetime.now()
                
                # Flood adverts every 20 minutes; zero-hop adverts every 5 minutes
                now = datetime.now()
                time_since_flood = (now - self.last_flood_advert).total_seconds()
                if time_since_flood >= self.flood_advert_interval:
                    await self.mesh_handler.send_flood_advert(count=5, delay=0.5)
                    self.last_flood_advert = now
                time_since_zero_hop = (now - self.last_zero_hop_advert).total_seconds()
                if time_since_zero_hop >= self.zero_hop_advert_interval:
                    await self.mesh_handler.send_zero_hop_advert(count=5, delay=0.5)
                    self.last_zero_hop_advert = now
                
                # Welcome message to public channel once per day
                if self.last_welcome_message is not None:
                    time_since_welcome = (now - self.last_welcome_message).total_seconds()
                    if time_since_welcome >= self.welcome_message_interval:
                        await self._send_welcome_message()
                        self.last_welcome_message = now
                
                # Check for periodic notifications
                time_since_check = (now - self.last_notification_check).total_seconds()
                
                if time_since_check >= self.notification_interval:
                    await self._check_notifications()
                    self.last_notification_check = now
                
                # Small sleep to avoid busy-waiting
                await asyncio.sleep(0.5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
        
        print("\nShutting down...")
        if self.mesh_handler:
            await self.mesh_handler.disconnect()
    
    async def _send_welcome_message(self):
        """Send welcome message to public channel (channel 0)."""
        try:
            cfg = config.get_config()
            radio_name = cfg.get_radio_name()
            message = WELCOME_MESSAGE.replace("Meshagotchi", radio_name, 1)
            await self.mesh_handler.send_public_message(message, channel=0)
        except Exception as e:
            print(f"Error sending welcome message: {e}")

    async def _check_notifications(self):
        """Check and send periodic notifications (async)."""
        try:
            notifications = self.game_engine.check_and_send_notifications()
            
            for node_id, message in notifications:
                self.mesh_handler.send(node_id, message)
            
            # Process notification queue
            await self.mesh_handler.process_pending_messages()
            
        except Exception as e:
            print(f"Error checking notifications: {e}")


async def main_async():
    """Main async entry point."""
    daemon = MeshAgotchiDaemon()
    
    try:
        await daemon.initialize()
        await daemon.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("MeshAgotchi daemon stopped.")


def main():
    """Main entry point - runs async main."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
