# Hero Creation Guide
> **Engine:** Cave Engine 1.4 | **Last Updated:** 2026-04-18

This guide is the single source of truth for adding new heroes to MOBA1. Follow every step in order.

---

## Step 1 — Define the Hero in HeroRegistry.py

Open `Data/HeroRegistry.py` and add your hero to `HERO_REGISTRY`. Use the full template below, then fill in your values.

```python
HERO_REGISTRY = {
    # ... existing heroes ...

    "YourHeroName": {
        # ──────────────────────────────────────────────
        # ROLE: "top" | "mid" | "jungle" | "adc" | "apc" | "support"
        # ──────────────────────────────────────────────
        "role": "top",

        # ──────────────────────────────────────────────
        # BASE STATS (Level 1 values)
        # ──────────────────────────────────────────────
        "stats": {
            "maxHP":    600,     # Base health points
            "recovery": 2.0,     # HP regen per second (out of combat)
            "armor":    30,      # Physical damage reduction
            "mr":       30,      # Magic damage reduction
            "speed":    335,     # Movement speed (MOBA units; engine converts via SPEED_RATIO)
            "range":    2.0,     # Attack range in world units (melee ≈ 2.0, ranged ≈ 8–14)
            "isRanged": False,   # True = spawns projectile on AA. False = instant melee hit
            "maxMana":  400,     # Mana pool (0 if hero uses no resource)
            "manaRegen": 1.5,    # Mana regen per second
            "ad":       52,      # Base attack damage
            "ap":       0,       # Base ability power (usually 0 for non-mages)
            "baseAS":   0.625,   # Base attack speed (standard = 0.625 attacks/sec)
        },

        # ──────────────────────────────────────────────
        # PER-LEVEL GROWTH (added each level-up)
        # ──────────────────────────────────────────────
        "growthStats": {
            "hp":    90,    # HP per level
            "armor": 4.0,   # Armor per level
            "mr":    1.5,   # MR per level
            "ad":    3.5,   # AD per level
            "mana":  40,    # Mana per level (omit if manaless)
            "ap":    0,     # AP per level (for mages)
            "as":    0.02,  # Bonus AS per level (as a multiplier added to baseAS)
        },

        # ──────────────────────────────────────────────
        # RANGED AUTO-ATTACK (only if isRanged = True)
        # ──────────────────────────────────────────────
        "attackProjectile":  "VFX_YourHero_Bolt",  # Template name in editor
        "attackProjSpeed":   35.0,                  # Projectile travel speed
        "vfx_attack_hit":    "VFX_YourHero_Impact", # VFX spawned on hit

        # ──────────────────────────────────────────────
        # PASSIVE (optional)
        # ──────────────────────────────────────────────
        "passive": {
            "id":            "HEMORRHAGE",   # See Passive IDs below
            "maxStacks":     5,
            "bleedDPS":      10,
            "bleedDuration": 5.0,
        },

        # ──────────────────────────────────────────────
        # SPECIAL FLAGS (optional)
        # ──────────────────────────────────────────────
        "startWithR": False,  # Set True for transform heroes (NatureGuardian)

        # ──────────────────────────────────────────────
        # SKILLS
        # See 02_SKILL_EFFECT_REFERENCE.md for all effect IDs
        # ──────────────────────────────────────────────
        "skills": {
            "Q": { ... },
            "W": { ... },
            "E": { ... },
            "R": { ... },
            "TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0},
        }
    },
}
```

### Base Stat Guidelines by Role

| Role | HP | Armor | MR | Speed | AD | Notes |
|---|---|---|---|---|---|---|
| top (tank) | 650–700 | 32–40 | 32–45 | 330–340 | 50–58 | High armor growth |
| top (fighter) | 580–650 | 30–38 | 30–35 | 335–345 | 52–60 | Balanced growth |
| mid (mage) | 500–560 | 20–26 | 30–38 | 325–345 | 48–54 | Add `ap` growth |
| jungle | 560–600 | 28–34 | 30–34 | 340–355 | 52–60 | Starts with Hunter's Resolve |
| adc | 500–540 | 22–26 | 28–32 | 325–335 | 50–58 | Add `as` growth ≈ 0.03 |
| apc | 490–530 | 20–24 | 30–36 | 320–335 | 46–52 | Add `ap` growth ≈ 2–4 |
| support | 540–650 | 30–45 | 35–45 | 330–340 | 46–54 | High HP/armor growth |

---

## Step 2 — Define Each Skill

Every skill is a dict inside `"skills"`. A standard skill looks like:

