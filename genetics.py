"""
Procedural ASCII pet generation system for MeshAgotchi.

Generates unique, cool ASCII art for pets based on generation seed.
Each pet can be a different type (alien, robot, monster, etc.) and has
extensive variation. Art evolves cohesively through all growth stages.
"""

import hashlib
import random
import time
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


def create_12x12_grid(lines: List[str]) -> str:
    """
    Create a 12x12 character grid (144 chars + 11 newlines = 155 total).
    Pads or truncates lines to exactly 12 characters, ensures exactly 12 lines.
    NO SPACES - automatically removes all spaces and uses characters creatively for padding.
    """
    # Remove empty lines and process
    processed_lines = []
    for line in lines:
        # Remove ALL spaces
        line = line.replace(' ', '')
        if line:  # Only add non-empty lines
            processed_lines.append(line)
    
    # Ensure exactly 12 lines
    while len(processed_lines) < 12:
        processed_lines.append('')
    processed_lines = processed_lines[:12]
    
    # Process each line to exactly 12 characters (no spaces)
    grid_lines = []
    for i, line in enumerate(processed_lines):
        # Remove any remaining spaces (safety check)
        line = line.replace(' ', '')
        
        if len(line) == 12:
            grid_lines.append(line)
        elif len(line) < 12:
            # Pad with decorative characters (no spaces)
            # Use different padding chars based on position for variety
            padding_chars = ['=', '-', '|', '.', '~', '*', '#', '@', '+', '_']
            pad_char = padding_chars[(i + len(line)) % len(padding_chars)]
            grid_lines.append(line + pad_char * (12 - len(line)))
        else:
            # Truncate to 12
            grid_lines.append(line[:12])
    
    return '\n'.join(grid_lines)


# ============================================================================
# EGG STAGE RENDERERS (20-40 chars)
# ============================================================================

def render_egg_robot(seed: str) -> str:
    """Render robot egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "==[===]==\n=[=?]=\n==[===]=="
    elif variant == 1:
        return "==+---+==\n=|?|=\n==+---+=="
    else:
        return "==[===]==\n=[=?]=\n==[===]=="


def render_egg_alien(seed: str) -> str:
    """Render alien egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "~~( )~~\n~(?)~\n~~( )~~"
    elif variant == 1:
        return "~~* *~~\n~*?*~\n~~* *~~"
    else:
        return "~~o o~~\n~o?o~\n~~o o~~"


def render_egg_monster(seed: str) -> str:
    """Render monster egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "##>---<##\n#>?<#\n##>---<##"
    elif variant == 1:
        return "##/---\\##\n#/?\\#\n##/---\\##"
    else:
        return "##<===>##\n#<?>#\n##<===>##"


def render_egg_creature(seed: str) -> str:
    """Render creature egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "~~( )~~\n~(?)~\n~~( )~~"
    elif variant == 1:
        return "~~{ }~~\n~{?}~\n~~{ }~~"
    else:
        return "~~^ ^~~\n~^?^~\n~~^ ^~~"


def render_egg_spirit(seed: str) -> str:
    """Render spirit egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "..* *..\n.*?*.\n..* *.."
    elif variant == 1:
        return "..~ ~..\n.~?~.\n..~ ~.."
    else:
        return ".....\n..?..\n....."


def render_egg_machine(seed: str) -> str:
    """Render machine egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "==#####==\n=#?#=\n==#####=="
    elif variant == 1:
        return "==@@@@==\n=@?@=\n==@@@@=="
    else:
        return "==+-+-+==\n=|?|=\n==+-+-+=="


def render_egg_beast(seed: str) -> str:
    """Render beast egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "~~( )~~\n~(?)~\n~~( )~~"
    elif variant == 1:
        return "~~o o~~\n~o?o~\n~~o o~~"
    else:
        return "~~^ ^~~\n~^?^~\n~~^ ^~~"


def render_egg_entity(seed: str) -> str:
    """Render entity egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "%%% %%\n%?%\n%%% %%"
    elif variant == 1:
        return "&&& &&\n&?&\n&&& &&"
    else:
        return "$$$ $$\n$?$\n$$$ $$"


def render_egg_cyborg(seed: str) -> str:
    """Render cyborg egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return "=[()]=\n=[(?)]=\n=[()]="
    elif variant == 1:
        return "=={ }==\n={?}=\n=={ }=="
    else:
        return "==|o|==\n=|?|=\n==|o|=="


def render_egg_phantom(seed: str) -> str:
    """Render phantom egg."""
    rng = get_seed_rng(seed)
    variant = rng.randint(0, 2)
    
    if variant == 0:
        return ".....\n..?..\n....."
    elif variant == 1:
        return "..''..\n.'?'.\n..''.."
    else:
        return "..::..\n.:?:.\n..::.."


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
        return f"=={eye_style}==\n=[====]=\n=|||=\n=[====]=="
    elif body_style == 1:
        return f"=={eye_style}==\n=+----+=\n=|||=\n=+----+=="
    else:
        return f"=={eye_style}==\n======\n=|||=\n======"


def render_child_alien(seed: str) -> str:
    """Render alien child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(* *)', '(O O)', '(0 0)'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"~~{eye_style}~~\n~(~~~~)~\n|^|\n~(____)~"
    elif body_style == 1:
        return f"~~{eye_style}~~\n~/~~~~\\~\n|^|\n~\\____/~"
    else:
        return f"~~{eye_style}~~\n~{eye_style}~\n|^|\n~(____)~"


def render_child_monster(seed: str) -> str:
    """Render monster child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['> <', 'V V', '^ ^', 'X X'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"##{eye_style}##\n#/~~~~\\#\n|>|\n#\\____/#"
    elif body_style == 1:
        return f"##{eye_style}##\n#<====>#\n|>|\n#<====>#"
    else:
        return f"##{eye_style}##\n#~~~~#\n|>|\n#____#"


def render_child_creature(seed: str) -> str:
    """Render creature child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(~ ~)', '(u u)'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"~~{eye_style}~~\n~(~~~~)~\n|^|\n~(____)~"
    elif body_style == 1:
        return f"~~{eye_style}~~\n~{{~~~~}}~\n|^|\n~{{____}}~"
    else:
        return f"~~{eye_style}~~\n~/~~~~\\~\n|^|\n~\\____/~"


def render_child_spirit(seed: str) -> str:
    """Render spirit child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['* *', '~ ~', '. .', 'o o'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"..{eye_style}..\n.*~~~~*.\n|~|\n.*____*."
    elif body_style == 1:
        return f"..{eye_style}..\n.~~~~~~.\n|~|\n.~____~."
    else:
        return f"..{eye_style}..\n..~~~~..\n|~|\n..____.."


def render_child_machine(seed: str) -> str:
    """Render machine child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['# #', '@ @', '+ +', '= ='])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"=={eye_style}==\n=#####=\n=|||=\n=#####=="
    elif body_style == 1:
        return f"=={eye_style}==\n=@@@@@=\n=|||=\n=@@@@@=="
    else:
        return f"=={eye_style}==\n=+++++=\n=|||=\n=+++++=="


