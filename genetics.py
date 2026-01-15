"""
Procedural ASCII pet generation system for MeshAgotchi.

Generates unique, cool ASCII art for pets based on generation seed.
Each pet can be a different type (alien, robot, monster, etc.) and has
extensive variation. Art evolves cohesively through all growth stages.
"""

import hashlib
import random
from typing import Dict, Tuple, Optional, List


# Pet types - users can get different types across generations
PET_TYPES = [
    'robot',      # Mechanical, uses brackets, equals, pipes
    'alien',      # Extraterrestrial, uses symbols, circles
    'monster',    # Aggressive, uses sharp chars, angles
    'creature',   # Organic, uses curves, parentheses
    'spirit',     # Ethereal, uses tildes, stars
    'machine',    # Industrial, uses hashes, at signs
    'beast',      # Animal-like, uses natural shapes
    'entity',     # Abstract, uses mixed symbols
    'cyborg',     # Hybrid, uses mix of mechanical/organic
    'phantom',    # Ghostly, uses light chars
]


def count_characters(art: str) -> int:
    """
    Count total characters including newlines.
    Each newline counts as 1 character.
    """
    return len(art)


def get_pet_type(generation_seed: str) -> str:
    """
    Determine pet type from generation seed.
    This allows users to get different types across generations.
    """
    # Use first 8 hex chars as integer for deterministic selection
    seed_int = int(generation_seed[:8], 16) if len(generation_seed) >= 8 else int(generation_seed, 16) if generation_seed else 0
    type_index = seed_int % len(PET_TYPES)
    return PET_TYPES[type_index]


def get_seed_rng(seed: str) -> random.Random:
    """Create deterministic RNG from seed."""
    seed_int = int(seed[:8], 16) if len(seed) >= 8 else int(seed, 16) if seed else 0
    return random.Random(seed_int)


# ============================================================================
# EGG STAGE RENDERERS (20-40 chars)
# ============================================================================

def render_egg_robot(seed: str) -> str:
    """Render robot egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "  [===]\n [ ? ]\n [===]"
    elif variant == 1:
        return "  +---+\n | ? |\n +---+"
    else:
        return "  =====\n [ ? ]\n ====="


def render_egg_alien(seed: str) -> str:
    """Render alien egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "   ( )\n  ( ? )\n   ( )"
    elif variant == 1:
        return "   * *\n  * ? *\n   * *"
    else:
        return "   o o\n  o ? o\n   o o"


def render_egg_monster(seed: str) -> str:
    """Render monster egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "  >---<\n > ? <\n >---<"
    elif variant == 1:
        return "  /---\\\n / ? \\\n /---\\"
    else:
        return "  <===>\n < ? >\n <===>"


def render_egg_creature(seed: str) -> str:
    """Render creature egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "   ( )\n  ( ? )\n   ( )"
    elif variant == 1:
        return "   { }\n  { ? }\n   { }"
    else:
        return "   ~ ~\n  ~ ? ~\n   ~ ~"


def render_egg_spirit(seed: str) -> str:
    """Render spirit egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "   * *\n  * ? *\n   * *"
    elif variant == 1:
        return "   ~ ~\n  ~ ? ~\n   ~ ~"
    else:
        return "   . .\n  . ? .\n   . ."


def render_egg_machine(seed: str) -> str:
    """Render machine egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "  #####\n # ? #\n #####"
    elif variant == 1:
        return "  @@@@\n @ ? @\n @@@@"
    else:
        return "  +-+-+\n | ? |\n +-+-+"


def render_egg_beast(seed: str) -> str:
    """Render beast egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "   ( )\n  ( ? )\n   ( )"
    elif variant == 1:
        return "   o o\n  o ? o\n   o o"
    else:
        return "   ^ ^\n  ^ ? ^\n   ^ ^"


def render_egg_entity(seed: str) -> str:
    """Render entity egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "   % %\n  % ? %\n   % %"
    elif variant == 1:
        return "   & &\n  & ? &\n   & &"
    else:
        return "   $ $\n  $ ? $\n   $ $"


def render_egg_cyborg(seed: str) -> str:
    """Render cyborg egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "  [ ( ) ]\n [ ( ? ) ]\n [ ( ) ]"
    elif variant == 1:
        return "  ={ }=\n ={ ? }=\n ={ }="
    else:
        return "  | o |\n | ? |\n | o |"


def render_egg_phantom(seed: str) -> str:
    """Render phantom egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "   . .\n  . ? .\n   . ."
    elif variant == 1:
        return "   ' '\n  ' ? '\n   ' '"
    else:
        return "   : :\n  : ? :\n   : :"


def render_egg(pet_type: str, seed: str) -> str:
    """Render egg stage art (20-40 chars)."""
    renderers = {
        'robot': render_egg_robot,
        'alien': render_egg_alien,
        'monster': render_egg_monster,
        'creature': render_egg_creature,
        'spirit': render_egg_spirit,
        'machine': render_egg_machine,
        'beast': render_egg_beast,
        'entity': render_egg_entity,
        'cyborg': render_egg_cyborg,
        'phantom': render_egg_phantom,
    }
    renderer = renderers.get(pet_type, render_egg_creature)
    art = renderer(seed)
    
    # Ensure within budget (40 chars max for egg)
    if count_characters(art) > 40:
        # Truncate if needed
        lines = art.split('\n')
        result = '\n'.join(lines[:3])
        if count_characters(result) > 40:
            result = result[:37] + "..."
        return result
    
    return art


# ============================================================================
# CHILD STAGE RENDERERS (40-60 chars)
# ============================================================================

