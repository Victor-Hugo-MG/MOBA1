import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon
import math

# ═══════════════════════════════════════════════════════════════════
# MobaVFX.py — Visual Effects Component Library
# Phase 115: Runtime VFX behaviors for all spawned effects.
# All templates reference these components to drive animations.
# ═══════════════════════════════════════════════════════════════════

# ───── COLOR CONSTANTS ────────────────────────────────────────────
class VFXColor:
	"""Centralized color palette for consistent VFX theming."""
	# Team Colors
	TEAM_A       = cave.Vector4(0.2, 0.5, 1.0, 1.0)   # Blue
	TEAM_B       = cave.Vector4(1.0, 0.2, 0.2, 1.0)   # Red
	NEUTRAL      = cave.Vector4(1.0, 1.0, 1.0, 1.0)   # White

	# Element Colors
	FIRE         = cave.Vector4(1.0, 0.4, 0.1, 1.0)
	ICE          = cave.Vector4(0.4, 0.7, 1.0, 1.0)
	LIGHTNING    = cave.Vector4(0.6, 0.3, 1.0, 1.0)
	NATURE       = cave.Vector4(0.2, 0.9, 0.3, 1.0)
	SHADOW       = cave.Vector4(0.4, 0.1, 0.5, 1.0)
	HOLY         = cave.Vector4(1.0, 0.9, 0.5, 1.0)
	ARCANE       = cave.Vector4(0.5, 0.2, 1.0, 1.0)

	# Status Colors
	HEAL         = cave.Vector4(0.2, 1.0, 0.4, 1.0)
	SHIELD       = cave.Vector4(1.0, 0.8, 0.2, 1.0)
	BUFF         = cave.Vector4(0.3, 0.8, 1.0, 1.0)
	DEBUFF       = cave.Vector4(0.8, 0.2, 0.2, 1.0)
	BARON        = cave.Vector4(0.6, 0.0, 1.0, 1.0)
	DRAGON       = cave.Vector4(1.0, 0.55, 0.0, 1.0)

	# Resonant Flux Colors
	RESONANCE_AMPLIFIED = cave.Vector4(1.0, 0.1, 0.1, 1.0)   # Imperium: Deep Red
	RESONANCE_HARMONIZED = cave.Vector4(0.1, 0.6, 1.0, 1.0)  # Families: Harmonic Blue
	RESONANCE_GLITCH     = cave.Vector4(0.4, 1.0, 0.2, 1.0)  # The Front: Neon Green
	RESONANCE_CHAOTIC    = cave.Vector4(0.6, 0.1, 0.9, 1.0)  # Monsters: Eldritch Purple


# ───── CORE LIFETIME COMPONENT ────────────────────────────────────
class VFXLifetime(cave.Component):
	"""Auto-destroys VFX after a set duration. Attached to all spawned effects."""
	def start(self, scene):
		self.timer = getattr(self, 'duration', 2.0)
		self.transf = self.entity.getTransform()
		self.mesh = self.entity.get("Mesh")
		self.initial_scale = self.transf.getScale().copy() if self.transf else cave.Vector3(1,1,1)

	def update(self):
		dt = cave.getDeltaTime()
		self.timer -= dt
		if self.timer <= 0:
			self.entity.kill()


# ───── FADE & DISSOLVE ────────────────────────────────────────────
class VFXFadeOut(cave.Component):
	"""Smoothly fades a VFX entity's material alpha to 0 over its lifetime."""
	def start(self, scene):
		self.timer = getattr(self, 'duration', 1.5)
		self.max_time = self.timer
		self.fade_start = getattr(self, 'fade_start_pct', 0.4)  # Start fading at 40% remaining
		self.mesh = self.entity.get("Mesh")

	def update(self):
		dt = cave.getDeltaTime()
		self.timer -= dt
		if self.timer <= 0:
			self.entity.kill()
			return

		progress = self.timer / self.max_time  # 1 → 0
		fade_threshold = self.fade_start
		if progress < fade_threshold and self.mesh:
			alpha = progress / fade_threshold  # 1 → 0 within fade range
			mat = self.mesh.getFinalMaterial()
			if mat:
				mat.uniforms.set("u_alpha", alpha)


