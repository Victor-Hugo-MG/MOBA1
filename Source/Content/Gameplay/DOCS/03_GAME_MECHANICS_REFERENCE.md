# Game Mechanics Reference
> **Engine:** Cave Engine 1.4 | **Last Updated:** 2026-04-18  
> Full catalogue of every implemented system in MOBA1.

---

## 🗺️ Map & Objectives

### Two-Team Structure
- **Team A** (Blue) spawns bottom-left; **Team B** (Red) spawns top-right.
- Three lanes: Top, Mid, Bot (configured via `LaneNodeComponent` markers in the editor).
- Each team has a **Nexus** (final objective), two **Inhibitors** per lane, and **lane Turrets**.

### Structures
| Structure | HP | Armor/MR | Notes |
|---|---|---|---|
| Lane Turret | 5000 | 100/100 | Heat-escalating damage on heroes; True Sight aura |
| Nexus Turret | 5000 | 100/100 | Protects Nexus |
| Inhibitor | 4000 | 100/100 | Respawns after 5 minutes; enables Super Minions when destroyed |
| Nexus | 5000 | 100/100 | Destroying this wins the game |

**Backdoor Protection:** Structures take only 33% damage if no enemy minions are nearby.  
**Sequential Integrity:** Inhibitors are invulnerable until their lane turret dies. Nexus is invulnerable until at least one inhibitor falls.

### Epic Monsters
| Monster | Reward | Respawn |
|---|---|---|
| Dragon | DRAGON_SLAYER permanent buff to entire team | 120s |
| Baron Nashor | BARON_BUFF (180s) to entire team + empowers nearby minions | 120s |

---

## ⚔️ Combat System

### Damage Types
| Type | Reduced By | Notes |
|---|---|---|
| `PHYSICAL` | Armor | Affected by armor pen / lethality |
| `MAGIC` | Magic Resist | Affected by magic pen |
| `TRUE` | Nothing | Cannot be reduced; ignores shields EXCEPT vs. invulnerability |
| `PURE` | Nothing | Also bypasses shields entirely |
| `HEAL` | Grievous Wounds | Visual only in FCT; green number |
| `GOLD` | — | Visual only; yellow number in FCT |

### Damage Formula (LoL-style)
```
multiplier = 100 / (100 + effective_resist)    # For positive resist
multiplier = 2 - 100 / (100 - effective_resist) # For negative resist (amplification)
final_dmg = raw_dmg × situational_mult × multiplier
```

### Armor / Magic Penetration
1. **% Penetration** applied first: `effective_resist = stat × (1 - pen%)`
2. **Flat Penetration (Lethality)** applied after: `effective_resist -= flat_pen`

### Shields
- `shieldHP` property on entity absorbs damage before HP.
- `DamageType.PURE` bypasses shields.
- Barrier summoner spell and skill shields both write to `shieldHP`.

### Lifesteal
- Applied only on `PHYSICAL` damage by heroes.
- Reads `lifeSteal` from entity properties (set by items via `recalculate_stats()`).

### Critical Hits
- `critChance` is rolled on each auto-attack.
- Default crit multiplier: `1.75x` (175%).
- Infinity Edge adds `+0.35x` to crit multiplier.

### Grievous Wounds (Healing Reduction)
- Applied via `EffectFlags.BLEED` on `EffectComponent`.
- Healing is reduced by **40%** while this flag is active.
- Applied by: Ignite, Thornmail, Executioner's Calling, Morellonomicon, Mortal Reminder.

---

## 🧠 Crowd Control

All CC is tracked through `EffectComponent.combined_flags` (bitmask).

| CC Type | Flag | Effect |
|---|---|---|
| STUN | `EffectFlags.STUN` | Can't move, attack, or cast. Interrupts dashes. |
| ROOT | `EffectFlags.ROOT` | Can't move. Can still attack and cast. |
| SILENCE | `EffectFlags.SILENCE` | Can't cast abilities. Can still move and AA. |
| DISARM | `EffectFlags.DISARM` | Can't auto-attack. Can still move and cast. |
| FEAR | `EffectFlags.FEAR` | Forced movement away from source. |
| CHARM | `EffectFlags.CHARM` | Forced movement toward source. |
| TAUNT | `EffectFlags.TAUNT` | Redirects attacks toward caster. |
| SLOW | `EffectFlags.SLOW` | Movement speed reduced by `magnitude` %. |
| GROUNDED | `EffectFlags.GROUNDED` | Cannot use dashes or blinks. |
| INVULNERABLE | `EffectFlags.INVULNERABLE` | Takes no damage (all types blocked). |
| UNTARGETABLE | `EffectFlags.UNTARGETABLE` | Cannot be targeted except by TRUE damage. |

