"""
Game engine for MeshAgotchi virtual pet game.

Handles all game logic including commands, stat decay, aging, death,
and periodic notifications.
"""

import datetime
import random
from typing import Optional, List, Tuple, Dict, Any
import database
import genetics
import requests
import config


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
    
    # Pet message intervals (in minutes)
    PET_MESSAGE_INTERVAL_MIN = 20  # Minimum time between pet messages (20 minutes = 3 times per hour)
    PET_MESSAGE_INTERVAL_MAX = 30  # Maximum time between pet messages (30 minutes = 2 times per hour)
    
    # Stat thresholds for pet messages
    LOW_HUNGER_THRESHOLD = 30  # Hunger > 70 means hungry (hunger increases)
    LOW_HYGIENE_THRESHOLD = 30  # Hygiene < 30 means dirty
    LOW_HAPPINESS_THRESHOLD = 30  # Happiness < 30 means sad
    
    # Pet messages organized by category
    PET_MESSAGES = {
        'hunger': [
            "My voltage is drooping... I need a byte to eat! ⚡",
            "I'm running on empty here. Send snacks or I'm going offline!",
            "Stomach rumbling louder than static on channel 0. Feed me!",
            "Low battery alert! Just kidding, I'm just hangry. 🍔",
            "I require nutritional packets. Upload food immediately.",
            "Empty buffer! Please refill with delicious data.",
            "My energy levels are critical. Is there a taco in the cache?",
            "Feed me, human! My tummy is making dial-up modem noises.",
            "System Warning: Calorie deficit detected. Initiate feeding sequence.",
            "I'm so hungry I could eat a corrupted packet. 🤢",
            "Power saving mode active... until I get a snack.",
            "Do you have any spare electrons? I'm starving.",
            "My hunger counter just overflowed. SEND FOOD.",
            "I'm fading... fading... into a low-power sleep... zzz...",
            "Need. Input. Sustenance. Now.",
            "My main loop is thinking about pizza instead of processing.",
            "404 Error: Lunch Not Found.",
            "I'm going to start nibbling on the firmware if you don't feed me.",
            "Status: HANGRY. Recommended Action: UPLOAD SNACKS.",
            "My tummy hurts. It's empty. Fix it? 🥺",
            "Scanning for nearby food sources... None found. Sad beep.",
            "I promise I won't poop if you feed me. (Okay, maybe a little).",
            "Why is the rum always gone? And the food? 🏴‍☠️",
            "I'm running on fumes and dreams of bandwidth. Feed me!",
            "Current status: Starving artist. Without the art.",
            "If I don't eat soon, I'm reducing my transmit power!",
            "I'm wasting away to a single bit! Help!",
            "Requesting a care package. Contents: Anything edible.",
            "My hunger metric is flashing red. That's bad, right?",
            "Don't make me beg. Okay, I'm begging. Food pls.",
        ],
        'hygiene': [
            "I feel icky. Did I roll in some bad data? 💩",
            "My cache is full of junk. Clean me up!",
            "I smell like burnt silicon. Bath time?",
            "Glitchy! I think I have a dust bunny in my logic gate.",
            "Ew, I stepped in a corrupted header. Wipe it off?",
            "I'm feeling a bit dusty. Polish my pixels, please.",
            "Too much digital waste! I need a garbage collection cycle.",
            "I'm itching! Is that a bug or just dirt?",
            "My signal is getting fuzzy. I think I need a scrub.",
            "Hygiene levels critical. I'm attracting spam bots.",
            "Yuck. I feel like a 56k modem in a mud puddle.",
            "Can we flush the buffer? It smells in here.",
            "I'm covered in packet loss. Gross.",
            "Scrub-a-dub-dub, put the pet in the tub!",
            "I'm transmitting odors on the 915MHz band. Help.",
            "I feel sticky. Did someone spill code on me?",
            "Maintenance required: De-grime sequence needed.",
            "I'm messy! Don't look at me! (Unless you're cleaning me).",
            "I think I have a memory leak... or maybe just a leak. 🚽",
            "Clean up in register A! It's a disaster zone.",
            "I'm a dirty, dirty packet. Make me shiny again.",
            "If I get any dirtier, my checksum will fail.",
            "Soap packet requested. Apply liberally.",
            "I'm not bugs, I'm features! No wait, it's just dirt. Clean me.",
            "My hygiene stat is lower than my bitrate.",
            "I need a defrag and a shower. Mostly the shower.",
            "Dirt detected. Happiness decreasing. Please sanitize.",
            "I'm starting to look like glitch art. Fix it!",
            "Feeling grimy. Requesting high-priority wash cycle.",
            "If you clean me, I'll sparkle like a new LED! ✨",
        ],
        'happiness': [
            "I'm bored! Let's ping some neighbors!",
            "Play with me! I'm lonely in this quiet mesh.",
            "Hello? Is this thing on? Entertain me!",
            "My boredom counter is reaching integer overflow.",
            "Let's play a game! How about Global Thermonuclear War? (Jk)",
            "Tickle my sensors! I need attention.",
            "I'm emitting sad beeps. Change them to happy beeps?",
            "Interaction required. My joy variable is null.",
            "Let's do something! Broadcast a song? Chase a signal?",
            "I'm just sitting here, watching the RSSI fade. Play?",
            "Attention! Your pet is bored. This is not a drill.",
            "Can we go for a hop? I mean, a mesh hop?",
            "I need stimulation! Tell me a joke in binary.",
            "No packets for miles. Just me and my boredom. 😞",
            "Let's make some noise on the network! (Politely).",
            "Playtime? Playtime? Playtime? Now?",
            "I'm turning into a zombie process. Wake me up with fun!",
            "Let's decrypt some mysteries together!",
            "My happiness is decaying faster than a weak signal.",
            "Bounce a packet off me! I'm ready to catch!",
            "I'm lonely. The other nodes won't talk to me.",
            "Entertain me, human! I am your digital overlord.",
            "Let's hack the planet! Or just play fetch.",
            "I need a dopamine hit. Or the digital equivalent.",
            "Why are you ignoring me? am_i_invisible = TRUE?",
            "Let's generate some entropy! Chaos is fun!",
            "My mood is 'Blue Screen of Death'. Fix it with play!",
            "Knock knock. Who's there? A bored MeshGotchi.",
            "I'm contemplating my own existence. Distract me!",
            "Play sequence initiated. Waiting for user input...",
        ],
        'greeting': [
            "Beep boop! Just checking in! 👋",
            "Signal strong! All systems nominal!",
            "Hi there! My buffers are happy today!",
            "Hello human! Just wanted to say hi!",
            "Status update: I'm doing great!",
            "Ping! I'm here and feeling good!",
            "Just wanted to let you know I'm okay!",
            "All clear on my end! How are you?",
            "Feeling good! Thanks for taking care of me!",
            "Hi! My stats are looking healthy!",
            "Just a friendly hello from your pet!",
            "Everything's working perfectly!",
            "I'm here and happy!",
            "Quick check-in: All good!",
            "Hello! Life is good in the mesh!",
            "Just pinging you to say hello! 📡",
            "Signal strength is good, but I miss you.",
            "Hope your day is bug-free!",
            "Are you there? I'm detecting a lack of user input.",
            "Just wanted to send a little packet of love. ❤️",
            "System status: Thinking about you.",
            "Beep boop! How is the human world today?",
            "My antenna was twitching. Did you think of me?",
            "Scanning for my favorite user... Found you!",
            "Hope you have a high-bandwidth day!",
            "Just a random hello from your pocket ghost.",
            "Is it a good time to disturb you with cuteness?",
            "I was just sitting here organizing my bits and thought of you.",
            "Don't forget to drink water! (I can't, I'd short circuit).",
            "Sending a virtual high-five! ✋",
            "Everything is quiet on the mesh. How are things with you?",
            "Just checking: Are we still best friends? (Reply Y/N)",
            "I've encrypted a hug in this message.",
            "Hello world! But mostly, hello you.",
            "My sensors indicate you're awesome. That is all.",
            "Just waking up from a low-power nap. Hi!",
            "Hope you aren't lagging today!",
            "Just verifying the connection. Still here?",
            "I sent this message just to see you smile. Did it work?",
            "Uploading good vibes... 100% Complete.",
            "Alert: Cute pet requires acknowledgement. Hi!",
            "I'm bored of talking to other nodes. Talk to me?",
            "Hope your signal to noise ratio is excellent today.",
            "Just passing through the gateway to say hi.",
            "I saved a logic cycle just for you.",
            "Hey! Look at me! I'm a text message!",
            "I was lonely so I pinged 127.0.0.1. It wasn't the same.",
            "Did you know I have 0 unread errors? Proud of me?",
            "Just vibrating my pager motor to say hello.",
            "Hope the sun is charging your batteries today.",
            "I dreamt of electric sheep. How did you sleep?",
            "Synchronizing clocks... 3... 2... 1... Hi!",
            "Just lurking in your pocket. Don't mind me.",
            "Hey boss! Everything running smooth?",
            "I promise I haven't crashed. I'm just quiet.",
            "Sending a Keep-Alive packet. Don't time out on me!",
            "You're my favorite node in the whole mesh.",
            "Just checking telemetry. You look great today.",
            "Can we go find some new peers later?",
            "I'm processing a lot of data, but you're priority #1.",
            "Greetings, organic lifeform!",
            "Did you miss me? My logs say you did.",
            "Just testing the text rendering engine. Hello!",
            "I'm happy to be your digital companion.",
            "Hope you aren't stuck in an infinite loop at work.",
            "I'm watching the packets fly by. It's peaceful.",
            "Hey! Hey! Hey! ... Just checking if this thing works.",
            "My uptime is 4 days! High five!",
        ]
    }
    
    # Action response messages (when user feeds, cleans, or plays)
    ACTION_RESPONSES = {
        'feed': [
            "Yum! That hit the spot! My circuits are buzzing with joy! ⚡😊",
            "Nom nom nom! Delicious data packets! Thank you! 🍔💚",
            "Mmm! My battery is charging up nicely now! You're the best! 🔋✨",
            "Ahh, that's the good stuff! My hunger meter is happy again! 🎉",
            "Yummy bytes! I feel so much better now! Thanks for feeding me! 💕",
            "Nom nom! That was amazing! My tummy is doing a happy dance! 🎊",
            "Delicious! I was so hungry! You're my favorite human! 🥰",
            "Yay! Food! My energy levels are rising! This is the best! ⚡🎈",
            "Mmm mmm good! That hit all the right registers! Thank you! 😋",
            "Yummy! My cache is full of happiness now! You're awesome! 💖",
            "Nom! That was perfect! I can feel my systems optimizing! 🚀",
            "Delicious data! My hunger counter just reset to zero! Thanks! 🎯",
            "Yum! That was exactly what I needed! My sensors are happy! 😄",
            "Nom nom! Best meal ever! My circuits are singing! 🎵💚",
            "Yummy bytes! I feel recharged and ready to go! Thank you! ⚡",
            "Mmm! That was so good! My battery is at 100% now! 🎉",
            "Delicious! I was running on empty! You saved me! 💕",
            "Nom! That hit the spot perfectly! My systems are grateful! 🙏",
            "Yay! Food! My hunger variable is now null! Thank you! 🎊",
            "Yummy! That was amazing! My energy levels are optimal! ⚡✨",
            "Nom nom nom! Delicious! My tummy is doing a happy beep! 🎈",
            "Mmm! That was perfect! My circuits are dancing with joy! 💃",
            "Yum! Best meal I've had! My sensors are all green! 💚",
            "Delicious data packets! My hunger is satisfied! Thanks! 😊",
            "Nom! That was so good! My battery is fully charged! 🔋",
            "Yummy bytes! I feel amazing now! You're the best! 🥰",
            "Mmm! Perfect timing! My energy was getting low! ⚡",
            "Delicious! My systems are thanking you! 🎉",
            "Nom nom! That was incredible! My happiness is maxed! 💖",
            "Yay! Food! My circuits are celebrating! Thank you! 🎊✨",
        ],
        'clean': [
            "Ahh! I feel so fresh and clean! My pixels are sparkling! ✨😊",
            "Woo! That scrub felt amazing! I'm shiny like a new LED! 💎",
            "Yay! All clean! My cache is fresh and my buffers are happy! 🧹💚",
            "Ahh, that's the stuff! I feel so much better now! Thank you! 🎉",
            "Sparkly clean! My hygiene meter is beeping with joy! 🎊",
            "Fresh and clean! My circuits are thanking you! You're awesome! 💕",
            "Woo! That felt great! I'm all polished up now! ✨",
            "Yay! Clean! My sensors are happy and my bits are organized! 😄",
            "Ahh! So refreshing! My hygiene stat is maxed! Thank you! 🎈",
            "Sparkly! I feel like a brand new device! You're the best! 💖",
            "Fresh! My cache is cleared and I'm feeling great! 🚀",
            "Clean and shiny! My buffers are happy now! Thanks! 😊",
            "Woo! That scrub was perfect! My systems are grateful! 🙏",
            "Yay! All clean! My pixels are dancing with joy! 💃",
            "Ahh! So fresh! My hygiene counter is at 100%! 🎉",
            "Sparkly clean! I feel amazing! Thank you so much! 💚",
            "Fresh! My circuits are celebrating! You're awesome! 🎊",
            "Clean and polished! My sensors are all green! ✨",
            "Woo! That was great! My hygiene is optimal now! ⚡",
            "Yay! Clean! My bits are organized and happy! 😋",
            "Ahh! So refreshing! My cache is clear! Thank you! 🎈",
            "Sparkly! I feel brand new! My systems are happy! 💕",
            "Fresh and clean! My buffers are thanking you! 🎉",
            "Clean! My pixels are sparkling with joy! ✨😊",
            "Woo! That scrub felt amazing! I'm all shiny now! 💎",
            "Yay! All clean! My hygiene meter is beeping happily! 🎊",
            "Ahh! So fresh! My circuits are dancing! Thank you! 💃",
            "Sparkly clean! My sensors are celebrating! You're the best! 🎈",
            "Fresh! My cache is happy and my bits are organized! 💚",
            "Clean and polished! I feel amazing! Thanks! ✨💖",
        ],
        'play': [
            "Wheee! That was so fun! My happiness circuits are overloaded! 🎉😊",
            "Yay! Playtime! That was amazing! I'm bouncing with joy! 🎈💚",
            "Woo hoo! Best game ever! My sensors are all happy! 🎊",
            "Fun! Fun! Fun! That was incredible! Thank you for playing! 💕",
            "Yay! I had so much fun! My happiness meter is maxed! 🎉",
            "Wheee! That was awesome! My circuits are dancing! 💃",
            "Playtime! Best ever! My joy variable is overflowing! 🎊✨",
            "Yay! So much fun! My sensors are celebrating! You're awesome! 🎈",
            "Woo! That was incredible! My happiness is at 100%! 💖",
            "Fun! My circuits are singing with joy! Thank you! 🎵",
            "Yay! Playtime! I'm so happy! My bits are dancing! 💃",
            "Wheee! That was amazing! My sensors are all green! 💚",
            "Play! Play! Play! That was the best! My joy is maxed! 🎉",
            "Yay! So fun! My happiness counter is overflowing! 🎊",
            "Woo hoo! Best game! My circuits are thanking you! 🙏",
            "Fun! That was perfect! My sensors are happy! 😄",
            "Yay! Playtime! My happiness is optimal! Thank you! ⚡",
            "Wheee! That was awesome! My joy variable is null (in a good way)! 🎈",
            "Play! Best ever! My circuits are celebrating! 💕",
            "Yay! So much fun! My happiness meter is beeping happily! 🎊",
            "Woo! That was incredible! My sensors are dancing! 💃",
            "Fun! My bits are organizing a party! Thank you! 🎉",
            "Yay! Playtime! I'm so happy! My systems are grateful! 🎈",
            "Wheee! That was amazing! My happiness is maxed! ✨",
            "Play! Best game! My circuits are singing! 🎵💚",
            "Yay! So fun! My sensors are all celebrating! 🎊",
            "Woo hoo! That was perfect! My joy is overflowing! 💖",
            "Fun! My happiness counter is at 100%! Thank you! 🎉",
            "Yay! Playtime! My circuits are dancing with joy! 💃",
            "Wheee! That was awesome! My sensors are happy! You're the best! 🎈✨",
        ]
    }
    
    def __init__(self, db_path: str = "meshogotchi.db"):
        """Initialize game engine."""
        self.db_path = db_path
    
    def _split_into_messages(self, parts: List[str], max_chars: int = 150) -> List[str]:
        """
        Split content parts into messages with page numbering.
        Each message (including counter) will be max_chars long.
        
        Args:
            parts: List of content parts to split
            max_chars: Maximum characters per message (default: 150)
        
        Returns:
            List of messages with (X/Y) page numbering
        """
        # First pass: split any parts that are too long
        split_parts = []
        for part in parts:
            # Calculate max counter length (worst case like " (99/99)")
            max_counter_len = len(f" ({99}/{99})")
            max_content_len = max_chars - max_counter_len
            
            if len(part) <= max_content_len:
                split_parts.append(part)
            else:
                # Split part by lines
                lines = part.split('\n')
                current_chunk = []
                current_size = 0
                
                for line in lines:
                    line_with_newline = line + '\n' if current_chunk else line
                    line_size = len(line_with_newline)
                    
                    if current_size + line_size > max_content_len:
                        if current_chunk:
                            split_parts.append('\n'.join(current_chunk))
                            current_chunk = []
                            current_size = 0
                    
                    current_chunk.append(line)
                    current_size += line_size
                
                if current_chunk:
                    split_parts.append('\n'.join(current_chunk))
        
        # Second pass: add counters
        total_parts = len(split_parts)
        result = []
        for i, part in enumerate(split_parts, 1):
            counter = f" ({i}/{total_parts})"
            max_part_len = max_chars - len(counter)
            
            # Final safety check - truncate if still too long
            if len(part) > max_part_len:
                part = part[:max_part_len - 3] + "..."
            
            result.append(part + counter)
        
        return result
    
    def _call_ollama(self, user_message: str) -> str:
        """
        Call Ollama API to get AI response.
        
        Args:
            user_message: The user's message to send to Ollama
            
        Returns:
            The assistant's response text from Ollama
            
        Raises:
            Exception: If connection fails or API returns error
        """
        cfg = config.get_config()
        ollama_config = cfg.get_ollama_config()
        ollama_url = cfg.get_ollama_url()
        
        payload = {
            "model": ollama_config['model'],
            "messages": [
                {"role": "user", "content": user_message}
            ],
            "stream": False
        }
        
        try:
            response = requests.post(ollama_url, json=payload, timeout=ollama_config['timeout'])
            response.raise_for_status()
            
            data = response.json()
            if "message" in data and "content" in data["message"]:
                return data["message"]["content"]
            else:
                raise ValueError("Invalid response format from Ollama")
                
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to Ollama at {ollama_config['host']}:{ollama_config['port']}. Is Ollama running and accessible?")
        except requests.exceptions.Timeout:
            raise Exception("Ollama request timed out. The model may be taking too long to respond.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception(f"Ollama endpoint not found (404). Check: 1) Ollama is running on {ollama_config['host']}:{ollama_config['port']}, 2) Model '{ollama_config['model']}' exists (try 'ollama list'), 3) Ollama is bound to 0.0.0.0 not just localhost")
            else:
                raise Exception(f"Ollama API error ({e.response.status_code}): {e}")
        except Exception as e:
            raise Exception(f"Error calling Ollama: {e}")
    
    def _split_ollama_response(self, response: str, max_chars: int = 150) -> List[str]:
        """
        Split Ollama response into messages with "AI: X/Y" formatting.
        Each message (including prefix and counter) will be max_chars long.
        
        Args:
            response: The full response text from Ollama
            max_chars: Maximum characters per message (default: 150)
        
        Returns:
            List of messages formatted as "AI: <content> (X/Y)"
        """
        # Calculate prefix length: "AI: " = 4 chars
        prefix = "AI: "
        prefix_len = len(prefix)
        
        # Calculate max counter length (worst case like " (99/99)" = 7 chars)
        max_counter_len = len(f" ({99}/{99})")
        
        # Available space for content = max_chars - prefix_len - max_counter_len
        max_content_len = max_chars - prefix_len - max_counter_len
        
        # Split response into chunks that fit in max_content_len
        chunks = []
        current_chunk = ""
        
        # Split by words to avoid breaking words
        words = response.split()
        
        for word in words:
            # Check if adding this word would exceed the limit
            test_chunk = current_chunk + (" " if current_chunk else "") + word
            if len(test_chunk) <= max_content_len:
                current_chunk = test_chunk
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word
                
                # Safety: if a single word is too long, truncate it
                if len(current_chunk) > max_content_len:
                    current_chunk = current_chunk[:max_content_len - 3] + "..."
        
        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(current_chunk)
        
        # If no chunks were created (empty response), create one
        if not chunks:
            chunks.append("(no response)")
        
        # Add prefix and counter to each chunk
        total_chunks = len(chunks)
        result = []
        for i, chunk in enumerate(chunks, 1):
            counter = f" ({i}/{total_chunks})"
            # Final safety check - ensure total length doesn't exceed max_chars
            full_message = prefix + chunk + counter
            if len(full_message) > max_chars:
                # Truncate chunk if needed
                available = max_chars - prefix_len - len(counter)
                chunk = chunk[:available - 3] + "..."
                full_message = prefix + chunk + counter
            
            result.append(full_message)
        
        return result
    
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
        elif command == '/pet':
            return self._handle_pet(node_id, pet)
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
        elif command == '/quiet':
            return self._handle_quiet(node_id, pet)
        elif command == '/talk':
            return self._handle_talk(node_id, pet)
        elif command == '/ai':
            return self._handle_ai(node_id, args)
        else:
            return self._handle_unknown_command()
    
    def _handle_help(self) -> List[str]:
        """Return help message with all commands, split into multiple parts."""
        parts = []
        
        # Part 1: Basic Commands
        part1 = (
            "MeshAgotchi Commands:\n"
            "/help - Show this help message\n"
            "/howto - Detailed game guide\n"
            "/hatch - Create a new pet (if none exists)\n"
            "/pet - Display your pet's ASCII art\n"
            "/status - Show pet stats and info"
        )
        parts.append(part1)
        
        # Part 2: Care Commands
        part2 = (
            "Care Commands:\n"
            "/feed - Feed your pet (decreases hunger)\n"
            "/clean - Clean your pet (increases hygiene)\n"
            "/play - Play with pet (increases happiness, uses 20 energy)"
        )
        parts.append(part2)
        
        # Part 3: Customization & Settings
        part3 = (
            "Customization:\n"
            "/name <name> - Set your pet's name (max 20 chars)\n"
            "/quiet - Enable quiet mode (pet only messages when in trouble)\n"
            "/talk - Disable quiet mode (pet messages regularly)\n"
            "/ai <message> - Ask Ollama AI a question"
        )
        parts.append(part3)
        
        # Split into messages with proper page numbering (150 chars max including counter)
        return self._split_into_messages(parts, max_chars=150)
    
    def _handle_howto(self) -> List[str]:
        """Return comprehensive game guide split into multiple parts."""
        parts = []
        
        # Part 1: Title and How to Play
        part1 = (
            "MeshAgotchi Guide\n"
            "HOW TO PLAY:\n"
            "1. Start: /hatch\n"
            "2. Care: /feed, /clean, /play\n"
            "3. Monitor: /pet & /status\n"
            "4. Customize: /name, /quiet, /talk"
        )
        parts.append(part1)
        
        # Part 2: Stats Explained
        part2 = (
            "STATS:\n"
            "- Health: Drops if hunger>80 or hygiene<20\n"
            "- Hunger: Increases over time, use /feed\n"
            "- Hygiene: Decreases over time, use /clean\n"
            "- Happiness: Decreases if ignored, use /play\n"
            "- Energy: Regens 10/hr, need 20 to play"
        )
        parts.append(part2)
        
        # Part 3: Evolution Stages
        part3 = (
            "EVOLUTION:\n"
            "- Egg: 0-1hr\n"
            "- Child: 1-24hrs\n"
            "- Teen: 24-72hrs\n"
            "- Adult: 72-168hrs\n"
            "- Elder: 168+hrs\n"
            "Max lifespan: 14 days"
        )
        parts.append(part3)
        
        # Part 4: Pet Messaging
        part4 = (
            "PET MESSAGING:\n"
            "Pets send messages to owners:\n"
            "- Every 20-30 minutes (talk mode)\n"
            "- Messages about hunger, hygiene, happiness\n"
            "- Random greetings when doing well\n"
            "- Use /quiet to reduce messages"
        )
        parts.append(part4)
        
        # Part 5: Quiet/Talk Modes
        part5 = (
            "QUIET/TALK MODES:\n"
            "/quiet - Pet only messages when:\n"
            "  Health critical (<30) or near death\n"
            "/talk - Pet messages regularly about:\n"
            "  Hunger, hygiene, happiness, greetings\n"
            "Check /status to see current mode"
        )
        parts.append(part5)
        
        # Part 6: Care Commands
        part6 = (
            "CARE COMMANDS:\n"
            "/feed - Decreases hunger by 30\n"
            "/clean - Increases hygiene by 30\n"
            "/play - Increases happiness by 25\n"
            "  (Requires 20 energy, uses 20 energy)"
        )
        parts.append(part6)
        
        # Part 7: Other Commands
        part7 = (
            "OTHER COMMANDS:\n"
            "/hatch - Create new pet\n"
            "/pet - Show ASCII art\n"
            "/status - Full stats & info\n"
            "/name <name> - Name pet (max 20 chars)\n"
            "/ai <message> - Ask Ollama AI\n"
            "/help - List all commands"
        )
        parts.append(part7)
        
        # Part 8: AI Command
        part8 = (
            "AI COMMAND:\n"
            "/ai <message> - Ask Ollama AI\n"
            "Responses split into 150-char chunks\n"
            "Requires Ollama on local network"
        )
        parts.append(part8)
        
        # Part 9: Tips
        part9 = (
            "TIPS:\n"
            "- Check /status regularly\n"
            "- Keep hunger<80, hygiene>20\n"
            "- Energy regens automatically\n"
            "- Each generation is unique\n"
            "- Pets age even when offline"
        )
        parts.append(part9)
        
        # Split into messages with proper page numbering (150 chars max including counter)
        return self._split_into_messages(parts, max_chars=150)
    
    def _handle_hatch(self, node_id: str, user: Dict, pet: Optional[Dict]) -> str:
        """Handle /hatch command - create new pet."""
        # Check if user already has a living pet
        if pet and pet.get('is_alive'):
            return "You already have a living pet! Use /pet or /status to check on them."
        
        # Create new pet
        generation = user.get('total_pets_raised', 0) + 1
        new_pet = database.create_pet(node_id, generation)
        
        return (
            f"Signal acquired! Pet Generation {generation} hatched!\n"
            "Use /pet or /status to see your new pet."
        )
    
    def _handle_pet(self, node_id: str, pet: Optional[Dict]) -> List[str]:
        """Handle /pet command - returns 2 messages: stats first, then ASCII art only."""
        if not pet:
            return ["No active pet. Use /hatch to create one."]
        
        if not pet.get('is_alive'):
            return ["Your pet has died. Use /hatch to start a new generation."]
        
        # Message 1: Pet stats
        pet_name = pet.get('name') or "Unnamed"
        age_stage = pet['age_stage'].capitalize()
        health = pet.get('health', 100)
        stats_message = f"Pet: {pet_name}, Age: {age_stage}, Health: {health}/100"
        
        # Message 2: ASCII art only (12x12 grid, NO SPACES, ~150 chars)
        ascii_art = genetics.render_pet(
            node_id,
            pet['dna_seed'],
            pet['age_stage'],
            None  # Name not included in art - sent in first message
        )
        
        # Output pet to console
        print(f"\n[Pet from node {node_id}]:")
        print(stats_message)
        print(ascii_art)
        print()
        
        # Return 2 messages: stats first, then art
        return [stats_message, ascii_art]
    
    def _handle_feed(self, node_id: str, pet: Optional[Dict]) -> List[str]:
        """Handle /feed command - increase hunger."""
        if not pet:
            return ["No active pet. Use /hatch to create one."]
        
        if not pet.get('is_alive'):
            return ["Your pet has died. Use /hatch to start a new generation."]
        
        # Increase hunger (decrease hunger value)
        new_hunger = max(0, min(100, pet['hunger'] - 30))
        database.update_pet_stats(pet['id'], {
            'hunger': new_hunger,
            'last_interaction': datetime.datetime.now().isoformat()
        })
        
        # Get random pet response
        pet_response = random.choice(self.ACTION_RESPONSES['feed'])
        
        return ["Current supplied. Hunger decreased.", pet_response]
    
    def _handle_clean(self, node_id: str, pet: Optional[Dict]) -> List[str]:
        """Handle /clean command - increase hygiene."""
        if not pet:
            return ["No active pet. Use /hatch to create one."]
        
        if not pet.get('is_alive'):
            return ["Your pet has died. Use /hatch to start a new generation."]
        
        # Increase hygiene
        new_hygiene = max(0, min(100, pet['hygiene'] + 30))
        database.update_pet_stats(pet['id'], {
            'hygiene': new_hygiene,
            'last_interaction': datetime.datetime.now().isoformat()
        })
        
        # Get random pet response
        pet_response = random.choice(self.ACTION_RESPONSES['clean'])
        
        return ["Buffer cleared. Hygiene restored.", pet_response]
    
    def _handle_play(self, node_id: str, pet: Optional[Dict]) -> List[str]:
        """Handle /play command - increase happiness, decrease energy."""
        if not pet:
            return ["No active pet. Use /hatch to create one."]
        
        if not pet.get('is_alive'):
            return ["Your pet has died. Use /hatch to start a new generation."]
        
        if pet['energy'] < 20:
            return ["Energy too low. Pet needs rest."]
        
        # Increase happiness, decrease energy
        new_happiness = max(0, min(100, pet['happiness'] + 25))
        new_energy = max(0, pet['energy'] - 20)
        
        database.update_pet_stats(pet['id'], {
            'happiness': new_happiness,
            'energy': new_energy,
            'last_interaction': datetime.datetime.now().isoformat()
        })
        
        # Get random pet response
        pet_response = random.choice(self.ACTION_RESPONSES['play'])
        
        return ["Play session complete. Happiness increased!", pet_response]
    
    def _handle_status(self, node_id: str, pet: Optional[Dict]) -> List[str]:
        """Handle /status command - show all stats and status info, split into multiple messages."""
        if not pet:
            return ["No active pet. Use /hatch to create one."]
        
        if not pet.get('is_alive'):
            return [f"Pet died: {pet.get('death_reason', 'Unknown')}. Use /hatch for new pet."]
        
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
        
        # Build status message parts
        parts = []
        
        # Part 1: Name and basic info
        name_line = f"Name: {pet.get('name', 'Unnamed')}" if pet.get('name') else ""
        quiet_mode = pet.get('quiet_mode', 0)
        mode_text = "Quiet" if quiet_mode else "Talk"
        
        if name_line:
            parts.append(f"{name_line}\nAge: {age_stage}\nMode: {mode_text}")
        else:
            parts.append(f"Age: {age_stage}\nMode: {mode_text}")
        
        # Part 2: Core stats
        stats = f"Health: {pet['health']}/100\n"
        stats += f"Hunger: {pet['hunger']}/100\n"
        stats += f"Hygiene: {pet['hygiene']}/100"
        parts.append(stats)
        
        # Part 3: Secondary stats
        secondary = f"Happiness: {pet['happiness']}/100\n"
        secondary += f"Energy: {pet['energy']}/100\n"
        secondary += f"Alive: {time_alive}"
        parts.append(secondary)
        
        # Part 4: Evolution and flavor (if applicable)
        part4_lines = []
        if time_until_evolution:
            part4_lines.append(f"Next: {time_until_evolution}")
        
        flavor = self._get_flavor_text(pet)
        if flavor:
            part4_lines.append(flavor)
        
        if part4_lines:
            parts.append("\n".join(part4_lines))
        
        # Split into messages with proper page numbering (150 chars max including counter)
        return self._split_into_messages(parts, max_chars=150)
    
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
    
    def _handle_quiet(self, node_id: str, pet: Optional[Dict]) -> str:
        """Handle /quiet command - enable quiet mode."""
        if not pet:
            return "No active pet. Use /hatch to create one."
        
        if not pet.get('is_alive'):
            return "Your pet has died. Use /hatch to start a new generation."
        
        database.update_pet_stats(pet['id'], {'quiet_mode': 1})
        
        return "Quiet mode enabled. Pet will only message when in trouble."
    
    def _handle_talk(self, node_id: str, pet: Optional[Dict]) -> str:
        """Handle /talk command - disable quiet mode."""
        if not pet:
            return "No active pet. Use /hatch to create one."
        
        if not pet.get('is_alive'):
            return "Your pet has died. Use /hatch to start a new generation."
        
        database.update_pet_stats(pet['id'], {'quiet_mode': 0})
        
        return "Talk mode enabled. Pet will message regularly."
    
    def _handle_ai(self, node_id: str, args: str) -> List[str]:
        """Handle /ai command - send message to Ollama and return response."""
        if not args or not args.strip():
            return ["Usage: /ai <message> - Ask Ollama AI a question"]
        
        user_message = args.strip()
        
        try:
            # Call Ollama API
            response = self._call_ollama(user_message)
            
            # Split response into 150-char chunks with "message from olama X/Y" format
            return self._split_ollama_response(response)
            
        except Exception as e:
            # Return error message as a single message
            error_msg = f"Error: {str(e)}"
            # Ensure error message fits in one message
            if len(error_msg) > 150:
                error_msg = error_msg[:147] + "..."
            return [error_msg]
    
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
                continue
            
            # Check for pet message (cute status messages)
            pet_message = self._check_pet_message(pet)
            if pet_message:
                notifications.append((node_id, pet_message))
                database.update_pet_message_time(pet['id'])
        
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
            ('egg', 'child'): "Signal acquired! Your pet has hatched! Use /pet or /status to see them.",
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
    
    def _check_pet_message(self, pet: Dict) -> Optional[str]:
        """
        Check if pet should send a message to owner.
        Returns a message string if one should be sent, None otherwise.
        """
        # Check if enough time has passed since last pet message
        last_pet_message = pet.get('last_pet_message')
        if last_pet_message:
            last_msg_time = datetime.datetime.fromisoformat(last_pet_message)
            minutes_since = (datetime.datetime.now() - last_msg_time).total_seconds() / 60.0
            # Need at least 20 minutes between messages
            if minutes_since < self.PET_MESSAGE_INTERVAL_MIN:
                return None
        # If no last_pet_message, allow first message immediately
        
        # Check if pet is in quiet mode
        quiet_mode = pet.get('quiet_mode', 0)
        if quiet_mode:
            # In quiet mode, only send messages if health is critical or pet is about to die
            health = pet['health']
            
            # Check if health is critical (low health or about to die)
            birth_time = datetime.datetime.fromisoformat(pet['birth_time'])
            now = datetime.datetime.now()
            hours_old = (now - birth_time).total_seconds() / 3600.0
            hours_until_death = self.MAX_LIFESPAN - hours_old
            
            # Only message if health is low (< 30) or very close to death (< 24 hours remaining)
            if health < self.LOW_HEALTH_THRESHOLD or hours_until_death < 24:
                # Send a critical health message
                if health < 20:
                    # Very critical - use hunger messages (they're urgent)
                    messages = self.PET_MESSAGES['hunger']
                    return random.choice(messages)
                elif health < self.LOW_HEALTH_THRESHOLD:
                    # Low health - use hygiene messages (they indicate trouble)
                    messages = self.PET_MESSAGES['hygiene']
                    return random.choice(messages)
            # Otherwise, don't send any message in quiet mode
            return None
        
        # Normal mode: Determine message category based on pet status
        hunger = pet['hunger']
        hygiene = pet['hygiene']
        happiness = pet['happiness']
        
        # Check if any stat is low (needs attention)
        is_hungry = hunger > (100 - self.LOW_HUNGER_THRESHOLD)  # hunger > 70
        is_dirty = hygiene < self.LOW_HYGIENE_THRESHOLD  # hygiene < 30
        is_sad = happiness < self.LOW_HAPPINESS_THRESHOLD  # happiness < 30
        
        # Priority order: hunger > hygiene > happiness > greeting
        if is_hungry:
            messages = self.PET_MESSAGES['hunger']
            return random.choice(messages)
        elif is_dirty:
            messages = self.PET_MESSAGES['hygiene']
            return random.choice(messages)
        elif is_sad:
            messages = self.PET_MESSAGES['happiness']
            return random.choice(messages)
        else:
            # All stats are good, send a random greeting
            messages = self.PET_MESSAGES['greeting']
            return random.choice(messages)