class VFXScaleFade(cave.Component):
	"""Scales up while fading out — perfect for explosions and bursts."""
	def start(self, scene):
		self.timer = getattr(self, 'duration', 0.6)
		self.max_time = self.timer
		self.transf = self.entity.getTransform()
		self.mesh = self.entity.get("Mesh")
		self.start_scale = getattr(self, 'start_scale', 0.3)
		self.end_scale = getattr(self, 'end_scale', 2.0)

	def update(self):
		dt = cave.getDeltaTime()
		self.timer -= dt
		if self.timer <= 0:
			self.entity.kill()
			return

		t = 1.0 - (self.timer / self.max_time)  # 0 → 1
		# Ease-out quad for snappy pop
		ease_t = 1.0 - (1.0 - t) * (1.0 - t)

		# Scale
		s = self.start_scale + (self.end_scale - self.start_scale) * ease_t
		self.transf.setScale(s, s, s)

		# Fade Alpha (last 50%)
		if t > 0.5 and self.mesh:
			alpha = 1.0 - ((t - 0.5) * 2.0)
			mat = self.mesh.getFinalMaterial()
			if mat:
				mat.uniforms.set("u_alpha", max(0, alpha))


# ───── MOVEMENT PATTERNS ──────────────────────────────────────────
class VFXRise(cave.Component):
	"""Slowly drifts upward — used for smoke, souls, healing particles."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.speed = getattr(self, 'rise_speed', 1.5)
		self.timer = getattr(self, 'duration', 2.0)

	def update(self):
		dt = cave.getDeltaTime()
		self.timer -= dt
		if self.timer <= 0:
			self.entity.kill()
			return
		self.transf.applyMovement(cave.Vector3(0, self.speed * dt, 0))


class VFXOrbit(cave.Component):
	"""Spins around a parent entity — used for aura/buff indicators."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.angle = 0.0
		self.radius = getattr(self, 'orbit_radius', 1.5)
		self.speed = getattr(self, 'orbit_speed', 3.0)  # radians/sec
		self.height = getattr(self, 'orbit_height', 0.5)

	def update(self):
		dt = cave.getDeltaTime()
		self.angle += self.speed * dt
		x = math.cos(self.angle) * self.radius
		z = math.sin(self.angle) * self.radius
		self.transf.setPosition(x, self.height, z)


# ───── PULSING & GLOW ────────────────────────────────────────────
class VFXPulse(cave.Component):
	"""Pulsing scale/glow effect — auras, shields, charged abilities."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.mesh = self.entity.get("Mesh")
		self.base_scale = self.transf.getScale().copy() if self.transf else cave.Vector3(1,1,1)
		self.pulse_amount = getattr(self, 'pulse_amount', 0.15)   # ±15% scale
		self.pulse_speed = getattr(self, 'pulse_speed', 4.0)      # Hz
		self.elapsed = 0.0
		self.color = getattr(self, 'pulse_color', None)

	def update(self):
		dt = cave.getDeltaTime()
		self.elapsed += dt
		wave = math.sin(self.elapsed * self.pulse_speed) * self.pulse_amount
		factor = 1.0 + wave

		# Scale Pulse
		self.transf.setScale(
			self.base_scale.x * factor,
			self.base_scale.y * factor,
			self.base_scale.z * factor
		)

		# Glow intensity on material
		if self.mesh and self.color:
			mat = self.mesh.getFinalMaterial()
			if mat:
				intensity = 0.5 + (wave + self.pulse_amount) / (2.0 * self.pulse_amount) * 0.5
				mat.uniforms.set("u_emissiveIntensity", intensity)


class VFXFlicker(cave.Component):
	"""Rapid on/off flicker — used for lightning, sparks, death warnings."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.flicker_rate = getattr(self, 'flicker_rate', 15.0)  # Hz
		self.elapsed = 0.0
		self.min_alpha = getattr(self, 'min_alpha', 0.2)

	def update(self):
		dt = cave.getDeltaTime()
		self.elapsed += dt
		# Square wave with sin smoothing
		val = (math.sin(self.elapsed * self.flicker_rate * 2 * math.pi) + 1.0) * 0.5
		alpha = self.min_alpha + val * (1.0 - self.min_alpha)
		if self.mesh:
			mat = self.mesh.getFinalMaterial()
			if mat:
				mat.uniforms.set("u_alpha", alpha)