def render_child_beast(seed: str) -> str:
    """Render beast child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(v v)', '(n n)'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"~~{eye_style}~~\n~/~~~~\\~\n|^|\n~\\____/~"
    elif body_style == 1:
        return f"~~{eye_style}~~\n~(~~~~)~\n|^|\n~(____)~"
    else:
        return f"~~{eye_style}~~\n~{{~~~~}}~\n|^|\n~{{____}}~"


def render_child_entity(seed: str) -> str:
    """Render entity child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['% %', '& &', '$ $', '# #'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"%%{eye_style}%%\n%~~~~%\n|^|\n%____%"
    elif body_style == 1:
        return f"&&{eye_style}&&\n&~~~~&\n|^|\n&____&"
    else:
        return f"$${eye_style}$$\n$~~~~$\n|^|\n$____$"


def render_child_cyborg(seed: str) -> str:
    """Render cyborg child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['[o o]', '(o o)', '[+ +]', '(= =)'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"=={eye_style}==\n=[====]=\n=|||=\n=[====]=="
    elif body_style == 1:
        return f"=={eye_style}==\n=(====)=\n=|||=\n=(====)=="
    else:
        return f"=={eye_style}==\n======\n=|||=\n======"


def render_child_phantom(seed: str) -> str:
    """Render phantom child."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['. .', "' '", ': :', 'o o'])
    body_style = rng.randint(0, 2)
    
    if body_style == 0:
        return f"..{eye_style}..\n..~~~~..\n|~|\n..____.."
    elif body_style == 1:
        return f"..{eye_style}..\n.'~~~~'.\n|~|\n.'____'."
    else:
        return f"..{eye_style}..\n.:~~~~:.\n|~|\n.:____:."


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
        lines.append("===||===")
    lines.append(f"=={eye_style}==")
    
    if body_variant == 0:
        lines.append("=[======]=")
        lines.append("=|||=")
        lines.append("=|====|=")
        lines.append("=[======]=")
        lines.append("==|| ||==")
    elif body_variant == 1:
        lines.append("=+------+=")
        lines.append("=|||=")
        lines.append("=|====|=")
        lines.append("=+------+=")
        lines.append("==|| ||==")
    else:
        lines.append("==========")
        lines.append("=|||=")
        lines.append("=|====|=")
        lines.append("==========")
        lines.append("==|| ||==")
    
    return '\n'.join(lines)


def render_teen_alien(seed: str) -> str:
    """Render alien teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(* *)', '(O O)', '(0 0)', '(^ ^)'])
    has_antenna = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_antenna:
        lines.append("~~~**~~~")
    lines.append(f"~~{eye_style}~~")
    
    if body_variant == 0:
        lines.append("~(~~~~~~)~")
        lines.append("|~~||~~|")
        lines.append("|~~^^~~|")
        lines.append("~(______)~")
        lines.append("~~|| ||~~")
    elif body_variant == 1:
        lines.append("~/~~~~~~\\~")
        lines.append("|~~||~~|")
        lines.append("|~~^^~~|")
        lines.append("~\\______/~")
        lines.append("~~|| ||~~")
    else:
        lines.append("~(~~~~~~)~")
        lines.append("|~~||~~|")
        lines.append("|~~~~~~|")
        lines.append("~(______)~")
        lines.append("~~|| ||~~")
    
    return '\n'.join(lines)


def render_teen_monster(seed: str) -> str:
    """Render monster teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['> <', 'V V', '^ ^', 'X X', '< >'])
    has_horns = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_horns:
        lines.append("###/\\###")
    lines.append(f"##{eye_style}##")
    
    if body_variant == 0:
        lines.append("#/~~~~~~\\#")
        lines.append("|~~||~~|")
        lines.append("|~~>>~~|")
        lines.append("#\\______/#")
        lines.append("##|| ||##")
    elif body_variant == 1:
        lines.append("#<======>#")
        lines.append("|~~||~~|")
        lines.append("|~~>>~~|")
        lines.append("#<======>#")
        lines.append("##|| ||##")
    else:
        lines.append("#~~~~~~~~#")
        lines.append("|~~||~~|")
        lines.append("|~~>>~~|")
        lines.append("#________#")
        lines.append("##|| ||##")
    
    return '\n'.join(lines)


def render_teen_creature(seed: str) -> str:
    """Render creature teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(~ ~)', '(u u)', '(v v)'])
    has_ears = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_ears:
        lines.append("~~~^ ^~~~")
    lines.append(f"~~{eye_style}~~")
    
    if body_variant == 0:
        lines.append("~(~~~~~~)~")
        lines.append("|~~||~~|")
        lines.append("|~~^^~~|")
        lines.append("~(______)~")
        lines.append("~~|| ||~~")
    elif body_variant == 1:
        lines.append("~{~~~~~~}~")
        lines.append("|~~||~~|")
        lines.append("|~~^^~~|")
        lines.append("~{______}~")
        lines.append("~~|| ||~~")
    else:
        lines.append("~/~~~~~~\\~")
        lines.append("|~~||~~|")
        lines.append("|~~^^~~|")
        lines.append("~\\______/~")
        lines.append("~~|| ||~~")
    
    return '\n'.join(lines)


def render_teen_spirit(seed: str) -> str:
    """Render spirit teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['* *', '~ ~', '. .', 'o o', '+ +'])
    has_aura = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_aura:
        lines.append("...~~~...")
    lines.append(f"..{eye_style}..")
    
    if body_variant == 0:
        lines.append(".*~~~~~~*.")
        lines.append("|~~||~~|")
        lines.append("|~~~~~~|")
        lines.append(".*______*.")
        lines.append("..|| ||..")
    elif body_variant == 1:
        lines.append(".~~~~~~~~.")
        lines.append("|~~||~~|")
        lines.append("|~~~~~~|")
        lines.append(".~______~.")
        lines.append("..|| ||..")
    else:
        lines.append("..~~~~~~..")
        lines.append("|~~||~~|")
        lines.append("|~~~~~~|")
        lines.append("..______..")
        lines.append("..|| ||..")
    
    return '\n'.join(lines)


def render_teen_machine(seed: str) -> str:
    """Render machine teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['# #', '@ @', '+ +', '= =', '$ $'])
    has_panel = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_panel:
        lines.append("===###===")
    lines.append(f"=={eye_style}==")
    
    if body_variant == 0:
        lines.append("=########=")
        lines.append("=|||=")
        lines.append("=|====|=")
        lines.append("=########=")
        lines.append("==|| ||==")
    elif body_variant == 1:
        lines.append("=@@@@@@@@=")
        lines.append("=|||=")
        lines.append("=|====|=")
        lines.append("=@@@@@@@@=")
        lines.append("==|| ||==")
    else:
        lines.append("=++++++++=")
        lines.append("=|||=")
        lines.append("=|====|=")
        lines.append("=++++++++=")
        lines.append("==|| ||==")
    
    return '\n'.join(lines)


def render_teen_beast(seed: str) -> str:
    """Render beast teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['(o o)', '(^ ^)', '(v v)', '(n n)', '(> <)'])
    has_mane = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_mane:
        lines.append("~~~^^^~~~")
    lines.append(f"~~{eye_style}~~")
    
    if body_variant == 0:
        lines.append("~/~~~~~~\\~")
        lines.append("|~~||~~|")
        lines.append("|~~^^~~|")
        lines.append("~\\______/~")
        lines.append("~~|| ||~~")
    elif body_variant == 1:
        lines.append("~(~~~~~~)~")
        lines.append("|~~||~~|")
        lines.append("|~~^^~~|")
        lines.append("~(______)~")
        lines.append("~~|| ||~~")
    else:
        lines.append("~{~~~~~~}~")
        lines.append("|~~||~~|")
        lines.append("|~~^^~~|")
        lines.append("~{______}~")
        lines.append("~~|| ||~~")
    
    return '\n'.join(lines)


def render_teen_entity(seed: str) -> str:
    """Render entity teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['% %', '& &', '$ $', '# #', '@ @'])
    has_symbols = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_symbols:
        lines.append("%%% %%%")
    lines.append(f"%%{eye_style}%%")
    
    if body_variant == 0:
        lines.append("%~~~~~~~~%")
        lines.append("|~~||~~|")
        lines.append("|~~^^~~|")
        lines.append("%______%")
        lines.append("%%|| ||%%")
    elif body_variant == 1:
        lines.append("&~~~~~~~~&")
        lines.append("|~~||~~|")
        lines.append("|~~^^~~|")
        lines.append("&______&")
        lines.append("&&|| ||&&")
    else:
        lines.append("$~~~~~~~~$")
        lines.append("|~~||~~|")
        lines.append("|~~^^~~|")
        lines.append("$______$")
        lines.append("$$|| ||$$")
    
    return '\n'.join(lines)


def render_teen_cyborg(seed: str) -> str:
    """Render cyborg teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['[o o]', '(o o)', '[+ +]', '(= =)', '[. .]'])
    has_tech = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_tech:
        lines.append("===[=]===")
    lines.append(f"=={eye_style}==")
    
    if body_variant == 0:
        lines.append("=[======]=")
        lines.append("=|||=")
        lines.append("=|====|=")
        lines.append("=[======]=")
        lines.append("==|| ||==")
    elif body_variant == 1:
        lines.append("=(======)=")
        lines.append("=|||=")
        lines.append("=|====|=")
        lines.append("=(======)=")
        lines.append("==|| ||==")
    else:
        lines.append("==========")
        lines.append("=|||=")
        lines.append("=|====|=")
        lines.append("==========")
        lines.append("==|| ||==")
    
    return '\n'.join(lines)