def render_child_robot(seed: str) -> str:
    """Render robot child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['[o o]', '[+ +]', '[= =]', '[. .]'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"  {eye_style}\n [====]\n | || |\n [====]"
    elif body_style == 1:
        return f"  {eye_style}\n +----+\n | || |\n +----+"
    else:
        return f"  {eye_style}\n ======\n | || |\n ======"


def render_child_alien(seed: str) -> str:
    """Render alien child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(* *)', '(O O)', '(0 0)'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"  {eye_style}\n (    )\n |  ^ |\n (____)"
    elif body_style == 1:
        return f"  {eye_style}\n /    \\\n |  ^ |\n \\____/"
    else:
        return f"  {eye_style}\n {eye_style}\n |  ^ |\n (____)"


def render_child_monster(seed: str) -> str:
    """Render monster child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['> <', 'V V', '^ ^', 'X X'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"  {eye_style}\n /    \\\n |  >  |\n \\____/"
    elif body_style == 1:
        return f"  {eye_style}\n <====>\n |  >  |\n <====>"
    else:
        return f"  {eye_style}\n #    #\n |  >  |\n #____#"


def render_child_creature(seed: str) -> str:
    """Render creature child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(~ ~)', '(u u)'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"  {eye_style}\n (    )\n |  ^ |\n (____)"
    elif body_style == 1:
        return f"  {eye_style}\n {{    }}\n |  ^ |\n {{____}}"
    else:
        return f"  {eye_style}\n /    \\\n |  ^ |\n \\____/"


def render_child_spirit(seed: str) -> str:
    """Render spirit child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['* *', '~ ~', '. .', 'o o'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"  {eye_style}\n *    *\n |  ~ |\n *____*"
    elif body_style == 1:
        return f"  {eye_style}\n ~    ~\n |  ~ |\n ~____~"
    else:
        return f"  {eye_style}\n .    .\n |  ~ |\n .____."


def render_child_machine(seed: str) -> str:
    """Render machine child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['# #', '@ @', '+ +', '= ='])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"  {eye_style}\n #####\n | || |\n #####"
    elif body_style == 1:
        return f"  {eye_style}\n @@@@@\n | || |\n @@@@@"
    else:
        return f"  {eye_style}\n +++++\n | || |\n +++++"


def render_child_beast(seed: str) -> str:
    """Render beast child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(v v)', '(n n)'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"  {eye_style}\n /    \\\n |  ^ |\n \\____/"
    elif body_style == 1:
        return f"  {eye_style}\n (    )\n |  ^ |\n (____)"
    else:
        return f"  {eye_style}\n {{    }}\n |  ^ |\n {{____}}"


def render_child_entity(seed: str) -> str:
    """Render entity child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['% %', '& &', '$ $', '# #'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"  {eye_style}\n %    %\n |  ^ |\n %____%"
    elif body_style == 1:
        return f"  {eye_style}\n &    &\n |  ^ |\n &____&"
    else:
        return f"  {eye_style}\n $    $\n |  ^ |\n $____$"


def render_child_cyborg(seed: str) -> str:
    """Render cyborg child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['[o o]', '(o o)', '[+ +]', '(= =)'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"  {eye_style}\n [====]\n | || |\n [====]"
    elif body_style == 1:
        return f"  {eye_style}\n (====)\n | || |\n (====)"
    else:
        return f"  {eye_style}\n ======\n | || |\n ======"


def render_child_phantom(seed: str) -> str:
    """Render phantom child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['. .', "' '", ': :', 'o o'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"  {eye_style}\n .    .\n |  ~ |\n .____."
    elif body_style == 1:
        return f"  {eye_style}\n '    '\n |  ~ |\n '____'"
    else:
        return f"  {eye_style}\n :    :\n |  ~ |\n :____:"


def render_child(pet_type: str, seed: str) -> str:
    """Render child stage art (40-60 chars)."""
    renderers = {
        'robot': render_child_robot,
        'alien': render_child_alien,
        'monster': render_child_monster,
        'creature': render_child_creature,
        'spirit': render_child_spirit,
        'machine': render_child_machine,
        'beast': render_child_beast,
        'entity': render_child_entity,
        'cyborg': render_child_cyborg,
        'phantom': render_child_phantom,
    }
    renderer = renderers.get(pet_type, render_child_creature)
    art = renderer(seed)
    
    # Ensure within budget (60 chars max for child)
    if count_characters(art) > 60:
        lines = art.split('\n')
        result = '\n'.join(lines[:4])
        if count_characters(result) > 60:
            result = result[:57] + "..."
        return result
    
    return art


# ============================================================================
# TEEN STAGE RENDERERS (60-100 chars)
# ============================================================================

def render_teen_robot(seed: str) -> str:
    """Render robot teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['[o o]', '[+ +]', '[= =]', '[. .]', '[X X]'])
    has_antenna = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_antenna:
        lines.append("   ||")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" [======]")
        lines.append(" |  ||  |")
        lines.append(" | ==== |")
        lines.append(" [======]")
        lines.append("  || ||")
    elif body_variant == 1:
        lines.append(" +------+")
        lines.append(" |  ||  |")
        lines.append(" | ==== |")
        lines.append(" +------+")
        lines.append("  || ||")
    else:
        lines.append(" ========")
        lines.append(" |  ||  |")
        lines.append(" | ==== |")
        lines.append(" ========")
        lines.append("  || ||")
    
    return '\n'.join(lines)


def render_teen_alien(seed: str) -> str:
    """Render alien teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(* *)', '(O O)', '(0 0)', '(^ ^)'])
    has_antenna = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_antenna:
        lines.append("   **")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" (      )")
        lines.append(" |  ||  |")
        lines.append(" |  ^^  |")
        lines.append(" (______)")
        lines.append("  || ||")
    elif body_variant == 1:
        lines.append(" /      \\")
        lines.append(" |  ||  |")
        lines.append(" |  ^^  |")
        lines.append(" \\______/")
        lines.append("  || ||")
    else:
        lines.append(" (      )")
        lines.append(" |  ||  |")
        lines.append(" |  ~~  |")
        lines.append(" (______)")
        lines.append("  || ||")
    
    return '\n'.join(lines)


def render_teen_monster(seed: str) -> str:
    """Render monster teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['> <', 'V V', '^ ^', 'X X', '< >'])
    has_horns = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_horns:
        lines.append("   /\\")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" /      \\")
        lines.append(" |  ||  |")
        lines.append(" |  >>  |")
        lines.append(" \\______/")
        lines.append("  || ||")
    elif body_variant == 1:
        lines.append(" <======>")
        lines.append(" |  ||  |")
        lines.append(" |  >>  |")
        lines.append(" <======>")
        lines.append("  || ||")
    else:
        lines.append(" #      #")
        lines.append(" |  ||  |")
        lines.append(" |  >>  |")
        lines.append(" #______#")
        lines.append("  || ||")
    
    return '\n'.join(lines)


def render_teen_creature(seed: str) -> str:
    """Render creature teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(~ ~)', '(u u)', '(v v)'])
    has_ears = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_ears:
        lines.append("   ^ ^")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" (      )")
        lines.append(" |  ||  |")
        lines.append(" |  ^^  |")
        lines.append(" (______)")
        lines.append("  || ||")
    elif body_variant == 1:
        lines.append(" {      }")
        lines.append(" |  ||  |")
        lines.append(" |  ^^  |")
        lines.append(" {______}")
        lines.append("  || ||")
    else:
        lines.append(" /      \\")
        lines.append(" |  ||  |")
        lines.append(" |  ^^  |")
        lines.append(" \\______/")
        lines.append("  || ||")
    
    return '\n'.join(lines)