# ───── ZONE EFFECTS ──────────────────────────────────────────────
class VFXZoneIndicator(cave.Component):
	"""Expanding ring for ground-targeted abilities (Frost Ring, Blizzard, etc.)."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.mesh = self.entity.get("Mesh")
		self.max_radius = getattr(self, 'max_radius', 7.0)
		self.expand_time = getattr(self, 'expand_time', 0.3)
		self.hold_time = getattr(self, 'hold_time', 2.0)
		self.timer = 0.0
		self.phase = "expand"  # expand → hold → fade

	def update(self):
		dt = cave.getDeltaTime()
		self.timer += dt

		if self.phase == "expand":
			t = min(self.timer / self.expand_time, 1.0)
			ease_t = t * t  # Ease-in
			radius = self.max_radius * ease_t
			self.transf.setScale(radius, 0.1, radius)
			if t >= 1.0:
				self.phase = "hold"
				self.timer = 0.0

		elif self.phase == "hold":
			if self.timer >= self.hold_time:
				self.phase = "fade"
				self.timer = 0.0

		elif self.phase == "fade":
			fade_dur = 0.5
			t = min(self.timer / fade_dur, 1.0)
			if self.mesh:
				mat = self.mesh.getFinalMaterial()
				if mat:
					mat.uniforms.set("u_alpha", 1.0 - t)
			if t >= 1.0:
				self.entity.kill()


class VFXGroundedZone(cave.Component):
	"""Persistent grounded/no-dash zone with a visible AoE border."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.mesh = self.entity.get("Mesh")
		self.radius = getattr(self, 'zone_radius', 8.0)
		self.duration = getattr(self, 'zone_duration', 5.0)
		self.timer = 0.0
		self.transf.setScale(self.radius, 0.05, self.radius)

	def update(self):
		dt = cave.getDeltaTime()
		self.timer += dt

		# Gentle rotation for visual flair
		self.transf.applyRotation(cave.Vector3(0, 15.0 * dt, 0))

		# Edge pulse
		if self.mesh:
			wave = (math.sin(self.timer * 3.0) + 1.0) * 0.5
			mat = self.mesh.getFinalMaterial()
			if mat:
				mat.uniforms.set("u_edgeGlow", 0.5 + wave * 0.5)

		if self.timer >= self.duration:
			self.entity.kill()