def render_teen_phantom(seed: str) -> str:
    """Render phantom teen."""
    rng = get_seed_rng(seed)
    eye_style = rng.choice(['. .', "' '", ': :', 'o o', '~ ~'])
    has_glow = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_glow:
        lines.append(".....")
    lines.append(f"..{eye_style}..")
    
    if body_variant == 0:
        lines.append("..~~~~~~..")
        lines.append("|~~||~~|")
        lines.append("|~~~~~~|")
        lines.append("..______..")
        lines.append("..|| ||..")
    elif body_variant == 1:
        lines.append(".'~~~~~~'.")
        lines.append("|~~||~~|")
        lines.append("|~~~~~~|")
        lines.append(".'______'.")
        lines.append("..|| ||..")
    else:
        lines.append(".:~~~~~~:.")
        lines.append("|~~||~~|")
        lines.append("|~~~~~~|")
        lines.append(".:______:.")
        lines.append("..|| ||..")
    
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
    """Render robot adult - 12x12 grid, NO SPACES."""
    rng = get_seed_rng(seed)
    eye_left = rng.choice(['o', '+', '=', '.', 'X', 'O'])
    eye_right = rng.choice(['o', '+', '=', '.', 'X', 'O'])
    has_antenna = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_antenna:
        lines.append("====||======")
    else:
        lines.append("============")
    
    # Head with eyes
    lines.append(f"==[{eye_left}{eye_right}]====")
    lines.append("==[====]====")
    
    # Body variants
    if body_variant == 0:
        lines.append("=[========]=")
        lines.append("=|||========")
        lines.append("=|======|==")
        lines.append("=|||========")
        lines.append("=[========]=")
    elif body_variant == 1:
        lines.append("=+--------+=")
        lines.append("=|||========")
        lines.append("=|======|==")
        lines.append("=|||========")
        lines.append("=+--------+=")
    else:
        lines.append("============")
        lines.append("=|||========")
        lines.append("=|======|==")
        lines.append("=|||========")
        lines.append("============")
    
    # Legs
    lines.append("==||====||==")
    lines.append("==||====||==")
    
    return create_12x12_grid(lines)


def render_adult_alien(seed: str) -> str:
    """Render alien adult - 12x12 grid, NO SPACES."""
    rng = get_seed_rng(seed)
    eye_left = rng.choice(['o', '*', 'O', '0', '^', '~'])
    eye_right = rng.choice(['o', '*', 'O', '0', '^', '~'])
    has_antenna = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_antenna:
        lines.append("~~~**~~~~~~")
    else:
        lines.append("~~~~~~~~~~~")
    
    # Head
    lines.append(f"~~({eye_left}{eye_right})~~~~")
    lines.append("~~(~~~~)~~~~")
    
    # Body
    if body_variant == 0:
        lines.append("~(~~~~~~~~)~")
        lines.append("|~~||~~~~~~|")
        lines.append("|~~^^~~~~~~|")
        lines.append("|~~||~~~~~~|")
        lines.append("~(________)~")
    elif body_variant == 1:
        lines.append("~/~~~~~~~~\\~")
        lines.append("|~~||~~~~~~|")
        lines.append("|~~^^~~~~~~|")
        lines.append("|~~||~~~~~~|")
        lines.append("~\\________/~")
    else:
        lines.append("~{~~~~~~~~}~")
        lines.append("|~~||~~~~~~|")
        lines.append("|~~^^~~~~~~|")
        lines.append("|~~||~~~~~~|")
        lines.append("~{________}~")
    
    # Legs
    lines.append("==||====||==")
    
    return create_12x12_grid(lines)


def render_adult_monster(seed: str) -> str:
    """Render monster adult - 12x12 grid, NO SPACES."""
    rng = get_seed_rng(seed)
    eye_left = rng.choice(['>', 'V', '^', 'X', '<'])
    eye_right = rng.choice(['<', 'V', '^', 'X', '>'])
    has_horns = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_horns:
        lines.append("###/\\/\\######")
    else:
        lines.append("############")
    
    lines.append(f"##{eye_left}{eye_right}########")
    lines.append("##/\\##########")
    
    if body_variant == 0:
        lines.append("#/~~~~~~~~\\##")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~>>>>~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("#\\________/#")
    elif body_variant == 1:
        lines.append("#<========>##")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~>>>>~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("#<========>##")
    else:
        lines.append("#~~~~~~~~##")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~>>>>~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("#________##")
    
    lines.append("##||====||##")
    lines.append("##||====||##")
    
    return create_12x12_grid(lines)


def render_adult_creature(seed: str) -> str:
    """Render creature adult - 12x12 grid, NO SPACES."""
    rng = get_seed_rng(seed)
    eye_left = rng.choice(['o', '^', '~', 'u', 'v', 'n'])
    eye_right = rng.choice(['o', '^', '~', 'u', 'v', 'n'])
    has_ears = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_ears:
        lines.append("~~~^^^^~~~~~")
    else:
        lines.append("~~~~~~~~~~~~")
    
    lines.append(f"~~({eye_left}{eye_right})~~~~~")
    lines.append("~~(~~~~)~~~~~")
    
    if body_variant == 0:
        lines.append("~(~~~~~~~~)~~")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~^^^^~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("~(________)~")
    elif body_variant == 1:
        lines.append("~{~~~~~~~~}~~")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~^^^^~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("~{________}~")
    else:
        lines.append("~/~~~~~~~~\\~~")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~^^^^~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("~\\________/~")
    
    lines.append("~~||====||~~")
    lines.append("~~||====||~~")
    
    return create_12x12_grid(lines)


def render_adult_spirit(seed: str) -> str:
    """Render spirit adult - 12x12 grid, NO SPACES."""
    rng = get_seed_rng(seed)
    eye_left = rng.choice(['*', '~', '.', 'o', '+'])
    eye_right = rng.choice(['*', '~', '.', 'o', '+'])
    has_aura = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_aura:
        lines.append("...~~~~~....")
    else:
        lines.append("............")
    
    lines.append(f"..{eye_left}{eye_right}........")
    lines.append("..*~*........")
    
    if body_variant == 0:
        lines.append(".*~~~~~~~~*.")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~~~~~~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append(".*________*.")
    elif body_variant == 1:
        lines.append(".~~~~~~~~~~.")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~~~~~~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append(".~________~.")
    else:
        lines.append("..~~~~~~~~..")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~~~~~~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("..________..")
    
    lines.append("..||====||..")
    lines.append("..||====||..")
    
    return create_12x12_grid(lines)


def render_adult_machine(seed: str) -> str:
    """Render machine adult - 12x12 grid, NO SPACES."""
    rng = get_seed_rng(seed)
    eye_left = rng.choice(['#', '@', '+', '=', '$', '%'])
    eye_right = rng.choice(['#', '@', '+', '=', '$', '%'])
    has_panel = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_panel:
        lines.append("===######====")
    else:
        lines.append("============")
    
    lines.append(f"=={eye_left}{eye_right}========")
    lines.append("==[====]======")
    
    if body_variant == 0:
        lines.append("=##########==")
        lines.append("=|||==========")
        lines.append("=|======|====")
        lines.append("=|||==========")
        lines.append("=##########==")
    elif body_variant == 1:
        lines.append("=@@@@@@@@@@==")
        lines.append("=|||==========")
        lines.append("=|======|====")
        lines.append("=|||==========")
        lines.append("=@@@@@@@@@@==")
    else:
        lines.append("=++++++++++==")
        lines.append("=|||==========")
        lines.append("=|======|====")
        lines.append("=|||==========")
        lines.append("=++++++++++==")
    
    lines.append("==||====||====")
    lines.append("==||====||====")
    
    return create_12x12_grid(lines)


