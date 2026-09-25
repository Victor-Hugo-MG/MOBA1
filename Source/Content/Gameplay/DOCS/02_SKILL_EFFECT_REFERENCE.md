# Skill Effect Reference
> **Engine:** Cave Engine 1.4 | **Last Updated:** 2026-04-18  
> All skill effects are handled by `executeAbilityEffect()` in `Player Toolkit (1771475844).py`.

---

## How Skills Execute

When a player presses a skill key, this pipeline runs:
1. `PlayerController` checks mana, cooldown, and CC status.
2. `AbilityState` (in `MobaStates.py`) handles the startup animation and timing.
3. `PlayerController.executeAbilityEffect(key, skill_data)` is called — this is where each `"effect"` string is dispatched.
4. VFX/SFX in the skill dict are spawned automatically after execution.

---

## Complete Effect ID Reference

### 🟠 Projectile Effects

#### `LINEAR_PROJECTILE`
Fires a straight-moving skillshot.

```python
"Q": {
    "effect":   "LINEAR_PROJECTILE",
    "speed":    30.0,          # World units per second
    "range":    12.0,          # Max travel distance before despawning
    "damage":   [80, 120, 160, 200, 240],  # Per skill level; can also be flat int
    "vfx_trail": "VFX_Name",  # Optional: attached trail VFX
    "vfx_hit":  "VFX_Name",   # Optional: impact VFX
}
```

#### `CONE_VOLLEY`
Fires multiple projectiles in a spread pattern.

```python
"Q": {
    "effect":  "CONE_VOLLEY",
    "count":   3,       # Number of projectiles
    "range":   6.0,     # Each projectile's range
    "damage":  [70, 110, 150, 190, 230],
}
```

---

### 🔵 Mobility Effects

#### `DASH`
Moves the hero forward at high speed for a duration. Does not allow repositioning — hero moves in their forward direction.

```python
"E": {
    "effect":   "DASH",
    "speed":    35.0,    # Dash velocity
    "duration": 0.25,    # Seconds of dash
    "isDash":   True,    # Must be True so AbilityState doesn't stop movement
    "damage":   [60, 90, 120, 150, 180],  # Optional: deals damage on impact
    "isUnstoppable": False,  # If True, CC does not cancel dash
}
```

#### `BLINK`
Instant teleport toward the cursor/forward direction (like Flash but cast as a skill).

```python
"W": {
    "effect": "BLINK",
    "range":  6.5,   # Max blink distance in world units
}
```

---

### 🟡 Crowd Control Effects

#### `STUN`
Applies `EffectFlags.STUN` — target cannot move or act.

```python
"E": {
    "effect":   "STUN",
    "duration": 1.25,    # Seconds
    "range":    3.5,     # AoE radius (if omitted, single target nearest)
}
```

#### `ROOT`
Applies `EffectFlags.ROOT` — target cannot move but can still attack/cast.

```python
"E": {"effect": "ROOT", "duration": 1.0, "range": 6.0}
```

#### `FEAR`
Applies `EffectFlags.FEAR` — target runs away from the caster uncontrollably.

```python
"W": {"effect": "FEAR", "duration": 1.5, "range": 5.0}
```

#### `PUSH_STUN`
Knocks the target back and briefly stuns them.

```python
"E": {
    "effect":   "PUSH_STUN",
    "range":    4.0,      # Cast range
    "distance": 6.0,      # Knockback distance
}
```

---

### 🟢 Heal / Shield Effects

#### `HP_SCALED_SHIELD`
Grants a flat shield that scales with the hero's max HP.

```python
"W": {
    "effect":   "HP_SCALED_SHIELD",
    "value":    [60, 90, 120, 150, 180],  # Base shield per level
    "duration": 3.0,
}
```

#### `HP_SHIELD`
Grants a flat shield (for supports giving shields to allies).

```python
"W": {"effect": "HP_SHIELD", "value": [100, 150, 200], "duration": 4.0}
```

#### `HEAL_PERCENT`
Restores a percentage of the target's max HP.

```python
"E": {"effect": "HEAL_PERCENT", "percent": 0.15}
```

---

### 🔴 Damage-over-Time Effects

#### `SUSTAINED_ZONE`
Creates a circular AoE zone that deals DPS while entities are inside it. Can channel (SPIN_DAMAGE) or be persistent.

```python
"R": {
    "effect":     "SUSTAINED_ZONE",
    "radius":     7.0,
    "dps":        [100, 150, 200],   # Damage per second
    "duration":   3.0,               # For non-channel zone; omit for channel
    "isChannel":  True,              # If True, hero must stand still to maintain
    "manaPerSec": 20,                # Mana drained per second while channeling
}
# Note: Uses ChannelState in MobaStates.py when isChannel = True
```

---

### 🟣 Stat Modifier Effects

#### `STAT_MOD`
Temporarily boosts one or more stats.

```python
"R": {
    "effect":    "STAT_MOD",
    "duration":  8.0,
    "modifiers": {
        "ad":    40,     # Flat AD bonus
        "speed": 80,     # Flat movement speed bonus
        "armor": 20,     # Flat armor bonus
        "mr":    20,     # Flat MR bonus
        "as":    0.4,    # Bonus attack speed multiplier
    },
}
```