# ───── PROJECTILE TRAIL ──────────────────────────────────────────
class VFXTrail(cave.Component):
	"""Leaves a fading trail behind a moving entity (skill shots, arrows)."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.trail_interval = getattr(self, 'trail_interval', 0.05)
		self.trail_duration = getattr(self, 'trail_life', 0.4)
		self.trail_template = getattr(self, 'trail_template', 'VFX_Trail_Dot')
		self.timer = 0.0

	def update(self):
		dt = cave.getDeltaTime()
		self.timer += dt
		if self.timer >= self.trail_interval:
			self.timer = 0.0
			scene = self.entity.getScene()
			pos = self.transf.worldPosition
			dot = scene.addFromTemplate(self.trail_template, pos)
			if dot:
				# Attach fade-out behavior
				fade = dot.add("VFXFadeOut")
				fade.duration = self.trail_duration


# ───── IMPACT / HIT EFFECTS ──────────────────────────────────────
class VFXImpactBurst(cave.Component):
	"""Single-frame burst that scales up quickly and fades — for hits and crits."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.mesh = self.entity.get("Mesh")
		self.timer = 0.0
		self.burst_duration = getattr(self, 'burst_duration', 0.35)
		self.is_crit = getattr(self, 'is_crit', False)
		self.max_scale = 2.0 if self.is_crit else 1.2

	def update(self):
		dt = cave.getDeltaTime()
		self.timer += dt
		t = min(self.timer / self.burst_duration, 1.0)

		# Fast expand, slow settle
		ease = 1.0 - (1.0 - t) * (1.0 - t) * (1.0 - t)  # Ease-out cubic
		s = self.max_scale * ease
		self.transf.setScale(s, s, s)

		# Fade in second half
		if t > 0.3 and self.mesh:
			alpha = 1.0 - ((t - 0.3) / 0.7)
			mat = self.mesh.getFinalMaterial()
			if mat:
				mat.uniforms.set("u_alpha", max(0, alpha))

		if t >= 1.0:
			self.entity.kill()


# ───── BEAM / TETHER ─────────────────────────────────────────────
class VFXBeam(cave.Component):
	"""Connects two points with a scaled quad — for tethers, drain, etc."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.mesh = self.entity.get("Mesh")
		self.source = getattr(self, 'source_entity', None)
		self.target = getattr(self, 'target_entity', None)
		self.elapsed = 0.0

	def update(self):
		dt = cave.getDeltaTime()
		self.elapsed += dt

		if not self.source or not self.target:
			return
		if not self.source.isActive() or not self.target.isActive():
			self.entity.kill()
			return

		src_pos = self.source.getTransform().worldPosition
		tgt_pos = self.target.getTransform().worldPosition

		# Position at midpoint
		mid = cave.Vector3(
			(src_pos.x + tgt_pos.x) * 0.5,
			(src_pos.y + tgt_pos.y) * 0.5,
			(src_pos.z + tgt_pos.z) * 0.5
		)
		self.transf.setPosition(mid.x, mid.y, mid.z)

		# Scale to match distance
		dx = tgt_pos.x - src_pos.x
		dz = tgt_pos.z - src_pos.z
		dist = math.sqrt(dx * dx + dz * dz)
		self.transf.setScale(0.3, 0.3, dist)

		# Rotate to face target
		angle = math.atan2(dx, dz) * (180.0 / math.pi)
		self.transf.setRotation(0, angle, 0)

		# Pulsing glow
		if self.mesh:
			wave = (math.sin(self.elapsed * 8.0) + 1.0) * 0.5
			mat = self.mesh.getFinalMaterial()
			if mat:
				mat.uniforms.set("u_emissiveIntensity", 0.5 + wave * 0.5)


# ───── STATUS INDICATOR (BUFF/DEBUFF AURA) ───────────────────────
class VFXStatusAura(cave.Component):
	"""Attaches to a hero to show buff/debuff state (Baron glow, Ignite burn, etc.)."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.mesh = self.entity.get("Mesh")
		self.elapsed = 0.0
		self.aura_type = getattr(self, 'aura_type', 'buff')  # buff, debuff, baron, dragon
		self.color = self._get_color()

	def _get_color(self):
		mapping = {
			'buff':   VFXColor.BUFF,
			'debuff': VFXColor.DEBUFF,
			'baron':  VFXColor.BARON,
			'dragon': VFXColor.DRAGON,
			'fire':   VFXColor.FIRE,
			'ice':    VFXColor.ICE,
			'heal':   VFXColor.HEAL,
			'shield': VFXColor.SHIELD,
			'resonance_amplified': VFXColor.RESONANCE_AMPLIFIED,
			'resonance_harmonized': VFXColor.RESONANCE_HARMONIZED,
			'resonance_glitch':     VFXColor.RESONANCE_GLITCH,
			'resonance_chaotic':    VFXColor.RESONANCE_CHAOTIC,
		}
		return mapping.get(self.aura_type, VFXColor.NEUTRAL)

	def update(self):
		dt = cave.getDeltaTime()
		self.elapsed += dt

		if not self.mesh:
			return

		mat = self.mesh.getFinalMaterial()
		if not mat:
			return

		# Pulsing emissive
		wave = (math.sin(self.elapsed * 3.0) + 1.0) * 0.5
		intensity = 0.3 + wave * 0.7
		mat.uniforms.set("u_emissiveColor", self.color)
		mat.uniforms.set("u_emissiveIntensity", intensity)