def render_teen_spirit(seed: str) -> str:
    """Render spirit teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['* *', '~ ~', '. .', 'o o', '+ +'])
    has_aura = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_aura:
        lines.append("   ~~~")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" *      *")
        lines.append(" |  ||  |")
        lines.append(" |  ~~  |")
        lines.append(" *______*")
        lines.append("  || ||")
    elif body_variant == 1:
        lines.append(" ~      ~")
        lines.append(" |  ||  |")
        lines.append(" |  ~~  |")
        lines.append(" ~______~")
        lines.append("  || ||")
    else:
        lines.append(" .      .")
        lines.append(" |  ||  |")
        lines.append(" |  ~~  |")
        lines.append(" .______.")
        lines.append("  || ||")
    
    return '\n'.join(lines)


def render_teen_machine(seed: str) -> str:
    """Render machine teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['# #', '@ @', '+ +', '= =', '$ $'])
    has_panel = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_panel:
        lines.append("   ###")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" ########")
        lines.append(" |  ||  |")
        lines.append(" | ==== |")
        lines.append(" ########")
        lines.append("  || ||")
    elif body_variant == 1:
        lines.append(" @@@@@@@@")
        lines.append(" |  ||  |")
        lines.append(" | ==== |")
        lines.append(" @@@@@@@@")
        lines.append("  || ||")
    else:
        lines.append(" ++++++++")
        lines.append(" |  ||  |")
        lines.append(" | ==== |")
        lines.append(" ++++++++")
        lines.append("  || ||")
    
    return '\n'.join(lines)


def render_teen_beast(seed: str) -> str:
    """Render beast teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(v v)', '(n n)', '(> <)'])
    has_mane = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_mane:
        lines.append("   ~~~")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" /      \\")
        lines.append(" |  ||  |")
        lines.append(" |  ^^  |")
        lines.append(" \\______/")
        lines.append("  || ||")
    elif body_variant == 1:
        lines.append(" (      )")
        lines.append(" |  ||  |")
        lines.append(" |  ^^  |")
        lines.append(" (______)")
        lines.append("  || ||")
    else:
        lines.append(" {      }")
        lines.append(" |  ||  |")
        lines.append(" |  ^^  |")
        lines.append(" {______}")
        lines.append("  || ||")
    
    return '\n'.join(lines)


def render_teen_entity(seed: str) -> str:
    """Render entity teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['% %', '& &', '$ $', '# #', '@ @'])
    has_symbols = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_symbols:
        lines.append("   %%%")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" %      %")
        lines.append(" |  ||  |")
        lines.append(" |  ^^  |")
        lines.append(" %______%")
        lines.append("  || ||")
    elif body_variant == 1:
        lines.append(" &      &")
        lines.append(" |  ||  |")
        lines.append(" |  ^^  |")
        lines.append(" &______&")
        lines.append("  || ||")
    else:
        lines.append(" $      $")
        lines.append(" |  ||  |")
        lines.append(" |  ^^  |")
        lines.append(" $______$")
        lines.append("  || ||")
    
    return '\n'.join(lines)


def render_teen_cyborg(seed: str) -> str:
    """Render cyborg teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['[o o]', '(o o)', '[+ +]', '(= =)', '[. .]'])
    has_tech = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_tech:
        lines.append("   [=]")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" [======]")
        lines.append(" |  ||  |")
        lines.append(" | ==== |")
        lines.append(" [======]")
        lines.append("  || ||")
    elif body_variant == 1:
        lines.append(" (======)")
        lines.append(" |  ||  |")
        lines.append(" | ==== |")
        lines.append(" (======)")
        lines.append("  || ||")
    else:
        lines.append(" ========")
        lines.append(" |  ||  |")
        lines.append(" | ==== |")
        lines.append(" ========")
        lines.append("  || ||")
    
    return '\n'.join(lines)


def render_teen_phantom(seed: str) -> str:
    """Render phantom teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['. .', "' '", ': :', 'o o', '~ ~'])
    has_glow = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_glow:
        lines.append("   ...")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" .      .")
        lines.append(" |  ||  |")
        lines.append(" |  ~~  |")
        lines.append(" .______.")
        lines.append("  || ||")
    elif body_variant == 1:
        lines.append(" '      '")
        lines.append(" |  ||  |")
        lines.append(" |  ~~  |")
        lines.append(" '______'")
        lines.append("  || ||")
    else:
        lines.append(" :      :")
        lines.append(" |  ||  |")
        lines.append(" |  ~~  |")
        lines.append(" :______:")
        lines.append("  || ||")
    
    return '\n'.join(lines)


