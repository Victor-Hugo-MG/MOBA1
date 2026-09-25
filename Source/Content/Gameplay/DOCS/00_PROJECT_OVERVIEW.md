# MOBA1 — Project Overview
> **Engine:** Cave Engine 1.4+ (Python Scripting)  
> **Last Audit:** 2026-05-02 — Strategic Objective & Announcer Update ✅  
> **Hero Count:** 28 • **Item Count:** 50+ • **Summoner Spells:** 9

---

## Folder Structure

```
MOBA1/
└── Source/Content/
    ├── Defaults/               Cave Engine system defaults (do not rename)
    └── Gameplay/
        ├── AI/                 NPC logic
        │   ├── MobaHeroAI.py     Bot hero AI (lane, combat, jungle, gank)
        │   ├── MobaJungle.py     Jungle monsters + JungleManager respawn
        │   ├── MobaMinions.py    Minion wave spawning + AI
        │   ├── MobaStructures.py Nexus, Inhibitors, Health Relics
        │   ├── MobaTurret.py     Turret targeting, scaling, plating
        │   └── MobaObjectives.py Objective-specific logic (Colossus, Spire)
        ├── Core/               Shared engine framework
        │   ├── MobaCommon.py       ← CENTRAL LIBRARY (all shared utilities)
        │   ├── MobaItems.py        Item effects, active items, passives
        │   ├── MobaPassives.py     Hero passive system (28 unique passives)
        │   ├── MobaStates.py       Player FSM (Idle/Move/Attack/Ability/Dash/Channel)
        │   ├── MobaEnvironment.py  Environmental hazards
        │   ├── SummonerSpells.py   Summoner spell logic (D/F keys)
        │   ├── DeathSystem.py      Death/respawn handling
        │   ├── EditorAssetCheck.py Asset validation
        │   └── Player Toolkit.py   ← PLAYER CONTROLLER (main hero component)
        ├── Data/               Static registries
        │   ├── AnimationRegistry.py  Animation name mapping
        │   ├── BuildRegistry.py      AI recommended builds
        │   ├── HeroRegistry.py       28 hero definitions
        │   ├── ItemRegistry.py       50+ items with recipes
        │   ├── MonsterRegistry.py    Jungle camp stats
        │   ├── RuneRegistry.py       Rune keystones + minor runes
        │   └── SkinRegistry.py       Hero skin templates
        ├── DOCS/               Developer documentation
        ├── UI/                 HUD, shop, lobby, kill feed
        │   ├── MobaUI.py           Master HUD + Shop + Announcer + FCT
        │   ├── MobaUIFX.py         Low HP vignette, health juice, etc.
        │   ├── MobaLobby.py        Draft lobby + matchmaking
        │   ├── MobaHUDExtensions.py Extended HUD widgets
        │   └── PerformanceHUD.py   Debug performance overlay
        └── VFX/                Visual effects & shader controllers
            ├── MobaVFX.py          20+ VFX behavior components
            └── MobaShaders.py      Hero/Minion/Turret/Environment shaders
```

---

## Strategic Objectives (Phase 132)

### Crystalline Colossus
The "Baron" equivalent of the OMO prototype.
- **Location**: Top-side River Pit.
- **Reward**: "Colossus Gaze" (AD/AP Boost, Minion Empowerment, 4s Recall).
- **Respawn**: 6 Minutes.

### Resonance Spires
Capture-able points that provide stacking team-wide buffs based on type (AD/AP, Resistances, Move Speed, or Haste).

---

## Announcer UI
High-impact global notifications for match milestones:
- **Multi-Kills**: Double, Triple, Quadra, Penta (with prioritized queueing).
- **Streaks**: Killing Spree to Legendary status.
- **Shut Downs**: High-bounty elimination alerts.
- **Objectives**: Global slain alerts for Dragon/Colossus.

---

## Import Convention