# ───── SHADER UTILITY: DAMAGE FLASH ──────────────────────────────
class VFXDamageFlash(cave.Component):
	"""Flashes the hero mesh red/white when hit — attached to the hero entity."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.flash_timer = 0.0
		self.flash_duration = 0.12
		self.flash_color = cave.Vector4(1.0, 0.3, 0.3, 1.0)  # Red tint
		self.original_color = cave.Vector4(1.0, 1.0, 1.0, 1.0)
		self.is_flashing = False

	def trigger_flash(self, color=None, duration=0.12):
		"""Called by apply_damage to trigger a visual hit flash."""
		self.flash_timer = duration
		self.flash_duration = duration
		if color:
			self.flash_color = color
		self.is_flashing = True
		self._set_color(self.flash_color)

	def update(self):
		if not self.is_flashing:
			return
		dt = cave.getDeltaTime()
		self.flash_timer -= dt

		if self.flash_timer <= 0:
			self.is_flashing = False
			self._set_color(self.original_color)
		else:
			# Lerp flash back to original
			t = 1.0 - (self.flash_timer / self.flash_duration)
			r = self.flash_color.x + (self.original_color.x - self.flash_color.x) * t
			g = self.flash_color.y + (self.original_color.y - self.flash_color.y) * t
			b = self.flash_color.z + (self.original_color.z - self.flash_color.z) * t
			self._set_color(cave.Vector4(r, g, b, 1.0))

	def _set_color(self, color):
		if self.mesh:
			mat = self.mesh.getFinalMaterial()
			if mat:
				mat.uniforms.set("u_baseColor", color)


# ───── SHADER UTILITY: OUTLINE / RIM LIGHT ───────────────────────
class VFXOutline(cave.Component):
	"""Drives a rim/outline shader uniform for hero selection or targeting."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.outline_color = getattr(self, 'outline_color', cave.Vector4(1.0, 0.8, 0.0, 1.0))
		self.outline_width = getattr(self, 'outline_width', 0.03)
		self.enabled = False

	def set_outline(self, enabled, color=None, width=None):
		self.enabled = enabled
		if color:
			self.outline_color = color
		if width:
			self.outline_width = width
		self._apply()

	def _apply(self):
		if not self.mesh:
			return
		mat = self.mesh.getFinalMaterial()
		if not mat:
			return
		if self.enabled:
			mat.uniforms.set("u_outlineColor", self.outline_color)
			mat.uniforms.set("u_outlineWidth", self.outline_width)
			mat.uniforms.set("u_outlineEnabled", 1.0)
		else:
			mat.uniforms.set("u_outlineEnabled", 0.0)


