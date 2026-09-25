import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon
import math

# ═══════════════════════════════════════════════════════════════════
# MobaShaders.py — Shader Controller Components
# Phase 115: Hero body shaders, environmental FX, and post-process.
# These components attach to hero/environment entities and drive
# uniforms on their materials every frame.
# ═══════════════════════════════════════════════════════════════════

class HeroShaderController(cave.Component):
	"""Master shader controller for hero entities.
	Drives all visual states: team color, damage flash, buff glow, stealth."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.pc = self.entity.getPy("PlayerController")
		self.elapsed = 0.0

		# Flash state
		self.flash_timer = 0.0
		self.flash_color = cave.Vector4(1, 1, 1, 1)

		# Team tint (subtle accent)
		self.team = MobaCommon.get_entity_team(self.entity)
		if self.team == "teamA":
			self.team_accent = cave.Vector4(0.85, 0.9, 1.0, 1.0)
		else:
			self.team_accent = cave.Vector4(1.0, 0.88, 0.85, 1.0)

	def update(self):
		if not self.mesh:
			return
		mat = self.mesh.getFinalMaterial()
		if not mat:
			return

		dt = cave.getDeltaTime()
		self.elapsed += dt

		# 1. Damage Flash (overrides everything briefly)
		if self.flash_timer > 0:
			self.flash_timer -= dt
			t = max(0, self.flash_timer / 0.15)
			r = 1.0 + (self.flash_color.x - 1.0) * t
			g = 1.0 + (self.flash_color.y - 1.0) * t
			b = 1.0 + (self.flash_color.z - 1.0) * t
			mat.uniforms.set("u_baseColor", cave.Vector4(r, g, b, 1.0))
			return  # Skip other effects during flash

		# 2. Buff/Status Glow
		props = self.entity.getProperties()
		has_baron = props.get("hasBaronBuff", False)
		has_shield = (getattr(self.pc, 'shield', 0) > 0) if self.pc else False

		if has_baron:
			wave = (math.sin(self.elapsed * 2.5) + 1.0) * 0.5
			mat.uniforms.set("u_emissiveColor", cave.Vector4(0.6, 0.0, 1.0, 1.0))
			mat.uniforms.set("u_emissiveIntensity", 0.3 + wave * 0.4)
		elif has_shield:
			wave = (math.sin(self.elapsed * 4.0) + 1.0) * 0.5
			mat.uniforms.set("u_emissiveColor", cave.Vector4(1.0, 0.85, 0.2, 1.0))
			mat.uniforms.set("u_emissiveIntensity", 0.2 + wave * 0.3)
		else:
			mat.uniforms.set("u_emissiveIntensity", 0.0)

		# 3. Base team tint (subtle)
		mat.uniforms.set("u_baseColor", self.team_accent)

	def trigger_hit_flash(self, dmg_type=None):
		"""Called externally when damage is received."""
		self.flash_timer = 0.15
		if dmg_type == MobaCommon.DamageType.PHYSICAL:
			self.flash_color = cave.Vector4(1.0, 0.3, 0.3, 1.0)
		elif dmg_type == MobaCommon.DamageType.MAGIC:
			self.flash_color = cave.Vector4(0.5, 0.2, 1.0, 1.0)
		elif dmg_type == MobaCommon.DamageType.TRUE:
			self.flash_color = cave.Vector4(1.0, 1.0, 1.0, 1.0)
		else:
			self.flash_color = cave.Vector4(1.0, 0.5, 0.5, 1.0)


class MinionShaderController(cave.Component):
	"""Simplified shader for minions — handles team color and Baron empowerment glow."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.elapsed = 0.0
		self.team = MobaCommon.get_entity_team(self.entity)

	def update(self):
		if not self.mesh:
			return
		mat = self.mesh.getFinalMaterial()
		if not mat:
			return

		dt = cave.getDeltaTime()
		self.elapsed += dt

		# Baron empowerment glow
		props = self.entity.getProperties()
		is_empowered = props.get("baronEmpowered", False)

		if is_empowered:
			wave = (math.sin(self.elapsed * 3.0) + 1.0) * 0.5
			mat.uniforms.set("u_emissiveColor", cave.Vector4(0.6, 0.0, 1.0, 1.0))
			mat.uniforms.set("u_emissiveIntensity", 0.4 + wave * 0.3)
		else:
			mat.uniforms.set("u_emissiveIntensity", 0.0)