def render_teen(pet_type: str, seed: str) -> str:
    """Render teen stage art (60-100 chars)."""
    renderers = {
        'robot': render_teen_robot,
        'alien': render_teen_alien,
        'monster': render_teen_monster,
        'creature': render_teen_creature,
        'spirit': render_teen_spirit,
        'machine': render_teen_machine,
        'beast': render_teen_beast,
        'entity': render_teen_entity,
        'cyborg': render_teen_cyborg,
        'phantom': render_teen_phantom,
    }
    renderer = renderers.get(pet_type, render_teen_creature)
    art = renderer(seed)
    
    # Ensure within budget (100 chars max for teen)
    if count_characters(art) > 100:
        lines = art.split('\n')
        result = '\n'.join(lines[:6])
        if count_characters(result) > 100:
            result = result[:97] + "..."
        return result
    
    return art


# ============================================================================
# ADULT STAGE RENDERERS (100-150 chars)
# ============================================================================

def render_adult_robot(seed: str) -> str:
    """Render robot adult."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['[o o]', '[+ +]', '[= =]', '[. .]', '[X X]', '[O O]'])
    has_antenna = rng.random() > 0.5
    has_panel = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_antenna:
        lines.append("    ||")
    if has_panel:
        lines.append("   [==]")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" [========]")
        lines.append(" |   ||   |")
        lines.append(" | ====== |")
        lines.append(" |   ||   |")
        lines.append(" [========]")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    elif body_variant == 1:
        lines.append(" +--------+")
        lines.append(" |   ||   |")
        lines.append(" | ====== |")
        lines.append(" |   ||   |")
        lines.append(" +--------+")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    else:
        lines.append(" ==========")
        lines.append(" |   ||   |")
        lines.append(" | ====== |")
        lines.append(" |   ||   |")
        lines.append(" ==========")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    
    return '\n'.join(lines)


def render_adult_alien(seed: str) -> str:
    """Render alien adult."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(* *)', '(O O)', '(0 0)', '(^ ^)', '(~ ~)'])
    has_antenna = rng.random() > 0.5
    has_pattern = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_antenna:
        lines.append("    **")
    if has_pattern:
        lines.append("   * * *")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" (        )")
        lines.append(" |   ||   |")
        lines.append(" |  ^^^^  |")
        lines.append(" |   ||   |")
        lines.append(" (________)")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    elif body_variant == 1:
        lines.append(" /        \\")
        lines.append(" |   ||   |")
        lines.append(" |  ^^^^  |")
        lines.append(" |   ||   |")
        lines.append(" \\________/")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    else:
        lines.append(" (        )")
        lines.append(" |   ||   |")
        lines.append(" |  ~~~~  |")
        lines.append(" |   ||   |")
        lines.append(" (________)")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    
    return '\n'.join(lines)


def render_adult_monster(seed: str) -> str:
    """Render monster adult."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['> <', 'V V', '^ ^', 'X X', '< >', '> >'])
    has_horns = rng.random() > 0.5
    has_spikes = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_horns:
        lines.append("   /\\/\\")
    if has_spikes:
        lines.append("   >>>>")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" /        \\")
        lines.append(" |   ||   |")
        lines.append(" |  >>>>  |")
        lines.append(" |   ||   |")
        lines.append(" \\________/")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    elif body_variant == 1:
        lines.append(" <========>")
        lines.append(" |   ||   |")
        lines.append(" |  >>>>  |")
        lines.append(" |   ||   |")
        lines.append(" <========>")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    else:
        lines.append(" #        #")
        lines.append(" |   ||   |")
        lines.append(" |  >>>>  |")
        lines.append(" |   ||   |")
        lines.append(" #________#")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    
    return '\n'.join(lines)


def render_adult_creature(seed: str) -> str:
    """Render creature adult."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(~ ~)', '(u u)', '(v v)', '(n n)'])
    has_ears = rng.random() > 0.5
    has_tail = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_ears:
        lines.append("   ^   ^")
    if has_tail:
        lines.append("   ~~~")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" (        )")
        lines.append(" |   ||   |")
        lines.append(" |  ^^^^  |")
        lines.append(" |   ||   |")
        lines.append(" (________)")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    elif body_variant == 1:
        lines.append(" {        }")
        lines.append(" |   ||   |")
        lines.append(" |  ^^^^  |")
        lines.append(" |   ||   |")
        lines.append(" {________}")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    else:
        lines.append(" /        \\")
        lines.append(" |   ||   |")
        lines.append(" |  ^^^^  |")
        lines.append(" |   ||   |")
        lines.append(" \\________/")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    
    return '\n'.join(lines)