def render_adult_beast(seed: str) -> str:
    """Render beast adult - 12x12 grid, NO SPACES."""
    rng = get_seed_rng(seed)
    eye_left = rng.choice(['o', '^', 'v', 'n', '>', 'U'])
    eye_right = rng.choice(['o', '^', 'v', 'n', '<', 'U'])
    has_mane = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_mane:
        lines.append("~~~^^^^^^~~~")
    else:
        lines.append("~~~~~~~~~~~~")
    
    lines.append(f"~~({eye_left}{eye_right})~~~~~")
    lines.append("~~(~~~~)~~~~~")
    
    if body_variant == 0:
        lines.append("~/~~~~~~~~\\~~")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~^^^^~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("~\\________/~")
    elif body_variant == 1:
        lines.append("~(~~~~~~~~)~~")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~^^^^~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("~(________)~")
    else:
        lines.append("~{~~~~~~~~}~~")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~^^^^~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("~{________}~")
    
    lines.append("~~||====||~~")
    lines.append("~~||====||~~")
    
    return create_12x12_grid(lines)


def render_adult_entity(seed: str) -> str:
    """Render entity adult - 12x12 grid, NO SPACES."""
    rng = get_seed_rng(seed)
    eye_left = rng.choice(['%', '&', '$', '#', '@', '!'])
    eye_right = rng.choice(['%', '&', '$', '#', '@', '!'])
    has_symbols = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_symbols:
        lines.append("%%%%&%%%%%%%")
    else:
        lines.append("%%%%%%%%%%%%")
    
    lines.append(f"%%{eye_left}{eye_right}%%%%%%%%")
    lines.append("%%[====]%%%%%%")
    
    if body_variant == 0:
        lines.append("%~~~~~~~~%%%")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~^^^^~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("%________%%%")
    elif body_variant == 1:
        lines.append("&~~~~~~~~&&&")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~^^^^~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("&________&&&")
    else:
        lines.append("$~~~~~~~~$$$")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~^^^^~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("$________$$$")
    
    lines.append("%%||====||%%%")
    lines.append("%%||====||%%%")
    
    return create_12x12_grid(lines)


def render_adult_cyborg(seed: str) -> str:
    """Render cyborg adult - 12x12 grid, NO SPACES."""
    rng = get_seed_rng(seed)
    eye_left = rng.choice(['o', '+', '=', '.', 'O'])
    eye_right = rng.choice(['o', '+', '=', '.', 'O'])
    use_brackets = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    lines.append("===[====]====")
    
    if use_brackets:
        lines.append(f"==[{eye_left}{eye_right}]======")
    else:
        lines.append(f"==({eye_left}{eye_right})======")
    
    lines.append("==[====]======")
    
    if body_variant == 0:
        lines.append("=[========]==")
        lines.append("=|||==========")
        lines.append("=|======|====")
        lines.append("=|||==========")
        lines.append("=[========]==")
    elif body_variant == 1:
        lines.append("=(========)==")
        lines.append("=|||==========")
        lines.append("=|======|====")
        lines.append("=|||==========")
        lines.append("=(========)==")
    else:
        lines.append("=============")
        lines.append("=|||==========")
        lines.append("=|======|====")
        lines.append("=|||==========")
        lines.append("=============")
    
    lines.append("==||====||====")
    lines.append("==||====||====")
    
    return create_12x12_grid(lines)


