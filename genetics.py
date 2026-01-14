"""
Procedural ASCII pet generation system for MeshAgotchi.

Implements the Family Trait (eyes from Node ID) and Individual Trait
(body from generation seed) system for generating unique pets.
"""

import hashlib
import random
from typing import Dict, Tuple, Optional


# Eye styles - Family Trait (persistent across generations for same Node ID)
EYE_STYLES = [
    "(o o)",   # 0
    "[- -]",   # 1
    "(* *)",   # 2
    "(^ ^)",   # 3
    "(> <)",   # 4
    "(+ +)",   # 5
    "(= =)",   # 6
    "(~ ~)",   # 7
    "(T T)",   # 8
    "(U U)",   # 9
    "(O O)",   # 10
    "(X X)",   # 11
    "(v v)",   # 12
    "(n n)",   # 13
    "(° °)",   # 14
    "(• •)",   # 15
]

# Body shapes for different age stages
BODY_SHAPES_CHILD = [
    "  /\\",
    " /  \\",
    "|    |",
]

BODY_SHAPES_TEEN = [
    "   /\\",
    "  /  \\",
    " |    |",
    " |____|",
]

BODY_SHAPES_ADULT = [
    "    /\\",
    "   /  \\",
    "  |    |",
    "  |____|",
    "   || ||",
]

# Mouth styles
MOUTH_STYLES = [
    "  v",      # 0 - sad
    "  ^",      # 1 - happy
    "  -",      # 2 - neutral
    "  o",      # 3 - surprised
    "  w",      # 4 - wide
    "  ~",      # 5 - wavy
    "  =",      # 6 - flat
    "  u",      # 7 - small smile
]

# Accessories (for adult/elder stages)
ACCESSORIES = [
    "",              # 0 - none
    "  /\\",         # 1 - hat
    "  ||",          # 2 - antenna
    "  **",          # 3 - stars
    "  ===",         # 4 - band
    "  ~~~",         # 5 - waves
]