def render_adult_spirit(seed: str) -> str:
    """Render spirit adult."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['* *', '~ ~', '. .', 'o o', '+ +', '* *'])
    has_aura = rng.random() > 0.5
    has_glow = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_aura:
        lines.append("   ~~~~~")
    if has_glow:
        lines.append("   ***")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" *        *")
        lines.append(" |   ||   |")
        lines.append(" |  ~~~~  |")
        lines.append(" |   ||   |")
        lines.append(" *________*")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    elif body_variant == 1:
        lines.append(" ~        ~")
        lines.append(" |   ||   |")
        lines.append(" |  ~~~~  |")
        lines.append(" |   ||   |")
        lines.append(" ~________~")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    else:
        lines.append(" .        .")
        lines.append(" |   ||   |")
        lines.append(" |  ~~~~  |")
        lines.append(" |   ||   |")
        lines.append(" .________.")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    
    return '\n'.join(lines)


def render_adult_machine(seed: str) -> str:
    """Render machine adult."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['# #', '@ @', '+ +', '= =', '$ $', '% %'])
    has_panel = rng.random() > 0.5
    has_tech = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_panel:
        lines.append("   ######")
    if has_tech:
        lines.append("   @@@@@")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" ##########")
        lines.append(" |   ||   |")
        lines.append(" | ====== |")
        lines.append(" |   ||   |")
        lines.append(" ##########")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    elif body_variant == 1:
        lines.append(" @@@@@@@@@@")
        lines.append(" |   ||   |")
        lines.append(" | ====== |")
        lines.append(" |   ||   |")
        lines.append(" @@@@@@@@@@")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    else:
        lines.append(" ++++++++++")
        lines.append(" |   ||   |")
        lines.append(" | ====== |")
        lines.append(" |   ||   |")
        lines.append(" ++++++++++")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    
    return '\n'.join(lines)


def render_adult_beast(seed: str) -> str:
    """Render beast adult."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(v v)', '(n n)', '(> <)', '(U U)'])
    has_mane = rng.random() > 0.5
    has_claws = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_mane:
        lines.append("   ~~~~~~~")
    if has_claws:
        lines.append("   >>>")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" /        \\")
        lines.append(" |   ||   |")
        lines.append(" |  ^^^^  |")
        lines.append(" |   ||   |")
        lines.append(" \\________/")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    elif body_variant == 1:
        lines.append(" (        )")
        lines.append(" |   ||   |")
        lines.append(" |  ^^^^  |")
        lines.append(" |   ||   |")
        lines.append(" (________)")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    else:
        lines.append(" {        }")
        lines.append(" |   ||   |")
        lines.append(" |  ^^^^  |")
        lines.append(" |   ||   |")
        lines.append(" {________}")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    
    return '\n'.join(lines)


def render_adult_entity(seed: str) -> str:
    """Render entity adult."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['% %', '& &', '$ $', '# #', '@ @', '! !'])
    has_symbols = rng.random() > 0.5
    has_pattern = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_symbols:
        lines.append("   %%%%%")
    if has_pattern:
        lines.append("   &&&")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" %        %")
        lines.append(" |   ||   |")
        lines.append(" |  ^^^^  |")
        lines.append(" |   ||   |")
        lines.append(" %________%")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    elif body_variant == 1:
        lines.append(" &        &")
        lines.append(" |   ||   |")
        lines.append(" |  ^^^^  |")
        lines.append(" |   ||   |")
        lines.append(" &________&")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    else:
        lines.append(" $        $")
        lines.append(" |   ||   |")
        lines.append(" |  ^^^^  |")
        lines.append(" |   ||   |")
        lines.append(" $________$")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    
    return '\n'.join(lines)


def render_adult_cyborg(seed: str) -> str:
    """Render cyborg adult."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['[o o]', '(o o)', '[+ +]', '(= =)', '[. .]', '[O O]'])
    has_tech = rng.random() > 0.5
    has_organic = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_tech:
        lines.append("   [====]")
    if has_organic:
        lines.append("   (    )")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" [========]")
        lines.append(" |   ||   |")
        lines.append(" | ====== |")
        lines.append(" |   ||   |")
        lines.append(" [========]")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    elif body_variant == 1:
        lines.append(" (========)")
        lines.append(" |   ||   |")
        lines.append(" | ====== |")
        lines.append(" |   ||   |")
        lines.append(" (========)")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    else:
        lines.append(" ==========")
        lines.append(" |   ||   |")
        lines.append(" | ====== |")
        lines.append(" |   ||   |")
        lines.append(" ==========")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    
    return '\n'.join(lines)


def render_adult_phantom(seed: str) -> str:
    """Render phantom adult."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['. .', "' '", ': :', 'o o', '~ ~', '. .'])
    has_glow = rng.random() > 0.5
    has_aura = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_glow:
        lines.append("   .....")
    if has_aura:
        lines.append("   ~~~")
    lines.append(f"  {eye_style}")
    
    if body_variant == 0:
        lines.append(" .        .")
        lines.append(" |   ||   |")
        lines.append(" |  ~~~~  |")
        lines.append(" |   ||   |")
        lines.append(" .________.")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    elif body_variant == 1:
        lines.append(" '        '")
        lines.append(" |   ||   |")
        lines.append(" |  ~~~~  |")
        lines.append(" |   ||   |")
        lines.append(" '________'")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    else:
        lines.append(" :        :")
        lines.append(" |   ||   |")
        lines.append(" |  ~~~~  |")
        lines.append(" |   ||   |")
        lines.append(" :________:")
        lines.append("  ||   ||")
        lines.append("  ||   ||")
    
    return '\n'.join(lines)


def render_adult(pet_type: str, seed: str) -> str:
    """Render adult stage art (100-150 chars)."""
    renderers = {
        'robot': render_adult_robot,
        'alien': render_adult_alien,
        'monster': render_adult_monster,
        'creature': render_adult_creature,
        'spirit': render_adult_spirit,
        'machine': render_adult_machine,
        'beast': render_adult_beast,
        'entity': render_adult_entity,
        'cyborg': render_adult_cyborg,
        'phantom': render_adult_phantom,
    }
    renderer = renderers.get(pet_type, render_adult_creature)
    art = renderer(seed)
    
    # Ensure within budget (150 chars max for adult)
    if count_characters(art) > 150:
        lines = art.split('\n')
        result = '\n'.join(lines[:9])
        if count_characters(result) > 150:
            result = result[:147] + "..."
        return result
    
    return art


# ============================================================================
# ELDER STAGE RENDERERS (150-198 chars)
# ============================================================================