# ───── STEALTHED / INVISIBLE SHADER ──────────────────────────────
class VFXStealth(cave.Component):
	"""Makes an entity appear translucent/invisible. Used for stealth heroes."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.is_stealthed = False
		self.ally_alpha = 0.4   # Allies see faint silhouette
		self.enemy_alpha = 0.0  # Enemies see nothing

	def set_stealth(self, active, is_ally=True):
		self.is_stealthed = active
		if not self.mesh:
			return
		mat = self.mesh.getFinalMaterial()
		if not mat:
			return

		if active:
			alpha = self.ally_alpha if is_ally else self.enemy_alpha
			mat.uniforms.set("u_alpha", alpha)
			mat.uniforms.set("u_baseColor", cave.Vector4(0.6, 0.8, 1.0, alpha))
		else:
			mat.uniforms.set("u_alpha", 1.0)
			mat.uniforms.set("u_baseColor", cave.Vector4(1.0, 1.0, 1.0, 1.0))


# ───── DEATH DISSOLVE ────────────────────────────────────────────
class VFXDeathDissolve(cave.Component):
	"""Dissolve shader effect on hero death — driven by u_dissolveProgress."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.timer = 0.0
		self.duration = getattr(self, 'dissolve_duration', 1.5)
		self.active = False

	def begin_dissolve(self):
		self.active = True
		self.timer = 0.0

	def update(self):
		if not self.active:
			return
		dt = cave.getDeltaTime()
		self.timer += dt
		progress = min(self.timer / self.duration, 1.0)

		if self.mesh:
			mat = self.mesh.getFinalMaterial()
			if mat:
				mat.uniforms.set("u_dissolveProgress", progress)
				# Edge glow during dissolution
				edge_glow = max(0, 1.0 - abs(progress - 0.5) * 4.0)
				mat.uniforms.set("u_dissolveEdgeGlow", edge_glow)

		if progress >= 1.0:
			self.active = False
			self.entity.deactivate(self.entity.getScene())


# ───── RECALL CIRCLE ─────────────────────────────────────────────
class VFXRecallCircle(cave.Component):
	"""Animated circle beneath hero during recall channel."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.mesh = self.entity.get("Mesh")
		self.elapsed = 0.0
		self.channel_time = getattr(self, 'channel_duration', 8.0)

	def update(self):
		dt = cave.getDeltaTime()
		self.elapsed += dt
		progress = min(self.elapsed / self.channel_time, 1.0)

		# Spinning ring
		self.transf.applyRotation(cave.Vector3(0, 120.0 * dt, 0))

		# Scale tightens as channel completes
		scale = 2.0 - progress * 1.2  # 2.0 → 0.8
		self.transf.setScale(scale, 0.1, scale)

		# Brightness increases
		if self.mesh:
			mat = self.mesh.getFinalMaterial()
			if mat:
				mat.uniforms.set("u_emissiveIntensity", 0.3 + progress * 0.7)

		if progress >= 1.0:
			# Channel complete — handled elsewhere, just clean up VFX
			self.entity.kill()


# ───── LEVEL UP BURST ────────────────────────────────────────────
class VFXLevelUp(cave.Component):
	"""Golden pillar + ring expansion on level up."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.mesh = self.entity.get("Mesh")
		self.timer = 0.0
		self.duration = 1.2

	def update(self):
		dt = cave.getDeltaTime()
		self.timer += dt
		t = min(self.timer / self.duration, 1.0)

		# Pillar shoots up
		height = 5.0 * t
		self.transf.setScale(0.8, height, 0.8)

		# Gold glow
		if self.mesh:
			mat = self.mesh.getFinalMaterial()
			if mat:
				alpha = 1.0 - t * t  # Quadratic fade
				mat.uniforms.set("u_baseColor", cave.Vector4(1.0, 0.85, 0.2, alpha))
				mat.uniforms.set("u_emissiveIntensity", 1.0 - t)

		if self.timer >= self.duration:
			self.entity.kill()


