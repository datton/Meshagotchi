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


class MeshAgotchiDaemon:
    """Main daemon class for MeshAgotchi."""
    
    def __init__(self):
        """Initialize daemon."""
        self.running = True
        self.mesh_handler = None
        self.game_engine = None
        self.last_notification_check = None
        self.notification_interval = 300  # 5 minutes in seconds
        self.last_advert_flood = None
        self.advert_flood_interval = 4 * 3600  # 4 hours in seconds (flood adverts 6 times per day)
        
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
        
        # Initialize advert flood time (start immediately)
        self.last_advert_flood = datetime.now()
        
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
                
                # Periodically flood zero-hop adverts throughout the day
                # This keeps the node discoverable to others
                now = datetime.now()
                time_since_advert = (now - self.last_advert_flood).total_seconds()
                if time_since_advert >= self.advert_flood_interval:
                    await self.mesh_handler.flood_advert(count=5, delay=0.5, zero_hop=True)
                    self.last_advert_flood = now
                
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
