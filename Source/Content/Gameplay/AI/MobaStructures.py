import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon
from UI import MobaUI

class StructureComponent(cave.Component):
	"""Base for Nexus and Inhibitor. Handles invulnerability and backdoor protection."""
	requires_uid = "" # UID of structure(s) that must die before this is vulnerable. Support comma separated.
	team = "teamA"
	
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.isInvulnerable = True if self.requires_uid else False
		self.update_timer = 0.0
		
		# Standard stats if not set in editor
		if "health" not in self.entity.getProperties():
			self.entity.getProperties()["health"] = 5000
			self.entity.getProperties()["maxHealth"] = 5000
		self.entity.getProperties()["armor"] = 100
		self.entity.getProperties()["magicResist"] = 100
		
		# Phase 35: Combat Feedback
		MobaCommon.setup_combat_feedback(self.entity)

	def update(self):
		if MobaCommon.is_match_over: return
		
		dt = cave.getDeltaTime()
		scene = self.entity.getScene()
		
		self.update_timer -= dt
		if self.update_timer <= 0:
			self.update_timer = 1.0 # Throttle checks
			self.check_invulnerability(scene)
			self.apply_backdoor_protection(scene)
			
		# Death Check
		if self.entity.getProperties().get("health", 0) <= 0:
			self.on_death()

	def check_invulnerability(self, scene):
		"""Sequential Structural Integrity."""
		# Split by comma for multiple requirements (e.g. Nexus requires both Nexus Turrets)
		uids = [s.strip() for s in self.requires_uid.split(",") if s.strip()]
		
		is_vulnerable = True
		for uid in uids:
			# If ANY requirement is still active, we are invulnerable
			found_active = False
			entities = MobaCommon.EntityRegistry.get("turret") + MobaCommon.EntityRegistry.get("inhibitor")
			for e in entities:
				if e.name == uid and e.isActive():
					found_active = True
					break
			if found_active:
				is_vulnerable = False
				break
				
		self.isInvulnerable = not is_vulnerable
		
		# Update EffectComponent if exists
		eff = self.entity.getPy("EffectComponent")
		if eff:
			if self.isInvulnerable: eff.add_flag(MobaCommon.EffectFlags.INVULNERABLE)
			else: eff.remove_flag(MobaCommon.EffectFlags.INVULNERABLE)

	def apply_backdoor_protection(self, scene):
		"""Backdoor Protection: High reduction if no enemy minions nearby."""
		if self.isInvulnerable: return
		
		team = self.entity.getProperties().get("team", self.team)
		enemyTag = "teamB" if team == "teamA" else "teamA"
		
		minions = [e for e in MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, 15.0) if e.hasTag(enemyTag) and e.hasTag("minion")]
		
		if not minions:
			# No minions! Apply 66% damage reduction via a property flag or direct taking.
			# Our apply_damage/takeDamage needs to check this.
			self.entity.getProperties()["backdoor_reduction"] = 0.33 # Take only 33% dmg
		else:
			self.entity.getProperties()["backdoor_reduction"] = 1.0

	def on_death(self):
		# Distribute rewards
		killer = self.entity.getProperties().get("lastAttacker")
		MobaCommon.RewardManager.distribute(self.entity, killer)
		
		# Phase 32: Announcements
		scene = self.entity.getScene()
		team_name = "Blue" if self.team == "teamA" else "Red"
		unit_name = "Inhibitor" if self.entity.hasTag("inhibitor") else "Turret"
		
		MobaUI.broadcast_event(f"The {team_name} {unit_name} has been destroyed!")
		
		# Visuals
		MobaCommon.spawn_vfx(scene, MobaCommon.Templates.VFX_TURRET_EXP, self.transf.worldPosition)
		
		self.entity.kill()

class NexusComponent(StructureComponent):
	"""The final objective."""
	def on_death(self):
		team = self.entity.getProperties().get("team", self.team)
		winner = "teamB" if team == "teamA" else "teamA"
		
		# Victory Sequence (Phase 30)
		MobaCommon.is_match_over = True
		
		# 1. Global Announcement
		winner_name = "Blue" if winner == "teamA" else "Red"
		MobaUI.broadcast_event(f"VICTORY — {winner_name} Team Wins!")
		
		# 2. Camera Focus
		cam = self.entity.getScene().getCamera()
		if cam:
			# Camera class extends Transform, so lookAt should be called on it directly
			try: cam.lookAtPosition(self.transf.worldPosition)
			except: pass
			
		# 3. VFX/SFX
		MobaCommon.spawn_vfx(self.entity.getScene(), MobaCommon.Templates.VFX_TURRET_EXP, self.transf.worldPosition)
		# MobaCommon.play_sfx(self.entity, "SFX_Nexus_Explosion") 
		
		self.entity.kill()

