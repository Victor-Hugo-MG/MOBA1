import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon

class TurretComponent(cave.Component):
	"""Defensive structure AI with target prioritization."""
	team = "teamA"
	
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.attack_range = 10.0
		self.attack_timer = 0.0
		self.attack_interval = 1.0
		self.target = None
		self.heat = 1.0 # Damage escalation factor
		self.heatMultiplier = 1.4
		self.target_update_timer = 0.0 # Throttling timer
		
		# Wave 24: Add EffectComponent and Stats
		self.entity.add("EffectComponent")
		if "health" not in self.entity.getProperties():
			self.entity.getProperties()["health"] = 5000
			self.entity.getProperties()["maxHealth"] = 5000
		self.entity.getProperties()["armor"] = 100
		self.entity.getProperties()["magicResist"] = 100
		
		# Phase 35: Combat Feedback
		MobaCommon.setup_combat_feedback(self.entity)
		
		# Wave 77: Scaling Tracker
		self.last_scaling_minute = -1
		self.base_stats = {
			"hp": 5000, "ad": 150, "armor": 100, "mr": 100
		}
		
		# --- Phase 100: Mid-lane Plating ---
		self.defender_timer = 0.0 # Time since defender left
		self.plates_active = True
		self.plate_thresholds = [0.8, 0.6, 0.4, 0.2] # % HP stages
		self.plates_broken = [] # Track which ones were already paid
		self.is_mid_lane = self.entity.hasTag("mid") or "mid" in self.entity.name.lower()
		
	def update(self):
		if MobaCommon.is_match_over:
			return
			
		dt = cave.getDeltaTime()
		scene = self.entity.getScene()
		
		if self.attack_timer > 0:
			self.attack_timer -= dt
			
		# Death Check
		if self.entity.getProperties().get("health", 0) <= 0:
			self.on_death()
			return
			
		# 1. Dynamic Scaling (Wave 77)
		mins = MobaCommon.GameTick.get_time_minutes()
		current_minute = int(mins)
		if current_minute > self.last_scaling_minute:
			self.last_scaling_minute = current_minute
			self.apply_scaling(mins)
			
		# Phase 100: Plating Expiration
		if mins > 14.0:
			self.plates_active = False

		# Phase 100: Defender Detection (OBB)
		if self.plates_active:
			if self.is_defender_present(scene):
				self.defender_timer = 0.0
				self.entity.getProperties()["isVulnerable"] = False
			else:
				self.defender_timer += dt
				if self.defender_timer >= 5.0:
					self.entity.getProperties()["isVulnerable"] = True
				else:
					self.entity.getProperties()["isVulnerable"] = False
		else:
			self.entity.getProperties()["isVulnerable"] = False

		# 2. Target Priority (Throttled)
		self.target_update_timer -= dt
		if self.target_update_timer <= 0:
			self.target_update_timer = 0.2
			self.find_best_target(scene)

		# 2. Target validation (Pre-attack check)
		if self.target:
			is_valid = self.target.isActive() and self.target.getProperties().get("health", 0) > 0
			
			# Filter: Is target still visible to our team?
			if is_valid and not MobaCommon.is_target_visible(self.entity, self.target):
				is_valid = False

			t_eff = self.target.getPy("EffectComponent")
			if t_eff and t_eff.is_untargetable():
				is_valid = False
			
			if not is_valid or (self.target.getTransform().worldPosition - self.transf.worldPosition).length() > self.attack_range:
				self.target = None
				self.heat = 1.0

		# 3. Attack Execution
		if self.target and self.attack_timer <= 0:
			self.fire_at_target()
			self.attack_timer = self.attack_interval

	def find_best_target(self, scene):
		team = self.entity.getProperties().get("team", self.team)
		enemyTag = "teamB" if team == "teamA" else "teamA"
		allyTag = "teamA" if team == "teamA" else "teamB"
		ents = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, self.attack_range)
		
		# True Sight Aura (if lane turret)
		is_lane = self.entity.getProperties().get("isLaneTurret", True)
		
		# Separate targets & Apply True Sight
		minions = []
		players = []
		aggressor = None
		
		for e in ents:
			if not e.isActive() or e.getProperties().get("health", 0) <= 0: continue
			
			# Phase 30: True Sight Reveal
			e_eff = e.getPy("EffectComponent")
			if is_lane and e.hasTag(enemyTag):
				if e_eff:
					# Reveals HIDDEN units in range
					MobaCommon.reveal_unit(e, 0.2)
			
			if e.hasTag(enemyTag) and MobaCommon.is_target_visible(self.entity, e):
				# Filter out untargetable
				if e_eff and e_eff.is_untargetable():
					continue
					
				if e.hasTag("minion"): minions.append(e)
				elif e.hasTag("player"): 
					players.append(e)
					# Check if this player attacked an allied hero recently (Aggro Swap)
					aggro_time = e.getProperties().get("last_hero_aggro_time", 0)
					if aggro_time > 0 and (scene.getElapsedSceneTime() - aggro_time) < 2.0:
						# They attacked an ally!
						aggressor = e
				
		# Priority Logic: Aggressor > Cannons > Standard Minions > Players
		if aggressor:
			self.target = aggressor
		elif minions:
			# Phase 30: Cannon Priority
			cannons = [m for m in minions if m.getProperties().get("isCannon", False)]
			if cannons:
				cannons.sort(key=lambda x: (x.getTransform().worldPosition - self.transf.worldPosition).length())
				self.target = cannons[0]
			else:
				minions.sort(key=lambda x: (x.getTransform().worldPosition - self.transf.worldPosition).length())
				self.target = minions[0]
		elif players:
			# Phase 20 Fix: Prioritize closest player
			players.sort(key=lambda x: (x.getTransform().worldPosition - self.transf.worldPosition).length())
			self.target = players[0]
		else:
			self.target = None
			self.heat = 1.0

	def fire_at_target(self):
		if not self.target: return
		
		# 1. Escalation Logic
		if self.target.hasTag("player"):
			self.heat = min(2.5, self.heat * self.heatMultiplier)
		else:
			self.heat = 1.0
		
		# 2. Spawn Homing Projectile (Phase 12: LoL Parity)
		base_dmg = self.entity.getProperties().get("attackDamage", 150)
		damage = base_dmg * self.heat

		MobaCommon.spawn_homing_projectile(
			self.entity.getScene(), 
			self.entity, 
			self.target,
			MobaCommon.Templates.PROJ_TURRET, 
			speed=30.0, 
			damage=damage, 
			hit_vfx=MobaCommon.Templates.VFX_TURRET_HIT
		)
		
		# 3. SFX
		MobaCommon.play_sfx(self.entity, MobaCommon.Templates.SFX_TURRET_FIRE, pitch_var=0.05)

	def apply_scaling(self, minutes):
		"""Phase 77: Recalculates turret potency based on game time."""
		# 4% growth per minute in AD/Resists
		scaling = MobaCommon.GameTick.get_temporal_scaling()
		
		props = self.entity.getProperties()
		props["attackDamage"] = int(self.base_stats["ad"] * scaling)
		props["armor"] = int(self.base_stats["armor"] * scaling)
		props["magicResist"] = int(self.base_stats["mr"] * scaling)
		
		# Plating Protection (Anti-Rush): +40 Resists for the first 5 mins
		if minutes < 5.0:
			props["armor"] += 40
			props["magicResist"] += 40
		
		# Log scaling for major phases
		if minutes in [14.0, 25.0]:
			MobaCommon.broadcast_event(f"The Towers have Hardened! Phase: {MobaCommon.GameTick.get_game_phase()}")

	def is_defender_present(self, scene):
		"""Phase 100: Oriented-Box Check for allied players."""
		lane_range = 16.0
		river_range = 6.0
		
		team = self.entity.getProperties().get("team", self.team)
		players = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, lane_range)
		
		inv_matrix = self.transf.getInverseMatrix()
		for p in players:
			if p.hasTag(team) and p.hasTag("player"):
				# Convert to local turret space
				local_p = inv_matrix * p.getTransform().worldPosition
				# abs(local_x) is side-to-side (river); local_z is ahead/behind (lane)
				# Standard Cave: Forward is Z.
				if abs(local_p.x) < river_range and 0 < local_p.z < lane_range:
					return True
		return False

	def take_damage(self, final_dmg, attacker):
		"""Phase 101: Simple HP subtraction. Plating logic is handled in MobaCommon.apply_damage."""
		current_hp = self.entity.getProperties().get("health", 0)
		self.entity.getProperties()["health"] = current_hp - final_dmg
		return final_dmg

	def grant_plate_gold(self, killer):
		"""Rewards ALL nearby enemy players for breaking a plate (Shared Gold logic)."""
		MobaCommon.play_sfx(self.entity, "SFX_Plate_Break", pitch_var=0.1)
		scene = self.entity.getScene()
		
		# Distribute 125G to enemies in range
		pos = self.transf.worldPosition
		team = self.entity.getProperties().get("team", self.team)
		enemy_team = "teamB" if team == "teamA" else "teamA"
		
		nearby = MobaCommon.get_entities_in_radius(scene, pos, 12.0)
		rewarded_count = 0
		for e in nearby:
			if e.hasTag(enemy_team) and e.hasTag("player"):
				pc = e.getPy("PlayerController")
				if pc:
					pc.leveling.gold += 125
					rewarded_count += 1
		
		msg = f"Tower Plate Secured! (+125G)" if rewarded_count > 0 else "Tower Plate Secured!"
		MobaCommon.broadcast_event(msg)
		
		# Feedback Visuals
		from UI import MobaUI
		MobaUI.spawn_fct(scene, pos + cave.Vector3(0, 5, 0), "+125G", cave.Vector4(1, 0.9, 0, 1))

	def on_death(self):
		killer = self.entity.getProperties().get("lastAttacker")
		
		# 1. Standard Killer Reward
		MobaCommon.RewardManager.distribute(self.entity, killer)
		
		# 2. Global Team Reward
		team = self.entity.getProperties().get("team", self.team)
		enemyTag = "teamB" if team == "teamA" else "teamA"
		players = MobaCommon.EntityRegistry.get_active("player")
		for p in players:
			if p.hasTag(enemyTag):
				pc = p.getPy("PlayerController")
				if pc:
					pc.leveling.gold += 250 # Global turret gold (bonus)
					pc.add_exp(150)
		
		# Optional: Spawn debris or trigger explosion VFX
		MobaCommon.spawn_vfx(self.entity.getScene(), MobaCommon.Templates.VFX_TURRET_EXP, self.transf.worldPosition)
		MobaCommon.cleanup_entity_state(self.entity)
		self.entity.kill()
