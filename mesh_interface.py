"""
MeshCore CLI wrapper for LoRa mesh communication.

Handles sending and receiving messages via MeshCore CLI with rate limiting
to prevent network flooding. Designed for Heltec V3 LoRa radio.
"""

import subprocess
import time
import re
from queue import Queue
from typing import Optional, Tuple
from datetime import datetime, timedelta


class MeshHandler:
    """
    Handles all MeshCore CLI communication with rate limiting.
    
    Hardware: Heltec V3 LoRa radio running latest MeshCore firmware,
    connected to Raspberry Pi via USB Serial.
    """
    
    def __init__(self, min_send_interval: float = 2.0, max_message_length: int = 200):
        """
        Initialize MeshHandler.
        
        Args:
            min_send_interval: Minimum seconds between sends (default: 2.0)
            max_message_length: Maximum message length in bytes (default: 200)
        """
        self.message_queue = Queue()
        self.last_send_time = None
        self.min_send_interval = min_send_interval
        self.max_message_length = max_message_length
    
    def listen(self) -> Optional[Tuple[str, str]]:
        """
        Polls MeshCore CLI for new messages.
        
        Returns:
            Tuple of (sender_node_id, message_text) or None if no message
        """
        try:
            # Try to receive message via MeshCore CLI
            # Note: Exact command syntax to be verified during implementation
            # Assumed: meshcore receive or meshcore listen
            result = subprocess.run(
                ["meshcore", "receive"],
                capture_output=True,
                text=True,
                timeout=1.0  # Non-blocking check
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse output - could be JSON or plain text
                # Try JSON first, fall back to plain text
                output = result.stdout.strip()
                
                # Simple parsing - adjust based on actual CLI output format
                # Example formats:
                # JSON: {"from": "!a1b2c3", "message": "hello"}
                # Plain: "!a1b2c3: hello"
                
                # Try to parse as JSON-like
                if output.startswith("{") and "from" in output.lower():
                    # Extract node_id and message from JSON-like format
                    # This is a simplified parser - adjust based on actual format
                    node_match = re.search(r'"from"\s*:\s*"([^"]+)"', output)
                    msg_match = re.search(r'"message"\s*:\s*"([^"]+)"', output)
                    
                    if node_match and msg_match:
                        node_id = node_match.group(1)
                        message = msg_match.group(1)
                        return (node_id, message)
                else:
                    # Try plain text format: "!nodeid: message"
                    if ":" in output:
                        parts = output.split(":", 1)
                        if len(parts) == 2:
                            node_id = parts[0].strip()
                            message = parts[1].strip()
                            return (node_id, message)
            
            return None
            
        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            # MeshCore CLI not found - return None (will be handled in main)
            return None
        except Exception as e:
            # Log error but don't crash
            print(f"Error listening for messages: {e}")
            return None
    
    def send(self, node_id: str, text: str):
        """
        Queue message for sending with rate limiting.
        
        Args:
            node_id: Target Node ID (e.g., "!a1b2c3")
            text: Message text to send
        """
        # Sanitize message
        sanitized = self._sanitize_message(text)
        
        # Add to queue
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
            
            # Send via MeshCore CLI
            # Note: Exact command syntax to be verified
            # Assumed: meshcore send <node_id> <message>
            result = subprocess.run(
                ["meshcore", "send", node_id, message],
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            if result.returncode == 0:
                self.last_send_time = now
            else:
                # Failed to send - put back in queue?
                # For now, just log error
                print(f"Failed to send message: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("Timeout sending message via MeshCore CLI")
        except FileNotFoundError:
            print("MeshCore CLI not found. Install meshcore-cli.")
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def _sanitize_message(self, text: str) -> str:
        """
        Remove excessive whitespace and ensure message is under max length.
        
        Args:
            text: Original message text
        
        Returns:
            Sanitized message
        """
        # Strip leading/trailing whitespace from each line
        lines = text.split('\n')
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