```python
# Correct — always import by package:
from Core import MobaCommon
from Core import MobaItems
from Core import MobaPassives
from Core import SummonerSpells
from Data import HeroRegistry
from Data import ItemRegistry
from Data import RuneRegistry
from UI   import MobaUI
from VFX  import MobaVFX

# WRONG — bare imports will fail:
import MobaCommon       # ❌
import MobaItems        # ❌
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  GAME LOOP                           │
│                                                      │
│  MobaLobby ─→ MatchOrchestrator ─→ PlayerController │
│       (Draft)      (Spawn Heroes)      (Per-frame)   │
│                                                      │
│  PlayerController.update()                           │
│    ├── processInput()     (Targeting, Smart Cast)    │
│    ├── FSM.run()          (Idle→Move→Attack→Ability) │
│    ├── summoner_spell_mgr.update(dt)                │
│    ├── inventory_mgr.update_support_quest()          │
│    └── vision_tick()                                 │
│                                                      │
│  MobaCommon (Shared Utilities)                       │
│    ├── apply_damage() → Recursion Guard + FCT + VFX │
│    ├── apply_heal() / apply_dot() / apply_cc()       │
│    ├── spawn_vfx() / play_sfx()                      │
│    ├── EntityRegistry (cached entity lookup)         │
│    ├── GameTick (tick-locked sync, time scaling)     │
│    └── RewardManager (gold/XP distribution)          │
│                                                      │
│  AI Systems                                          │
│    ├── HeroAIComponent   (bot decision-making)       │
│    ├── TurretComponent   (Plating, Priority Target)  │
│    ├── MinionAI          (Lane node following)       │
│    └── ObjectiveBase     (Boss leash & agro logic)   │
└─────────────────────────────────────────────────────┘
```

---

## Quick Reference

| Topic | File |
|---|---|
| Add a new hero | `Data/HeroRegistry.py` + `DOCS/01_HERO_CREATION_GUIDE.md` |
| Add a new item | `Data/ItemRegistry.py` |
| Understand skill effects | `DOCS/02_SKILL_EFFECT_REFERENCE.md` |
| All game systems | `DOCS/03_GAME_MECHANICS_REFERENCE.md` |
| Summoner spells | `Core/SummonerSpells.py` + `DOCS/04_SUMMONER_SPELLS_REFERENCE.md` |
| VFX components | `VFX/MobaVFX.py` + `DOCS/06_VFX_SHADER_REFERENCE.md` |
| Editor setup | `DOCS/05_EDITOR_SETUP_GUIDE.md` |
| Cave Engine API | Help menu inside Cave Engine editor |

---

## Hero Roster (28 Heroes)

| Name | Role | Lane | Archetype |
|---|---|---|---|
| Kael | Warrior | Top | Fighter |
| Cyrus | Techno Knight | Top | Fighter/Tank |
| Borum | Juggernaut | Top | Tank |
| Zora | Assassin | Mid/Jungle | Burst |
| Eira | Ice Mage | Mid | Control Mage |
| Ignis | Fire Mage | Mid | Burst Mage |
| Zarek | Storm Mage | Mid | Artillery |
| Mortis | Necromancer | Mid | Sustain Mage |
| Sora | Wind Walker | Mid | Skirmisher |
| Krix | Berserker | Top/Jungle | Diver |
| Orix | Guardian | Support | Tank |
| Bastian | Knight | Top | Tank |
| Ragnar | Berserker | Top | Diver |
| Umbra | Shadow Stalker | Jungle | Assassin |
| Ezra | Arcane Slinger | ADC | Marksman |
| Kenji | Wind Guardian | Mid | Skirmisher |
| Arath | Darkin Apostle | Top | Drain Tank |
| Thorne | Nature Guardian | Top | Tank |
| Silvan | Forest Spirit | Support | Enchanter |
| Spirit | Spirit Form | Support | Enchanter |
| Fiore | Duelist | Top | Fighter |
| Nyx | Night Hunter | ADC | Marksman |
| Sol | Ember Mage | Mid | Burst Mage |
| Vern | Mystic | Mid | Control Mage |
| Mara | Tidecaller | Support | Enchanter |
| Dredge | Deep Terror | Jungle | Diver |
| Vento | Wind Enchanter | Support | Enchanter |
| Lyra | Star Weaver | Support | Enchanter |
