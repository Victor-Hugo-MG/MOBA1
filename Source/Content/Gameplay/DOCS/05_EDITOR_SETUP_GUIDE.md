# Cave Engine Editor Setup Guide
> **Engine:** Cave Engine 1.4+ | **Last Updated:** 2026-05-02  
> Follow this guide top-to-bottom before pressing Play. Every section maps to a concrete action inside Cave Engine.

---

## Part 1 — Project Import

1. Open Cave Engine → **File → Open Project** → navigate to `MOBA1/` folder.
2. Confirm the project root loads. You should see the `Source/Content/` tree in the Asset Browser.
3. Open **Help → Python Stubs** and confirm the stubs path points to your Cave Engine install.  
   This enables autocomplete for `cave.*` APIs in any external editor (VS Code, PyCharm).

---

## Part 2 — Required Template Names

Every name below **must exist as a Template** in your project. To create a template: right-click any entity in the scene → **Save as Template** → name it exactly as shown.

> [!IMPORTANT]
> Names are case-sensitive. A typo in a template name means the entity will silently never spawn.

### Hero & Player
| Template Name | What It Is |
|---|---|
| `PlayerTemplate` | Base hero entity (with CharacterComponent, HealthBar child, Mesh child) |

### Projectiles
| Template Name | What It Is |
|---|---|
| `Proj_Basic` | Generic player projectile |
| `Proj_Minion` | Ranged minion projectile |
| `TurretProjectile` | Turret shot (mapped to `MobaCommon.Templates.PROJ_TURRET`) |

### Minions
| Template Name | What It Is |
|---|---|
| `Minion_Melee` | Standard melee minion |
| `Minion_Ranged` | Ranged minion |
| `Minion_Cannon` | Cannon (siege) minion |
| `Minion_Super` | Super minion (spawns after inhibitor dies) |

### UI & HUD
| Template Name | What It Is |
|---|---|
| `UI_KillFeedItem` | Kill feed line entry |
| `UI_HealthBar_Overhead` | Floating HP bar above units |
| `UI_FloatingText` | Floating combat text (damage numbers) |
| `MINIMAP_HERO` | Hero dot on minimap |
| `MINIMAP_BASIC` | Generic dot on minimap |
| `UI_Ping_Indicator` | Ping icon on HUD |

### VFX & Objectives
| Template Name | What It Is |
|---|---|
| `VFX_Ping_Marker` | World ping marker on ground |
| `VFX_Recall_Circle` | Recall channel ring |
| `VFX_LevelUp_Gold` | Level-up burst |
| `VFX_Impact_Standard` | Generic hit impact |
| `VFX_Baron_Aura` | Visual buff for Colossus capture |
| `VFX_Objective_Capture_Global` | Pit burst on boss death |
| `VFX_Turret_Explosion` | Turret/structure destruction |
| `WardTemplate` | Ward entity (carries WardComponent) |

---

## Part 3 — Entity Tags Required

Tags are set in the Cave Engine editor's Entity Properties panel. Every script uses these exact strings.

| Tag | Which Entities Need It |
|---|---|
| `player` | Every hero entity |
| `teamA` | All Blue Team entities (heroes, minions, turrets, structures) |
| `teamB` | All Red Team entities |
| `minion` | All minion entities |
| `turret` | All turret entities |
| `inhibitor` | All inhibitor entities |
| `nexus` | Both nexus entities |
| `ward` | All placed ward entities |
| `monster` | All jungle camp entities |
| `spawner` | MinionSpawner entities |
| `lane_node` | LaneNodeComponent marker entities |
| `JungleManager` | The single JungleManager entity |
| `teamA_fountain` | Blue team fountain/base zone entity |
| `teamB_fountain` | Red team fountain/base zone entity |
| `dragon` | Dragon epic monster |
| `baron` | Crystalline Colossus epic monster |

---

## Part 4 — Scene Properties Required

Select your **Scene** root in the editor → open **Properties**. Add these keys:

| Property Key | Type | Value | Purpose |
|---|---|---|---|
| `base_A_pos` | Vector3 | Your Team A fountain position | Minion pathing fallback |
| `base_B_pos` | Vector3 | Your Team B fountain position | Minion pathing fallback |
| `IsARAM` | Bool | `false` | ARAM mode flag |
| `map_bounds_min` | Vector3 | `(-100, 0, -100)` | Minimap coordinate mapping |
| `map_bounds_max` | Vector3 | `(100, 0, 100)` | Minimap coordinate mapping |

---

## Part 5 — Global Announcement Setup

The `AnnouncementBanner` component requires a specific hierarchy to work with the prioritized queueing system.

1. Create a root UI entity named **`GlobalAnnouncer`**.
2. Add the **`AnnouncementBanner`** component.
3. Add child entities for different backdrops:
   - `Backdrop_Default`
   - `Backdrop_Double`
   - `Backdrop_Triple`
   - `Backdrop_Penta`
   - `Backdrop_STREAK`
   - `Backdrop_SHUTDOWN`
4. Add a child entity named **`Text`** with a `UIElementComponent`.

---

## Part 6 — Hero Entity Setup (Step-by-Step)

### 6a — Entity Hierarchy
```
Hero_TeamA_1  (root entity)
├── Mesh       (child entity with MeshComponent + AnimationComponent)
├── Health Bar (child entity)
│   ├── Bar       (UIElementComponent — the green bar)
│   └── ShadowBar (UIElementComponent — the white delay bar)
```

### 6b — Components on the Root Entity
| Component | Settings |
|---|---|
| `CharacterComponent` | Enable physics; set height/radius to match your mesh |
| `PlayerController` | `heroName = "Ironclad"` (must match HeroRegistry) |
| `EffectComponent` | Standard CC/Buff handler |
| `DeathManager` | Handles gray screen and respawn |

---

## Part 7 — Objective Setup

### Turret Plating
To enable plating, add these properties to your Turret entity:
- `isLaneTurret` = `true`
- `laneID` = `1` (Plating currently active on Mid Lane only)
- `plates` = `5` (Number of plates)
- `plateHP` = `1000` (HP per plate)

### Crystalline Colossus (Boss)
1. Place a monster entity in the top river pit.
2. Add the **`CrystallineColossus`** component (from `AI/MobaObjectives.py`).
3. Add tags: `monster`, `baron`.
4. The system automatically handles "Colossus Gaze" buff distribution on death.

---

## Part 8 — First Play Test Checklist

- [ ] Hero spawns at fountain position.
- [ ] Right-click (MB1) moves the character.
- [ ] Q/W/E/R cast abilities with appropriate range indicators.
- [ ] Killing a hero triggers the "Enemy Slain" announcement banner.
- [ ] Capturing Colossus grants a visual aura and 4s recall time.
- [ ] Minions near a Colossus-buffed hero increase in scale (1.5x).
- [ ] Console shows zero errors.

---

## Common Runtime Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `Entity not found: GlobalAnnouncer` | UI banner named wrong | Name the announcer entity exactly `"GlobalAnnouncer"` |
| `KeyError: 'BARON_BUFF'` | Recalculate stats fail | Ensure `BARON_BUFF` is added to `PlayerController.activeEffects` |
| Hero doesn't move | Physics overlap | Confirm `CharacterComponent` is on root entity, not on Mesh child |
| Plating not breaking | Mid-laner present | Plating only takes damage if the mid-laner has been away for 5+ seconds |
