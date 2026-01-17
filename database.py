"""
SQLite database management for MeshAgotchi.

Handles all database operations for users and pets.
"""

import sqlite3
import datetime
from typing import Optional, Dict, List, Tuple, Any


DB_PATH = "meshogotchi.db"


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_database():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            node_id TEXT PRIMARY KEY,
            current_pet_id INTEGER,
            total_pets_raised INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Pets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id TEXT NOT NULL,
            generation INTEGER NOT NULL,
            dna_seed TEXT NOT NULL,
            name TEXT,
            birth_time TIMESTAMP NOT NULL,
            last_interaction TIMESTAMP NOT NULL,
            last_notification TIMESTAMP,
            last_age_stage TEXT,
            age_stage TEXT NOT NULL,
            hunger INTEGER DEFAULT 50,
            hygiene INTEGER DEFAULT 50,
            happiness INTEGER DEFAULT 50,
            energy INTEGER DEFAULT 100,
            health INTEGER DEFAULT 100,
            is_alive BOOLEAN DEFAULT 1,
            death_reason TEXT,
            FOREIGN KEY (owner_id) REFERENCES users(node_id)
        )
    """)
    
    # Contacts table - maps client names to node IDs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            name TEXT PRIMARY KEY,
            node_id TEXT NOT NULL,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # BLE devices table - stores successfully connected BLE devices
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ble_devices (
            address TEXT PRIMARY KEY,
            name TEXT,
            pairing_code TEXT,
            last_connected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def get_or_create_user(node_id: str) -> Dict[str, Any]:
    """
    Get user by node_id, or create if doesn't exist.
    
    Returns:
        Dictionary with user data
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Try to get existing user
    cursor.execute("SELECT * FROM users WHERE node_id = ?", (node_id,))
    row = cursor.fetchone()
    
    if row:
        user = dict(row)
    else:
        # Create new user
        cursor.execute("""
            INSERT INTO users (node_id, current_pet_id, total_pets_raised)
            VALUES (?, NULL, 0)
        """, (node_id,))
        conn.commit()
        
        # Fetch the newly created user
        cursor.execute("SELECT * FROM users WHERE node_id = ?", (node_id,))
        row = cursor.fetchone()
        user = dict(row)
    
    conn.close()
    return user


def get_user_pet(node_id: str) -> Optional[Dict[str, Any]]:
    """
    Get current active pet for a user.
    
    Returns:
        Dictionary with pet data, or None if no active pet
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get user first
    cursor.execute("SELECT current_pet_id FROM users WHERE node_id = ?", (node_id,))
    user_row = cursor.fetchone()
    
    if not user_row or user_row['current_pet_id'] is None:
        conn.close()
        return None
    
    pet_id = user_row['current_pet_id']
    
    # Get pet
    cursor.execute("SELECT * FROM pets WHERE id = ? AND is_alive = 1", (pet_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_all_alive_pets() -> List[Dict[str, Any]]:
    """
    Get all living pets for notification checking.
    
    Returns:
        List of pet dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM pets WHERE is_alive = 1")
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]


def create_pet(owner_id: str, generation: int) -> Dict[str, Any]:
    """
    Create a new pet.
    
    Args:
        owner_id: Node ID of the owner
        generation: Generation number (1, 2, 3...)
    
    Returns:
        Dictionary with new pet data
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Generate DNA seed
    timestamp = datetime.datetime.now().isoformat()
    from genetics import hash_generation_seed
    dna_seed = hash_generation_seed(owner_id, timestamp, generation)
    
    # Create pet
    now = datetime.datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO pets (
            owner_id, generation, dna_seed, birth_time, last_interaction,
            last_age_stage, age_stage, hunger, hygiene, happiness,
            energy, health, is_alive
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        owner_id, generation, dna_seed, now, now,
        'egg', 'egg', 50, 50, 50, 100, 100
    ))
    
    pet_id = cursor.lastrowid
    
    # Update user's current_pet_id and increment total_pets_raised
    cursor.execute("""
        UPDATE users 
        SET current_pet_id = ?, total_pets_raised = total_pets_raised + 1
        WHERE node_id = ?
    """, (pet_id, owner_id))
    
    conn.commit()
    
    # Fetch the new pet
    cursor.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    return dict(row)


def update_pet_stats(pet_id: int, stats_dict: Dict[str, Any]):
    """
    Update pet stats.
    
    Args:
        pet_id: Pet ID
        stats_dict: Dictionary of fields to update (e.g., {'hunger': 70, 'health': 80})
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build update query dynamically
    set_clauses = []
    values = []
    
    for key, value in stats_dict.items():
        set_clauses.append(f"{key} = ?")
        values.append(value)
    
    if set_clauses:
        query = f"UPDATE pets SET {', '.join(set_clauses)} WHERE id = ?"
        values.append(pet_id)
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()