def render_elder_robot(seed: str) -> str:
    """Render robot elder."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['[o o]', '[+ +]', '[= =]', '[. .]', '[X X]', '[O O]', '[| |]'])
    has_antenna = rng.random() > 0.5
    has_panel = rng.random() > 0.5
    has_wisdom = True  # Elders always have wisdom markers
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_antenna:
        lines.append("     ||")
    if has_panel:
        lines.append("    [==]")
    lines.append(f"   {eye_style}")
    
    if body_variant == 0:
        lines.append("  [==========]")
        lines.append("  |    ||    |")
        lines.append("  | ======== |")
        lines.append("  |    ||    |")
        lines.append("  [==========]")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    elif body_variant == 1:
        lines.append("  +----------+")
        lines.append("  |    ||    |")
        lines.append("  | ======== |")
        lines.append("  |    ||    |")
        lines.append("  +----------+")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    else:
        lines.append("  ============")
        lines.append("  |    ||    |")
        lines.append("  | ======== |")
        lines.append("  |    ||    |")
        lines.append("  ============")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    
    art = '\n'.join(lines)
    # Ensure within 198 char budget
    if count_characters(art) > 198:
        # Trim if needed
        lines = art.split('\n')
        while count_characters('\n'.join(lines)) > 198 and len(lines) > 1:
            lines.pop()
        art = '\n'.join(lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


def render_elder_alien(seed: str) -> str:
    """Render alien elder."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(* *)', '(O O)', '(0 0)', '(^ ^)', '(~ ~)', '(U U)'])
    has_antenna = rng.random() > 0.5
    has_pattern = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_antenna:
        lines.append("     **")
    if has_pattern:
        lines.append("    * * *")
    lines.append(f"   {eye_style}")
    
    if body_variant == 0:
        lines.append("  (          )")
        lines.append("  |    ||    |")
        lines.append("  |  ^^^^^^  |")
        lines.append("  |    ||    |")
        lines.append("  (__________)")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    elif body_variant == 1:
        lines.append("  /          \\")
        lines.append("  |    ||    |")
        lines.append("  |  ^^^^^^  |")
        lines.append("  |    ||    |")
        lines.append("  \\__________/")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    else:
        lines.append("  (          )")
        lines.append("  |    ||    |")
        lines.append("  |  ~~~~~~  |")
        lines.append("  |    ||    |")
        lines.append("  (__________)")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    
    art = '\n'.join(lines)
    if count_characters(art) > 198:
        lines = art.split('\n')
        while count_characters('\n'.join(lines)) > 198 and len(lines) > 1:
            lines.pop()
        art = '\n'.join(lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


def render_elder_monster(seed: str) -> str:
    """Render monster elder."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['> <', 'V V', '^ ^', 'X X', '< >', '> >', 'V V'])
    has_horns = rng.random() > 0.5
    has_spikes = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_horns:
        lines.append("   /\\/\\/\\")
    if has_spikes:
        lines.append("   >>>>>>")
    lines.append(f"   {eye_style}")
    
    if body_variant == 0:
        lines.append("  /          \\")
        lines.append("  |    ||    |")
        lines.append("  |  >>>>>>  |")
        lines.append("  |    ||    |")
        lines.append("  \\__________/")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    elif body_variant == 1:
        lines.append("  <==========>")
        lines.append("  |    ||    |")
        lines.append("  |  >>>>>>  |")
        lines.append("  |    ||    |")
        lines.append("  <==========>")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    else:
        lines.append("  #          #")
        lines.append("  |    ||    |")
        lines.append("  |  >>>>>>  |")
        lines.append("  |    ||    |")
        lines.append("  #__________#")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    
    art = '\n'.join(lines)
    if count_characters(art) > 198:
        lines = art.split('\n')
        while count_characters('\n'.join(lines)) > 198 and len(lines) > 1:
            lines.pop()
        art = '\n'.join(lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


def render_elder_creature(seed: str) -> str:
    """Render creature elder."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(~ ~)', '(u u)', '(v v)', '(n n)', '(U U)'])
    has_ears = rng.random() > 0.5
    has_tail = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_ears:
        lines.append("    ^     ^")
    if has_tail:
        lines.append("    ~~~~~")
    lines.append(f"   {eye_style}")
    
    if body_variant == 0:
        lines.append("  (          )")
        lines.append("  |    ||    |")
        lines.append("  |  ^^^^^^  |")
        lines.append("  |    ||    |")
        lines.append("  (__________)")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    elif body_variant == 1:
        lines.append("  {          }")
        lines.append("  |    ||    |")
        lines.append("  |  ^^^^^^  |")
        lines.append("  |    ||    |")
        lines.append("  {__________}")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    else:
        lines.append("  /          \\")
        lines.append("  |    ||    |")
        lines.append("  |  ^^^^^^  |")
        lines.append("  |    ||    |")
        lines.append("  \\__________/")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    
    art = '\n'.join(lines)
    if count_characters(art) > 198:
        lines = art.split('\n')
        while count_characters('\n'.join(lines)) > 198 and len(lines) > 1:
            lines.pop()
        art = '\n'.join(lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


def render_elder_spirit(seed: str) -> str:
    """Render spirit elder."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['* *', '~ ~', '. .', 'o o', '+ +', '* *', '~ ~'])
    has_aura = rng.random() > 0.5
    has_glow = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_aura:
        lines.append("    ~~~~~~~")
    if has_glow:
        lines.append("    *****")
    lines.append(f"   {eye_style}")
    
    if body_variant == 0:
        lines.append("  *          *")
        lines.append("  |    ||    |")
        lines.append("  |  ~~~~~~  |")
        lines.append("  |    ||    |")
        lines.append("  *__________*")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    elif body_variant == 1:
        lines.append("  ~          ~")
        lines.append("  |    ||    |")
        lines.append("  |  ~~~~~~  |")
        lines.append("  |    ||    |")
        lines.append("  ~__________~")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    else:
        lines.append("  .          .")
        lines.append("  |    ||    |")
        lines.append("  |  ~~~~~~  |")
        lines.append("  |    ||    |")
        lines.append("  .__________.")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    
    art = '\n'.join(lines)
    if count_characters(art) > 198:
        lines = art.split('\n')
        while count_characters('\n'.join(lines)) > 198 and len(lines) > 1:
            lines.pop()
        art = '\n'.join(lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


def render_elder_machine(seed: str) -> str:
    """Render machine elder."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['# #', '@ @', '+ +', '= =', '$ $', '% %', '# #'])
    has_panel = rng.random() > 0.5
    has_tech = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_panel:
        lines.append("    ########")
    if has_tech:
        lines.append("    @@@@@@@")
    lines.append(f"   {eye_style}")
    
    if body_variant == 0:
        lines.append("  ############")
        lines.append("  |    ||    |")
        lines.append("  | ======== |")
        lines.append("  |    ||    |")
        lines.append("  ############")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    elif body_variant == 1:
        lines.append("  @@@@@@@@@@@@")
        lines.append("  |    ||    |")
        lines.append("  | ======== |")
        lines.append("  |    ||    |")
        lines.append("  @@@@@@@@@@@@")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    else:
        lines.append("  ++++++++++++")
        lines.append("  |    ||    |")
        lines.append("  | ======== |")
        lines.append("  |    ||    |")
        lines.append("  ++++++++++++")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    
    art = '\n'.join(lines)
    if count_characters(art) > 198:
        lines = art.split('\n')
        while count_characters('\n'.join(lines)) > 198 and len(lines) > 1:
            lines.pop()
        art = '\n'.join(lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


def render_elder_beast(seed: str) -> str:
    """Render beast elder."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(v v)', '(n n)', '(> <)', '(U U)', '(O O)'])
    has_mane = rng.random() > 0.5
    has_claws = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_mane:
        lines.append("    ~~~~~~~~~")
    if has_claws:
        lines.append("    >>>>>")
    lines.append(f"   {eye_style}")
    
    if body_variant == 0:
        lines.append("  /          \\")
        lines.append("  |    ||    |")
        lines.append("  |  ^^^^^^  |")
        lines.append("  |    ||    |")
        lines.append("  \\__________/")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    elif body_variant == 1:
        lines.append("  (          )")
        lines.append("  |    ||    |")
        lines.append("  |  ^^^^^^  |")
        lines.append("  |    ||    |")
        lines.append("  (__________)")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    else:
        lines.append("  {          }")
        lines.append("  |    ||    |")
        lines.append("  |  ^^^^^^  |")
        lines.append("  |    ||    |")
        lines.append("  {__________}")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    
    art = '\n'.join(lines)
    if count_characters(art) > 198:
        lines = art.split('\n')
        while count_characters('\n'.join(lines)) > 198 and len(lines) > 1:
            lines.pop()
        art = '\n'.join(lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


def render_elder_entity(seed: str) -> str:
    """Render entity elder."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['% %', '& &', '$ $', '# #', '@ @', '! !', '% %'])
    has_symbols = rng.random() > 0.5
    has_pattern = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_symbols:
        lines.append("    %%%%%%%")
    if has_pattern:
        lines.append("    &&&&&")
    lines.append(f"   {eye_style}")
    
    if body_variant == 0:
        lines.append("  %          %")
        lines.append("  |    ||    |")
        lines.append("  |  ^^^^^^  |")
        lines.append("  |    ||    |")
        lines.append("  %__________%")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    elif body_variant == 1:
        lines.append("  &          &")
        lines.append("  |    ||    |")
        lines.append("  |  ^^^^^^  |")
        lines.append("  |    ||    |")
        lines.append("  &__________&")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    else:
        lines.append("  $          $")
        lines.append("  |    ||    |")
        lines.append("  |  ^^^^^^  |")
        lines.append("  |    ||    |")
        lines.append("  $__________$")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    
    art = '\n'.join(lines)
    if count_characters(art) > 198:
        lines = art.split('\n')
        while count_characters('\n'.join(lines)) > 198 and len(lines) > 1:
            lines.pop()
        art = '\n'.join(lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


def render_elder_cyborg(seed: str) -> str:
    """Render cyborg elder."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['[o o]', '(o o)', '[+ +]', '(= =)', '[. .]', '[O O]', '[| |]'])
    has_tech = rng.random() > 0.5
    has_organic = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_tech:
        lines.append("    [====]")
    if has_organic:
        lines.append("    (    )")
    lines.append(f"   {eye_style}")
    
    if body_variant == 0:
        lines.append("  [==========]")
        lines.append("  |    ||    |")
        lines.append("  | ======== |")
        lines.append("  |    ||    |")
        lines.append("  [==========]")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    elif body_variant == 1:
        lines.append("  (==========)")
        lines.append("  |    ||    |")
        lines.append("  | ======== |")
        lines.append("  |    ||    |")
        lines.append("  (==========)")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    else:
        lines.append("  ============")
        lines.append("  |    ||    |")
        lines.append("  | ======== |")
        lines.append("  |    ||    |")
        lines.append("  ============")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    
    art = '\n'.join(lines)
    if count_characters(art) > 198:
        lines = art.split('\n')
        while count_characters('\n'.join(lines)) > 198 and len(lines) > 1:
            lines.pop()
        art = '\n'.join(lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


def render_elder_phantom(seed: str) -> str:
    """Render phantom elder."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['. .', "' '", ': :', 'o o', '~ ~', '. .', "' '"])
    has_glow = rng.random() > 0.5
    has_aura = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_glow:
        lines.append("    .......")
    if has_aura:
        lines.append("    ~~~~~")
    lines.append(f"   {eye_style}")
    
    if body_variant == 0:
        lines.append("  .          .")
        lines.append("  |    ||    |")
        lines.append("  |  ~~~~~~  |")
        lines.append("  |    ||    |")
        lines.append("  .__________.")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    elif body_variant == 1:
        lines.append("  '          '")
        lines.append("  |    ||    |")
        lines.append("  |  ~~~~~~  |")
        lines.append("  |    ||    |")
        lines.append("  '__________'")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    else:
        lines.append("  :          :")
        lines.append("  |    ||    |")
        lines.append("  |  ~~~~~~  |")
        lines.append("  |    ||    |")
        lines.append("  :__________:")
        lines.append("   ||    ||")
        lines.append("   ||    ||")
        lines.append("  /        \\")
        lines.append(" |  WISE  |")
        lines.append("  \\________/")
    
    art = '\n'.join(lines)
    if count_characters(art) > 198:
        lines = art.split('\n')
        while count_characters('\n'.join(lines)) > 198 and len(lines) > 1:
            lines.pop()
        art = '\n'.join(lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


def render_elder(pet_type: str, seed: str) -> str:
    """Render elder stage art (150-198 chars)."""
    renderers = {
        'robot': render_elder_robot,
        'alien': render_elder_alien,
        'monster': render_elder_monster,
        'creature': render_elder_creature,
        'spirit': render_elder_spirit,
        'machine': render_elder_machine,
        'beast': render_elder_beast,
        'entity': render_elder_entity,
        'cyborg': render_elder_cyborg,
        'phantom': render_elder_phantom,
    }
    renderer = renderers.get(pet_type, render_elder_creature)
    art = renderer(seed)
    
    # Ensure within budget (198 chars max for elder)
    if count_characters(art) > 198:
        lines = art.split('\n')
        while count_characters('\n'.join(lines)) > 198 and len(lines) > 1:
            lines.pop()
        art = '\n'.join(lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


# ============================================================================
# MAIN RENDER FUNCTION
# ============================================================================

def render_pet(node_id: str, generation_seed: str, age_stage: str, name: Optional[str] = None) -> str:
    """
    Main render function. Generates ASCII art for pet.
    
    Args:
        node_id: Owner's Node ID (kept for compatibility, not used for type)
        generation_seed: Unique seed for this generation (determines type and variations)
        age_stage: One of 'egg', 'child', 'teen', 'adult', 'elder'
        name: Optional pet name to display (within character budget)
    
    Returns:
        Multi-line ASCII art string (max 198 characters total)
    """
    # Get pet type from generation seed (allows different types across generations)
    pet_type = get_pet_type(generation_seed)
    
    # Route to appropriate stage renderer
    if age_stage == 'egg':
        art = render_egg(pet_type, generation_seed)
    elif age_stage == 'child':
        art = render_child(pet_type, generation_seed)
    elif age_stage == 'teen':
        art = render_teen(pet_type, generation_seed)
    elif age_stage == 'adult':
        art = render_adult(pet_type, generation_seed)
    elif age_stage == 'elder':
        art = render_elder(pet_type, generation_seed)
    else:
        # Fallback to child if unknown stage
        art = render_child(pet_type, generation_seed)
    
    # Add name if provided (within character budget)
    if name:
        name_line = f"\n  {name}"
        if count_characters(art + name_line) <= 198:
            art += name_line
        # If adding name would exceed budget, try shorter format
        elif count_characters(art) < 195:
            short_name = name[:10] if len(name) > 10 else name
            name_line = f"\n {short_name}"
            if count_characters(art + name_line) <= 198:
                art += name_line
    
    # Final safety check - ensure never exceeds 198
    if count_characters(art) > 198:
        # Truncate if absolutely necessary
        lines = art.split('\n')
        result_lines = []
        char_count = 0
        for line in lines:
            line_with_newline = line + '\n' if result_lines else line
            if char_count + len(line_with_newline) <= 195:
                result_lines.append(line)
                char_count += len(line_with_newline)
            else:
                break
        art = '\n'.join(result_lines)
        if count_characters(art) > 198:
            art = art[:195] + "..."
    
    return art


# ============================================================================
# LEGACY FUNCTIONS (for compatibility)
# ============================================================================

def hash_generation_seed(owner_id: str, timestamp: str, generation: int) -> str:
    """
    Create unique seed for individual traits based on owner, time, and generation.
    Returns a hex string for use as seed.
    """
    seed_string = f"{owner_id}:{timestamp}:{generation}"
    return hashlib.md5(seed_string.encode()).hexdigest()


if __name__ == "__main__":
    # Demo: Show different types across generations
    print("=" * 60)
    print("PET TYPE DEMONSTRATION")
    print("=" * 60)
    print("\nSame user, different generations = different types!")
    print("-" * 60)
    
    owner = "!test123"
    for gen in range(1, 4):
        timestamp = f"2024-01-{gen:02d}T12:00:00"
        seed = hash_generation_seed(owner, timestamp, gen)
        pet_type = get_pet_type(seed)
        pet = render_pet(owner, seed, "adult", f"Gen{gen}")
        print(f"\nGeneration {gen} - Type: {pet_type.upper()}")
        print(pet)
        print(f"Characters: {count_characters(pet)}")
    
    print("\n" + "=" * 60)
    print("All stages for one pet type:")
    print("-" * 60)
    
    seed = hash_generation_seed(owner, "2024-01-01T12:00:00", 1)
    pet_type = get_pet_type(seed)
    print(f"\nType: {pet_type.upper()}")
    
    for stage in ['egg', 'child', 'teen', 'adult', 'elder']:
        pet = render_pet(owner, seed, stage)
        print(f"\n{stage.upper()} stage ({count_characters(pet)} chars):")
        print(pet)
