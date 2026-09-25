import cave
from Core import MobaCommon

class WardComponent(cave.Component):
	"""
	Phase 123: Vision Ward logic.
	Provides vision in a radius and remains invisible to enemies.
	"""
	def start(self, scene):
		self.timer = MobaCommon.VisionConstants.WARD_DURATION
		self.team = self.entity.getProperties().get("team", "teamA")
		
		# Vision is auto-discovered by VisionManager via EntityRegistry tags
		# The ward just needs to be tagged correctly and have visionRange set
		self.entity.getProperties()["visionRange"] = MobaCommon.VisionConstants.WARD_SIGHT_RADIUS
		self.entity.getProperties()["hasTrueSight"] = True
		
		# Wards are stealth units
		self.entity.addTag("invisible")
		self.entity.addTag("ward")
		self.entity.addTag(self.team)
		
		# Professional visual: Fades in/out
		scene = self.entity.getScene()
		MobaCommon.spawn_vfx(scene, "VFX_Ward_Spawn", self.entity.getTransform().worldPosition)
		
		# Phase 125: Vision Score Tracking
		owner = self.entity.getProperties().get("owner")
		if owner:
			MobaCommon.MatchStatsManager.track_vision(owner.name, 1)

	def update(self):
		dt = cave.getDeltaTime()
		self.timer -= dt
		
		# Reveal handling (if swept by Oracle)
		reveal_timer = self.entity.getProperties().get("reveal_timer", 0.0)
		if reveal_timer > 0:
			reveal_timer -= dt
			self.entity.getProperties()["reveal_timer"] = reveal_timer
			self.entity.removeTag("invisible")
			# Visual reveal effect
			mesh = self.entity.get("Mesh")
			if mesh:
				mesh.getProperties()["isVisibleToEnemies"] = True
		else:
			self.entity.addTag("invisible")
			mesh = self.entity.get("Mesh")
			if mesh:
				mesh.getProperties()["isVisibleToEnemies"] = False

		if self.timer <= 0:
			self.entity.kill()

	def on_death(self):
		# Vision is auto-cleaned by EntityRegistry when the entity is killed
		pass

class OracleSweepComponent(cave.Component):
	"""
	Phase 123: Oracle Lens logic.
	Reveals nearby invisible units and wards.
	"""
	def start(self, scene):
		self.timer = MobaCommon.VisionConstants.ORACLE_DURATION
		self.radius = MobaCommon.VisionConstants.ORACLE_RADIUS
		self.team = self.entity.getProperties().get("team", "teamA")
		
		# Spawn the scanning ring VFX
		self.vfx = MobaCommon.spawn_vfx(
			self.entity.getScene(),
			"VFX_Oracle_Ring", 
			self.entity.getTransform().worldPosition,
			duration=self.timer
		)

	def update(self):
		dt = cave.getDeltaTime()
		self.timer -= dt
		if self.timer <= 0:
			self.entity.kill()
			return
			
		scene = self.entity.getScene()
		pos = self.entity.getTransform().worldPosition
		enemy_team = "teamB" if self.team == "teamA" else "teamA"
		
		# Scan for wards
		wards = MobaCommon.EntityRegistry.get_active("ward")
		for w in wards:
			if w.hasTag(enemy_team):
				dist = (w.getTransform().worldPosition - pos).length()
				if dist < self.radius:
					# Reveal the ward for 4 seconds
					w.getProperties()["reveal_timer"] = 4.0
					MobaCommon.spawn_vfx(scene, "VFX_Ward_Revealed", w.getTransform().worldPosition, duration=0.5)

		# Scan for invisible champions
		enemies = MobaCommon.EntityRegistry.get_active(enemy_team)
		for e in enemies:
			if e.hasTag("invisible") and e.hasTag("player"):
				dist = (e.getTransform().worldPosition - pos).length()
				if dist < self.radius:
					e.getProperties()["reveal_timer"] = 1.0 # Reveal briefly while in range