class InhibitorComponent(StructureComponent):
	"""Destruction enables Super Minions; resposns after 5 mins."""
	respawn_timer = 0.0
	is_destroyed = False
	laneID = 1 # 0=Top, 1=Mid, 2=Bot
	
	def start(self, scene):
		super().start(scene)
		self.entity.getProperties()["health"] = 4000
		self.entity.getProperties()["maxHealth"] = 4000
		self.last_dmg_time = 0.0

	def update(self):
		dt = cave.getDeltaTime()
		scene = self.entity.getScene()
		
		hp = self.entity.getProperties().get("health", 4000)
		if hasattr(self, "_prev_hp") and hp < self._prev_hp:
			self.last_dmg_time = scene.getElapsedSceneTime()
		self._prev_hp = hp
		
		if self.is_destroyed:
			self.respawn_timer -= dt
			if self.respawn_timer <= 0:
				self.respawn()
			return

		super().update()
		
		# HP Regen (If out of combat for 10s)
		if not self.is_destroyed:
			elapsed = scene.getElapsedSceneTime()
			if (elapsed - self.last_dmg_time) > 10.0:
				hp = self.entity.getProperties().get("health", 0)
				max_hp = self.entity.getProperties().get("maxHealth", 4000)
				if hp < max_hp and MobaCommon.GameTick.is_tick_frame():
					self.entity.getProperties()["health"] = min(max_hp, hp + (max_hp * 0.01))

	def on_death(self):
		scene = self.entity.getScene()
		self.is_destroyed = True
		self.respawn_timer = 300.0 # 5 minutes
		self.respawn_at = scene.getElapsedSceneTime() + self.respawn_timer
		
		# Visual "death"
		mesh = self.entity.getChild("Mesh")
		if mesh: mesh.deactivate(scene)
		
		# Disable collision
		char = self.entity.get("Character")
		if char: char.disable()
		
		# Register destruction globally (Crucial for MinionSpawner)
		MobaCommon.InhibitorRegistry.set_destroyed(self.team, self.laneID, self.respawn_at)
		
		# Enable Super Minions for team (Direct override for immediate effect)
		spawner = self.find_local_spawner()
		if spawner:
			spawner.isSuperWave = True
			
		MobaUI.broadcast_event(f"{MobaCommon.Team.get_enemy(self.team).upper()} Inhibitor Destroyed!")

	def respawn(self):
		scene = self.entity.getScene()
		self.is_destroyed = False
		self.entity.getProperties()["health"] = self.entity.getProperties()["maxHealth"]
		
		# Visual/Logic Enable
		mesh = self.entity.getChild("Mesh")
		if mesh: mesh.activate(scene)
		
		char = self.entity.get("Character")
		if char: char.enable()
		
		# Update spawner
		spawner = self.find_local_spawner()
		if spawner:
			spawner.isSuperWave = False
			
		MobaUI.broadcast_event(f"The {self.team.upper()} Inhibitor has respawned!")

	def find_local_spawner(self):
		from AI.MobaMinions import MinionSpawner
		spawners = MobaCommon.EntityRegistry.get("spawner")
		for s in spawners:
			comp = s.getPy("MinionSpawner")
			# Phase 73: Match both Team AND Lane
			if comp and comp.team == self.team and comp.laneID == self.laneID:
				return comp
		return None

class HealthRelicComponent(cave.Component):
	"""Phase 30: Spawnable healing pickup with AE restoration."""
	respawn_time = 60.0
	timer = 0.0
	is_active = True
	
	def update(self):
		if not self.is_active:
			self.timer -= cave.getDeltaTime()
			if self.timer <= 0:
				self.is_active = True
				mesh = self.entity.getChild("Mesh")
				if mesh: mesh.activate(self.entity.getScene())
			return
		
		# Cave Engine has no trigger callbacks (on_trigger_enter/exit).
		# We must manually check proximity each frame.
		scene = self.entity.getScene()
		pos = self.entity.getTransform().worldPosition
		pickup_radius = 2.0
		nearby = MobaCommon.get_entities_in_radius(scene, pos, pickup_radius)
		for e in nearby:
			if e.isActive() and e.hasTag("player"):
				self.consume(e)
				return

	def consume(self, collector):
		scene = self.entity.getScene()
		self.is_active = False
		self.timer = self.respawn_time
		mesh = self.entity.getChild("Mesh")
		if mesh: mesh.deactivate(scene)
		
		# AOE Restore (15% HP/Mana)
		scene = self.entity.getScene()
		pos = self.entity.getTransform().worldPosition
		team = collector.getProperties().get("team") or "NEUTRAL"
		
		nearby = MobaCommon.get_entities_in_radius(scene, pos, 6.0)
		for e in nearby:
			if e.hasTag(team) and (e.hasTag("player") or e.hasTag("minion")):
				hp_gain = e.getProperties().get("maxHealth", 100) * 0.15
				MobaCommon.apply_heal(e, hp_gain, source=self.entity)
				# Mana for players
				pc = e.getPy("PlayerController")
				if pc:
					pc.mana = min(pc.maxMana, pc.mana + (pc.maxMana * 0.15))
		
		MobaCommon.spawn_vfx(scene, MobaCommon.Templates.VFX_BUFF_GREEN, pos, duration=1.0)
		MobaCommon.play_sfx(self.entity, "SFX_Heal_Pickup")