### Tenacity
- Reduces **duration** of all hard CC (Stun, Fear, Charm, Root).
- Capped at 60% (`tenacity = 0.6`).
- Provided by Mercury's Treads.

### Cleanse (Summoner Spell)
- Removes **all** active CC effects instantly (clears `EffectComponent.active_effects`).

---

## 🏃 Movement System

### Movement Speed
- Stored in MOBA units (e.g. 335).
- Converted to engine world units via `SPEED_RATIO = 1.0 / 56.6`.
- `CharacterComponent.setWalkDirection(0, 0, speed * dt)` moves the entity locally forward.
- Pattern: **Rotate entity toward target → Walk local Z**.

### Dash vs. Blink
- **Dash** (`DashState`): Physics-based, moves through space, can be interrupted by CC (unless `isUnstoppable`).
- **Blink** (`BLINK` effect): Instant teleport, no travel time, blocked by `GROUNDED`.

### Recall
- Channeled ability (4 seconds).
- Interrupted by any damage taken.
- Grants `EffectFlags.RECALLING` during channel.
- On success: teleports to fountain, full HP/mana restored.

---

## ⬆️ Leveling & Experience

### XP System
- Heroes gain XP from killing enemies. XP also distributed to nearby allies.
- Ally XP share: 50% of base XP split among allies within **14 world units**.
- Allies who are dead or invulnerable (fountain) are excluded from XP share.

### Level Caps & XP Scaling
- Max level: **18**.
- XP required per level grows: `expToNext = int(prev × 1.15) + 100`.

### Skill Points
- 1 skill point at level 1.
- 1 skill point per level-up.
- Q/W/E max 5 levels. R max 3 levels (requires lvl 6, 11, 16 to unlock each rank).

### Stat Growth
- Per-level growth defined in `growthStats` in HeroRegistry.
- Applied in `recalculate_stats()` as: `base_stat + (growth × (level - 1))`.

---

## 💰 Economy

### Passive Gold Income
- Starts at **2 minutes** into the match.
- Grants **2.04 gold/second** to all living heroes.

### Kill/Assist Rewards
| Event | Gold | XP |
|---|---|---|
| Kill hero | 300G | 500 XP |
| Kill minion (CS) | 20G | 60 XP |
| Kill jungle monster | `goldValue` property | `xpValue` property |
| Destroy turret | 250G global + killer reward | 150 XP global |

### Assist System
- Assist window: **10 seconds** after dealing damage.
- Assist pool: 50% of kill gold/XP split among contributors.

### Killing Spree / Bounties
- 3+ kills in a spree triggers **Shutdown Bounty**.
- Bounty base: `150G + (50G × kills above 3)`.
- Bounty resets on death.

### Shutdown Announcements
- Spree thresholds: 3 = "Killing Spree", 4 = "Rampage", 5+ = "Unstoppable", etc.
- Multi-kill window: **10 seconds** (Double Kill, Triple Kill, Quadra Kill, PENTAKILL).

---

## 🌿 Vision & Fog of War

### Vision Ranges
- Heroes, minions, wards, and turrets each contribute to their team's vision pool.
- Default hero vision range: **15 world units** (set as `visionRange` in entity properties).

### Brush (Bushes)
- `BrushComponent` applies `EffectFlags.HIDDEN` to entities inside.
- Hidden entities are invisible to enemies **unless** an enemy enters the same brush or has True Sight.
- `BrushComponent.brush_id` is stored on entities inside; vision system checks for matching brush IDs.

### Wards
| Trinket | Stealth | Duration | Notes |
|---|---|---|---|
| Warding Totem (yellow) | Yes | 90s | Only revealed by True Sight / Oracle Lens |
| Oracle Lens (red) | — | 10s sweep | Sweeps 6-unit radius; reveals nearby enemy wards |
| Farsight Alteration (blue) | No | Permanent | Destroyed in 1 hit; requires level 9; range 40 units |

### True Sight
- Turrets always have True Sight.
- Wards marked `"hasTrueSight": True` also reveal Hidden units.
- `reveal_unit(entity, duration)` grants REVEALED flag — bypasses HIDDEN for that duration.
- Combat reveals both attacker and defender for **3.5 seconds**.

### VisionManager
- Cache updated every **4 game ticks** (~7.5 Hz).
- `VisionManager.update(scene)` is called from `is_target_visible()`.

---

## 🌀 Items & Shop

### Shop Access
- Players can shop only while inside the **Fountain** area (`FountainComponent` radius: 12 units).
- `canShop` property enabled when in fountain; disabled on exit.