class TurretShaderController(cave.Component):
	"""Turret shader — warning pulse when targeting, destruction glow."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.elapsed = 0.0
		self.is_targeting = False

	def set_targeting(self, active):
		self.is_targeting = active

	def update(self):
		if not self.mesh:
			return
		mat = self.mesh.getFinalMaterial()
		if not mat:
			return

		dt = cave.getDeltaTime()
		self.elapsed += dt

		if self.is_targeting:
			# Aggressive red pulse
			wave = (math.sin(self.elapsed * 6.0) + 1.0) * 0.5
			mat.uniforms.set("u_emissiveColor", cave.Vector4(1.0, 0.2, 0.1, 1.0))
			mat.uniforms.set("u_emissiveIntensity", 0.3 + wave * 0.5)
		else:
			# Idle ambient glow
			wave = (math.sin(self.elapsed * 1.5) + 1.0) * 0.5
			mat.uniforms.set("u_emissiveIntensity", 0.05 + wave * 0.1)


class EnvironmentShaderController(cave.Component):
	"""Drives environmental shader effects: day/night tinting, fog of war."""
	def start(self, scene):
		self.elapsed = 0.0

	def update(self):
		dt = cave.getDeltaTime()
		self.elapsed += dt

		# Time-of-day cycle (matches game time)
		game_mins = MobaCommon.GameTick.get_time_minutes()

		# Gradual tint change: bright early → darker late game
		# 0-10 min: Bright morning (warm)
		# 10-20 min: Neutral
		# 20-30 min: Dusk (cool, slightly dark)
		# 30+ min: Night (dark purple tint)
		if game_mins < 10:
			ambient = cave.Vector4(1.0, 0.95, 0.85, 1.0)
		elif game_mins < 20:
			ambient = cave.Vector4(0.95, 0.95, 1.0, 1.0)
		elif game_mins < 30:
			t = (game_mins - 20) / 10.0
			ambient = cave.Vector4(
				0.95 - t * 0.15,
				0.95 - t * 0.2,
				1.0 - t * 0.05,
				1.0
			)
		else:
			ambient = cave.Vector4(0.75, 0.7, 0.9, 1.0)

		# Apply to global lighting if available
		scene = self.entity.getScene()
		light = scene.get("Directional_Light") if scene else None
		if light:
			mesh = light.get("Mesh")
			if mesh:
				mat = mesh.getFinalMaterial()
				if mat:
					mat.uniforms.set("u_ambientColor", ambient)


class WaterShaderController(cave.Component):
	"""Animated water surface for river/ARAM bridge areas."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.elapsed = 0.0

	def update(self):
		if not self.mesh:
			return
		mat = self.mesh.getFinalMaterial()
		if not mat:
			return

		dt = cave.getDeltaTime()
		self.elapsed += dt

		# Scrolling UV offset for flowing water
		mat.uniforms.set("u_uvOffset", cave.Vector2(
			self.elapsed * 0.05,
			self.elapsed * 0.02
		))

		# Specular shimmer
		shimmer = (math.sin(self.elapsed * 2.0) + 1.0) * 0.5
		mat.uniforms.set("u_specularIntensity", 0.5 + shimmer * 0.3)