def hash_node_id(node_id: str) -> int:
    """
    Convert Node ID to consistent integer (0-255).
    This ensures the same Node ID always maps to the same eye style.
    """
    # Remove leading ! if present
    clean_id = node_id.lstrip('!')
    # Hash to get consistent value
    hash_obj = hashlib.md5(clean_id.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    return hash_int % 256


def hash_generation_seed(owner_id: str, timestamp: str, generation: int) -> str:
    """
    Create unique seed for individual traits based on owner, time, and generation.
    Returns a hex string for use as seed.
    """
    seed_string = f"{owner_id}:{timestamp}:{generation}"
    return hashlib.md5(seed_string.encode()).hexdigest()


def get_family_eyes(node_id: str) -> str:
    """
    Returns eye style based on Node ID (persistent across generations).
    This is the Family Trait - same owner always has same eyes.
    """
    hash_val = hash_node_id(node_id)
    eye_index = hash_val % len(EYE_STYLES)
    return EYE_STYLES[eye_index]


def get_individual_traits(seed: str) -> Tuple[str, str, str]:
    """
    Returns body, mouth, and accessory based on generation seed.
    This is the Individual Trait - different for each pet generation.
    
    Returns: (body_type, mouth, accessory)
    """
    # Use seed to create deterministic random
    seed_int = int(seed[:8], 16)  # Use first 8 hex chars as int
    rng = random.Random(seed_int)
    
    # Select body variation (simple index)
    body_variant = rng.randint(0, 2)
    
    # Select mouth
    mouth_index = rng.randint(0, len(MOUTH_STYLES) - 1)
    mouth = MOUTH_STYLES[mouth_index]
    
    # Select accessory (more likely to have one for adult/elder)
    accessory_index = rng.randint(0, len(ACCESSORIES) - 1)
    accessory = ACCESSORIES[accessory_index]
    
    return (str(body_variant), mouth, accessory)


def render_pet(node_id: str, generation_seed: str, age_stage: str, name: Optional[str] = None) -> str:
    """
    Main render function. Generates ASCII art for pet.
    
    Args:
        node_id: Owner's Node ID (for Family Trait - eyes)
        generation_seed: Unique seed for this generation (for Individual Trait)
        age_stage: One of 'egg', 'child', 'teen', 'adult', 'elder'
        name: Optional pet name to display
    
    Returns:
        Multi-line ASCII art string (max 5 lines)
    """
    eyes = get_family_eyes(node_id)
    body_variant, mouth, accessory = get_individual_traits(generation_seed)
    
    lines = []
    
    if age_stage == 'egg':
        # Simple egg representation
        lines.append("   ___")
        lines.append("  /   \\")
        lines.append(" |  ?  |")
        lines.append("  \\___/")
        if name:
            lines.append(f"  {name}")
    elif age_stage == 'child':
        # Simple 4-line ASCII (max 5 with name)
        lines.append(f"  {eyes}")
        # Simple body (2 lines instead of 3)
        lines.append("  /\\")
        lines.append(" |  |")
        lines.append(f"  {mouth}")
        if name:
            lines.append(f"  {name}")
    elif age_stage == 'teen':
        # 4-5 lines with more detail
        if accessory and accessory.strip():
            lines.append(accessory)
        lines.append(f"  {eyes}")
        # Use 2 body lines to stay within limit
        lines.append("  /\\")
        lines.append(" |__|")
        lines.append(f"  {mouth}")
        if name and len(lines) < 5:
            lines.append(f"  {name}")
    elif age_stage in ('adult', 'elder'):
        # Full 5-line with accessories
        if accessory and accessory.strip():
            lines.append(accessory)
        else:
            # If no accessory, add empty line or skip
            pass
        lines.append(f"  {eyes}")
        # Use compact body to fit in 5 lines total
        lines.append("   /\\")
        lines.append("  |__|")
        lines.append("   ||")
        lines.append(f"  {mouth}")
        # Name and elder indicator
        if age_stage == 'elder':
            if name:
                lines[-1] = f"  {name} (wise)"
            else:
                lines[-1] = f"  {lines[-1]} (wise)"
        elif name and len(lines) < 5:
            lines.append(f"  {name}")
    
    # Ensure max 5 lines (excluding name if it's on separate line)
    # Actually, name can be part of the 5 lines
    result = "\n".join(lines[:5])
    
    return result


def demo_family_traits():
    """
    Generate 3 pets for Owner A (same eyes, different bodies) 
    and 3 pets for Owner B (different eyes, different bodies).
    
    Demonstrates the Family Trait system.
    """
    owner_a = "!a1b2c3"
    owner_b = "!x9y8z7"
    
    print("=" * 50)
    print("FAMILY TRAIT DEMONSTRATION")
    print("=" * 50)
    print("\nOwner A (Node ID: !a1b2c3)")
    print("-" * 50)
    
    # Generate 3 pets for Owner A
    for gen in range(1, 4):
        timestamp = f"2024-01-{gen:02d}T12:00:00"
        seed = hash_generation_seed(owner_a, timestamp, gen)
        pet = render_pet(owner_a, seed, "adult", f"Gen{gen}")
        print(f"\nGeneration {gen}:")
        print(pet)
    
    print("\n" + "=" * 50)
    print("Owner B (Node ID: !x9y8z7)")
    print("-" * 50)
    
    # Generate 3 pets for Owner B
    for gen in range(1, 4):
        timestamp = f"2024-01-{gen:02d}T12:00:00"
        seed = hash_generation_seed(owner_b, timestamp, gen)
        pet = render_pet(owner_b, seed, "adult", f"Gen{gen}")
        print(f"\nGeneration {gen}:")
        print(pet)
    
    print("\n" + "=" * 50)
    print("NOTICE: Owner A's pets all have the SAME EYES (Family Trait)")
    print("        Owner B's pets all have the SAME EYES (different from A)")
    print("        But each pet has a DIFFERENT BODY (Individual Trait)")
    print("=" * 50)


if __name__ == "__main__":
    demo_family_traits()