def render_adult_phantom(seed: str) -> str:
    """Render phantom adult - 12x12 grid, NO SPACES."""
    rng = get_seed_rng(seed)
    eye_left = rng.choice(['.', "'", ':', 'o', '~'])
    eye_right = rng.choice(['.', "'", ':', 'o', '~'])
    has_glow = rng.random() > 0.5
    body_variant = rng.randint(0, 2)
    
    lines = []
    if has_glow:
        lines.append(".....~~~~~~~")
    else:
        lines.append("............")
    
    lines.append(f"..{eye_left}{eye_right}........")
    lines.append("..~~~~........")
    
    if body_variant == 0:
        lines.append("..~~~~~~~~..")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~~~~~~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append("..________..")
    elif body_variant == 1:
        lines.append(".'~~~~~~~~'.")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~~~~~~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append(".'________'.")
    else:
        lines.append(".:~~~~~~~~:.")
        lines.append("|~~~||~~~~~~|")
        lines.append("|~~~~~~~~~~|")
        lines.append("|~~~||~~~~~~|")
        lines.append(".:________:.")
    
    lines.append("..||====||..")
    lines.append("..||====||..")
    
    return create_12x12_grid(lines)


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
        lines.append("=====||=====")
    if has_panel:
        lines.append("====[==]====")
    lines.append(f"==={eye_style}===")
    
    if body_variant == 0:
        lines.append("==[==========]==")
        lines.append("==|====||====|==")
        lines.append("==|========|==")
        lines.append("==|====||====|==")
        lines.append("==[==========]==")
        lines.append("===||====||===")
        lines.append("===||====||===")
        lines.append("==/========\\==")
        lines.append("=|==WISE==|=")
        lines.append("==\\________/==")
    elif body_variant == 1:
        lines.append("==+----------+==")
        lines.append("==|====||====|==")
        lines.append("==|========|==")
        lines.append("==|====||====|==")
        lines.append("==+----------+==")
        lines.append("===||====||===")
        lines.append("===||====||===")
        lines.append("==/========\\==")
        lines.append("=|==WISE==|=")
        lines.append("==\\________/==")
    else:
        lines.append("==============")
        lines.append("==|====||====|==")
        lines.append("==|========|==")
        lines.append("==|====||====|==")
        lines.append("==============")
        lines.append("===||====||===")
        lines.append("===||====||===")
        lines.append("==/========\\==")
        lines.append("=|==WISE==|=")
        lines.append("==\\________/==")
    
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
        lines.append("~~~~~**~~~~~")
    if has_pattern:
        lines.append("~~~~* * *~~~~")
    lines.append(f"~~~{eye_style}~~~")
    
    if body_variant == 0:
        lines.append("~~(~~~~~~~~~~)~~")
        lines.append("~~|====||====|~~")
        lines.append("~~|~~^^^^^^~~|~~")
        lines.append("~~|====||====|~~")
        lines.append("~~(__________)~~")
        lines.append("~~~||====||~~~")
        lines.append("~~~||====||~~~")
        lines.append("~~/========\\~~")
        lines.append("~|~~WISE~~|~")
        lines.append("~~\\________/~~")
    elif body_variant == 1:
        lines.append("~~/~~~~~~~~~~\\~~")
        lines.append("~~|====||====|~~")
        lines.append("~~|~~^^^^^^~~|~~")
        lines.append("~~|====||====|~~")
        lines.append("~~\\__________/~~")
        lines.append("~~~||====||~~~")
        lines.append("~~~||====||~~~")
        lines.append("~~/========\\~~")
        lines.append("~|~~WISE~~|~")
        lines.append("~~\\________/~~")
    else:
        lines.append("~~(~~~~~~~~~~)~~")
        lines.append("~~|====||====|~~")
        lines.append("~~|~~~~~~~~~~|~~")
        lines.append("~~|====||====|~~")
        lines.append("~~(__________)~~")
        lines.append("~~~||====||~~~")
        lines.append("~~~||====||~~~")
        lines.append("~~/========\\~~")
        lines.append("~|~~WISE~~|~")
        lines.append("~~\\________/~~")
    
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
        lines.append("###/\\/\\/\\###")
    if has_spikes:
        lines.append("###>>>>>>###")
    lines.append(f"###{eye_style}###")
    
    if body_variant == 0:
        lines.append("##/~~~~~~~~~~\\##")
        lines.append("##|====||====|##")
        lines.append("##|~~>>>>>>~~|##")
        lines.append("##|====||====|##")
        lines.append("##\\__________/##")
        lines.append("###||====||###")
        lines.append("###||====||###")
        lines.append("##/========\\##")
        lines.append("#|==WISE==|#")
        lines.append("##\\________/##")
    elif body_variant == 1:
        lines.append("##<==========>##")
        lines.append("##|====||====|##")
        lines.append("##|~~>>>>>>~~|##")
        lines.append("##|====||====|##")
        lines.append("##<==========>##")
        lines.append("###||====||###")
        lines.append("###||====||###")
        lines.append("##/========\\##")
        lines.append("#|==WISE==|#")
        lines.append("##\\________/##")
    else:
        lines.append("##~~~~~~~~~~##")
        lines.append("##|====||====|##")
        lines.append("##|~~>>>>>>~~|##")
        lines.append("##|====||====|##")
        lines.append("##__________##")
        lines.append("###||====||###")
        lines.append("###||====||###")
        lines.append("##/========\\##")
        lines.append("#|==WISE==|#")
        lines.append("##\\________/##")
    
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
        lines.append("~~~~^     ^~~~~")
    if has_tail:
        lines.append("~~~~^^^^^~~~~")
    lines.append(f"~~~{eye_style}~~~")
    
    if body_variant == 0:
        lines.append("~~(~~~~~~~~~~)~~")
        lines.append("~~|====||====|~~")
        lines.append("~~|~~^^^^^^~~|~~")
        lines.append("~~|====||====|~~")
        lines.append("~~(__________)~~")
        lines.append("~~~||====||~~~")
        lines.append("~~~||====||~~~")
        lines.append("~~/========\\~~")
        lines.append("~|~~WISE~~|~")
        lines.append("~~\\________/~~")
    elif body_variant == 1:
        lines.append("~~{~~~~~~~~~~}~~")
        lines.append("~~|====||====|~~")
        lines.append("~~|~~^^^^^^~~|~~")
        lines.append("~~|====||====|~~")
        lines.append("~~{__________}~~")
        lines.append("~~~||====||~~~")
        lines.append("~~~||====||~~~")
        lines.append("~~/========\\~~")
        lines.append("~|~~WISE~~|~")
        lines.append("~~\\________/~~")
    else:
        lines.append("~~/~~~~~~~~~~\\~~")
        lines.append("~~|====||====|~~")
        lines.append("~~|~~^^^^^^~~|~~")
        lines.append("~~|====||====|~~")
        lines.append("~~\\__________/~~")
        lines.append("~~~||====||~~~")
        lines.append("~~~||====||~~~")
        lines.append("~~/========\\~~")
        lines.append("~|~~WISE~~|~")
        lines.append("~~\\________/~~")
    
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
        lines.append("....~~~~~~~....")
    if has_glow:
        lines.append("....*****....")
    lines.append(f"...{eye_style}...")
    
    if body_variant == 0:
        lines.append("..*~~~~~~~~~~*..")
        lines.append("..|====||====|..")
        lines.append("..|~~~~~~~~~~|..")
        lines.append("..|====||====|..")
        lines.append("..*__________*..")
        lines.append("...||====||...")
        lines.append("...||====||...")
        lines.append("../========\\..")
        lines.append(".|==WISE==|.")
        lines.append("..\\________/..")
    elif body_variant == 1:
        lines.append("..~~~~~~~~~~~~..")
        lines.append("..|====||====|..")
        lines.append("..|~~~~~~~~~~|..")
        lines.append("..|====||====|..")
        lines.append("..~__________~..")
        lines.append("...||====||...")
        lines.append("...||====||...")
        lines.append("../========\\..")
        lines.append(".|==WISE==|.")
        lines.append("..\\________/..")
    else:
        lines.append("...~~~~~~~~~~...")
        lines.append("..|====||====|..")
        lines.append("..|~~~~~~~~~~|..")
        lines.append("..|====||====|..")
        lines.append("...__________...")
        lines.append("...||====||...")
        lines.append("...||====||...")
        lines.append("../========\\..")
        lines.append(".|==WISE==|.")
        lines.append("..\\________/..")
    
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
        lines.append("====########====")
    if has_tech:
        lines.append("====@@@@@@@====")
    lines.append(f"==={eye_style}===")
    
    if body_variant == 0:
        lines.append("==############==")
        lines.append("==|====||====|==")
        lines.append("==|========|==")
        lines.append("==|====||====|==")
        lines.append("==############==")
        lines.append("===||====||===")
        lines.append("===||====||===")
        lines.append("==/========\\==")
        lines.append("=|==WISE==|=")
        lines.append("==\\________/==")
    elif body_variant == 1:
        lines.append("==@@@@@@@@@@@@==")
        lines.append("==|====||====|==")
        lines.append("==|========|==")
        lines.append("==|====||====|==")
        lines.append("==@@@@@@@@@@@@==")
        lines.append("===||====||===")
        lines.append("===||====||===")
        lines.append("==/========\\==")
        lines.append("=|==WISE==|=")
        lines.append("==\\________/==")
    else:
        lines.append("==++++++++++++==")
        lines.append("==|====||====|==")
        lines.append("==|========|==")
        lines.append("==|====||====|==")
        lines.append("==++++++++++++==")
        lines.append("===||====||===")
        lines.append("===||====||===")
        lines.append("==/========\\==")
        lines.append("=|==WISE==|=")
        lines.append("==\\________/==")
    
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
        lines.append("~~~~^^^^^^^^^~~~~")
    if has_claws:
        lines.append("~~~~>>>>>>~~~~")
    lines.append(f"~~~{eye_style}~~~")
    
    if body_variant == 0:
        lines.append("~~/~~~~~~~~~~\\~~")
        lines.append("~~|====||====|~~")
        lines.append("~~|~~^^^^^^~~|~~")
        lines.append("~~|====||====|~~")
        lines.append("~~\\__________/~~")
        lines.append("~~~||====||~~~")
        lines.append("~~~||====||~~~")
        lines.append("~~/========\\~~")
        lines.append("~|~~WISE~~|~")
        lines.append("~~\\________/~~")
    elif body_variant == 1:
        lines.append("~~(~~~~~~~~~~)~~")
        lines.append("~~|====||====|~~")
        lines.append("~~|~~^^^^^^~~|~~")
        lines.append("~~|====||====|~~")
        lines.append("~~(__________)~~")
        lines.append("~~~||====||~~~")
        lines.append("~~~||====||~~~")
        lines.append("~~/========\\~~")
        lines.append("~|~~WISE~~|~")
        lines.append("~~\\________/~~")
    else:
        lines.append("~~{~~~~~~~~~~}~~")
        lines.append("~~|====||====|~~")
        lines.append("~~|~~^^^^^^~~|~~")
        lines.append("~~|====||====|~~")
        lines.append("~~{__________}~~")
        lines.append("~~~||====||~~~")
        lines.append("~~~||====||~~~")
        lines.append("~~/========\\~~")
        lines.append("~|~~WISE~~|~")
        lines.append("~~\\________/~~")
    
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
        lines.append("%%%% %%%%%%%")
    if has_pattern:
        lines.append("&&&& &&&&&")
    lines.append(f"%%%{eye_style}%%%")
    
    if body_variant == 0:
        lines.append("%%~~~~~~~~~~%%")
        lines.append("%%|====||====|%%")
        lines.append("%%|~~^^^^^^~~|%%")
        lines.append("%%|====||====|%%")
        lines.append("%%__________%%")
        lines.append("%%%||====||%%%")
        lines.append("%%%||====||%%%")
        lines.append("%%/========\\%%")
        lines.append("%|==WISE==|%")
        lines.append("%%\\________/%%")
    elif body_variant == 1:
        lines.append("&&~~~~~~~~~~&&")
        lines.append("&&|====||====|&&")
        lines.append("&&|~~^^^^^^~~|&&")
        lines.append("&&|====||====|&&")
        lines.append("&&__________&&")
        lines.append("&&&||====||&&&")
        lines.append("&&&||====||&&&")
        lines.append("&&/========\\&&")
        lines.append("&|==WISE==|&")
        lines.append("&&\\________/&&")
    else:
        lines.append("$$~~~~~~~~~~$$")
        lines.append("$$|====||====|$$")
        lines.append("$$|~~^^^^^^~~|$$")
        lines.append("$$|====||====|$$")
        lines.append("$$__________$$")
        lines.append("$$$||====||$$$")
        lines.append("$$$||====||$$$")
        lines.append("$$/========\\$$")
        lines.append("$|==WISE==|$")
        lines.append("$$\\________/$$")
    
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
        lines.append("====[====]====")
    if has_organic:
        lines.append("====(    )====")
    lines.append(f"==={eye_style}===")
    
    if body_variant == 0:
        lines.append("==[==========]==")
        lines.append("==|====||====|==")
        lines.append("==|========|==")
        lines.append("==|====||====|==")
        lines.append("==[==========]==")
        lines.append("===||====||===")
        lines.append("===||====||===")
        lines.append("==/========\\==")
        lines.append("=|==WISE==|=")
        lines.append("==\\________/==")
    elif body_variant == 1:
        lines.append("==(==========)==")
        lines.append("==|====||====|==")
        lines.append("==|========|==")
        lines.append("==|====||====|==")
        lines.append("==(==========)==")
        lines.append("===||====||===")
        lines.append("===||====||===")
        lines.append("==/========\\==")
        lines.append("=|==WISE==|=")
        lines.append("==\\________/==")
    else:
        lines.append("==============")
        lines.append("==|====||====|==")
        lines.append("==|========|==")
        lines.append("==|====||====|==")
        lines.append("==============")
        lines.append("===||====||===")
        lines.append("===||====||===")
        lines.append("==/========\\==")
        lines.append("=|==WISE==|=")
        lines.append("==\\________/==")
    
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
        lines.append(".....")
    if has_aura:
        lines.append("....~~~~~....")
    lines.append(f"...{eye_style}...")
    
    if body_variant == 0:
        lines.append("...~~~~~~~~~~...")
        lines.append("..|====||====|..")
        lines.append("..|~~~~~~~~~~|..")
        lines.append("..|====||====|..")
        lines.append("...__________...")
        lines.append("...||====||...")
        lines.append("...||====||...")
        lines.append("../========\\..")
        lines.append(".|==WISE==|.")
        lines.append("..\\________/..")
    elif body_variant == 1:
        lines.append(".'~~~~~~~~~~'.")
        lines.append("..|====||====|..")
        lines.append("..|~~~~~~~~~~|..")
        lines.append("..|====||====|..")
        lines.append(".'__________'.")
        lines.append("...||====||...")
        lines.append("...||====||...")
        lines.append("../========\\..")
        lines.append(".|==WISE==|.")
        lines.append("..\\________/..")
    else:
        lines.append(".:~~~~~~~~~~:.")
        lines.append("..|====||====|..")
        lines.append("..|~~~~~~~~~~|..")
        lines.append("..|====||====|..")
        lines.append(".:__________:.")
        lines.append("...||====||...")
        lines.append("...||====||...")
        lines.append("../========\\..")
        lines.append(".|==WISE==|.")
        lines.append("..\\________/..")
    
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
# EXPRESSION SYSTEM - Adds variety while keeping core shape
# ============================================================================

