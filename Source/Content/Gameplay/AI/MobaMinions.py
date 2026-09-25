import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon
from Data import AnimationRegistry

class MinionComponent(cave.Component):
	"""Basic lane minion AI."""
	team = "teamA"
	laneID = 0
	
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.character = self.entity.get("Character")
		
		# Safety: Handle missing Mesh or Animation
		self.animator = None
		mesh = self.entity.getChild("Mesh")
		if mesh:
			try: self.animator = mesh.get("Animation")
			except: pass
		self.target = None
		
		# Wave 24: Detect Ranged status from entity properties or attack_range
		self.isRanged = self.entity.getProperties().get("isRanged", False)
		self.attack_range = self.entity.getProperties().get("range", 1.5 if not self.isRanged else 8.0)
		self.aggro_range = 10.0 # Phase 20: Aggro radius for target finding
		self.attack_timer = 0.0

		self.target_update_timer = 0.0
		
		# Phase 31: Waypoint Navigation
		self.path_nodes = [] # List of Vector3
		self.current_node_index = 0
		self.is_conflict_zone = False # Once reached, ignores pathing for targets
		
		# Stuck Detection System
		self.stuck_timer = 0.0
		self.last_pos = self.transf.worldPosition.copy()
		self.unjam_timer = 0.0
		self.unjam_dir = cave.Vector3(0, 0, 1)

		
		# Phase 31: Temporal Scaling (Non-Hero NPCs)
		scale = MobaCommon.GameTick.get_temporal_scaling()
		base_hp = self.entity.getProperties().get("health", 500)
		self.entity.getProperties()["health"] = int(base_hp * scale)
		self.entity.getProperties()["maxHealth"] = int(base_hp * scale)
		base_dmg = self.entity.getProperties().get("attackDamage", 15)
		self.entity.getProperties()["attackDamage"] = int(base_dmg * scale)
		
		# Phase 31: Baron Buff Empowerment
		self.isBaronEmpowered = False
		self.baron_check_timer = 0.0
		
		# Wave 24: Add EffectComponent and Stats
		self.entity.add("EffectComponent")
		self.entity.getProperties()["armor"] = 0
		self.entity.getProperties()["magicResist"] = 0
		if "health" not in self.entity.getProperties():
			self.entity.getProperties()["health"] = 500
			self.entity.getProperties()["maxHealth"] = 500
			
		# Phase 71: Base Stat Mirrors for refresh_stats clean-read
		props = self.entity.getProperties()
		props["base_ad"] = props.get("attackDamage", 15)
		props["base_armor"] = props.get("armor", 0)
		props["base_magicResist"] = props.get("magicResist", 0)
		props["base_moveSpeed"] = props.get("speed", 250)
		props["base_maxHealth"] = props.get("maxHealth", 500)
			
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
			MobaCommon.cleanup_entity_state(self.entity)
			self.entity.kill()
			return
			
		# 1. Target Finding - Throttled (Phase 20)
		self.target_update_timer -= dt
		if self.target_update_timer <= 0:
			self.target_update_timer = 0.5 # Re-evaluate every 0.5s
			
			team = self.entity.getProperties().get("team", self.team)
			enemyTag = "teamB" if team == "teamA" else "teamA"
			allyTag = team
			
			ents = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, self.aggro_range)
			
			priority_target = None
			# --- Phase 81: Social Aggro (Call-for-Help) ---
			now = scene.getElapsedSceneTime()
			for e in ents:
				if e.isActive() and e.hasTag(allyTag) and e.hasTag("player"):
					contribs = e.getProperties().get("contributions", {})
					for attacker_name, data in contribs.items():
						atk_time, attacker_ref = data
						if (now - atk_time) < 2.0 and attacker_ref and attacker_ref.isActive() and attacker_ref.hasTag("player"):
							if (attacker_ref.getTransform().worldPosition - self.transf.worldPosition).length() <= self.aggro_range:
								priority_target = attacker_ref
								break
					if priority_target: break

			if priority_target:
				self.target = priority_target
			else:
				# Default: Closest enemy within range
				best_e = None
				best_d = 999.0
				for e in ents:
					if e.hasTag(enemyTag) and MobaCommon.is_target_visible(self.entity, e):
						d = (e.getTransform().worldPosition - self.transf.worldPosition).length()
						if d < best_d:
							best_d = d
							best_e = e
				self.target = best_e
						
		# 2. State Logic
		if self.target and self.target.isActive():
			# Phase 100: Re-verify Visibility
			if not MobaCommon.is_target_visible(self.entity, self.target):
				self.target = None
				return

			t_pos = self.target.getTransform().worldPosition
			dist = (t_pos - self.transf.worldPosition).length()
			
			if dist <= self.attack_range:
				self.attack(dt)
			else:
				self.move_to(t_pos, dt)
				
			# Target cleanup
			if self.target and self.target.getProperties().get("health", 0) <= 0:
				self.target = None
		else:
			self.target = None # Wave 27: Cleanup inactive target
			# Path toward enemy base if no target
			team = self.entity.getProperties().get("team", self.team)
			# Phase 16: Pull base positions from scene properties for map agnosticism
			base_a = scene.getProperties().get("base_A_pos", cave.Vector3(50, 0, 50))
			base_b = scene.getProperties().get("base_B_pos", cave.Vector3(-50, 0, -50))
			
			# Phase 31: Waypoint Navigation
			if self.path_nodes and self.current_node_index < len(self.path_nodes):
				node_pos = self.path_nodes[self.current_node_index]
				dist_to_node = (node_pos - self.transf.worldPosition).length()
				if dist_to_node < 3.0:
					self.current_node_index += 1
					# Continue to next node or default base
					return
				self.move_to(node_pos, dt)
			else:
				base_pos = base_b if team == "teamA" else base_a
				self.move_to(base_pos, dt)

		# --- Stuck Detection Pulse ---
		self.stuck_timer += dt
		if self.stuck_timer >= 1.0:
			dist_moved = (self.transf.worldPosition - self.last_pos).length()
			if dist_moved < 0.5: # If moving < 0.5 units per second, we are jammed
				self.unjam_timer = 0.8 # Apply jitter for 0.8s
				# Random perpendicular-ish direction
				import random
				self.unjam_dir = cave.Vector3(random.uniform(-1, 1), 0, random.uniform(-1, 1)).normalized()
			
			self.last_pos = self.transf.worldPosition.copy()
			self.stuck_timer = 0

		# Phase 31: Baron Buff Empowerment Check
		self.baron_check_timer -= dt
		if self.baron_check_timer <= 0:
			self.baron_check_timer = 1.0
			self.update_baron_empowerment(scene)

	def update_baron_empowerment(self, scene):
		"""Checks if a nearby allied hero has the Baron Buff."""
		team = self.entity.getProperties().get("team", self.team)
		heroes = [e for e in MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, 15.0) 
				 if e.hasTag("player") and e.hasTag(team)]
		
		was_empowered = self.isBaronEmpowered
		self.isBaronEmpowered = False
		for h in heroes:
			pc = h.getPy("PlayerController")
			if pc and pc.hasEffect("BARON_BUFF"):
				self.isBaronEmpowered = True
				break
		
		if self.isBaronEmpowered and not was_empowered:
			# Apply Buff Visuals/Stats (Phase 40: Centralized Refactor)
			self.transf.setScale(1.5, 1.5, 1.5)
			self.attack_range *= 1.5 # 50% Range Boost for sieging
			eff = self.entity.getPy("EffectComponent")
			if eff: eff.apply("BARON_BUFF", 999.0) # Persistent while hero is nearby
		elif not self.isBaronEmpowered and was_empowered:
			# Revert Stats
			self.transf.setScale(1.0, 1.0, 1.0)
			self.attack_range /= 1.5 # Restore original range
			eff = self.entity.getPy("EffectComponent")
			if eff:
				# Clear the buff
				if "BARON_BUFF" in eff.active_effects:
					del eff.active_effects["BARON_BUFF"]
					eff._recalculate_flags()
				MobaCommon.refresh_stats(self.entity)

	def move_to(self, target_pos, dt):
		# Optimization (Phase 69): Skip calculation if target_pos is essentially current pos
		diff = target_pos - self.transf.worldPosition
		if (diff.x * diff.x + diff.y * diff.y + diff.z * diff.z) < 0.25: # 0.5m threshold
			if self.character:
				self.character.setWalkDirection(0, 0, 0)
			return
			
		dir = diff.normalized()
		
		# --- Professional Polish: Unjam Jitter ---
		if self.unjam_timer > 0:
			self.unjam_timer -= dt
			# Blend target direction with unjam jitter (70/30 split)
			dir = (dir * 0.7 + self.unjam_dir * 0.3).normalized()

		speed = self.entity.getProperties().get("speed", 250) * MobaCommon.SPEED_RATIO
		tr = self.entity.getProperties().get("turnRate", 360)
		MobaCommon.rotate_towards(self.transf, dir, dt, tr)
		
		
		if self.character:
			# Displacement Correction: setWalkDirection expects (m/s * dt)
			self.character.setWalkDirection(0, 0, speed * dt)

			
		if self.animator:
			# Retrieve minion-specific walk animation or fallback to default
			minion_type = self.entity.getProperties().get("minionType", "Minion_Melee")
			anim_name = AnimationRegistry.get_anim(minion_type, "walk")
			try: self.animator.playByName(anim_name, 0.2, loop=True)
			except: pass

	def attack(self, dt):
		if self.attack_timer <= 0:
			self.attack_timer = 1.5 # Attack cooldown
			if self.animator:
				minion_type = self.entity.getProperties().get("minionType", "Minion_Melee")
				anim_name = AnimationRegistry.get_anim(minion_type, "attack")
				self.animator.playByName(anim_name, 0.1)
			
			dmg = self.entity.getProperties().get("attackDamage", 15)
			
			if self.isRanged:
				# Spawn Projectile (Phase 24)
				MobaCommon.spawn_homing_projectile(
					self.entity.getScene(),
					self.entity,
					self.target,
					MobaCommon.Templates.PROJ_MINION,
					25.0,
					dmg,
					hit_vfx=MobaCommon.Templates.VFX_ATTACK_HIT
				)
			else:
				# Melee: Immediate Damage
				MobaCommon.apply_damage(self.target, dmg, MobaCommon.DamageType.PHYSICAL, attacker=self.entity)
				# Generic hit sound
				MobaCommon.play_sfx(self.entity, "SFX_Minion_Attack", pitch_var=0.15)