# ───── RESONANCE GLITCH FX ───────────────────────────────────────
class VFXGlitch(cave.Component):
	"""Simulates a digital signal failure for 'The Front' abilities."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.transf = self.entity.getTransform()
		self.elapsed = 0.0
		
		# Properties
		self.glitch_rate = getattr(self, 'glitch_rate', 0.15) # Frequency of snaps
		self.intensity = getattr(self, 'intensity', 1.0)
		self.base_pos = self.transf.getPosition()
		self.base_scale = self.transf.getScale()

	def update(self):
		dt = cave.getDeltaTime()
		self.elapsed += dt
		
		if not self.mesh: return
		mat = self.mesh.getFinalMaterial()
		if not mat: return

		import random
		
		# 1. Chromatic Jitter (Randomly swap between Green and Orange)
		if random.random() < 0.2:
			color = VFXColor.RESONANCE_GLITCH if random.random() > 0.5 else cave.Vector4(1.0, 0.5, 0.0, 1.0)
			mat.uniforms.set("u_emissiveColor", color)
			mat.uniforms.set("u_emissiveIntensity", 1.0 * self.intensity)
		else:
			mat.uniforms.set("u_emissiveIntensity", 0.2 * self.intensity)

		# 2. Positional Snap (Digital jitter)
		if self.elapsed % self.glitch_rate < 0.05:
			offset = cave.Vector3(
				random.uniform(-0.2, 0.2),
				random.uniform(-0.1, 0.1),
				random.uniform(-0.2, 0.2)
			)
			self.transf.setPosition(self.base_pos.x + offset.x, self.base_pos.y + offset.y, self.base_pos.z + offset.z)
			
			# Sudden scale stretch
			self.transf.setScale(self.base_scale.x * 1.5, self.base_scale.y * 0.5, self.base_scale.z)
		else:
			self.transf.setPosition(self.base_pos.x, self.base_pos.y, self.base_pos.z)
			self.transf.setScale(self.base_scale.x, self.base_scale.y, self.base_scale.z)

		# 3. Alpha Flicker
		mat.uniforms.set("u_alpha", 0.3 if random.random() < 0.1 else 1.0)


# ───── RESONANCE HARMONIC FX ─────────────────────────────────────
class VFXHarmonic(cave.Component):
	"""Crystalline, geometric effects for 'Rich Families' abilities."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.transf = self.entity.getTransform()
		self.elapsed = 0.0
		
		# Properties
		self.rotation_speed = getattr(self, 'rotation_speed', 120.0) # Deg/sec
		self.pulse_frequency = getattr(self, 'pulse_frequency', 2.0)
		self.color = VFXColor.RESONANCE_HARMONIZED
		
	def update(self):
		dt = cave.getDeltaTime()
		self.elapsed += dt
		
		if not self.mesh: return
		mat = self.mesh.getFinalMaterial()
		if not mat: return

		# 1. Perfect Rotation (Crystalline spin)
		rot = self.transf.getRotation()
		self.transf.setRotation(rot.x, rot.y + self.rotation_speed * dt, rot.z)

		# 2. Prismatic Pulse (Elegant shimmer)
		wave = (math.sin(self.elapsed * self.pulse_frequency) + 1.0) * 0.5
		# Shift color slightly towards gold for 'Family' feel
		shifted_color = cave.Vector4(
			self.color.x + wave * 0.2,
			self.color.y + wave * 0.1,
			self.color.z,
			1.0
		)
		mat.uniforms.set("u_emissiveColor", shifted_color)
		mat.uniforms.set("u_emissiveIntensity", 0.4 + wave * 0.6)

		# 3. Geometric Scale Breathing
		scale_wave = 1.0 + math.sin(self.elapsed * self.pulse_frequency * 2) * 0.05
		self.transf.setScale(scale_wave, scale_wave, scale_wave)