def apply_expression(art: str, expression_seed: str, pet_type: str) -> str:
    """
    Apply animated expression and pose variations to ASCII art while preserving core structure.
    
    This function:
    1. Changes facial expressions (winking, smiling, etc.)
    2. Changes body poses (arms up/down, body lean, stance)
    3. Preserves the pet's art style and core shape
    
    Args:
        art: Base ASCII art (deterministic from generation_seed)
        expression_seed: Seed that changes each time (time-based)
        pet_type: Pet type for expression style matching
    
    Returns:
        Modified art with expression and pose applied
    """
    if not art:
        return art
    
    rng = get_seed_rng(expression_seed)
    lines = art.split('\n')
    
    # Expression types: wink, smile, happy, neutral, surprised, sleepy
    expression_type = rng.choice(['wink', 'smile', 'happy', 'neutral', 'surprised', 'sleepy', 'excited'])
    
    # Pose types: neutral, arms_up, arms_out, lean_left, lean_right, crouch, stretch
    pose_type = rng.choice(['neutral', 'arms_up', 'arms_out', 'lean_left', 'lean_right', 'crouch', 'stretch', 'wave'])
    
    # Find the line with eyes (usually first or second non-empty line)
    # Look for common eye patterns (NO SPACES - patterns are adjacent)
    eye_line_idx = None
    eye_patterns = [
        'oo', 'OO', '00', '**', '++', '==', '..', '^^', '~~', 
        'XX', 'xx', 'uu', 'UU', '[o', '(o', '{o', ']o', ')o', '}o',
        'o]', 'o)', 'o}', '[O', '(O', '{O', ']O', ')O', '}O', 'O]', 'O)', 'O}',
        '[+', '(+', '{+', ']+', ')+', '}+', '[=', '(=', '{=', ']=', ')=', '}=',
        '[*', '(*', '{*', ']*', ')*', '}*', '[.', '(.', '{.', '].', ').', '}.',
        '[^', '(^', '{^', ']^', ')^', '}^', '[~', '(~', '{~', ']~', ')~', '}~',
        '[X', '(X', '{X', ']X', ')X', '}X', '[x', '(x', '{x', ']x', ')x', '}x',
        '><', 'VV', '^^', '<>', '>', '<', 'V', '^'
    ]
    
    for i, line in enumerate(lines):
        # Check if line contains eye patterns (no spaces)
        if any(pattern in line for pattern in eye_patterns):
            eye_line_idx = i
            break
    
    if eye_line_idx is None:
        # No eyes found, still apply pose variations
        lines = apply_pose_variations(lines, pose_type, pet_type, rng)
        return '\n'.join(lines)
    
    eye_line = lines[eye_line_idx]
    modified_line = eye_line
    
    # Apply expression based on pet type and expression
    if pet_type == 'robot':
        modified_line = _apply_robot_expression(eye_line, expression_type, rng)
    elif pet_type == 'alien':
        modified_line = _apply_alien_expression(eye_line, expression_type, rng)
    elif pet_type == 'monster':
        modified_line = _apply_monster_expression(eye_line, expression_type, rng)
    elif pet_type == 'creature':
        modified_line = _apply_creature_expression(eye_line, expression_type, rng)
    elif pet_type == 'spirit':
        modified_line = _apply_spirit_expression(eye_line, expression_type, rng)
    elif pet_type == 'machine':
        modified_line = _apply_machine_expression(eye_line, expression_type, rng)
    elif pet_type == 'beast':
        modified_line = _apply_beast_expression(eye_line, expression_type, rng)
    elif pet_type == 'entity':
        modified_line = _apply_entity_expression(eye_line, expression_type, rng)
    elif pet_type == 'cyborg':
        modified_line = _apply_cyborg_expression(eye_line, expression_type, rng)
    elif pet_type == 'phantom':
        modified_line = _apply_phantom_expression(eye_line, expression_type, rng)
    else:
        modified_line = _apply_creature_expression(eye_line, expression_type, rng)
    
    # Update the line
    lines[eye_line_idx] = modified_line
    
    # Apply pose variations to the entire art (preserves style, changes position)
    lines = apply_pose_variations(lines, pose_type, pet_type, rng)
    
    return '\n'.join(lines)