class LaneNodeComponent(cave.Component):
	"""Phase 31: A marker for minion navigation. Place these in the editor."""
	laneID = 0 # 0=Top, 1=Mid, 2=Bot
	order = 0  # 0, 1, 2, 3...
	
	def start(self, scene):
		# No logic needed, just a marker
		pass

class MinionSpawner(cave.Component):
	"""Spawns waves of minions at intervals."""
	team = "teamA"
	laneID = 0 # Phase 74: Mission Critical initialization
	
	def start(self, scene):
		self.wave_interval = 30.0 # Standard MOBA wave
		self.timer = self.wave_interval
		self.wave_count = 0 # Phase 26
		self.isSuperWave = False # Phase 30: Triggered by Inhibitor destruction
		
	def update(self):
		if MobaCommon.is_match_over: return # Phase 74: Prevent phantom spawns
		self.timer -= cave.getDeltaTime()
		if self.timer <= 0:
			# Phase 31: Attempt to collect nodes from entities if not in properties
			scene = self.entity.getScene()  # Phase 70: Fix undefined scene
			lane_key = f"{self.team}_lane{self.laneID}_nodes"
			self.cached_nodes = scene.getProperties().get(lane_key, [])
			
			if not self.cached_nodes:
				# Optimized: Use tag if available, fallback to specific entities
				nodes = []
				for e in MobaCommon.EntityRegistry.get("lane_node"):
					comp = e.getPy("LaneNodeComponent")
					if comp and comp.laneID == self.laneID:
						nodes.append((comp.order, e.getTransform().worldPosition))
				
				# Sort by order: Team A follows 0->N, Team B follows N->0
				nodes.sort(key=lambda x: x[0])
				if self.team == "teamB":
					nodes.reverse()
				
				self.cached_nodes = [n[1] for n in nodes]
			
			self.spawn_wave()
			self.timer = self.wave_interval
			
	def spawn_wave(self):
		scene = self.entity.getScene()
		spawn_pos = self.entity.getTransform().worldPosition
		self.wave_count += 1
		
		# Phase 77: Check for Super Minion status based on enemy inhibitor
		enemy_team = "teamB" if self.team == "teamA" else "teamA"
		self.isSuperWave = MobaCommon.InhibitorRegistry.is_down(enemy_team, self.laneID, scene.getElapsedSceneTime())
		
		# 3 Melee Minions
		for i in range(3):
			m = scene.addFromTemplate(MobaCommon.Templates.MINION_MELEE, spawn_pos + cave.Vector3(i-1, 0, 0))
			m.addTag(self.team)
			m.addTag("minion")
			m.getProperties()["team"] = self.team # Synchronize for logic
			
			# Phase 31: Path Assignment
			mc = m.getPy("MinionComponent")
			if mc: mc.path_nodes = self.cached_nodes
			
		# 3 Ranged Minions (Phase 24)
		for i in range(3):
			m = scene.addFromTemplate(MobaCommon.Templates.MINION_RANGED, spawn_pos + cave.Vector3(i-1, 0, -2))
			m.addTag(self.team)
			m.addTag("minion")
			m.getProperties()["team"] = self.team
			m.getProperties()["isRanged"] = True
			m.getProperties()["range"] = 8.0
			m.getProperties()["attackDamage"] = 12 # Ranged deal less dmg but safer
			
			# Phase 71: Restore missing path nodes
			mc = m.getPy("MinionComponent")
			if mc: mc.path_nodes = self.cached_nodes

		# Phase 26: Cannon Minion logic (every 3rd wave)
		if self.wave_count % 3 == 0:
			m = scene.addFromTemplate(MobaCommon.Templates.MINION_CANNON, spawn_pos + cave.Vector3(0, 0, -4))
			m.addTag(self.team)
			m.addTag("minion")
			m.getProperties()["team"] = self.team
			m.getProperties()["isRanged"] = True
			m.getProperties()["range"] = 9.0 # Long range for siege
			m.getProperties()["health"] = 900
			m.getProperties()["maxHealth"] = 900
			m.getProperties()["attackDamage"] = 40 # High siege damage
			m.getProperties()["isCannon"] = True # Flag for targeting/buffs
			
			# Phase 71: Restore missing path nodes
			mc = m.getPy("MinionComponent")
			if mc: mc.path_nodes = self.cached_nodes

		# Phase 30: Super Minion Spawning
		if self.isSuperWave:
			# Super minion replaces/augments wave
			m = scene.addFromTemplate("Minion_Super", spawn_pos + cave.Vector3(0, 0, -6))
			m.addTag(self.team)
			m.addTag("minion")
			m.getProperties()["team"] = self.team
			m.getProperties()["health"] = 2500
			m.getProperties()["maxHealth"] = 2500
			m.getProperties()["attackDamage"] = 120
			m.getProperties()["isSuper"] = True
			
			# Phase 71: Restore missing path nodes
			mc = m.getPy("MinionComponent")
			if mc: mc.path_nodes = self.cached_nodes