class HeroGlitchController(cave.Component):
	"""Permanent/Toggleable glitch effect for 'The Front' faction heroes."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.elapsed = 0.0
		self.is_active = True
		
		# Colors from FactionIdentity / VFXColor
		self.glitch_color = cave.Vector4(0.4, 1.0, 0.2, 1.0) # Neon Green
		self.alt_color = cave.Vector4(1.0, 0.5, 0.0, 1.0)    # Orange Accent

	def update(self):
		if not self.is_active or not self.mesh: return
		mat = self.mesh.getFinalMaterial()
		if not mat: return

		import random
		dt = cave.getDeltaTime()
		self.elapsed += dt

		# 1. Subtle Jitter (Every 2-3 seconds, a major 'pop')
		glitch_chance = 0.02
		if random.random() < glitch_chance:
			# Sudden Brightness Spike
			mat.uniforms.set("u_emissiveIntensity", 1.5)
			mat.uniforms.set("u_emissiveColor", self.alt_color if random.random() > 0.5 else self.glitch_color)
			
			# Rim-light flickering
			mat.uniforms.set("u_outlineEnabled", 1.0)
			mat.uniforms.set("u_outlineColor", self.glitch_color)
			mat.uniforms.set("u_outlineWidth", random.uniform(0.1, 0.5))
		else:
			# Baseline state
			wave = (math.sin(self.elapsed * 5.0) + 1.0) * 0.5
			mat.uniforms.set("u_emissiveIntensity", 0.1 + wave * 0.2)
			mat.uniforms.set("u_emissiveColor", self.glitch_color)
			
			if random.random() < 0.1: # Constant micro-flicker
				mat.uniforms.set("u_outlineEnabled", 0.0)

		# 2. Random Alpha 'Dropouts' (Digital transparency artifacts)
		if random.random() < 0.005:
			mat.uniforms.set("u_alpha", 0.5)
		else:
			mat.uniforms.set("u_alpha", 1.0)


class HeroHarmonicController(cave.Component):
	"""Polished, crystalline shader style for 'Rich Family' heroes."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.elapsed = 0.0
		self.is_active = True
		
		# Elegant palette
		self.harmonic_color = cave.Vector4(0.2, 0.6, 1.0, 1.0) # Sapphire Blue
		self.gold_accent = cave.Vector4(1.0, 0.8, 0.2, 1.0)    # Gold

	def update(self):
		if not self.is_active or not self.mesh: return
		mat = self.mesh.getFinalMaterial()
		if not mat: return

		dt = cave.getDeltaTime()
		self.elapsed += dt

		# 1. Stable Emissive Pulse (Breathing aura)
		wave = (math.sin(self.elapsed * 1.5) + 1.0) * 0.5
		mat.uniforms.set("u_emissiveColor", self.harmonic_color)
		mat.uniforms.set("u_emissiveIntensity", 0.15 + wave * 0.1)

		# 2. Crystalline Rim-Light (Jewel effect)
		# Uses a high-frequency sine for a 'twinkle'
		twinkle = (math.sin(self.elapsed * 10.0) + 1.0) * 0.5
		mat.uniforms.set("u_outlineEnabled", 1.0)
		mat.uniforms.set("u_outlineColor", self.gold_accent if twinkle > 0.8 else self.harmonic_color)
		mat.uniforms.set("u_outlineWidth", 0.2 + twinkle * 0.1)

		# 3. Prism Tint (Subtle shifting of base color)
		prism = (math.cos(self.elapsed * 0.5) + 1.0) * 0.5
		base_tint = cave.Vector4(0.9, 0.95 + prism * 0.05, 1.0, 1.0)
		mat.uniforms.set("u_baseColor", base_tint)


