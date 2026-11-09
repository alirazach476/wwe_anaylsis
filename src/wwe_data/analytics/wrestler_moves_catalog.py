"""Curated finishers, signature moves, and notable managers keyed by normalized ring name."""

from __future__ import annotations

import re


def normalize_ring_name(name: str) -> str:
    s = str(name or "").lower()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = s.replace("'", "").replace("'", "").replace('"', "")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# finishers / signatures / managers — curated for PLE-era stars
WRESTLER_MOVES: dict[str, dict[str, list[str]]] = {
    "john cena": {
        "finishers": ["Attitude Adjustment", "STF / STFU"],
        "signatures": ["Five Knuckle Shuffle", "Protobomb", "Shoulder block", "Diving leg drop"],
        "managers": [],
    },
    "randy orton": {
        "finishers": ["RKO", "Punt Kick"],
        "signatures": ["Garvin Stomp", "Elevated DDT", "Snap powerslam"],
        "managers": ["Ric Flair (Legacy era)"],
    },
    "the rock": {
        "finishers": ["Rock Bottom", "People's Elbow"],
        "signatures": ["Spinebuster", "Samoan Drop", "Sharpshooter"],
        "managers": [],
    },
    "the undertaker": {
        "finishers": ["Tombstone Piledriver", "Last Ride", "Hell's Gate"],
        "signatures": ["Chokeslam", "Old School", "Snake Eyes", "Big Boot"],
        "managers": ["Paul Bearer"],
    },
    "kane": {
        "finishers": ["Chokeslam", "Tombstone Piledriver"],
        "signatures": ["Flying clothesline", "Sidewalk slam", "Uppercut"],
        "managers": ["Paul Bearer", "Tori"],
    },
    "triple h": {
        "finishers": ["Pedigree"],
        "signatures": ["Spinebuster", "Facebuster", "Sledgehammer shot"],
        "managers": ["Chyna", "Ric Flair", "Shawn Michaels (DX)"],
    },
    "brock lesnar": {
        "finishers": ["F-5", "Kimura Lock"],
        "signatures": ["German suplexes", "Fireman's carry takeover", "Knee strikes"],
        "managers": ["Paul Heyman"],
    },
    "paul heyman": {
        "finishers": [],
        "signatures": [],
        "managers": [],
        "role": "manager",
        "clients": ["Brock Lesnar", "Big Show", "CM Punk", "Curtis Axel", "Roman Reigns", "The Bloodline"],
    },
    "cm punk": {
        "finishers": ["GTS (Go To Sleep)", "Anaconda Vise"],
        "signatures": ["Pepsi Plunge", "Arm stretch", "Springboard clothesline"],
        "managers": ["Paul Heyman", "Serena", "Luke Gallows"],
    },
    "roman reigns": {
        "finishers": ["Spear", "Guillotine Choke"],
        "signatures": ["Superman Punch", "Drive-By", "Samuran Drop"],
        "managers": ["Paul Heyman"],
    },
    "seth rollins": {
        "finishers": ["Curb Stomp", "Pedigree", "Blackout / Falcon Arrow"],
        "signatures": ["Buckle bomb", "Suicide dive", "Frog splash"],
        "managers": ["Jamie Noble", "Joey Mercury", "Paul Heyman"],
    },
    "seth freakin rollins": {
        "finishers": ["Curb Stomp", "Pedigree"],
        "signatures": ["Buckle bomb", "Suicide dive"],
        "managers": ["Jamie Noble", "Joey Mercury"],
    },
    "dean ambrose": {
        "finishers": ["Dirty Deeds"],
        "signatures": ["Suicide dive", "Lunatic Lariat", "Elbow drop"],
        "managers": [],
    },
    "jon moxley": {
        "finishers": ["Death Rider / Paradigm Shift", "Bulldog choke"],
        "signatures": ["Toe kick", "Elbows"],
        "managers": [],
    },
    "edge": {
        "finishers": ["Spear", "Edgecution", "Edgecator"],
        "signatures": ["Electric chair drop", "Flapjack"],
        "managers": ["Lita", "Vickie Guerrero"],
    },
    "christian": {
        "finishers": ["Killswitch", "Unprettier"],
        "signatures": ["Frog splash", "Tornado DDT"],
        "managers": ["Lita", "Captain Charisma era allies"],
    },
    "jeff hardy": {
        "finishers": ["Swanton Bomb", "Twist of Fate"],
        "signatures": ["Whisper in the Wind", "Poetry in Motion"],
        "managers": ["Lita"],
    },
    "matt hardy": {
        "finishers": ["Twist of Fate", "Side Effect"],
        "signatures": ["Moonsault", "Corner clothesline"],
        "managers": [],
    },
    "rey mysterio": {
        "finishers": ["619", "West Coast Pop", "Frog splash"],
        "signatures": ["Hurricanrana", "Droppin' Dimes", "Springboard DDT"],
        "managers": [],
    },
    "eddie guerrero": {
        "finishers": ["Frog Splash", "Lasso from El Paso"],
        "signatures": ["Three amigos", "Tornado DDT"],
        "managers": [],
    },
    "chris jericho": {
        "finishers": ["Walls of Jericho", "Codebreaker", "Lionsault"],
        "signatures": ["Breakdown", "Missile dropkick"],
        "managers": [],
    },
    "chris benoit": {
        "finishers": ["Crippler Crossface", "Diving headbutt"],
        "signatures": ["German suplexes", "Snap suplex"],
        "managers": [],
    },
    "kurt angle": {
        "finishers": ["Angle Slam", "Ankle Lock"],
        "signatures": ["Olympic slam setup", "German suplex"],
        "managers": ["Paul Heyman (Team Angle era)"],
    },
    "big show": {
        "finishers": ["Chokeslam", "KO Punch", "Colossal Clutch"],
        "signatures": ["Overhead belly-to-belly", "Spear"],
        "managers": ["Paul Heyman", "John Laurinaitis"],
    },
    "the miz": {
        "finishers": ["Skull-Crushing Finale", "Figure-four leglock"],
        "signatures": ["Reality Check", "Awesome clothesline"],
        "managers": ["Alex Riley", "Maryse"],
    },
    "sheamus": {
        "finishers": ["Brogue Kick", "Celtic Cross", "White Noise"],
        "signatures": ["Irish Curse backbreaker", "Cloverleaf"],
        "managers": [],
    },
    "cody rhodes": {
        "finishers": ["Cross Rhodes", "Cody Cutter"],
        "signatures": ["Disaster Kick", "Figure-four"],
        "managers": ["Dusty Rhodes (legacy)", "Brandi Rhodes"],
    },
    "dashing cody rhodes": {
        "finishers": ["Cross Rhodes"],
        "signatures": ["Beautiful Disaster"],
        "managers": [],
    },
    "drew mcintyre": {
        "finishers": ["Claymore Kick", "Future Shock DDT"],
        "signatures": ["Glasgow Kiss", "Scottish Embrace"],
        "managers": [],
    },
    "kofi kingston": {
        "finishers": ["Trouble in Paradise", "SOS"],
        "signatures": ["Boom Drop", "Boom of Doom"],
        "managers": [],
    },
    "big e": {
        "finishers": ["Big Ending", "Apollo X"],
        "signatures": ["Spear", "Belly-to-belly"],
        "managers": [],
    },
    "xavier woods": {
        "finishers": ["Lost in the Woods", "Shining Wizard"],
        "signatures": ["Tornado DDT"],
        "managers": [],
    },
    "jey uso": {
        "finishers": ["Uso Splash", "Spear"],
        "signatures": ["Superkick", "Samoan drop"],
        "managers": ["Paul Heyman (Bloodline)"],
    },
    "jimmy uso": {
        "finishers": ["Uso Splash"],
        "signatures": ["Superkick", "Samoan drop"],
        "managers": ["Paul Heyman (Bloodline)"],
    },
    "solo sikoa": {
        "finishers": ["Samoan Spike", "Spinning Solo"],
        "signatures": ["Splash", "Uraken"],
        "managers": ["Paul Heyman", "Tama Tonga"],
    },
    "sami zayn": {
        "finishers": ["Helluva Kick", "Blue Thunder Bomb"],
        "signatures": ["Exploder", "Elbows"],
        "managers": [],
    },
    "kevin owens": {
        "finishers": ["Pop-up Powerbomb", "Stunner", "Package Piledriver"],
        "signatures": ["Swanton", "Cannonball"],
        "managers": [],
    },
    "aj styles": {
        "finishers": ["Styles Clash", "Phenomenal Forearm", "Calf Crusher"],
        "signatures": ["Spiral Tap", "Pele Kick"],
        "managers": [],
    },
    "finn balor": {
        "finishers": ["Coup de Grâce", "1916 / Balor Bomb"],
        "signatures": ["Sling Blade", "Double stomp"],
        "managers": [],
    },
    "shinsuke nakamura": {
        "finishers": ["Kinshasa", "Bomaye"],
        "signatures": ["Knee strikes", "Inverted atomic drop"],
        "managers": [],
    },
    "gunther": {
        "finishers": ["Powerbomb", "Sleeper / sleeper-hold finish"],
        "signatures": ["Chop exchange", "Lariat", "Dropkick"],
        "managers": [],
    },
    "walter": {
        "finishers": ["Powerbomb", "Sleeper"],
        "signatures": ["Chop", "Lariat"],
        "managers": [],
    },
    "becky lynch": {
        "finishers": ["Manhandle Slam", "Dis-arm-her"],
        "signatures": ["Bexploder", "Cannonball"],
        "managers": [],
    },
    "charlotte flair": {
        "finishers": ["Natural Selection", "Figure-eight"],
        "signatures": ["Spear", "Moonsault"],
        "managers": ["Ric Flair"],
    },
    "bayley": {
        "finishers": ["Rose Plant", "Bayley-to-Belly"],
        "signatures": ["Diving elbow", "Armbar"],
        "managers": [],
    },
    "sasha banks": {
        "finishers": ["Bank Statement", "Double knee stomps"],
        "signatures": ["Frog splash", "Suicide dive"],
        "managers": [],
    },
    "mercedes mone": {
        "finishers": ["Bank Statement"],
        "signatures": ["Frog splash"],
        "managers": [],
    },
    "asuka": {
        "finishers": ["Asuka Lock", "Spin kick"],
        "signatures": ["Hip attack", "Knees"],
        "managers": [],
    },
    "rhea ripley": {
        "finishers": ["Riptide", "Prism Trap"],
        "signatures": ["Suplexes", "Big boot"],
        "managers": ["Dominik Mysterio (Judgment Day era)"],
    },
    "bianca belair": {
        "finishers": ["K.O.D. (Kiss of Death)", "450 splash"],
        "signatures": ["Hair whip", "Handspring moonsault"],
        "managers": [],
    },
    "alexa bliss": {
        "finishers": ["Twisted Bliss", "Sister Abigail"],
        "signatures": ["Sparkle Splash", "Snap DDT"],
        "managers": ["Lilly"],
    },
    "liv morgan": {
        "finishers": ["Oblivion", "Jericho-style Codebreaker variant"],
        "signatures": ["Springboard DDT", "Senton"],
        "managers": [],
    },
    "naomi": {
        "finishers": ["Rear View", "Split-legged moonsault"],
        "signatures": ["Springboard"],
        "managers": [],
    },
    "natalya": {
        "finishers": ["Sharpshooter", "Natalya special"],
        "signatures": ["Powerslam", "Disco"],
        "managers": [],
    },
    "trish stratus": {
        "finishers": ["Stratusfaction", "Chick Kick"],
        "signatures": ["Stratus Splash"],
        "managers": [],
    },
    "mickie james": {
        "finishers": ["Mick Kick", "DDT"],
        "signatures": ["Springboard"],
        "managers": [],
    },
    "beth phoenix": {
        "finishers": ["Glam Slam", "Beth Valley Driver"],
        "signatures": ["Spear"],
        "managers": [],
    },
    "nia jax": {
        "finishers": ["Annihilator", "Samuran Drop"],
        "signatures": ["Running hip attack"],
        "managers": [],
    },
    "batista": {
        "finishers": ["Batista Bomb", "Spear"],
        "signatures": ["Powerslam", "Spinebuster"],
        "managers": ["Ric Flair (Evolution)"],
    },
    "shawn michaels": {
        "finishers": ["Sweet Chin Music"],
        "signatures": ["Flying forearm", "Moonsault", "Figure-four"],
        "managers": ["Sensational Sherri", "Diesel (era)"],
    },
    "stone cold steve austin": {
        "finishers": ["Stone Cold Stunner"],
        "signatures": ["Lou Thesz press", "Mudhole stomps"],
        "managers": [],
    },
    "rob van dam": {
        "finishers": ["Five-Star Frog Splash", "Van Daminator"],
        "signatures": ["Rolling Thunder", "Monkey flip"],
        "managers": [],
    },
    "booker t": {
        "finishers": ["Book End", "Scissors Kick"],
        "signatures": ["Houston Hangover", "Spineroonie"],
        "managers": ["Sharmell"],
    },
    "goldust": {
        "finishers": ["Final Cut", "Curtain Call"],
        "signatures": ["Shattered Dreams"],
        "managers": ["Marlena / Terri"],
    },
    "dolph ziggler": {
        "finishers": ["Zig Zag", "Fameasser"],
        "signatures": ["Jumping DDT", "Superkick"],
        "managers": ["Vickie Guerrero", "AJ Lee", "Lana"],
    },
    "daniel bryan": {
        "finishers": ["Yes! Lock / LeBell Lock", "Running knee"],
        "signatures": ["Busaiku Knee", "Suicide dive"],
        "managers": ["Brie Bella"],
    },
    "bryan danielson": {
        "finishers": ["LeBell Lock", "Busaiku Knee"],
        "signatures": ["Cattle Mutilation"],
        "managers": [],
    },
    "bray wyatt": {
        "finishers": ["Sister Abigail", "Mandible Claw"],
        "signatures": ["Running body block", "Uraken"],
        "managers": ["The Wyatt Family"],
    },
    "braun strowman": {
        "finishers": ["Running powerslam", "Chokeslam"],
        "signatures": ["Yokosuka cutter", "Powerslam"],
        "managers": [],
    },
    "bobby lashley": {
        "finishers": ["Hurt Lock", "Spear"],
        "signatures": ["Delayed vertical suplex", "Knee strikes"],
        "managers": ["MVP", "Shelton Benjamin", "Cedric Alexander"],
    },
    "r truth": {
        "finishers": ["Lie Detector", "What's Up?"],
        "signatures": ["Scissors Kick"],
        "managers": ["Little Jimmy"],
    },
    "john morrison": {
        "finishers": ["Starship Pain", "Moonlight Drive"],
        "signatures": ["Springboard kick"],
        "managers": ["Melina"],
    },
    "cesaro": {
        "finishers": ["Neutralizer", "Sharpshooter", "Giant Swing"],
        "signatures": ["Uppercuts", "Pop-up European uppercut"],
        "managers": ["Zeb Colter", "Paul Heyman (brief)"],
    },
    "ludwig kaiser": {
        "finishers": ["Swinging neckbreaker", "Sword"],
        "signatures": ["Chops"],
        "managers": [],
    },
    "shelton benjamin": {
        "finishers": ["Paydirt", "T-Bone Suplex"],
        "signatures": ["Springboard"],
        "managers": ["Momma Benjamin", "MVP"],
    },
    "mark henry": {
        "finishers": ["World's Strongest Slam", "Bearhug"],
        "signatures": ["Powerslam"],
        "managers": ["Theodore Long", "Tony Atlas"],
    },
    "ryback": {
        "finishers": ["Shell Shocked", "Meat Hook Clothesline"],
        "signatures": ["Big boot"],
        "managers": ["Paul Heyman (brief)"],
    },
    "baron corbin": {
        "finishers": ["End of Days", "Deep Six"],
        "signatures": ["Clothesline"],
        "managers": [],
    },
    "jack swagger": {
        "finishers": ["Patriot Lock", "Swagger Bomb"],
        "signatures": ["Gutwrench"],
        "managers": ["Zeb Colter", "Lilian Garcia (brief kayfabe)"],
    },
    "ric flair": {
        "finishers": ["Figure-four leglock"],
        "signatures": ["Chop", "Low blow"],
        "managers": ["Woman", "Arnold Skaaland (legacy)"],
    },
    "william regal": {
        "finishers": ["Knee Trembler", "Regaleplex / Power of the Punch"],
        "signatures": ["European uppercut"],
        "managers": [],
    },
    "damian priest": {
        "finishers": ["South of Heaven", "Reckoning"],
        "signatures": ["Razor's Edge", "Broken arrow"],
        "managers": [],
    },
    "dominik mysterio": {
        "finishers": ["Frogsplash", "Three amigos"],
        "signatures": ["619 setup"],
        "managers": ["Rhea Ripley", "Judgment Day"],
    },
    "dirty dominik mysterio": {
        "finishers": ["Frogsplash"],
        "signatures": ["619"],
        "managers": ["Rhea Ripley"],
    },
    "la knight": {
        "finishers": ["BFT (Blunt Force Trauma)", "Fameasser"],
        "signatures": ["Diving elbow"],
        "managers": [],
    },
    "logan paul": {
        "finishers": ["RKO (borrowed)", "Knockout punch / Sturm und Drang setups"],
        "signatures": ["Springboard"],
        "managers": [],
    },
    "jade cargill": {
        "finishers": ["Jaded"],
        "signatures": ["Powerbomb", "Clothesline"],
        "managers": [],
    },
    "tiffany stratton": {
        "finishers": ["Prettiest Moonsault Ever"],
        "signatures": ["High crossbody"],
        "managers": [],
    },
    "iyo sky": {
        "finishers": ["Over the Moonsault", "Codebreaker"],
        "signatures": ["Meteora"],
        "managers": [],
    },
    "kairi sane": {
        "finishers": ["Insane Elbow"],
        "signatures": ["Sliding D"],
        "managers": [],
    },
    "giulia": {
        "finishers": ["Northern Lights Bomb", "Octopus Hold"],
        "signatures": ["Kick combinations"],
        "managers": [],
    },
    "oba femi": {
        "finishers": ["Pop-up fallaway slam", "Chokeslam"],
        "signatures": ["Uppercuts"],
        "managers": [],
    },
    "sol ruca": {
        "finishers": ["Sol Snatcher"],
        "signatures": ["X-Factor", "Handspring"],
        "managers": ["Zaria"],
    },
    "dragon lee": {
        "finishers": ["Running knee", "Dragon's Wing"],
        "signatures": ["Suicide dive"],
        "managers": [],
    },
    "je von evans": {
        "finishers": ["450 splash", "Springboard cutter"],
        "signatures": ["Tornado DDT"],
        "managers": [],
    },
    "jevon evans": {
        "finishers": ["450 splash", "Springboard cutter"],
        "signatures": ["Tornado DDT"],
        "managers": [],
    },
    "hardcore holly": {
        "finishers": ["Alabama Slam"],
        "signatures": ["DDT"],
        "managers": [],
    },
    "carlito": {
        "finishers": ["Backstabber", "Carlito Code"],
        "signatures": ["Apple spit"],
        "managers": [],
    },
    "chavo guerrero": {
        "finishers": ["Frog splash", "Tornado DDT"],
        "signatures": ["Three amigos"],
        "managers": ["Kerwin White", "Bam Neely"],
    },
    "montel vontavious porter": {
        "finishers": ["Play of the Day", "Drive-By Kick"],
        "signatures": ["Facebuster"],
        "managers": [],
    },
    "mvp": {
        "finishers": ["Play of the Day", "Drive-By Kick"],
        "signatures": ["Facebuster"],
        "managers": [],
    },
    "brie bella": {
        "finishers": ["Bella Buster", "Yes! Lock"],
        "signatures": ["Twin magic"],
        "managers": [],
    },
    "nikki bella": {
        "finishers": ["Rack Attack 2.0"],
        "signatures": ["Atomic drop"],
        "managers": [],
    },
    "shane mcmahon": {
        "finishers": ["Coast to Coast", "Leap of Faith"],
        "signatures": ["Elbow drop from cage"],
        "managers": [],
    },
    "paul bearer": {
        "finishers": [],
        "signatures": [],
        "managers": [],
        "role": "manager",
        "clients": ["The Undertaker", "Kane", "Mankind"],
    },
    "zeb colter": {
        "finishers": [],
        "signatures": [],
        "role": "manager",
        "clients": ["Jack Swagger", "Antonio Cesaro", "Alberto Del Rio"],
    },
    "vickie guerrero": {
        "finishers": [],
        "signatures": [],
        "role": "manager",
        "clients": ["Edge", "Dolph Ziggler", "A.J. Lee"],
    },
    "lita": {
        "finishers": ["Litasault", "Twist of Fate"],
        "signatures": ["Twisted sister"],
        "managers": [],
    },
    "stephanie mcmahon": {
        "finishers": ["Pedigree"],
        "signatures": ["Low blow"],
        "managers": [],
    },
    "bron breakker": {
        "finishers": ["Spear", "Military Press Powerslam"],
        "signatures": ["Clothesline"],
        "managers": ["Paul Heyman (The Vision)"],
    },
    "jacob fatu": {
        "finishers": ["Samoan Spike", "Moonsault"],
        "signatures": ["Chop"],
        "managers": ["Solo Sikoa"],
    },
    "tama tonga": {
        "finishers": ["Gun Stun", "Tornado DDT"],
        "signatures": ["Superkick"],
        "managers": [],
    },
}