#### `EMPOWERED_MS_AA`
Grants a movement speed boost and empowers the next auto-attack.

```python
"Q": {
    "effect":   "EMPOWERED_MS_AA",
    "msBoost":  0.35,    # 35% movement speed bonus
    "duration": 4.0,
}
```

#### `HP_SCALED_DAMAGE`
Deals damage that scales with the target's missing or max HP.

```python
"Q": {"effect": "HP_SCALED_DAMAGE", "damage": [60, 90, 120], "range": 3.0}
```

---

### ⚫ Special / Unique Effects

#### `EXECUTE_TRUE`
Deals true damage that scales upward based on the target's missing HP (execute mechanic).

```python
"R": {
    "effect":     "EXECUTE_TRUE",
    "baseDamage": [150, 250, 350],   # Minimum (0% missing HP)
    "range":      3.0,
    "isBlocking": True,  # If True, ability startup is uninterruptible
}
```

#### `ACTIVE_STEALTH`
Grants invisibility for a duration (entering brush or breaking attack cancels).

```python
"E": {"effect": "ACTIVE_STEALTH", "duration": 2.5}
```

#### `APPLY_MARK`
Places a debuff mark on the target, which can be detonated by another skill.

```python
"Q": {"effect": "APPLY_MARK",  "range": 10.0, "duration": 6.0}
"E": {"effect": "DETONATE",    "range": 12.0, "damage": [100, 140, 180, 220, 260]}
```

#### `DEFLECT_PROJECTILE`
Creates a temporary wind wall that destroys/reflects incoming projectiles.

```python
"W": {
    "effect":   "DEFLECT_PROJECTILE",
    "duration": 4.0,
    "projType": 2,   # 0 = physical only, 1 = magical only, 2 = all
}
```

#### `RECT_SWEETSPOT`
A rectangular skillshot with a "sweet spot" at the far end that deals bonus damage.

```python
"Q": {
    "effect":      "RECT_SWEETSPOT",
    "width":       4,          # Rectangle width
    "length":      10,         # Rectangle length
    "sweetLength": 2.5,        # How far out the sweet spot starts
    "damage":      [20, 40, 60, 80, 100],
    "bonusDamage": [40, 80, 120, 160, 200],   # Extra damage in the sweet spot
}
```

#### `SUMMON_ENTITY`
Spawns a creature from a template at or near the hero.

```python
"W": {
    "effect":   "SUMMON_ENTITY",
    "template": "GhoulTemplate",   # Must be a valid Cave Engine template name
    "duration": 20.0,              # How long summon lives (or 0 for permanent)
}
```

#### `SUMMON_SENTRY`
Spawns a stationary sentry that attacks nearby enemies.

```python
"R": {
    "effect":   "SUMMON_SENTRY",
    "duration": 12.0,
    "template": "SentryTemplate",
}
```

#### `CREATE_WALL`
Spawns a physical barrier that blocks movement.

```python
"Q": {"effect": "CREATE_WALL", "duration": 5.0, "template": "WallTemplate"}
```

#### `GROUNDED_ZONE`
Creates a zone that applies the GROUNDED status (prevents jumps/blinks) to enemies inside.

```python
"W": {"effect": "GROUNDED_ZONE", "radius": 6.0, "duration": 4.0}
```

#### `TRANSFORM`
Switches the player to a completely different hero kit (swap all skills/stats).

```python
"R": {
    "effect":     "TRANSFORM",
    "targetHero": "SpiritForm",   # Exact key in HERO_REGISTRY
    "cd":         6.0,
}
```

#### `INVULNERABLE`
Makes the hero untargetable and immune to all damage for a duration.

```python
"R": {"effect": "INVULNERABLE", "duration": 2.5}
```

#### `STAT_STEAL`
Steals move speed or AD from target, adding it to the caster temporarily.

```python
"E": {"effect": "STAT_STEAL", "magnitude": 20, "duration": 4.0, "range": 6.0}
```

#### `BLEED_PULL`
Fires a hook that pulls target toward you and applies a bleed DoT.

```python
"E": {
    "effect":   "BLEED_PULL",
    "range":    8.0,
    "dps":      20,
    "duration": 3.0,
}
```

#### `SUMMON_WARD`
Used exclusively by the TRINKET slot. Places a ward at cursor position.

```python
"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
```

---

## Cooldown Format

Cooldowns can be:
- **List of 5** → `[8, 7, 6, 5, 4]` (one per skill level, Q–E max 5 levels)
- **List of 3** → `[120, 100, 80]` (for Ultimates, max 3 levels)
- **Flat number** → `6.0` (same at every level)

## Damage Format

```python
"damage": [80, 120, 160, 200, 240]   # Per-level scaling list
"damage": 100                         # Flat value (no scaling)
```

## VFX/SFX Keys Summary

| Key | When Triggered |
|---|---|
| `vfx_cast` | On cast at caster position |
| `vfx_trail` | Attached to projectile while in flight |
| `vfx_hit` | At the point of impact / target position |
| `vfx_persistent` | If `True`, `vfx_cast` loops while skill is active |
| `sfx_cast` | Sound at cast |
| `sfx_hit` | Sound at impact |
| `animStartup` | Animation name to play during cast startup |
