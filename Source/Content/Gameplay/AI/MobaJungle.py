import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core import MobaCommon
import random
import math

class JungleMonsterComponent(cave.Component):
	"""AI for neutral camp monsters."""
	campID = ""
	isEpic = False
	
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.spawn_pos = self.transf.worldPosition.copy()
		self.character = self.entity.get("Character")
		self.target = None
		self.leash_range = 18.0
		self.social_radius = 8.0 # Range where patience doesn't decay
		self.patience_max = 5.0
		self.patience = self.patience_max
		self.resetting = False
		self.attack_timer = 0.0
		self.target_update_timer = 0.0
		self.regen_timer = 0.0
		
		# Wave 24: Add EffectComponent and Stats
		self.entity.add("EffectComponent")
		self.entity.getProperties()["armor"] = 20
		self.entity.getProperties()["magicResist"] = 20
		if "health" not in self.entity.getProperties():
			self.entity.getProperties()["health"] = 1000
			self.entity.getProperties()["maxHealth"] = 1000
		
		# Phase 73/77: Scaling Initialization
		p = self.entity.getProperties()
		p["base_ad"] = p.get("attackDamage", 25)
		p["base_armor"] = p.get("armor", 20)
		p["base_magicResist"] = p.get("magicResist", 20)
		p["base_moveSpeed"] = p.get("speed", 350)
		p["base_maxHealth"] = p.get("maxHealth", 1000)
		
		# Apply Dynamic Temporal Scaling
		scale = MobaCommon.GameTick.get_temporal_scaling()
		p["maxHealth"] = int(p["base_maxHealth"] * scale)
		p["health"] = p["maxHealth"]
		p["attackDamage"] = int(p["base_ad"] * scale)
			
		# Phase 35: Combat Feedback
		MobaCommon.setup_combat_feedback(self.entity)
		
	def update(self):
		if MobaCommon.is_match_over:
			self.character.setWalkDirection(0, 0, 0)
			return
			
		dt = cave.getDeltaTime()
		scene = self.entity.getScene()
		
		if self.attack_timer > 0:
			self.attack_timer -= dt
			
		# CC Check
		eff = self.entity.getPy("EffectComponent")
		is_cced = eff.has_flag(MobaCommon.EffectFlags.STUN | MobaCommon.EffectFlags.ROOT) if eff else False
		if is_cced:
			self.character.setWalkDirection(0, 0, 0)
			return
			
		# Death Check
		if self.entity.getProperties().get("health", 0) <= 0:
			killer = self.entity.getProperties().get("lastAttacker")
			MobaCommon.RewardManager.distribute(self.entity, killer)
			
			# Phase 31: Epic Monster Epic Rewards
			if self.isEpic:
				self.distribute_epic_rewards(scene, killer)
				
			# Queue Respawn
			mgr_list = MobaCommon.EntityRegistry.get("JungleManager")
			if mgr_list and len(mgr_list) > 0:
				mgr_comp = mgr_list[0].getPy("JungleManager")
				if mgr_comp:
					template = self.entity.getRootTemplate()
					t_name = template.name if template else self.entity.name
					# Phase 27: Send campID to ensure unique tracking
					mgr_comp.queue_respawn(self.campID, t_name, self.spawn_pos, 120.0)
				
			self.entity.kill()
			return
			
		dist_from_spawn = (self.transf.worldPosition - self.spawn_pos).length()
		
		# 1. Patience & Reset Logic
		if self.resetting:
			# Invulnerable while resetting to prevent combat locking
			eff.add_flag(MobaCommon.EffectFlags.INVULNERABLE)
			self.move_to(self.spawn_pos, dt, speed_mult=1.5)
			
			# Rapid Regeneration
			self.regen_timer += dt
			if self.regen_timer >= 0.2:
				self.regen_timer = 0.0
				max_hp = self.entity.getProperties().get("maxHealth", 1000)
				MobaCommon.apply_heal(self.entity, max_hp * 0.08) # 40% per sec
			
			if dist_from_spawn < 0.8:
				self.resetting = False
				self.patience = self.patience_max
				eff.remove_flag(MobaCommon.EffectFlags.INVULNERABLE)
			return

		# Aggro Source Check
		if self.target:
			if dist_from_spawn > self.social_radius:
				self.patience -= dt # Decay outside social circle
			
			if dist_from_spawn > self.leash_range:
				self.patience = -1 # Immediate reset
		else:
			# Lost target? Recover patience slowly
			self.patience = min(self.patience_max, self.patience + dt * 0.5)

		if self.patience <= 0:
			self.resetting = True
			self.target = None
			return

		# 2. Aggro Logic (Throttled)
		if not self.target and not self.resetting:
			self.target_update_timer -= dt
			if self.target_update_timer <= 0:
				# Use a wider search for aggro once poked
				ents = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, 8.0)
				for e in ents:
					if e.hasTag("player") and MobaCommon.is_target_visible(self.entity, e):
						e_eff = e.getPy("EffectComponent")
						if e_eff and (e_eff.is_untargetable() or e_eff.is_invulnerable()):
							continue
						self.target = e
						break
				self.target_update_timer = 0.4
					
		# 3. Behavior
		if self.target and self.target.isActive():
			t_pos = self.target.getTransform().worldPosition
			dist = (t_pos - self.transf.worldPosition).length()
			if dist < 2.5:
				self.attack()
				self.character.setWalkDirection(0, 0, 0)
			else:
				self.move_to(t_pos, dt)
				
			if self.target.getProperties().get("health", 0) <= 0:
				self.target = None
		else:
			self.target = None
			# Move back to spawn if idle but not resetting
			if dist_from_spawn > 1.0:
				self.move_to(self.spawn_pos, dt, speed_mult=0.6)
			else:
				self.character.setWalkDirection(0, 0, 0)
				
		# --- Phase 105: Scuttle Roam AI ---
		if "scuttle" in self.entity.name.lower() and not self.resetting:
			# Roam around spawn pos
			if not self.target:
				self.move_to(self.spawn_pos + cave.Vector3(math.sin(MobaCommon.GameTick.get_time_minutes()*2)*5, 0, 0), dt, speed_mult=0.4)
			else:
				# Run away from attacker
				escape_dir = (self.transf.worldPosition - self.target.getTransform().worldPosition).normalized()
				self.move_to(self.transf.worldPosition + escape_dir * 5.0, dt, speed_mult=1.2)

	def move_to(self, target_pos, dt, speed_mult=1.0):
		dir = (target_pos - self.transf.worldPosition).normalized()
		speed = self.entity.getProperties().get("speed", 350) * MobaCommon.SPEED_RATIO * speed_mult
		tr = self.entity.getProperties().get("turnRate", 300)
		MobaCommon.rotate_towards(self.transf, dir, dt, tr)
		self.character.setWalkDirection(0, 0, speed * dt)

	def attack(self):
		if self.attack_timer <= 0 and self.target and self.target.isActive():
			self.attack_timer = 1.2
			dmg = self.entity.getProperties().get("attackDamage", 25)
			
			# --- Specialized Monster Effects (Phase 40/63) ---
			name = self.entity.name.lower()
			
			# Phase 63: Intruder Punishment Logic
			t_pc = self.target.getPy("PlayerController")
			if t_pc:
				has_jungle_item = any("Resolve" in item_id for item_id in getattr(t_pc, 'inventory', []))
				match_time = self.entity.getScene().getElapsedSceneTime()
				if not has_jungle_item and match_time < 600.0:
					dmg *= 1.5 # 50% Bonus damage to non-junglers
					# Apply a visual bleed to signal danger
					MobaCommon.apply_dot(self.target, 10, 2.0, source=self.entity)

			if "red" in name:
				# Red Buff: Burn (DoT) + Slow
				MobaCommon.apply_dot(self.target, 15, 3.0, source=self.entity)
				MobaCommon.apply_cc(self.target, "SLOW", 1.5, magnitude=0.25)
			elif "blue" in name:
				# Blue Buff: Mana Burn / CDR Penalty (Systemic)
				t_pc = self.target.getPy("PlayerController")
				if t_pc:
					t_pc.mana = max(0, t_pc.mana - 20)
			elif self.isEpic:
				# Epic (Baron/Dragon): AoE Cleave
				MobaCommon.apply_circular_aoe(
					self.entity.getScene(), 
					self.transf.worldPosition + self.transf.getForwardVector() * 2.0,
					4.0, dmg * 0.5, 
					MobaCommon.DamageType.PHYSICAL, 
					attacker=self.entity
				)
			
			# Apply damage to main target
			MobaCommon.apply_damage(self.target, dmg, MobaCommon.DamageType.PHYSICAL, attacker=self.entity)
			# Generic monster hit sound
			MobaCommon.play_sfx(self.entity, MobaCommon.Templates.SFX_JUNGLE_ATK, pitch_var=0.15)

	def distribute_epic_rewards(self, scene, killer):
		"""Phase 31: Global buffs for Dragon/Baron kills."""
		name = self.entity.name.lower()
		team = killer.getProperties().get("team") if killer else "teamA"
		allies = MobaCommon.EntityRegistry.get_team_entities(team, "player")
		
		from UI import MobaUI
		if "dragon" in name:
			MobaCommon.GlobalObjectiveManager.add_dragon(team)
			MobaUI.broadcast_event(f"{team} has slain the DRAGON!")
			for a in allies:
				# Apply a stack-based stat refresh
				a_pc = a.getPy("PlayerController")
				if a_pc:
					a_pc.recalculate_stats()
		elif "baron" in name:
			MobaUI.broadcast_event(f"{team} has slain BARON NASHOR!")
			for a in allies:
				a_pc = a.getPy("PlayerController")
				if a_pc:
					a_pc.applyEffect("BARON_BUFF", duration=180.0)
					a.getProperties()["hasBaronBuff"] = True
		elif "scuttle" in name:
			MobaUI.broadcast_event(f"{team} has secured a Rift Scuttler!")
			# Spawn Speed Shrine (Phase 105)
			shrine = scene.addFromTemplate("SpeedShrineTemplate", self.spawn_pos)
			if shrine:
				shrine.getProperties()["team"] = team
				shrine.addTag(team)
				shrine.addTag("vision_ward") # Gives vision like a ward
				shrine.scheduleKill(90.0) # Lasts 90 seconds