# Names we treat as managers/valets when mined from “(with …)” card text
KNOWN_MANAGERS: set[str] = {
    normalize_ring_name(n)
    for n in [
        "Paul Heyman",
        "Paul Bearer",
        "Zeb Colter",
        "Vickie Guerrero",
        "Theodore Long",
        "Jim Cornette",
        "Maryse",
        "Lana",
        "MVP",
        "Armando Estrada",
        "Ric Flair",
        "Sherri Martel",
        "Sensational Sherri",
        "Miss Elizabeth",
        "Sunny",
        "Terri",
        "Marlena",
        "Lita",
        "Stephanie McMahon",
        "Shane McMahon",
        "Vince McMahon",
        "Jamie Noble",
        "Joey Mercury",
        "Luke Gallows",
        "Serena",
        "Alex Riley",
        "Lilian Garcia",
        "Brandi Rhodes",
        "Dusty Rhodes",
        "Rhea Ripley",
        "Judgment Day",
        "The Wyatt Family",
        "Lilly",
        "Zaria",
        "Sharmell",
        "Momma Benjamin",
        "Tony Atlas",
        "John Laurinaitis",
        "Captain Lou Albano",
        "Bobby Heenan",
        "Jimmy Hart",
        "Mr. Fuji",
        "Slick",
        "General Adnan",
        "Harvey Wippleman",
        "Clarence Mason",
        "Jack Tunney",
        "Arnold Skaaland",
        "Woman",
        "Kimberly",
        "Debra",
        "Ivory",
        "Tori",
        "Stacy Keibler",
        "Kerwin White",
        "Bam Neely",
        "Little Jimmy",
        "Melina",
        "AJ Lee",
        "A.J. Lee",
        "Cedric Alexander",
        "Shelton Benjamin",
        "Tama Tonga",
        "Solo Sikoa",
    ]
}