class HeroAmplifiedController(cave.Component):
	"""Aggressive, high-output shader style for 'The Imperium' heroes."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.elapsed = 0.0
		self.is_active = True
		
		# Brutal palette
		self.energy_color = cave.Vector4(1.0, 0.1, 0.1, 1.0) # Deep Red
		self.shock_color = cave.Vector4(1.0, 0.5, 0.5, 1.0)  # Light Red/Pink

	def update(self):
		if not self.is_active or not self.mesh: return
		mat = self.mesh.getFinalMaterial()
		if not mat: return

		dt = cave.getDeltaTime()
		self.elapsed += dt

		import random

		# 1. High-Frequency Emissive (Overloaded reactor feel)
		wave = (math.sin(self.elapsed * 12.0) + 1.0) * 0.5
		mat.uniforms.set("u_emissiveColor", self.energy_color)
		mat.uniforms.set("u_emissiveIntensity", 0.3 + wave * 0.4)

		# 2. Concussive Rim-Light (Electrical arcs)
		if random.random() < 0.1: # Rapid flicker
			mat.uniforms.set("u_outlineEnabled", 1.0)
			mat.uniforms.set("u_outlineColor", self.shock_color)
			mat.uniforms.set("u_outlineWidth", random.uniform(0.3, 0.8))
		else:
			mat.uniforms.set("u_outlineWidth", 0.2)
			mat.uniforms.set("u_outlineColor", self.energy_color)

		# 3. Heavy Tint (Industrial/Military look)
		mat.uniforms.set("u_baseColor", cave.Vector4(1.0, 0.9, 0.9, 1.0))


class HeroChaoticController(cave.Component):
	"""Unstable, warping shader style for 'Monster' heroes."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.elapsed = 0.0
		self.is_active = True
		self.color = cave.Vector4(0.6, 0.1, 0.9, 1.0) # Eldritch Purple

	def update(self):
		if not self.is_active or not self.mesh: return
		mat = self.mesh.getFinalMaterial()
		if not mat: return

		dt = cave.getDeltaTime()
		self.elapsed += dt

		# 1. Dark Eldritch Pulse
		wave = (math.sin(self.elapsed * 0.8) + 1.0) * 0.5
		mat.uniforms.set("u_emissiveColor", self.color)
		mat.uniforms.set("u_emissiveIntensity", 0.1 + wave * 0.5)

		# 2. Warp Outlines (Oily shimmer)
		mat.uniforms.set("u_outlineEnabled", 1.0)
		mat.uniforms.set("u_outlineColor", cave.Vector4(0.1, 0.0, 0.2, 1.0)) # Dark void
		mat.uniforms.set("u_outlineWidth", 0.4 + math.sin(self.elapsed * 4.0) * 0.2)

		# 3. Sickly Tint
		mat.uniforms.set("u_baseColor", cave.Vector4(0.8, 0.7, 0.9, 1.0))


class HeroOrganicController(cave.Component):
	"""Living, fluid shader style for 'Nomade' heroes."""
	def start(self, scene):
		self.mesh = self.entity.get("Mesh")
		self.elapsed = 0.0
		self.is_active = True
		self.color = cave.Vector4(0.2, 0.9, 0.3, 1.0) # Nature Green

	def update(self):
		if not self.is_active or not self.mesh: return
		mat = self.mesh.getFinalMaterial()
		if not mat: return

		dt = cave.getDeltaTime()
		self.elapsed += dt

		# 1. Soft Life Pulse (Breathing)
		wave = (math.sin(self.elapsed * 2.0) + 1.0) * 0.5
		mat.uniforms.set("u_emissiveColor", self.color)
		mat.uniforms.set("u_emissiveIntensity", 0.05 + wave * 0.2)

		# 2. Leaf Rim-Light
		mat.uniforms.set("u_outlineEnabled", 1.0)
		mat.uniforms.set("u_outlineColor", cave.Vector4(0.8, 1.0, 0.5, 1.0)) # Pale green
		mat.uniforms.set("u_outlineWidth", 0.1 + wave * 0.1)

		# 3. Natural Tint
		mat.uniforms.set("u_baseColor", cave.Vector4(0.95, 1.0, 0.9, 1.0))