class SpeedShrineComponent(cave.Component):
	"""Phase 105: Circular rift zone that grants vision and movement speed."""
	team = "teamA"
	radius = 6.0
	
	def update(self):
		scene = self.entity.getScene()
		pos = self.entity.getTransform().worldPosition
		
		# Vision is handled by the 'vision_ward' tag in VisionManager
		
		# Speed Boost
		ents = MobaCommon.get_entities_in_radius(scene, pos, self.radius)
		for e in ents:
			if e.hasTag(self.team) and e.hasTag("player"):
				ec = e.getPy("EffectComponent")
				if ec:
					# Apply a high-frequency short duration refresh
					ec.apply("MS_BOOST", 0.5, flags=MobaCommon.EffectFlags.NONE, magnitude=0.3)

class JungleManager(cave.Component):
	"""Manages respawn timers for jungle camps."""
	def start(self, scene):
		# Phase 27: Use dict to prevent duplicate camp timers
		self.respawn_queue = {} # {campID: [template, pos, remaining_time]}
		self.plant_spawned = False
		self.plant_locations = [
			cave.Vector3(0, 0, 15), # North River
			cave.Vector3(0, 0, -15), # South River
			cave.Vector3(12, 0, 5),  # East Jungle Entrance
			cave.Vector3(-12, 0, -5) # West Jungle Entrance
		]
		
	def update(self):
		scene = self.entity.getScene()
		match_time = MobaCommon.GameTick.get_time_minutes()
		if match_time >= 6.5 and not self.plant_spawned:
			self.spawn_plants(scene)
			self.plant_spawned = True

		if not self.respawn_queue: return
		
		# Phase 27: Deterministic Update via GameTick pulses
		if not MobaCommon.GameTick.is_tick_frame():
			return
			
		dt = 0.1 
		to_spawn = []
		for campID, data in self.respawn_queue.items():
			data[2] -= dt
			if data[2] <= 0:
				to_spawn.append(campID)
				
		for campID in to_spawn:
			data = self.respawn_queue.pop(campID)
			template_name = data[0]
			spawn_pos = data[1]
			
			# Spawn new monster
			new_monster = scene.addFromTemplate(template_name, spawn_pos)
			if new_monster:
				comp = new_monster.getPy("JungleMonsterComponent")
				if comp:
					comp.campID = campID # Restore camp ID
				
	def queue_respawn(self, campID, template, pos, delay):
		if not campID:
			campID = f"auto_{template}_{int(pos.x)}_{int(pos.z)}"
			
		if campID in self.respawn_queue:
			return
			
		self.respawn_queue[campID] = [template, pos, delay]

	def spawn_plants(self, scene):
		"""Phase 100: Spawn mid-game Honeyfruits."""
		MobaCommon.broadcast_event("The River Harvest has begun! Honeyfruits have spawned.")
		for loc in self.plant_locations:
			plant = scene.addFromTemplate("HoneyfruitTemplate", loc)
			if plant:
				# Add the logic component if not already in template
				if not plant.getPy("PlantComponent"):
					plant.add("PlantComponent")