ALIASES: dict[str, str] = {
    "stone cold": "stone cold steve austin",
    "steve austin": "stone cold steve austin",
    "undertaker": "the undertaker",
    "taker": "the undertaker",
    "hhhtools": "triple h",
    "hunter hearst helmsley": "triple h",
    "freakin rollins": "seth rollins",
    "seth freakin rollins": "seth rollins",
    "ambrose": "dean ambrose",
    "the miz": "the miz",
    "michael cole": "michael cole",
    "wwe champion john cena": "john cena",
    "us champion john cena": "john cena",
    "intercontinental champion john cena": "john cena",
}


def lookup_moves(canonical_name: str) -> dict[str, list[str] | str]:
    key = normalize_ring_name(canonical_name)
    key = ALIASES.get(key, key)
    # try dropping leading the
    if key not in WRESTLER_MOVES and key.startswith("the "):
        key = key[4:]
    data = WRESTLER_MOVES.get(key) or WRESTLER_MOVES.get(f"the {key}")
    if not data:
        # Prefer token-boundary / prefix matches on scraped compound names
        tokens = set(key.split())
        best: tuple[int, dict] | None = None
        for k, v in WRESTLER_MOVES.items():
            score = 0
            if key == k:
                score = 100
            elif key.startswith(k + " ") or key.endswith(" " + k):
                score = 80
            elif len(k) >= 8 and k in key:
                score = 60
            elif len(key) >= 8 and key in k:
                score = 50
            elif (
                len(k.split()) >= 2
                and all(len(t) >= 3 for t in k.split())
                and set(k.split()).issubset(tokens)
            ):
                score = 70
            if score and (best is None or score > best[0]):
                best = (score, v)
        data = best[1] if best and best[0] >= 60 else None
    if not data:
        return {"finishers": [], "signatures": [], "managers": [], "role": "wrestler"}
    out = {
        "finishers": list(data.get("finishers") or []),
        "signatures": list(data.get("signatures") or []),
        "managers": list(data.get("managers") or []),
        "role": data.get("role") or "wrestler",
    }
    if data.get("clients"):
        out["clients"] = list(data["clients"])
    return out
