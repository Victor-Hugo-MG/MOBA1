import cave
from Core import MobaCommon
from UI import MobaUI

class ObjectiveBase(cave.Component):
	"""
	Base logic for Strategic Neutral Bosses.
	Handles Aggro-Leashing: if the boss is pulled too far from its pit, it becomes
	invulnerable, resets its position, and heals rapidly.
	"""
	def start(self, scene):
		self.spawn_pos = self.entity.getTransform().worldPosition.copy()
		self.max_leash = 12.0 # Max distance from center before reset
		self.is_resetting = False
		self.aggro_target = None
		
		# Stats
		props = self.entity.getProperties()
		self.max_health = props.get("maxHealth", 5000)
		
	def update(self):
		dt = cave.getDeltaTime()
		transf = self.entity.getTransform()
		props = self.entity.getProperties()
		
		# 1. Death Check
		if props.get("health", 1) <= 0:
			self.handle_reward()
			self.entity.kill()
			return

		# 2. Leash Check
		dist_from_spawn = (transf.worldPosition - self.spawn_pos).length()
		if dist_from_spawn > self.max_leash:
			self.is_resetting = True
			
		if self.is_resetting:
			self.aggro_target = None
			diff = self.spawn_pos - transf.worldPosition
			if diff.length() > 0.5:
				# Fast move back
				move_step = diff.normalized() * 8.0 * dt
				transf.move(move_step.x, 0, move_step.z, False)  # Cave API: move() not translate()
				# Rapid Heal
				props["health"] = min(self.max_health, props["health"] + self.max_health * 0.2 * dt)
			else:
				self.is_resetting = False
		
		# 3. Combat & Defense Logic
		if self.aggro_target and not self.is_resetting:
			self.handle_attack(dt)
		else:
			# Scan for targets if idle
			self.scan_for_targets()

	def scan_for_targets(self):
		scene = self.entity.getScene()
		pos = self.entity.getTransform().worldPosition
		targets = MobaCommon.get_entities_in_radius(scene, pos, 10.0) # Aggro range
		for t in targets:
			if t.hasTag("player") and MobaCommon.is_target_visible(self.entity, t):
				self.aggro_target = t
				break

	def handle_attack(self, dt):
		"""To be overridden for specific attack types."""
		pass

	def handle_reward(self):
		"""To be overridden by subclasses."""
		pass

class SpireGuardian(ObjectiveBase):
	"""
	Phase 118: Guards the Resonance Spires. 
	Attacks with 'Flux Bolts' that deal magic damage and apply a stacking slow.
	"""
	def start(self, scene):
		super().start(scene)
		self.spire_type = self.entity.getProperties().get("spireType", MobaCommon.ResonanceSpireType.AMPLIFIED)
		self.attack_cooldown = 0.0
		
	def handle_attack(self, dt):
		self.attack_cooldown -= dt
		if self.attack_cooldown <= 0 and self.aggro_target and self.aggro_target.isActive():
			# Fire a Flux Bolt at the aggro target
			MobaCommon.spawn_homing_projectile(
				self.entity.getScene(), self.entity, self.aggro_target, 
				"Flux_Bolt", speed=20.0, damage=80.0, hit_vfx="VFX_Flux_Impact"
			)
			self.attack_cooldown = 1.5 # Attack speed

	def handle_reward(self):
		killer = self.entity.getProperties().get("lastAttacker")
		if killer:
			team = MobaCommon.get_entity_team(killer)
			if team:
				MobaCommon.ObjectiveBuffs.apply_spire(team, self.spire_type)
				# Phase 124: Start Respawn Timer (5 minutes for spires)
				MobaCommon.GlobalObjectiveManager.start_respawn(f"SPIRE_{self.spire_type}", 300.0)

class CrystallineColossus(ObjectiveBase):
	"""
	Phase 118: The 'Baron' equivalent. 
	Attacks with a powerful 'Crystal Beam' and occasional ground slams.
	"""
	def start(self, scene):
		super().start(scene)
		self.attack_cooldown = 0.0
		
	def handle_attack(self, dt):
		self.attack_cooldown -= dt
		if self.attack_cooldown <= 0 and self.aggro_target and self.aggro_target.isActive():
			# Heavy Crystal Beam
			MobaCommon.spawn_homing_projectile(
				self.entity.getScene(), self.entity, self.aggro_target, 
				"Crystal_Beam", speed=25.0, damage=150.0, hit_vfx="VFX_Crystal_Impact"
			)
			self.attack_cooldown = 1.0 # Faster attack than spire

	def handle_reward(self):
		killer = self.entity.getProperties().get("lastAttacker")
		if killer:
			team = MobaCommon.get_entity_team(killer)
			if team:
				MobaCommon.ObjectiveBuffs.apply_colossus(team)
				# Phase 124: Capture Visuals at the pit
				MobaCommon.spawn_vfx(self.entity.getScene(), "VFX_Objective_Capture_Global", self.entity.getTransform().worldPosition)
				# Phase 124: Start Respawn Timer (6 minutes for Colossus)
				MobaCommon.GlobalObjectiveManager.start_respawn("COLOSSUS", 360.0)
