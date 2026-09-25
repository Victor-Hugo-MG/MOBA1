# Summoner Spells Reference
> **Engine:** Cave Engine 1.4 | **Last Updated:** 2026-04-18  
> Summoner spells are the D/F slots managed by `SummonerSpellManager` in `Core/SummonerSpells.py`.

---

## Overview

Every hero has two summoner spell slots: **D** and **F**. They are set on the `PlayerController` before the match starts (via lobby or `cave.getGlobalDict()`).

Summoner spells are blocked while **stunned** (except Cleanse), and each has its own independent cooldown tracked in `SummonerSpellManager.spells`.

---

## All 9 Summoner Spells

### Flash
| Stat | Value |
|---|---|
| Cooldown | 300s (5 min) |
| Range | 8 world units |

**Effect:** Instantly teleports the hero a short distance in the direction they are currently facing (forward vector). VFX spawned at both origin and destination.

**Code path:** `_cast_flash()` → `Transform.setPosition()`

---

### Ignite
| Stat | Value |
|---|---|
| Cooldown | 180s (3 min) |
| Range | 6 world units |
| Damage | 70 + (20 × level) true damage over 5s |
| Tick Rate | Every 0.5s |

**Effect:** Applies a true damage DoT to the nearest enemy within range. Also applies **Grievous Wounds** (40% healing reduction via `EffectFlags.BLEED`) for the full 5s duration.

**Code path:** `_cast_ignite()` → `apply_dot()` + `EffectComponent.apply(BLEED)`

---

### Smite
| Stat | Value |
|---|---|
| Cooldown | 90s (1.5 min) |
| Range | 5 world units |
| Damage | 900 true damage |
| Heal | 10% of caster's max HP |

**Effect:** Deals massive true damage to the nearest **monster or minion** in range. Heals the caster for 10% of their max HP regardless of whether the target dies.

**Code path:** `_cast_smite()` → `apply_damage(TRUE)` + `apply_heal()`

**Note:** Non-jungle heroes deal 50% reduced damage to monsters before 10 minutes (jungle gating system).

---

### Teleport
| Stat | Value |
|---|---|
| Cooldown | 360s (6 min) |
| Channel Time | 4 seconds |

**Effect:** Channels for 4 seconds, then teleports to the nearest allied **turret or ward**. The channel is interrupted by taking any damage. On completion, spawns arrive VFX at the destination.

**Code path:** `_cast_teleport()` → `pc.beginChannel("TP", ...)` → `_on_teleport_complete()`

---

### Ghost
| Stat | Value |
|---|---|
| Cooldown | 210s (3.5 min) |
| Duration | 10 seconds |
| Speed Bonus | +28% movement speed |

**Effect:** Grants a 28% movement speed bonus. The bonus is stored in `ghost_bonus_speed` property and added via `EffectComponent`. Also spawns a vfx aura.

**Code path:** `_cast_ghost()` → `EffectComponent.apply("ghost_speed", ...)`

---

### Heal
| Stat | Value |
|---|---|
| Cooldown | 240s (4 min) |
| Heal Amount | 90 + (15 × level) HP |
| Speed Bonus | +30% for 1 second |
| AoE Range | 35 world units for ally |

**Effect:** Immediately heals the caster and the **nearest ally within 35 units** for the same amount. Also grants a brief 30% movement speed bonus to the caster.

**Code path:** `_cast_heal()` → `apply_heal(self)` + `apply_heal(ally)` + `EffectComponent.apply("heal_speed")`

---

### Barrier
| Stat | Value |
|---|---|
| Cooldown | 180s (3 min) |
| Shield Amount | 115 + (10 × level) |
| Duration | 2.5 seconds |

**Effect:** Grants an instant shield to the caster. The shield absorbs damage before HP is reduced. Both `EffectComponent` and `PlayerController.shield` are updated.

**Code path:** `_cast_barrier()` → `EffectComponent.apply(SHIELD)` + `pc.shield += amount`

---

### Exhaust
| Stat | Value |
|---|---|
| Cooldown | 210s (3.5 min) |
| Range | 6.5 world units |
| Duration | 3 seconds |
| Slow | 30% movement speed reduction |
| Damage Reduction | 40% less damage dealt by target |

**Effect:** Applies a **SLOW** CC and a damage reduction debuff (`exhausted` effect with `magnitude = 0.4`) to the nearest enemy within range.

**Code path:** `_cast_exhaust()` → `apply_cc("SLOW", ...)` + `EffectComponent.apply("exhausted")`

---

### Cleanse
| Stat | Value |
|---|---|
| Cooldown | 210s (3.5 min) |

**Effect:** Removes **all** active effects from the caster's `EffectComponent` instantly (clears `active_effects` dict and recalculates flags). This includes all CC (Stun, Root, Slow, Fear, etc.).

**Note:** Cleanse is the only summoner spell that can be cast while stunned.

**Code path:** `_cast_cleanse()` → `ec.active_effects = {}; ec._recalculate_flags()`

---

## Assigning Summoner Spells

In Cave Engine editor or via `cave.getGlobalDict()`:

```python
# Set in lobby before match start:
cave.getGlobalDict()["PlayerSpellD"] = "Flash"
cave.getGlobalDict()["PlayerSpellF"] = "Ignite"
```

In code, `SummonerSpellManager` is initialized inside `PlayerController.start()`:

```python
self.summoner_spells = SummonerSpellManager(self, spell_d_id="Flash", spell_f_id="Ignite")
```

Casting is triggered by input in `PlayerController.update()`:

```python
if input.keyPressed("D"):
    self.summoner_spells.try_cast("D")
if input.keyPressed("F"):
    self.summoner_spells.try_cast("F")
```

---

## Adding a New Summoner Spell

1. Add entry to `SPELL_REGISTRY` in `Core/SummonerSpells.py`:

```python
"Snowball": {
    "cd":     70.0,
    "range":  30.0,
    "damage": 10,
    "description": "Launch a snowball that marks the first enemy hit for 6s.",
    "icon":   "Icon_Spell_Snowball"
},
```

2. Add the cast handler inside `SummonerSpellManager._execute_spell()`:

```python
elif spell_id == "Snowball":
    return self._cast_snowball(scene, data)
```

3. Implement `_cast_snowball(self, scene, data)`:

```python
def _cast_snowball(self, scene, data):
    # Use standard helpers from MobaCommon
    target = MobaCommon.get_closest_target(
        self.entity.getTransform().worldPosition,
        data["range"],
        self.entity
    )
    if not target:
        return False

    MobaCommon.apply_damage(target, data["damage"], MobaCommon.DamageType.PHYSICAL, self.entity)
    MobaCommon.play_sfx(self.entity, MobaCommon.Templates.SFX_SNOWBALL)
    return True
```

4. Add the spell name to the lobby's available spell list (in `UI/MobaLobby.py`).