### Inventory
- 6 item slots + 1 dedicated Trinket slot.
- **One pair of boots** maximum (enforced by type flag `isBoots`).
- Jungle item (`Hunter's Resolve`) is unsellable and evolves at a gold threshold.

### Item Tiers
| Tier | Examples | Price Range |
|---|---|---|
| Tier 1 (Basic) | Long Sword, Ruby Crystal | 250–450G |
| Tier 2 (Advanced) | Chain Vest, Blasting Wand | 700–1100G |
| Tier 3 (Legendary) | Black Cleaver, Kraken Slayer | 2300–3400G |
| Jungle (Starter) | Hunter's Resolve | 450G (one-time) |
| Trinkets | Warding Totem, Oracle Lens | Free |
| Boots | Steelcaps, Treads, Sorcs... | 900–1100G |

### Item Passives in Code
| Effect ID | Trigger | Behavior |
|---|---|---|
| `IMMOLATE` | `onTick` | Sunfire Aegis: burns nearby enemies |
| `LIFELINE_CHECK` | `onTick` | Sterak's/Phantom Dancer: shield at <30% HP |
| `GRIEVOUS_WOUNDS` | `onHit` | 40% healing reduction for 3s on target |
| `CLEAVE_SHRED` | `onHit` | Black Cleaver: stacks 5% armor reduction |
| `BRING_IT_DOWN` | `onHit` | Kraken Slayer: 3-stack true damage proc |
| `THORNS` | `onTakeDamage` | Thornmail: reflect magic dmg back |
| `IGNORE_PAIN` | `onTakeDamage` | Death's Dance: defer 30% phys dmg as DoT |
| `AA_REDUCTION` | `onTakeDamage` | Plated Steelcaps: 12% less AA damage |
| `GIANT_SLAYER` | `situationalDamage` | LDR: up to 15% more dmg vs high HP targets |
| `STASIS` | `active` | Zhonya's: 2.5s invulnerable + stun on self |
| `GHOST_STEP` | `active` | Ghostblade: 20% MS bonus for 6s |

### Jungle Item Evolution
1. **Hunter's Resolve** → farm enough gold → auto-evolves (or AI buys manually).
2. Paths: `AD` → Slayer's Resolve | `AP` → Arcane Resolve | `TANK` → Goliath's Resolve.

---

## 🤖 AI (Bot Heroes)

### States
| State | Behavior |
|---|---|
| `LANE` | Follows minions, attacks nearest turret |
| `COMBAT` | Engages enemy hero in range; uses skill combo |
| `RETREAT` | Runs to fountain; shops if at base |
| `RECALLING` | Stands still during recall channel |
| `JUNGLE` | Moves between and clears jungle camps |
| `GANK` | Moves to overextended/low HP enemy to engage |
| `FOLLOW` | Follows the highest-level allied hero (late game grouping) |

### Strategic Logic (think_strategy, runs every 0.5s)
1. Critical HP (<15%): Force retreat.
2. Economic reset: Base if enough gold + wave pushed, or if HP < 40% + safe.
3. Late game (12+ min or level 11+): Group with strongest ally.
4. Jungle role: Weigh gank value vs farm value; switch accordingly.

### Turret Diving Rules
A bot will only dive under enemy turret if:
- Allied minions are in the lane (wave pushed) — OR — assassin targets <15% HP — OR — late-game tank.
- Below level 4 and before 4 minutes: Hard blocked.
- Took 3+ turret shots: Retreat unless tank + ally also diving.
- Being targeted and squishy: Retreat if target has >2× attacker's AD worth of HP remaining.
- Outnumbered: Retreat.

### Itemization (AI)
- Detects jungle rtem and evolves it based on archetype.

### AI Stuck Detection (Unjam Logic)
Bots are equipped with a logic-based "Stuck Detector" for maps without perfect navigation meshes:
- **Pulse**: Every 0.5s–1.0s, the bot compares its current position to its last saved position.
- **Threshold**: If it has moved less than 0.5 units while the movement state is active, it enters the **Jammed** state.
- **Unjam Jitter**: The bot applies a temporary (0.8s) random horizontal offset to its movement vector, effectively "wiggling" around the physical obstruction (walls, other units).

---

## 💎 Advanced Item Synergies

### Unique Passive Stacking
- **Penetration**: Multiplicative stacking for percentage penetration (LoL formula).
- **Deathcap**: Total AP multiplied by 1.35x globally in `recalculate_stats()`.
- **Infinity Edge**: Crit damage increased to 210% (1.75 + 0.35).