# ───── RESONANCE AMPLIFIED FX ────────────────────────────────────
class VFXAmplified(cave.Component):
	"""Aggressive, high-frequency energy effects for 'The Imperium' tech."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.transf = self.entity.getTransform()
		self.elapsed = 0.0
		
		# Properties
		self.frequency = getattr(self, 'frequency', 15.0) # Concussive vibration
		self.color = VFXColor.RESONANCE_AMPLIFIED
		
	def update(self):
		dt = cave.getDeltaTime()
		self.elapsed += dt
		
		if not self.mesh: return
		mat = self.mesh.getFinalMaterial()
		if not mat: return

		import random

		# 1. Jagged Vibration (High frequency shake)
		shake = math.sin(self.elapsed * self.frequency) * 0.1
		pos = self.transf.getPosition()
		self.transf.setPosition(pos.x + shake, pos.y, pos.z + shake)

		# 2. Concussive Burst (Sudden emissive jumps)
		if random.random() < 0.3:
			mat.uniforms.set("u_emissiveIntensity", 2.0)
			mat.uniforms.set("u_emissiveColor", cave.Vector4(1.0, 1.0, 1.0, 1.0)) # White flash
		else:
			mat.uniforms.set("u_emissiveIntensity", 0.5)
			mat.uniforms.set("u_emissiveColor", self.color)

		# 3. Erratic Scale (Pulsing like a heartbeat)
		pulse = 1.0 + math.sin(self.elapsed * 8.0) * 0.2
		self.transf.setScale(pulse, pulse, pulse)


# ───── RESONANCE CHAOTIC FX ──────────────────────────────────────
class VFXChaotic(cave.Component):
	"""Oily, warping eldritch effects for 'Monsters' and 'Mutants'."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.transf = self.entity.getTransform()
		self.elapsed = 0.0
		self.color = VFXColor.RESONANCE_CHAOTIC

	def update(self):
		dt = cave.getDeltaTime()
		self.elapsed += dt
		
		if not self.mesh: return
		mat = self.mesh.getFinalMaterial()
		if not mat: return

		# 1. Oily Warp (UV Distortion simulation)
		warp_x = math.sin(self.elapsed * 2.0) * 0.05
		warp_y = math.cos(self.elapsed * 3.0) * 0.05
		mat.uniforms.set("u_uvOffset", cave.Vector2(warp_x, warp_y))

		# 2. Eldritch Pulse (Slow, dark breathing)
		wave = (math.sin(self.elapsed * 1.5) + 1.0) * 0.5
		mat.uniforms.set("u_emissiveColor", self.color)
		mat.uniforms.set("u_emissiveIntensity", 0.2 + wave * 0.8)

		# 3. Unstable Scale (Wobble)
		wobble = 1.0 + math.sin(self.elapsed * 10.0) * 0.05
		self.transf.setScale(wobble, 1.0 / wobble, wobble)


# ───── RESONANCE ORGANIC FX ──────────────────────────────────────
class VFXOrganic(cave.Component):
	"""Fluid, nature-based effects for 'Nomade's' and 'Survivalists'."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.transf = self.entity.getTransform()
		self.elapsed = 0.0
		self.color = VFXColor.NATURE
		self.base_scale = self.transf.getScale()

	def update(self):
		dt = cave.getDeltaTime()
		self.elapsed += dt
		
		if not self.mesh: return
		mat = self.mesh.getFinalMaterial()
		if not mat: return

		# 1. Growth Expansion (Start small, reach full size)
		growth = min(self.elapsed * 2.0, 1.0)
		self.transf.setScale(
			self.base_scale.x * growth,
			self.base_scale.y * growth,
			self.base_scale.z * growth
		)

		# 2. Nature Glow (Soft breathing)
		wave = (math.sin(self.elapsed * 2.5) + 1.0) * 0.5
		mat.uniforms.set("u_emissiveColor", self.color)
		mat.uniforms.set("u_emissiveIntensity", 0.1 + wave * 0.3)

		# 3. Drifting Motion (Floating leaves/spores)
		drift = math.sin(self.elapsed) * 0.2
		pos = self.transf.getPosition()
		self.transf.setPosition(pos.x, pos.y + drift * dt, pos.z)