```python
"Q": {
    "effect":    "LINEAR_PROJECTILE",  # REQUIRED. What this skill does.
    "cd":        [8, 7, 6, 5, 4],     # Cooldown per skill level (list of 5, or flat float)
    "mana":      50,                   # Mana cost (0 for manaless heroes)
    "icon":      "Icon_YourHero_Q",   # Texture asset name in editor

    # Skill-specific parameters (see 02_SKILL_EFFECT_REFERENCE.md):
    "speed":     30.0,   # Projectile speed
    "range":     12.0,   # Max range
    "damage":    [80, 120, 160, 200, 240],  # Damage per level

    # VFX/SFX (all optional but recommended):
    "vfx_cast":      "VFX_Name",   # Spawned at cast position
    "vfx_trail":     "VFX_Name",   # Attached to projectile while flying
    "vfx_hit":       "VFX_Name",   # Spawned at impact point
    "vfx_persistent": True,        # If True, vfx_cast loops until skill ends
    "sfx_cast":      "SFX_Name",   # Sound played at cast
    "sfx_hit":       "SFX_Name",   # Sound played at hit
    "animStartup":   "p-ability",  # Animation to play during startup
}
```

### Multi-Stage Skills (Combo Skills)

For skills that re-cast for a second/third effect (like Darkin Q):

```python
"Q": {
    "cd": [14, 12, 10, 8, 6],
    "mana": 60,
    "stageWindow": 4.0,   # Seconds player has to re-press for next stage
    "stages": [
        {"effect": "DASH", "speed": 35.0, "duration": 0.2},
        {"effect": "STUN", "duration": 1.25, "range": 3.5},
    ],
}
```

### Transform Skills (TRANSFORM effect)

For heroes that switch between two forms (NatureGuardian / SpiritForm):

```python
# In Hero A:
"R": {
    "effect": "TRANSFORM",
    "targetHero": "HeroBName",  # Must match exact key in HERO_REGISTRY
    "cd": 6.0,
    "vfx_cast": "VFX_Transformation",
}
# Hero B must also have an R skill with "TRANSFORM" back to Hero A's name.
```

---

## Step 3 — Add the Hero to Build Registry (for AI bots)

Open `Data/BuildRegistry.py` and add a build order:

```python
BUILD_REGISTRY = {
    "YourHeroName": [
        "Long Sword",           # First thing to buy
        "Trinity Force",        # Core item
        "Sterak's Gage",        # Sustain
        "Black Cleaver",        # Armor shred
        "Death's Dance",        # Defense
        "Boots of Speed",       # Mobility
    ],
}
```

---

## Step 4 — (Optional) Add a Skin

Open `Data/SkinRegistry.py` and add skin variants:

```python
SKIN_REGISTRY = {
    "YourHeroName": {
        "default": {"mesh": "YourHero_Mesh", "material": "YourHero_Mat"},
        "ChromeEdition": {"mesh": "YourHero_Chrome_Mesh", "material": "YourHero_Chrome_Mat"},
    },
}
```

---

## Step 5 — Create the Entity Template in Cave Engine Editor

1. **Duplicate** an existing hero template (e.g., Player Template) in the editor.
2. **Rename** it to `YourHeroName`.
3. **Assign** the `PlayerController` component and set `heroName = "YourHeroName"`.
4. **Set the team tag** (`teamA` or `teamB`) on the entity.
5. **Attach** a `DeathManager` component to the same entity.
6. **Set up** the `Mesh` child entity with your hero's 3D model and `AnimationComponent`.
7. **Confirm** the entity has a `CharacterComponent` (for physics movement).
8. **Run** `EditorAssetCheck` to verify all required template names exist.

---

## Step 6 — Verify

Run the syntax check from the Gameplay folder:

```powershell
py -c "import ast, pathlib; [print(f) for f in pathlib.Path('.').rglob('*.py') if not (lambda s: (ast.parse(s), True)[1])(f.read_text(encoding='utf-8',errors='replace'))]"
```

Zero output = all files valid.

---

## Passive IDs Reference

| ID | Behavior | Required Keys |
|---|---|---|
| `HEMORRHAGE` | Stack-based bleed on AA | `maxStacks`, `bleedDPS`, `bleedDuration` |
| `ARCANE_COMET` | Next AA after ability deals bonus magic dmg | `bonusDamage` |
| (custom) | Implement in Player Toolkit `onAttackHit()` | Any |

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Hero not found at runtime | Verify key in `HERO_REGISTRY` matches `heroName` on entity exactly (case-sensitive) |
| Skills never execute | Ensure `"effect"` key exists; check `executeAbilityEffect()` in Player Toolkit |
| Transform broken | Both form names must exist as keys in `HERO_REGISTRY`; both must have a TRANSFORM R |
| AI bot doesn't buy items | Add the hero to `BuildRegistry.py` |
| Ranged AA not spawning | Set `"isRanged": True` in stats AND set `"attackProjectile"` to a valid template name |