### Active Item Implementation
All active items (Stasis, Ghost Step, etc.) are handled in `MobaItems.ItemEffectManager.process_active`. They use a **Command-Pattern** dispatch:
1. `PlayerController` detects keypress (1-6).
2. Calls `MobaItems.process_active(self, item_id)`.
3. Triggers targeted or self-cast effects via `applyEffect`.


## 🌊 Minion Waves

### Spawn Timing
- Wave interval: **30 seconds**.
- First wave spawns 30s after match start.
- Waves follow `LaneNodeComponent` waypoints placed in the editor.

### Wave Composition
| Wave | Melee | Ranged | Cannon | Super |
|---|---|---|---|---|
| Standard | 3 | 3 | — | — |
| Every 3rd | 3 | 3 | 1 | — |
| Super Wave (inhibitor down) | 3 | 3 | 1 | 1 |

### Minion Temporal Scaling
- HP and damage scale by `1.0 + (minutes × 0.05)` (5% per minute, heroes excluded).

### Baron Buff Empowerment
- Nearby allied minions gain 1.5× scale when a hero with BARON_BUFF is within 15 units.

### Target Priority
Minions attack in this priority: Hero (if they attacked an ally in last 2s) → Melee → Ranged → Turrets → Inhibitor → Nexus.

---

## 💀 Death & Respawn

### Respawn Timer Formula (LoL-style)
```
brw = BASE_TIMER (6) + (level × PER_LEVEL (2))
if match_time > 15 min:
    extra_minutes = (match_time - 900) / 60
    brw *= 1.0 + (extra_minutes × 0.005)
death_timer = min(brw, MAX_TIMER (52.5))
```

### Death State
1. `EffectFlags.UNTARGETABLE | INVULNERABLE` applied for death duration + 1s.
2. Movement stopped. "p-death" animation plays.
3. Death overlay (gray screen) shows with countdown timer.
4. VFX and SFX spawn at death position.

### Respawn
1. Teleport to team fountain position.
2. HP and mana restored to 100%.
3. "dead" effect cleared from EffectComponent.
4. Idle animation plays + respawn VFX.

---

## 🎮 Player Input

### Input Buffering
- Inputs are stored in `inputBuffer` for up to `INPUT_BUFFER_TIME = 0.2s`.
- FSM reads the buffer on each state tick; a later input overrides a pending one.

### Casting Modes
| Mode | Key | Behavior |
|---|---|---|
| `NORMAL` | 0 | Shows indicator, must confirm with click |
| `QUICK` | 1 | Fires immediately at cursor position |
| `QUICK_WITH_INDICATOR` | 2 | Shows indicator but fires on key-up |

### Orbwalking (Animation Cancel)
- During AA recovery phase, any `MOVE`, `ATTACK`, or `CAST` input clips the backswing and transitions immediately.

---

## 🔊 Audio

### `play_sfx(target, path, volume, loop, pitch_var)`
- `target` can be: `cave.Scene` (global), `cave.Entity` (3D positioned), or `cave.Vector3`.
- Returns a handler ID (int) for stopping looped sounds.
- `stop_managed_ambience()` stops the active ambient loop on scene cleanup.

---

## 📊 Match Statistics

Tracked per unique hero name in `MatchStatsManager.stats`:

| Stat | Description |
|---|---|
| kills | How many heroes killed |
| deaths | How many times died |
| assists | Assisted kills (10s window) |
| gold | Total gold earned |
| damage | Total damage dealt this match |
| items | Current inventory list |
| level | Current level |

Match results can be saved to `match_history.json` via `save_match_result()`.

---

## 🕐 Game Systems Timing Reference

| System | Update Rate | Code Location |
|---|---|---|
| GameTick (logic) | 30 Hz | `MobaCommon.GameTick` |
| EntityRegistry rebuild | 30 Hz (once/tick) | `MobaCommon.EntityRegistry.tick()` |
| SpatialGrid rebuild | 30 Hz (once/tick) | `MobaCommon.SpatialGrid.rebuild()` |
| VisionManager cache | ~7.5 Hz (every 4 ticks) | `MobaCommon.VisionManager.update()` |
| AI think loop | 2 Hz (every 0.5s) | `HeroAIComponent.think_strategy()` |
| Turret targeting | 5 Hz (every 0.2s) | `TurretComponent.find_best_target()` |
| Minion target update | 2 Hz (every 0.5s) | `MinionComponent.update()` |
| Bush visibility | 10 Hz (every 0.1s) | `BushComponent.update()` |
| Jungle respawn check | 30 Hz (tick-gated) | `JungleManager.update()` |