def update_pet_notification_time(pet_id: int):
    """Update last_notification timestamp for a pet."""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.datetime.now().isoformat()
    cursor.execute("UPDATE pets SET last_notification = ? WHERE id = ?", (now, pet_id))
    
    conn.commit()
    conn.close()


def mark_pet_dead(pet_id: int, reason: str):
    """
    Mark a pet as dead.
    
    Args:
        pet_id: Pet ID
        reason: Reason for death
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE pets 
        SET is_alive = 0, death_reason = ?
        WHERE id = ?
    """, (reason, pet_id))
    
    # Clear user's current_pet_id
    cursor.execute("""
        UPDATE users 
        SET current_pet_id = NULL
        WHERE current_pet_id = ?
    """, (pet_id,))
    
    conn.commit()
    conn.close()


def store_contact(name: str, node_id: str):
    """
    Store or update a contact mapping (name -> node_id).
    
    Args:
        name: Client name (e.g., "Mattd-t1000-002")
        node_id: Node ID (e.g., "0b2c2328618f")
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    name = name.strip()
    node_id = node_id.strip()
    
    if not name or not node_id:
        conn.close()
        return
    
    now = datetime.datetime.now().isoformat()
    cursor.execute("""
        INSERT OR REPLACE INTO contacts (name, node_id, last_seen, updated_at)
        VALUES (?, ?, ?, ?)
    """, (name, node_id, now, now))
    
    conn.commit()
    conn.close()


def get_node_id_by_name(name: str) -> Optional[str]:
    """
    Get node ID for a given client name.
    
    Args:
        name: Client name (e.g., "Mattd-t1000-002")
        
    Returns:
        Node ID if found, None otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    name = name.strip()
    cursor.execute("SELECT node_id FROM contacts WHERE name = ?", (name,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return row['node_id']
    return None


def get_all_contacts() -> List[Dict[str, Any]]:
    """
    Get all contacts.
    
    Returns:
        List of contact dictionaries with name and node_id
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, node_id, last_seen FROM contacts ORDER BY name")
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]


def store_ble_device(address: str, name: str, pairing_code: Optional[str] = None):
    """
    Store or update a BLE device connection info.
    
    Args:
        address: BLE MAC address (e.g., "C2:2B:A1:D5:3E:B6")
        name: Device name/advertisement name
        pairing_code: Pairing code (if provided)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    address = address.strip().upper()
    name = name.strip() if name else None
    
    if not address:
        conn.close()
        return
    
    now = datetime.datetime.now().isoformat()
    
    # Check if device already exists
    cursor.execute("SELECT address FROM ble_devices WHERE address = ?", (address,))
    exists = cursor.fetchone()
    
    if exists:
        # Update existing device
        if pairing_code:
            cursor.execute("""
                UPDATE ble_devices 
                SET name = ?, pairing_code = ?, last_connected = ?
                WHERE address = ?
            """, (name, pairing_code, now, address))
        else:
            cursor.execute("""
                UPDATE ble_devices 
                SET name = ?, last_connected = ?
                WHERE address = ?
            """, (name, now, address))
    else:
        # Insert new device
        cursor.execute("""
            INSERT INTO ble_devices (address, name, pairing_code, last_connected, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (address, name, pairing_code, now, now))
    
    conn.commit()
    conn.close()


def get_stored_ble_device() -> Optional[Dict[str, Any]]:
    """
    Get the most recently connected BLE device.
    
    Returns:
        Dictionary with device info (address, name, pairing_code) or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT address, name, pairing_code, last_connected 
        FROM ble_devices 
        ORDER BY last_connected DESC 
        LIMIT 1
    """)
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return dict(row)
    return None


def update_ble_device_connection(address: str):
    """
    Update the last_connected timestamp for a BLE device.
    
    Args:
        address: BLE MAC address
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    address = address.strip().upper()
    now = datetime.datetime.now().isoformat()
    
    cursor.execute("""
        UPDATE ble_devices 
        SET last_connected = ?
        WHERE address = ?
    """, (now, address))
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Test database initialization
    init_database()
    print("Database initialized successfully!")
    
    # Test user creation
    user = get_or_create_user("!test123")
    print(f"Created/found user: {user}")
    
    # Test pet creation
    pet = create_pet("!test123", 1)
    print(f"Created pet: {pet}")
