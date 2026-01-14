"""
Main daemon entry point for MeshAgotchi.

Initializes database, starts MeshHandler listener loop, routes commands
to GameEngine, and handles periodic notifications.
"""

import signal
import sys
import time
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
    
    def initialize(self):
        """Initialize database and components."""
        print("Initializing MeshAgotchi...")
        
        # Initialize database
        database.init_database()
        print("Database initialized.")
        
        # Create MeshHandler
        # If your device is at /dev/ttyUSB0, pass serial_port="/dev/ttyUSB0"
        # If meshcli auto-detects, you can leave it as None
        import os
        serial_port = os.getenv("MESHCLI_SERIAL_PORT", None)  # e.g., "/dev/ttyUSB0"
        self.mesh_handler = mesh_interface.MeshHandler(
            min_send_interval=2.0,
            max_message_length=200,
            serial_port=serial_port
        )
        print("MeshHandler initialized.")
        
        # Initialize and configure radio
        if not self.mesh_handler.initialize_radio():
            print("Warning: Radio initialization failed. Continuing anyway...")
            print("Game may not function correctly without radio connection.")
        print()  # Blank line for readability
        
        # Create GameEngine
        self.game_engine = game_engine.GameEngine()
        print("GameEngine initialized.")
        
        # Initialize notification check time
        self.last_notification_check = datetime.now()
        
        # Initialize advert flood time (start immediately)
        self.last_advert_flood = datetime.now()
        
        print("MeshAgotchi daemon ready!")
        print("Listening for messages via MeshCore CLI...")
        print("Press Ctrl+C to stop.\n")
    
    def run(self):
        """Main event loop."""
        if not self.mesh_handler or not self.game_engine:
            print("Error: Components not initialized!")
            return
        
        while self.running:
            try:
                # Check for incoming messages
                message = self.mesh_handler.listen()
                
                if message:
                    sender_node_id, command_text = message
                    print(f"[{datetime.now()}] *** MESSAGE RECEIVED ***")
                    print(f"  From: {sender_node_id}")
                    print(f"  Command: {command_text}")

                    # If we can't resolve sender to a node id, we cannot safely process commands
                    # (user/pet identity depends on node_id) and we definitely cannot reply.
                    if sender_node_id is None:
                        print("[DEBUG] Skipping command processing: sender node id is unknown (None).")
                        continue
                    
                    # Process command
                    print(f"[DEBUG] Processing command with game engine...")
                    response = self.game_engine.process_command(sender_node_id, command_text)
                    print(f"[DEBUG] Game engine response: {response[:200]}...")
                    
                    # Send response
                    if response:
                        # IMPORTANT: Destination MUST be the hex node id.
                        # If we couldn't resolve the sender into a node id, we cannot reply.
                        if sender_node_id is None:
                            print("[DEBUG] Cannot send response: sender node id is unknown (None).")
                        else:
                            print(f"[DEBUG] Sending response to {sender_node_id}...")
                            self.mesh_handler.send(sender_node_id, response)
                            print(f"[{datetime.now()}] *** RESPONSE SENT ***")
                            print(f"  To: {sender_node_id}")
                            print(f"  Response: {response[:100]}...")
                    else:
                        print(f"[DEBUG] No response to send (response was empty)")
                
                # Process pending messages in queue
                self.mesh_handler.process_pending_messages()
                
                # Periodically discover and add new nodes as friends
                # This ensures the node can receive messages from anyone
                if not hasattr(self, 'last_discovery_check'):
                    self.last_discovery_check = datetime.now()
                
                discovery_interval = 60  # Check every 60 seconds
                time_since_discovery = (datetime.now() - self.last_discovery_check).total_seconds()
                if time_since_discovery >= discovery_interval:
                    self.mesh_handler.discover_and_add_nodes()
                    self.last_discovery_check = datetime.now()
                
                # Periodically flood zero-hop adverts throughout the day
                # This keeps the node discoverable to others
                now = datetime.now()
                time_since_advert = (now - self.last_advert_flood).total_seconds()
                if time_since_advert >= self.advert_flood_interval:
                    print(f"\n[{now}] Flooding zero-hop adverts to maintain discoverability...")
                    self.mesh_handler.flood_advert(count=5, delay=0.5, zero_hop=True)
                    self.last_advert_flood = now
                    print(f"Advert flood complete. Next flood in {self.advert_flood_interval / 3600:.1f} hours.\n")
                
                # Check for periodic notifications
                time_since_check = (now - self.last_notification_check).total_seconds()
                
                if time_since_check >= self.notification_interval:
                    self._check_notifications()
                    self.last_notification_check = now
                
                # Small sleep to avoid busy-waiting
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(1)  # Brief pause before retrying
        
        print("\nShutting down...")
    
    def _check_notifications(self):
        """Check and send periodic notifications."""
        try:
            notifications = self.game_engine.check_and_send_notifications()
            
            for node_id, message in notifications:
                print(f"[{datetime.now()}] Notification to {node_id}: {message[:50]}...")
                self.mesh_handler.send(node_id, message)
            
            # Process notification queue
            self.mesh_handler.process_pending_messages()
            
        except Exception as e:
            print(f"Error checking notifications: {e}")


def main():
    """Main entry point."""
    daemon = MeshAgotchiDaemon()
    
    try:
        daemon.initialize()
        daemon.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    
    print("MeshAgotchi daemon stopped.")


if __name__ == "__main__":
    main()
