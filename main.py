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
                    print(f"[{datetime.now()}] Received from {sender_node_id}: {command_text}")
                    
                    # Process command
                    response = self.game_engine.process_command(sender_node_id, command_text)
                    
                    # Send response
                    self.mesh_handler.send(sender_node_id, response)
                    print(f"[{datetime.now()}] Sent to {sender_node_id}: {response[:50]}...")
                
                # Process pending messages in queue
                self.mesh_handler.process_pending_messages()
                
                # Check for periodic notifications
                now = datetime.now()
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
