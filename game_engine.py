"""
Game engine for MeshAgotchi virtual pet game.

Handles all game logic including commands, stat decay, aging, death,
and periodic notifications.
"""

import datetime
from typing import Optional, List, Tuple, Dict, Any
import database
import genetics


class GameEngine:
    """Main game engine for processing commands and managing pet state."""
    
    # Aging thresholds (in hours)
    AGE_EGG_MAX = 1
    AGE_CHILD_MAX = 24
    AGE_TEEN_MAX = 72
    AGE_ADULT_MAX = 168  # 7 days
    MAX_LIFESPAN = 336  # 14 days
    
    # Stat decay rates (per hour)
    HUNGER_DECAY = 5  # Increases (gets hungrier)
    HYGIENE_DECAY = 3  # Decreases (gets dirtier)
    HAPPINESS_DECAY = 2  # Decreases if no interaction
    ENERGY_REGEN = 10  # Regenerates naturally
    HEALTH_DECAY = 2  # When hunger < 20 or hygiene < 20
    
    # Stat thresholds
    LOW_HEALTH_THRESHOLD = 30
    LOW_HYGIENE_THRESHOLD = 30
    
    # Notification intervals (in hours)
    NOTIFICATION_INTERVAL = 1  # Minimum time between same-type notifications
    
    def __init__(self, db_path: str = "meshogotchi.db"):
        """Initialize game engine."""
        self.db_path = db_path
    
    def process_command(self, node_id: str, command_text: str):
        """
        Main entry point for processing commands.
        
        Args:
            node_id: User's Node ID
            command_text: Raw command text from user
        
        Returns:
            Response message to send back
        """
        # Parse command
        command_text = command_text.strip()
        
        if not command_text.startswith('/'):
            # Not a command, treat as unknown
            return (
                "Welcome to MeshAgotchi!\n"
                "A virtual pet game on LoRa mesh networks. "
                "Hatch and care for your unique pet by feeding, cleaning, and playing with them.\n"
                "Send /help to get started."
            )
        
        # Split command and args
        parts = command_text.split(None, 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Get user and pet
        user = database.get_or_create_user(node_id)
        pet = database.get_user_pet(node_id)
        
        # Update pet decay if pet exists
        if pet:
            self._update_pet_decay(pet['id'])
            self._check_aging(pet['id'])
            self._check_death(pet['id'])
            # Refresh pet data
            pet = database.get_user_pet(node_id)
        
        # Route to handler
        if command == '/help':
            return self._handle_help()
        elif command == '/howto':
            return self._handle_howto()
        elif command == '/hatch':
            return self._handle_hatch(node_id, user, pet)
        elif command == '/stats':
            return self._handle_stats(node_id, pet)
        elif command == '/feed':
            return self._handle_feed(node_id, pet)
        elif command == '/clean':
            return self._handle_clean(node_id, pet)
        elif command == '/play':
            return self._handle_play(node_id, pet)
        elif command == '/status':
            return self._handle_status(node_id, pet)
        elif command == '/name':
            return self._handle_name(node_id, pet, args)
        else:
            return self._handle_unknown_command()
    
    def _handle_help(self) -> str:
        """Return help message with all commands."""
        return (
            "Commands:\n"
            "/help - Help\n"
            "/howto - Game guide\n"
            "/hatch - New pet\n"
            "/stats - Stats & art\n"
            "/feed - Feed\n"
            "/clean - Clean\n"
            "/play - Play\n"
            "/status - Status\n"
            "/name <n> - Name"
        )
    
    def _handle_howto(self) -> List[str]:
        """Return comprehensive game guide split into multiple parts."""
        parts = []
        
        # Part 1: Title and How to Play
        part1 = (
            "MeshAgotchi Guide\n"
            "HOW TO PLAY:\n"
            "1. Start: /hatch\n"
            "2. Care: /feed, /clean, /play\n"
            "3. Monitor: /stats\n"
            "4. Check: /status"
        )
        parts.append(part1)
        
        # Part 2: Stats
        part2 = (
            "STATS:\n"
            "- Health: Drops if hunger>80 or hygiene<20\n"
            "- Hunger: Increases, use /feed\n"
            "- Hygiene: Decreases, use /clean\n"
            "- Happiness: Use /play\n"
            "- Energy: Regen 10/hr, need 20 for /play"
        )
        parts.append(part2)
        
        # Part 3: Evolution Stages
        part3 = (
            "EVOLUTION:\n"
            "- Egg: 0-1hr\n"
            "- Child: 1-24hrs\n"
            "- Teen: 24-72hrs\n"
            "- Adult: 72-168hrs\n"
            "- Elder: 168+hrs"
        )
        parts.append(part3)
        
        # Part 4: Commands
        part4 = (
            "COMMANDS:\n"
            "/hatch - New pet\n"
            "/stats - Stats & art\n"
            "/feed - Decrease hunger\n"
            "/clean - Increase hygiene\n"
            "/play - Increase happiness"
        )
        parts.append(part4)
        
        # Part 5: More Commands and Tips
        part5 = (
            "/status - Quick status\n"
            "/name <n> - Name pet\n"
            "/help - List commands\n"
            "/howto - This guide\n\n"
            "TIPS:\n"
            "- Check /status regularly\n"
            "- Keep hunger<80, hygiene>20"
        )
        parts.append(part5)
        
        # Part 6: Final Tips
        part6 = (
            "- Energy regens auto\n"
            "- Wait if too low to play\n"
            "- Each generation unique\n"
            "based on Node ID"
        )
        parts.append(part6)
        
        # Add counters to each part and ensure they're under 200 chars
        total_parts = len(parts)
        result = []
        for i, part in enumerate(parts, 1):
            counter = f" ({i}/{total_parts})"
            # Ensure part + counter is under 200 chars
            max_part_len = 200 - len(counter)
            if len(part) > max_part_len:
                part = part[:max_part_len - 3] + "..."
            result.append(part + counter)
        
        return result
    
    def _handle_hatch(self, node_id: str, user: Dict, pet: Optional[Dict]) -> str:
        """Handle /hatch command - create new pet."""
        # Check if user already has a living pet
        if pet and pet.get('is_alive'):
            return "You already have a living pet! Use /stats to check on them."
        
        # Create new pet
        generation = user.get('total_pets_raised', 0) + 1
        new_pet = database.create_pet(node_id, generation)
        
        return (
            f"Signal acquired! Pet Generation {generation} hatched!\n"
            "Use /stats to see your new pet."
        )
    
    def _handle_stats(self, node_id: str, pet: Optional[Dict]) -> str:
        """Handle /stats command - show pet stats and ASCII art."""
        if not pet:
            return "No active pet. Use /hatch to create one."
        
        if not pet.get('is_alive'):
            return "Your pet has died. Use /hatch to start a new generation."
        
        # Generate ASCII art
        ascii_art = genetics.render_pet(
            node_id,
            pet['dna_seed'],
            pet['age_stage'],
            pet.get('name')
        )
        
        # Build stats message
        name_line = f"Name: {pet.get('name', 'Unnamed')}" if pet.get('name') else ""
        stats = (
            f"{ascii_art}\n"
            f"Age: {pet['age_stage']}\n"
            f"Health: {pet['health']}/100\n"
            f"Hunger: {pet['hunger']}/100\n"
            f"Hygiene: {pet['hygiene']}/100\n"
            f"Happiness: {pet['happiness']}/100\n"
            f"Energy: {pet['energy']}/100"
        )
        
        if name_line:
            stats = f"{name_line}\n{stats}"
        
        # Add flavor text
        flavor = self._get_flavor_text(pet)
        if flavor:
            stats += f"\n{flavor}"
        
        return stats
    
    def _handle_feed(self, node_id: str, pet: Optional[Dict]) -> str:
        """Handle /feed command - increase hunger."""
        if not pet:
            return "No active pet. Use /hatch to create one."
        
        if not pet.get('is_alive'):
            return "Your pet has died. Use /hatch to start a new generation."
        
        # Increase hunger (decrease hunger value)
        new_hunger = max(0, min(100, pet['hunger'] - 30))
        database.update_pet_stats(pet['id'], {
            'hunger': new_hunger,
            'last_interaction': datetime.datetime.now().isoformat()
        })
        
        return "Current supplied. Hunger decreased."
    
    def _handle_clean(self, node_id: str, pet: Optional[Dict]) -> str:
        """Handle /clean command - increase hygiene."""
        if not pet:
            return "No active pet. Use /hatch to create one."
        
        if not pet.get('is_alive'):
            return "Your pet has died. Use /hatch to start a new generation."
        
        # Increase hygiene
        new_hygiene = max(0, min(100, pet['hygiene'] + 30))
        database.update_pet_stats(pet['id'], {
            'hygiene': new_hygiene,
            'last_interaction': datetime.datetime.now().isoformat()
        })
        
        return "Buffer cleared. Hygiene restored."
    
    def _handle_play(self, node_id: str, pet: Optional[Dict]) -> str:
        """Handle /play command - increase happiness, decrease energy."""
        if not pet:
            return "No active pet. Use /hatch to create one."
        
        if not pet.get('is_alive'):
            return "Your pet has died. Use /hatch to start a new generation."
        
        if pet['energy'] < 20:
            return "Energy too low. Pet needs rest."
        
        # Increase happiness, decrease energy
        new_happiness = max(0, min(100, pet['happiness'] + 25))
        new_energy = max(0, pet['energy'] - 20)
        
        database.update_pet_stats(pet['id'], {
            'happiness': new_happiness,
            'energy': new_energy,
            'last_interaction': datetime.datetime.now().isoformat()
        })
        
        return "Play session complete. Happiness increased!"
    
    def _handle_status(self, node_id: str, pet: Optional[Dict]) -> str:
        """Handle /status command - quick status check."""
        if not pet:
            return "No active pet. Use /hatch to create one."
        
        if not pet.get('is_alive'):
            return f"Pet died: {pet.get('death_reason', 'Unknown')}. Use /hatch for new pet."
        
        # Calculate time alive
        birth_time = datetime.datetime.fromisoformat(pet['birth_time'])
        now = datetime.datetime.now()
        hours_old = (now - birth_time).total_seconds() / 3600.0
        
        # Format time alive
        if hours_old < 24:
            time_alive = f"{hours_old:.1f} hours"
        else:
            days = hours_old / 24.0
            time_alive = f"{days:.1f} days ({hours_old:.1f} hours)"
        
        # Calculate time until next evolution
        age_stage = pet['age_stage']
        time_until_evolution = None
        
        if age_stage == 'egg':
            hours_until = self.AGE_CHILD_MAX - hours_old
            if hours_until > 0:
                time_until_evolution = f"{hours_until:.1f} hours until child"
        elif age_stage == 'child':
            hours_until = self.AGE_TEEN_MAX - hours_old
            if hours_until > 0:
                if hours_until < 24:
                    time_until_evolution = f"{hours_until:.1f} hours until teen"
                else:
                    days_until = hours_until / 24.0
                    time_until_evolution = f"{days_until:.1f} days until teen"
        elif age_stage == 'teen':
            hours_until = self.AGE_TEEN_MAX - hours_old
            if hours_until > 0:
                if hours_until < 24:
                    time_until_evolution = f"{hours_until:.1f} hours until adult"
                else:
                    days_until = hours_until / 24.0
                    time_until_evolution = f"{days_until:.1f} days until adult"
        elif age_stage == 'adult':
            hours_until = self.AGE_ADULT_MAX - hours_old
            if hours_until > 0:
                if hours_until < 24:
                    time_until_evolution = f"{hours_until:.1f} hours until elder"
                else:
                    days_until = hours_until / 24.0
                    time_until_evolution = f"{days_until:.1f} days until elder"
        # elder -> death: don't show time until death
        
        # Build status message
        status = f"Status: {age_stage}\n"
        status += f"Health: {pet['health']}/100\n"
        status += f"Alive: {time_alive}"
        
        if time_until_evolution:
            status += f"\nNext evolution: {time_until_evolution}"
        
        return status
    
    def _handle_name(self, node_id: str, pet: Optional[Dict], name: str) -> str:
        """Handle /name command - assign name to pet."""
        if not pet:
            return "No active pet. Use /hatch to create one."
        
        if not pet.get('is_alive'):
            return "Your pet has died. Use /hatch to start a new generation."
        
        if not name or not name.strip():
            return "Usage: /name <name>"
        
        # Sanitize name (max 20 chars)
        name = name.strip()[:20]
        
        database.update_pet_stats(pet['id'], {'name': name})
        
        return f"Pet named: {name}"
    
    def _handle_unknown_command(self) -> str:
        """Handle unknown commands."""
        return (
            "Welcome to MeshAgotchi!\n"
            "A virtual pet game on LoRa mesh networks. "
            "Hatch and care for your unique pet by feeding, cleaning, and playing with them.\n"
            "Send /help to get started."
        )
    
    def _update_pet_decay(self, pet_id: int):
        """Calculate time since last interaction and apply stat decay."""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
        pet_row = cursor.fetchone()
        
        if not pet_row:
            conn.close()
            return
        
        pet = dict(pet_row)
        
        # Calculate hours since last interaction
        last_interaction = datetime.datetime.fromisoformat(pet['last_interaction'])
        now = datetime.datetime.now()
        hours_elapsed = (now - last_interaction).total_seconds() / 3600.0
        
        if hours_elapsed <= 0:
            conn.close()
            return
        
        # Apply decay
        new_hunger = min(100, pet['hunger'] + int(self.HUNGER_DECAY * hours_elapsed))
        new_hygiene = max(0, pet['hygiene'] - int(self.HYGIENE_DECAY * hours_elapsed))
        new_happiness = max(0, pet['happiness'] - int(self.HAPPINESS_DECAY * hours_elapsed))
        new_energy = min(100, pet['energy'] + int(self.ENERGY_REGEN * hours_elapsed))
        
        # Health decay if hunger or hygiene too low (check new values after decay)
        new_health = pet['health']
        if new_hunger > 80 or new_hygiene < 20:  # Hunger > 80 means very hungry, hygiene < 20 means very dirty
            new_health = max(0, pet['health'] - int(self.HEALTH_DECAY * hours_elapsed))
        
        # Update stats
        database.update_pet_stats(pet_id, {
            'hunger': new_hunger,
            'hygiene': new_hygiene,
            'happiness': new_happiness,
            'energy': new_energy,
            'health': new_health,
            'last_interaction': now.isoformat()
        })
        
        conn.close()
    
    def _check_aging(self, pet_id: int):
        """Update age_stage based on hours since birth."""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
        pet_row = cursor.fetchone()
        
        if not pet_row:
            conn.close()
            return
        
        pet = dict(pet_row)
        
        # Calculate hours since birth
        birth_time = datetime.datetime.fromisoformat(pet['birth_time'])
        now = datetime.datetime.now()
        hours_old = (now - birth_time).total_seconds() / 3600.0
        
        # Determine age stage
        new_stage = pet['age_stage']
        if hours_old <= self.AGE_EGG_MAX:
            new_stage = 'egg'
        elif hours_old <= self.AGE_CHILD_MAX:
            new_stage = 'child'
        elif hours_old <= self.AGE_TEEN_MAX:
            new_stage = 'teen'
        elif hours_old <= self.AGE_ADULT_MAX:
            new_stage = 'adult'
        else:
            new_stage = 'elder'
        
        # Update if changed
        if new_stage != pet['age_stage']:
            # Store old stage for upgrade detection before updating
            old_stage = pet['age_stage']
            database.update_pet_stats(pet_id, {
                'age_stage': new_stage,
                'last_age_stage': old_stage  # Store old stage for upgrade detection
            })
        
        conn.close()
    
    def _check_death(self, pet_id: int):
        """Check if pet should die."""
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
        pet_row = cursor.fetchone()
        
        if not pet_row:
            conn.close()
            return
        
        pet = dict(pet_row)
        
        if not pet.get('is_alive'):
            conn.close()
            return
        
        # Check death conditions
        death_reason = None
        
        if pet['health'] <= 0:
            death_reason = "Health depleted (neglect)"
        else:
            # Check age
            birth_time = datetime.datetime.fromisoformat(pet['birth_time'])
            now = datetime.datetime.now()
            hours_old = (now - birth_time).total_seconds() / 3600.0
            
            if hours_old >= self.MAX_LIFESPAN:
                death_reason = "Natural death (old age)"
        
        if death_reason:
            database.mark_pet_dead(pet_id, death_reason)
        
        conn.close()
    
    def check_and_send_notifications(self) -> List[Tuple[str, str]]:
        """
        Periodic notification system.
        Checks all alive pets and generates notifications.
        
        Returns:
            List of (node_id, message) tuples to send
        """
        notifications = []
        pets = database.get_all_alive_pets()
        
        for pet in pets:
            node_id = pet['owner_id']
            
            # Update aging first to detect upgrades
            self._check_aging(pet['id'])
            # Refresh pet data after aging check
            updated_pet = database.get_user_pet(node_id)
            if not updated_pet or not updated_pet.get('is_alive'):
                continue
            pet = updated_pet
            
            # Check for age upgrade
            age_notification = self._check_age_upgrade(pet)
            if age_notification:
                notifications.append((node_id, age_notification))
                # Update last_age_stage to current to prevent duplicate notifications
                database.update_pet_stats(pet['id'], {'last_age_stage': pet['age_stage']})
                database.update_pet_notification_time(pet['id'])
                continue  # Age upgrade is priority, skip other checks
            
            # Check health notification
            health_notification = self._check_health_notification(pet)
            if health_notification:
                notifications.append((node_id, health_notification))
                database.update_pet_notification_time(pet['id'])
                continue
            
            # Check hygiene notification
            hygiene_notification = self._check_hygiene_notification(pet)
            if hygiene_notification:
                notifications.append((node_id, hygiene_notification))
                database.update_pet_notification_time(pet['id'])
        
        return notifications
    
    def _check_age_upgrade(self, pet: Dict) -> Optional[str]:
        """Detect if pet has aged up since last check."""
        current_stage = pet.get('age_stage')
        last_stage = pet.get('last_age_stage')
        
        if current_stage != last_stage and last_stage is not None:
            return self._generate_age_upgrade_message(pet, last_stage, current_stage)
        
        return None
    
    def _check_health_notification(self, pet: Dict) -> Optional[str]:
        """Check if health is critically low."""
        if pet['health'] >= self.LOW_HEALTH_THRESHOLD:
            return None
        
        # Check if enough time has passed since last notification
        last_notification = pet.get('last_notification')
        if last_notification:
            last_notif_time = datetime.datetime.fromisoformat(last_notification)
            hours_since = (datetime.datetime.now() - last_notif_time).total_seconds() / 3600.0
            if hours_since < self.NOTIFICATION_INTERVAL:
                return None
        
        return "WARNING: Health critical (<30). Packet loss imminent. Use /feed and /clean."
    
    def _check_hygiene_notification(self, pet: Dict) -> Optional[str]:
        """Check if hygiene is critically low."""
        if pet['hygiene'] >= self.LOW_HYGIENE_THRESHOLD:
            return None
        
        # Check if enough time has passed since last notification
        last_notification = pet.get('last_notification')
        if last_notification:
            last_notif_time = datetime.datetime.fromisoformat(last_notification)
            hours_since = (datetime.datetime.now() - last_notif_time).total_seconds() / 3600.0
            if hours_since < self.NOTIFICATION_INTERVAL:
                return None
        
        return "WARNING: Buffer overflow detected. Hygiene critical. Use /clean."
    
    def _generate_age_upgrade_message(self, pet: Dict, old_stage: str, new_stage: str) -> str:
        """Generate celebration message for aging up."""
        messages = {
            ('egg', 'child'): "Signal acquired! Your pet has hatched! Use /stats to see them.",
            ('child', 'teen'): "Firmware update complete! Your pet is now a Teen.",
            ('teen', 'adult'): "System upgrade successful! Your pet reached Adulthood!",
            ('adult', 'elder'): "Legacy mode activated. Your pet is now an Elder.",
        }
        
        key = (old_stage, new_stage)
        return messages.get(key, f"Age upgrade: {old_stage} -> {new_stage}")
    
    def _get_flavor_text(self, pet: Dict) -> str:
        """Generate MeshCore-themed status messages."""
        messages = []
        
        if pet['hunger'] > 80:
            messages.append("Low voltage detected. Supply current.")
        if pet['hygiene'] < 20:
            messages.append("Buffer overflow! CRC mismatch in sector 4 (Poop).")
        if pet['happiness'] > 80:
            messages.append("Signal Strength: 100%.")
        if pet['health'] < 20:
            messages.append("Packet loss critical... disconnecting...")
        
        return " ".join(messages) if messages else ""
