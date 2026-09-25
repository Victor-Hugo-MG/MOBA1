# VFX & Shader Reference

> **Files:** `VFX/MobaVFX.py` · `VFX/MobaShaders.py`  
> **Last Updated:** 2026-04-25

---

## How VFX Works

All visual effects are spawned via `MobaCommon.spawn_vfx()`:

```python
# Spawn a burst at a position, auto-destroy after 2 seconds
MobaCommon.spawn_vfx(scene, "VFX_Fireball_Burst", position, duration=2.0)

# Attach a persistent aura to a hero (follows them)
MobaCommon.spawn_vfx(scene, "VFX_Baron_Aura", pos, duration=180.0, parent=hero_entity)
```

The `template_name` must match a Template configured in the Cave Engine editor. Each template should have the appropriate `MobaVFX` component(s) attached.

---

## VFX Components (attach to Templates)

### Lifecycle

| Component | Purpose | Key Properties |
|---|---|---|
| `VFXLifetime` | Auto-destroy after duration | `duration` (float) |
| `VFXFadeOut` | Alpha fade → 0 over time | `duration`, `fade_start_pct` |
| `VFXScaleFade` | Scale up + fade out (explosions) | `duration`, `start_scale`, `end_scale` |

### Movement

| Component | Purpose | Key Properties |
|---|---|---|
| `VFXRise` | Drift upward (smoke, souls) | `rise_speed`, `duration` |
| `VFXOrbit` | Rotate around parent | `orbit_radius`, `orbit_speed`, `orbit_height` |
| `VFXTrail` | Leave fading dots behind entity | `trail_interval`, `trail_life`, `trail_template` |

### Animation

| Component | Purpose | Key Properties |
|---|---|---|
| `VFXPulse` | Oscillating scale + emissive | `pulse_amount`, `pulse_speed`, `pulse_color` |
| `VFXFlicker` | Rapid alpha on/off | `flicker_rate`, `min_alpha` |
| `VFXImpactBurst` | Fast pop-and-fade hit marker | `burst_duration`, `is_crit` |

### Zones

| Component | Purpose | Key Properties |
|---|---|---|
| `VFXZoneIndicator` | Expand ring → hold → fade | `max_radius`, `expand_time`, `hold_time` |
| `VFXGroundedZone` | Persistent rotating AoE | `zone_radius`, `zone_duration` |

### Advanced

| Component | Purpose | Key Properties |
|---|---|---|
| `VFXBeam` | Connect two entities (tether) | `source_entity`, `target_entity` |
| `VFXStatusAura` | Colored buff/debuff glow | `aura_type` (buff/debuff/baron/dragon/fire/ice/heal/shield) |
| `VFXDamageFlash` | Red flash on hero hit | Call `trigger_flash(color, duration)` |
| `VFXOutline` | Rim-light for targeting | Call `set_outline(enabled, color, width)` |
| `VFXStealth` | Translucent/invisible | Call `set_stealth(active, is_ally)` |
| `VFXDeathDissolve` | Dissolve on death | Call `begin_dissolve()` |
| `VFXRecallCircle` | Spinning recall channel | `channel_duration` |
| `VFXLevelUp` | Golden pillar burst | Auto-plays on spawn |

---

## Shader Controllers (attach to Entities)

| Controller | Target | What It Drives |
|---|---|---|
| `HeroShaderController` | Hero mesh | Team tint, damage flash, Baron/Shield glow |
| `MinionShaderController` | Minion mesh | Team color, Baron empowerment emissive |
| `TurretShaderController` | Turret mesh | Targeting pulse, idle glow |
| `EnvironmentShaderController` | Scene root | Day/night ambient tinting |
| `WaterShaderController` | River mesh | UV scrolling, specular shimmer |

### HeroShaderController API

```python
# Trigger when the hero takes damage
shader = entity.getPy("HeroShaderController")
shader.trigger_hit_flash(dmg_type=MobaCommon.DamageType.PHYSICAL)
```

---

## Uniform Contract

All VFX/Shader materials should expose these uniforms in the Cave Engine editor:

| Uniform | Type | Purpose |
|---|---|---|
| `u_baseColor` | Vector4 | Base tint |
| `u_alpha` | float | Transparency (0-1) |
| `u_emissiveColor` | Vector4 | Glow color |
| `u_emissiveIntensity` | float | Glow strength (0-1) |
| `u_outlineColor` | Vector4 | Rim-light color |
| `u_outlineWidth` | float | Rim-light thickness |
| `u_outlineEnabled` | float | Toggle outline (0/1) |
| `u_dissolveProgress` | float | Death dissolve (0-1) |
| `u_dissolveEdgeGlow` | float | Edge highlight during dissolve |
| `u_edgeGlow` | float | Zone border brightness |
| `u_uvOffset` | Vector2 | Water UV scrolling |
| `u_specularIntensity` | float | Water shimmer |

---

## VFX Color Palette

Use `VFXColor` constants for consistency:

```python
from VFX.MobaVFX import VFXColor

VFXColor.FIRE          # (1.0, 0.4, 0.1, 1.0) — Orange
VFXColor.ICE           # (0.4, 0.7, 1.0, 1.0) — Light Blue
VFXColor.LIGHTNING      # (0.6, 0.3, 1.0, 1.0) — Purple
VFXColor.NATURE         # (0.2, 0.9, 0.3, 1.0) — Green
VFXColor.HEAL           # (0.2, 1.0, 0.4, 1.0) — Bright Green
VFXColor.SHIELD         # (1.0, 0.8, 0.2, 1.0) — Gold
VFXColor.BARON          # (0.6, 0.0, 1.0, 1.0) — Deep Purple
VFXColor.DRAGON         # (1.0, 0.55, 0.0, 1.0) — Orange
```

---

## Template Setup Checklist

When creating a new VFX template in the Cave Editor:

1. Create a new Entity
2. Add a **Mesh** component (plane/sphere/quad)
3. Create a **Material** with the uniforms listed above
4. Add the appropriate **VFX Component(s)** (e.g. `VFXScaleFade` + `VFXLifetime`)
5. Set component properties (duration, scale, etc.)
6. Save as Template with a name matching `Templates.VFX_*` constants
7. Register the template name in `MobaCommon.Templates` class