def apply_pose_variations(lines: List[str], pose_type: str, pet_type: str, rng: random.Random) -> List[str]:
    """
    Apply pose variations to pet art while preserving core art style.
    
    Changes arm positions, body lean, stance, etc. to make pet appear in different poses.
    Preserves the pet type's character and overall shape.
    
    Args:
        lines: List of art lines
        pose_type: Type of pose to apply
        pet_type: Pet type for style matching
        rng: Random number generator
    
    Returns:
        Modified lines with pose applied
    """
    if len(lines) < 8:  # Need enough lines for pose variations
        return lines
    
    result_lines = [line.replace(' ', '') for line in lines.copy()]  # Remove spaces first
    
    # Find body section (middle lines, usually lines 3-8 in 12-line grid)
    body_start = max(2, len(result_lines) // 4)
    body_end = min(len(result_lines) - 3, len(result_lines) * 3 // 4)
    
    # Find arm/limb lines - look for vertical bars, brackets, etc.
    arm_line_indices = []
    for i in range(body_start, body_end):
        line = result_lines[i]
        # Look for arm indicators
        if any(char in line for char in ['|', '/', '\\']) and any(char in line for char in ['(', ')', '[', ']', '{', '}', '=', '-']):
            arm_line_indices.append(i)
    
    # Find leg lines (bottom section)
    leg_start = max(0, len(result_lines) - 4)
    leg_line_indices = []
    for i in range(leg_start, len(result_lines)):
        if '||' in result_lines[i] or (result_lines[i].count('|') >= 2):
            leg_line_indices.append(i)
    
    # Apply pose based on type - make changes that are visible but preserve style
    if pose_type == 'arms_up':
        # Arms raised - modify arm lines to point upward
        for idx in arm_line_indices[:3] if arm_line_indices else range(body_start, min(body_start + 2, body_end)):
            if idx < len(result_lines):
                line = result_lines[idx]
                chars = list(line)
                # Convert horizontal arms to upward pointing
                for i in range(len(chars)):
                    if chars[i] == '|' and (i < len(chars) // 3 or i > len(chars) * 2 // 3):
                        chars[i] = '/' if i < len(chars) // 2 else '\\'
                    elif chars[i] == '=' and (i < 2 or i > len(chars) - 3):
                        chars[i] = '/'
                result_lines[idx] = ''.join(chars)
    
    elif pose_type == 'arms_out':
        # Arms spread horizontally
        for idx in arm_line_indices[:2] if arm_line_indices else range(body_start, min(body_start + 2, body_end)):
            if idx < len(result_lines):
                line = result_lines[idx]
                chars = list(line)
                # Make arms extend outward
                for i in range(len(chars)):
                    if chars[i] == '|' and (i < 3 or i > len(chars) - 4):
                        chars[i] = '\\' if i < len(chars) // 2 else '/'
                result_lines[idx] = ''.join(chars)
    
    elif pose_type == 'lean_left':
        # Body leans left - shift characters
        for idx in range(body_start, body_end):
            if idx < len(result_lines):
                line = result_lines[idx]
                if len(line) >= 12:
                    # Shift left: move first char to end (creates visual lean)
                    if line[0] in ['=', '-', '|', '~', '#', '@']:
                        result_lines[idx] = line[1:6] + line[0] + line[6:]
    
    elif pose_type == 'lean_right':
        # Body leans right - shift characters
        for idx in range(body_start, body_end):
            if idx < len(result_lines):
                line = result_lines[idx]
                if len(line) >= 12:
                    # Shift right: move last char to beginning
                    if line[-1] in ['=', '-', '|', '~', '#', '@']:
                        result_lines[idx] = line[:6] + line[-1] + line[6:-1]
    
    elif pose_type == 'crouch':
        # Crouching - make body more compact, legs wider
        for idx in range(body_start + 1, body_end - 1):
            if idx < len(result_lines):
                line = result_lines[idx]
                # Compress body slightly
                result_lines[idx] = line.replace('==', '=').replace('--', '-')
        # Widen legs
        for idx in leg_line_indices:
            if idx < len(result_lines):
                line = result_lines[idx]
                result_lines[idx] = line.replace('||', '| |').replace('||', '| |')
    
    elif pose_type == 'stretch':
        # Stretching - extend body vertically
        for idx in range(body_start, min(body_start + 4, body_end)):
            if idx < len(result_lines):
                line = result_lines[idx]
                # Make body appear taller
                result_lines[idx] = line.replace('=', '|').replace('-', '|')
    
    elif pose_type == 'wave':
        # Waving - one arm up
        if arm_line_indices:
            idx = arm_line_indices[0] if arm_line_indices else body_start
            if idx < len(result_lines):
                line = result_lines[idx]
                chars = list(line)
                # Left side waves (first few chars)
                for i in range(min(4, len(chars))):
                    if chars[i] in ['|', '=']:
                        chars[i] = '/'
                result_lines[idx] = ''.join(chars)
    
    elif pose_type == 'neutral':
        # Neutral pose - minimal changes, just ensure no spaces
        pass
    
    # Final cleanup: ensure no spaces and proper length
    for i, line in enumerate(result_lines):
        result_lines[i] = line.replace(' ', '')
        # Ensure line doesn't exceed 12 chars (will be handled by create_12x12_grid)
        if len(result_lines[i]) > 12:
            result_lines[i] = result_lines[i][:12]
    
    return result_lines


def _apply_robot_expression(eye_line: str, expr: str, rng: random.Random) -> str:
    """Apply expression to robot eyes - NO SPACES."""
    result = eye_line
    if expr == 'wink':
        # Wink: one eye closed (randomly left or right)
        if rng.random() > 0.5:
            result = result.replace('[oo]', '[o-]').replace('[++]', '[+-]').replace('[==]', '[=-]').replace('[..]', '[.-]').replace('[XX]', '[X-]').replace('[OO]', '[O-]')
            result = result.replace('[o+', '[o-').replace('[+o', '[+-').replace('[=o', '[=-').replace('[o=', '[o-')
        else:
            result = result.replace('[oo]', '[-o]').replace('[++]', '[-+]').replace('[==]', '[-=]').replace('[..]', '[-.]').replace('[XX]', '[-X]').replace('[OO]', '[-O]')
            result = result.replace('o]', '-]').replace('+]', '-]').replace('=]', '-]')
    elif expr == 'smile' or expr == 'happy':
        # Brighter eyes
        result = result.replace('[oo]', '[OO]').replace('[..]', '[oo]').replace('[==]', '[OO]')
        result = result.replace('[o+', '[OO').replace('[+o', '[OO')
    elif expr == 'surprised':
        # Wider eyes
        result = result.replace('[oo]', '[OO]').replace('[==]', '[OO]').replace('[..]', '[OO]')
    elif expr == 'sleepy':
        # Half-closed
        result = result.replace('[oo]', '[--]').replace('[OO]', '[--]').replace('[==]', '[--]')
    elif expr == 'excited':
        # Sparkly
        result = result.replace('[oo]', '[++]').replace('[..]', '[++]').replace('[==]', '[++]')
    return result if result != eye_line else eye_line


def _apply_alien_expression(eye_line: str, expr: str, rng: random.Random) -> str:
    """Apply expression to alien eyes."""
    result = eye_line
    if expr == 'wink':
        if rng.random() > 0.5:
            result = result.replace('(o o)', '(o -)').replace('(* *)', '(* -)').replace('(O O)', '(O -)').replace('(0 0)', '(0 -)').replace('(^ ^)', '(^ -)').replace('(~ ~)', '(~ -)')
        else:
            result = result.replace('(o o)', '(- o)').replace('(* *)', '(- *)').replace('(O O)', '(- O)').replace('(0 0)', '(- 0)').replace('(^ ^)', '(- ^)').replace('(~ ~)', '(- ~)')
    elif expr == 'smile' or expr == 'happy':
        result = result.replace('(o o)', '(^ ^)').replace('(* *)', '(^ ^)').replace('(0 0)', '(^ ^)')
    elif expr == 'surprised':
        result = result.replace('(o o)', '(O O)').replace('(* *)', '(O O)').replace('(^ ^)', '(O O)')
    elif expr == 'sleepy':
        result = result.replace('(o o)', '(~ ~)').replace('(O O)', '(~ ~)').replace('(* *)', '(~ ~)')
    elif expr == 'excited':
        result = result.replace('(o o)', '(* *)').replace('(^ ^)', '(* *)').replace('(0 0)', '(* *)')
    return result if result != eye_line else eye_line


def _apply_monster_expression(eye_line: str, expr: str, rng: random.Random) -> str:
    """Apply expression to monster eyes."""
    result = eye_line
    if expr == 'wink':
        if rng.random() > 0.5:
            result = result.replace('> <', '> -').replace('V V', 'V -').replace('^ ^', '^ -').replace('X X', 'X -')
        else:
            result = result.replace('> <', '- <').replace('V V', '- V').replace('^ ^', '- ^').replace('X X', '- X')
    elif expr == 'smile' or expr == 'happy':
        result = result.replace('> <', '^ ^').replace('V V', '^ ^').replace('X X', '^ ^')
    elif expr == 'surprised':
        result = result.replace('> <', 'O O').replace('V V', 'O O').replace('^ ^', 'O O')
    elif expr == 'sleepy':
        result = result.replace('> <', '- -').replace('V V', '- -').replace('^ ^', '- -')
    elif expr == 'excited':
        result = result.replace('> <', '* *').replace('V V', '* *').replace('^ ^', '* *')
    return result if result != eye_line else eye_line


def _apply_creature_expression(eye_line: str, expr: str, rng: random.Random) -> str:
    """Apply expression to creature eyes."""
    result = eye_line
    if expr == 'wink':
        if rng.random() > 0.5:
            result = result.replace('(o o)', '(o -)').replace('(^ ^)', '(^ -)').replace('(~ ~)', '(~ -)').replace('(u u)', '(u -)')
        else:
            result = result.replace('(o o)', '(- o)').replace('(^ ^)', '(- ^)').replace('(~ ~)', '(- ~)').replace('(u u)', '(- u)')
    elif expr == 'smile' or expr == 'happy':
        result = result.replace('(o o)', '(^ ^)').replace('(u u)', '(^ ^)').replace('(~ ~)', '(^ ^)')
    elif expr == 'surprised':
        result = result.replace('(o o)', '(O O)').replace('(^ ^)', '(O O)').replace('(u u)', '(O O)')
    elif expr == 'sleepy':
        result = result.replace('(o o)', '(~ ~)').replace('(^ ^)', '(~ ~)').replace('(u u)', '(~ ~)')
    elif expr == 'excited':
        result = result.replace('(o o)', '(* *)').replace('(^ ^)', '(* *)').replace('(u u)', '(* *)')
    return result if result != eye_line else eye_line


def _apply_spirit_expression(eye_line: str, expr: str, rng: random.Random) -> str:
    """Apply expression to spirit eyes."""
    result = eye_line
    if expr == 'wink':
        if rng.random() > 0.5:
            result = result.replace('* *', '* -').replace('o o', 'o -').replace('~ ~', '~ -')
        else:
            result = result.replace('* *', '- *').replace('o o', '- o').replace('~ ~', '- ~')
    elif expr == 'smile' or expr == 'happy':
        result = result.replace('* *', '^ ^').replace('o o', '^ ^').replace('~ ~', '^ ^')
    elif expr == 'surprised':
        result = result.replace('* *', 'O O').replace('o o', 'O O').replace('~ ~', 'O O')
    elif expr == 'sleepy':
        result = result.replace('* *', '~ ~').replace('o o', '~ ~')
    elif expr == 'excited':
        result = result.replace('* *', '** **').replace('o o', '** **').replace('~ ~', '** **')
    return result if result != eye_line else eye_line


def _apply_machine_expression(eye_line: str, expr: str, rng: random.Random) -> str:
    """Apply expression to machine eyes."""
    result = eye_line
    if expr == 'wink':
        if rng.random() > 0.5:
            result = result.replace('@ @', '@ -').replace('# #', '# -').replace('= =', '= -')
        else:
            result = result.replace('@ @', '- @').replace('# #', '- #').replace('= =', '- =')
    elif expr == 'smile' or expr == 'happy':
        result = result.replace('@ @', 'O O').replace('# #', 'O O').replace('= =', 'O O')
    elif expr == 'surprised':
        result = result.replace('@ @', 'O O').replace('# #', 'O O').replace('= =', 'O O')
    elif expr == 'sleepy':
        result = result.replace('@ @', '- -').replace('# #', '- -').replace('= =', '- -')
    elif expr == 'excited':
        result = result.replace('@ @', '* *').replace('# #', '* *').replace('= =', '* *')
    return result if result != eye_line else eye_line


def _apply_beast_expression(eye_line: str, expr: str, rng: random.Random) -> str:
    """Apply expression to beast eyes."""
    result = eye_line
    if expr == 'wink':
        if rng.random() > 0.5:
            result = result.replace('o o', 'o -').replace('O O', 'O -').replace('* *', '* -')
        else:
            result = result.replace('o o', '- o').replace('O O', '- O').replace('* *', '- *')
    elif expr == 'smile' or expr == 'happy':
        result = result.replace('o o', '^ ^').replace('O O', '^ ^').replace('* *', '^ ^')
    elif expr == 'surprised':
        result = result.replace('o o', 'O O').replace('* *', 'O O')
    elif expr == 'sleepy':
        result = result.replace('o o', '~ ~').replace('O O', '~ ~').replace('* *', '~ ~')
    elif expr == 'excited':
        result = result.replace('o o', '* *').replace('O O', '* *')
    return result if result != eye_line else eye_line


def _apply_entity_expression(eye_line: str, expr: str, rng: random.Random) -> str:
    """Apply expression to entity eyes."""
    result = eye_line
    if expr == 'wink':
        if rng.random() > 0.5:
            result = result.replace('o o', 'o -').replace('* *', '* -').replace('+ +', '+ -')
        else:
            result = result.replace('o o', '- o').replace('* *', '- *').replace('+ +', '- +')
    elif expr == 'smile' or expr == 'happy':
        result = result.replace('o o', '^ ^').replace('* *', '^ ^').replace('+ +', '^ ^')
    elif expr == 'surprised':
        result = result.replace('o o', 'O O').replace('* *', 'O O').replace('+ +', 'O O')
    elif expr == 'sleepy':
        result = result.replace('o o', '~ ~').replace('* *', '~ ~').replace('+ +', '~ ~')
    elif expr == 'excited':
        result = result.replace('o o', '* *').replace('+ +', '* *')
    return result if result != eye_line else eye_line


def _apply_cyborg_expression(eye_line: str, expr: str, rng: random.Random) -> str:
    """Apply expression to cyborg eyes."""
    result = eye_line
    if expr == 'wink':
        if rng.random() > 0.5:
            result = result.replace('[o o]', '[o -]').replace('(o o)', '(o -)').replace('[+ +]', '[+ -]')
        else:
            result = result.replace('[o o]', '[- o]').replace('(o o)', '(- o)').replace('[+ +]', '[- +]')
    elif expr == 'smile' or expr == 'happy':
        result = result.replace('[o o]', '[^ ^]').replace('(o o)', '(^ ^)').replace('[+ +]', '[^ ^]')
    elif expr == 'surprised':
        result = result.replace('[o o]', '[O O]').replace('(o o)', '(O O)').replace('[+ +]', '[O O]')
    elif expr == 'sleepy':
        result = result.replace('[o o]', '[- -]').replace('(o o)', '(~ ~)').replace('[+ +]', '[- -]')
    elif expr == 'excited':
        result = result.replace('[o o]', '[+ +]').replace('(o o)', '(* *)').replace('[- -]', '[+ +]')
    return result if result != eye_line else eye_line


def _apply_phantom_expression(eye_line: str, expr: str, rng: random.Random) -> str:
    """Apply expression to phantom eyes."""
    result = eye_line
    if expr == 'wink':
        if rng.random() > 0.5:
            result = result.replace('o o', 'o -').replace('~ ~', '~ -').replace('. .', '. -')
        else:
            result = result.replace('o o', '- o').replace('~ ~', '- ~').replace('. .', '- .')
    elif expr == 'smile' or expr == 'happy':
        result = result.replace('o o', '^ ^').replace('. .', '^ ^').replace('~ ~', '^ ^')
    elif expr == 'surprised':
        result = result.replace('o o', 'O O').replace('. .', 'O O').replace('~ ~', 'O O')
    elif expr == 'sleepy':
        result = result.replace('o o', '~ ~').replace('. .', '~ ~')
    elif expr == 'excited':
        result = result.replace('o o', '* *').replace('. .', '* *').replace('~ ~', '* *')
    return result if result != eye_line else eye_line


# ============================================================================
# MAIN RENDER FUNCTION
# ============================================================================

def render_pet(node_id: str, generation_seed: str, age_stage: str, name: Optional[str] = None, expression_seed: Optional[str] = None) -> str:
    """
    Main render function. Generates ASCII art for pet - 12x12 grid, NO SPACES.
    
    Args:
        node_id: Owner's Node ID (kept for compatibility, not used for type)
        generation_seed: Unique seed for this generation (determines type and variations)
        age_stage: One of 'egg', 'child', 'teen', 'adult', 'elder'
        name: NOT USED - name is sent separately in first message
        expression_seed: Optional seed for expression variation (defaults to time-based)
    
    Returns:
        Multi-line ASCII art string (12x12 grid = 144 chars + 11 newlines = 155 chars total)
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
    
    # Apply animated expression and pose variations (changes each time, but keeps core shape)
    # Use time-based seed if not provided to ensure variety each call
    # Each time /pet is called, the pet appears in a different pose/expression
    # while preserving the pet's art style and recognizable shape
    if expression_seed is None:
        # Use current time (seconds since epoch) for variety
        # Combine with generation_seed to ensure same pet gets different expressions/poses each time
        time_seed = f"{generation_seed}:{int(time.time())}"
        expression_seed = hashlib.md5(time_seed.encode()).hexdigest()
    
    # Apply expression and pose variations to make pet appear animated/varied
    # This includes: facial expressions (wink, smile, etc.) and body poses (arms up, lean, etc.)
    art = apply_expression(art, expression_seed, pet_type)
    
    # Ensure no spaces in final art
    art = art.replace(' ', '')
    
    # Ensure exactly 12x12 grid
    lines = art.split('\n')
    art = create_12x12_grid(lines)
    
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
