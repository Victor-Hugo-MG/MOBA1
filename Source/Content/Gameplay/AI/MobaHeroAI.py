import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon
from Core import MobaStates
from Data import BuildRegistry
import math
import random

class HeroAIComponent(cave.Component):
	"""Basic AI for bot-controlled heroes in ARAM."""
	team = "teamB"
	
	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		self.transf = self.entity.getTransform()
		self.character = self.entity.get("Character")
		
		# Safety: Pre-fetch animator
		self.animator = None
		mesh = self.entity.getChild("Mesh")
		if mesh:
			try: self.animator = mesh.get("Animation")
			except: pass
		
		# Phase 58: Role & Archetype Initialization
		self.role = "top"
		if self.pc and hasattr(self.pc, "heroData"):
			self.role = self.pc.heroData.get("role", "top")
		
		self.target = None
		self.state = "LANE" # LANE, COMBAT, RETREAT, RECALLING, JUNGLE, GANK
		self.state_timer = 0.0
		self.skill_timer = 0.0
		self.recall_check_timer = 0.0
		
		# Phase 60: Tactical & Anti-Exploit Initialization
		self.anchor_pos = self.transf.worldPosition
		self.state_latch_timer = 0.0
		self.last_hp = self.entity.getProperties().get("health", 100)
		self.turret_hit_count = 0
		self.dive_intent = False # Broad-casted for allies
		
		self.is_diving = False
		self.chase_timer = 0.0
		self.think_timer = random.uniform(0, 0.5) 
		self.think_interval = 0.5 
		
		# Stuck Detection (Professional Polish)
		self.last_pos = self.transf.worldPosition.copy()
		self.stuck_timer = 0
		self.unjam_timer = 0
		self.unjam_dir = cave.Vector3(0,0,0)
		
		# Phase 76: Jungle Route Logic
		self.jungle_route_index = 0
		# Standard path: Gromp -> Blue -> Wolves -> Raptors -> Red -> Krugs
		# (Generic camp names mapping to campID in MobaJungle)
		self.jungle_path = ["gromp", "blue", "wolves", "raptors", "red", "krugs"]
		self.camp_target_pos = None
		
		# Phase 126: Advanced Personalities
		# Assign a personality based on role or random choice
		self.personality = MobaCommon.AIPersonality.FARMER
		if self.role == "jungle": self.personality = MobaCommon.AIPersonality.ASSASSIN
		elif self.role == "support": self.personality = MobaCommon.AIPersonality.SUPPORTIVE
		else:
			self.personality = random.choice([MobaCommon.AIPersonality.BULLY, MobaCommon.AIPersonality.FARMER, MobaCommon.AIPersonality.TACTICIAN])
			
		# Phase 128: Difficulty
		self.difficulty = self.entity.getProperties().get("aiDifficulty", MobaCommon.AIDifficulty.NORMAL)
	def update(self):
		if not self.pc or self.pc.respawnTimer > 0 or MobaCommon.is_match_over:
			if MobaCommon.is_match_over:
				self.character.setWalkDirection(0, 0, 0)
			return 
			
		dt = cave.getDeltaTime()
		scene = self.entity.getScene()
		props = self.entity.getProperties()
		hp = props.get("health", 0)
		max_hp = max(1, props.get("maxHealth", 1))
		hp_pct = hp / max_hp
		
		# 1. Timers & Latching
		self.state_latch_timer = max(0, self.state_latch_timer - dt)
		self.think_timer -= dt
		
		# 2. Turret Hit Tracking (Heat Counter)
		in_turret = self.is_in_turret_range(scene)
		if in_turret and hp < self.last_hp:
			# If HP dropped by a significant amount (Turret shot vs Minion poke)
			if (self.last_hp - hp) > (max_hp * 0.05):
				self.turret_hit_count += 1
		elif not in_turret:
			self.turret_hit_count = 0
		self.last_hp = hp

		# 3. Throttled Strategic "Think" Loop (Respects Latch)
		if self.think_timer <= 0:
			self.think_timer = self.think_interval
			# Latch allows RETREAT or target-death to override
			can_think = self.state_latch_timer <= 0 or self.state == "LANE" or (self.target and not self.target.isActive())
			if can_think:
				old_state = self.state
				self.think_strategy(scene, hp_pct)
				if self.state != old_state:
					self.state_latch_timer = 2.0 # Commit to new state
					
			# Stuck Check (every 0.5s)
			if self.state not in ["RECALLING", "IDLE"]:
				dist_moved = (self.transf.worldPosition - self.last_pos).length()
				if dist_moved < 0.4: # Jammed
					self.unjam_timer = 1.0
					import random as _rand
					self.unjam_dir = cave.Vector3(_rand.uniform(-1, 1), 0, _rand.uniform(-1, 1)).normalized()
				self.last_pos = self.transf.worldPosition.copy()

		# 4. Per-Frame Safety Overrides (Priority)
		if self.handle_dodging(scene):
			return # Dodging overrides thinking/acting
			
		if in_turret:
			if not self.handle_tower_safety(scene, hp_pct):
				self.state = "RETREAT"
				self.state_latch_timer = 1.0 # Short latch for safety exit

		# 5. Per-Frame State Execution
		if self.state == "RETREAT":
			self.handle_retreat(scene)
		elif self.state == "RECALLING":
			self.character.setWalkDirection(0, 0, 0)
		elif self.state == "COMBAT":
			self.handle_combat(scene, dt)
		elif self.state == "JUNGLE":
			self.handle_jungle_loop(scene, dt)
		elif self.state == "GANK":
			self.handle_gank_execution(scene, dt)
		elif self.state == "FOLLOW":
			self.handle_follow(scene, dt)
		else: # LANE
			self.follow_lane(scene)
			self.anchor_pos = self.transf.worldPosition # Update anchor while in lane

	def handle_shopping_logic(self, scene):
		"""Phase 62: AI Strategic Itemization with Target-Focused Logic."""
		# 1. Performance Throttle: Only shop every 2.5 seconds at fountain
		if not hasattr(self, "_last_shop_time"): self._last_shop_time = 0
		if scene.getElapsedSceneTime() - self._last_shop_time < 2.5: return
		self._last_shop_time = scene.getElapsedSceneTime()

		# 2. Check if at fountain
		fountains = scene.getEntitiesWithTag(f"{self.team}_fountain")
		at_fountain = False
		for f in fountains:
			if (f.getTransform().worldPosition - self.transf.worldPosition).length() < 12.0:
				at_fountain = True
				break
		if not at_fountain or not self.pc: return

		# 3. Get Build Order (Core Items)
		build = BuildRegistry.get_recommended_build(self.pc.heroName)
		from Data import ItemRegistry
		
		# 4. Target-Focused Buying
		for target_name in build:
			# Phase 63: Evolution Check (Before buying new items)
			if "Hunter's Resolve" in self.pc.inventory:
				path = "AD"
				arch = self.get_archetype()
				if arch == "diver": path = "TANK"
				elif arch in ["burst", "caster"]: path = "AP"
				self.pc.inventory_mgr.evolve_jungle_item(path)
				continue
			
			item_data = ItemRegistry.ITEM_REGISTRY.get(target_name)
			if not item_data: continue
			
			# If we have gold for the whole thing, buy it!
			if self.pc.buy_item(target_name): 
				continue # Try next target in build

			# Otherwise, try to buy components we are missing
			recipe = item_data.get("recipe", [])
			for comp in recipe:
				# How many of this component do we currently have?
				owned_count = self.pc.inventory.count(comp)
				# How many does the recipe need?
				needed_count = recipe.count(comp)
				
				if owned_count < needed_count:
					if self.pc.buy_item(comp):
						# Bought a component! Stop to check next target/comp in next shop pulse
						return 
			
			# If we are here, we can't afford anything else for this target.
			return

	def handle_tower_safety(self, scene, hp_pct):
		"""Phase 60: Sophisticated Dynamic Aggro & Team-Sense logic."""
		if not self.target or not self.target.isActive(): return True
		
		arch = self.get_archetype()
		is_tank_type = arch == "diver"
		is_assassin = arch == "burst"
		game_time = scene.getElapsedSceneTime()
		level = self.pc.leveling.level if self.pc else 1
		is_late_game = game_time > 720 or level >= 13
		
		# --- GATED RULES ---
		# 1. Minion Push Rule
		if not self.is_wave_pushed(scene):
			# Exceptions for Late Game or Assassins
			can_solo_dive = False
			enemy_hp_pct = self.target.getProperties().get("health", 0) / self.target.getProperties().get("maxHealth", 1)
			
			if is_late_game and is_tank_type: can_solo_dive = True
			if is_assassin and enemy_hp_pct < 0.15: can_solo_dive = True # Assassin finishes off
			
			if not can_solo_dive: return False

		# 2. Early Game Feeding Protection
		if level < 4 and game_time < 240.0:
			return False # Hard gate for lvl 3

		# 3. Heat Check (3-Shot Rule)
		if self.turret_hit_count >= 3:
			# Tanks take more shots if allies are present
			if is_tank_type and self.is_ally_attacking_target(scene):
				if hp_pct < 0.3: return False # Exit at 30% HP
			else:
				return False

		# 4. Dynamic Aggro Math (Individual Survival)
		enemy_hp = self.target.getProperties().get("health", 0)
		turret_dmg = 150 # Est shot
		
		if self.is_being_targeted_by_turret(scene):
			# Squishy math
			if not is_tank_type:
				if enemy_hp > (self.pc.attackDamage * 2): # Hard-coded guess for now
					return False
			
			if (self.entity.getProperties().get("health", 0)) < turret_dmg:
				return False

		# 5. Numerical Disadvantage
		if self.get_nearby_enemy_count(scene) > 1:
			return False

		return True

	def is_in_turret_range(self, scene):
		enemy_team = "teamA" if self.team == "teamB" else "teamB"
		# Phase 70: Use EntityRegistry instead of getEntitiesWithTag
		for t in MobaCommon.EntityRegistry.get_team_entities(enemy_team, "turret"):
			if not t.isActive(): continue
			dist = (t.getTransform().worldPosition - self.transf.worldPosition).length()
			if dist < 12.0: # Turret aggro radius
				return True
		return False

	def get_best_offensive_cd(self):
		"""Returns the lowest remaining cooldown among Q, W, E, R."""
		if not self.pc: return 99
		cds = []
		for k in ["Q", "W", "E", "R"]:
			timer = self.pc.cooldowns.get(k)
			max_cd = self.pc.cooldownDurations.get(k, 0)
			rem = max(0, max_cd - timer.get()) if timer else 0
			cds.append(rem)
		return min(cds)

	def handle_follow(self, scene, dt):
		"""Phase 59: Ally-following for Late Game grouping."""
		if not hasattr(self, "alpha_leader") or not self.alpha_leader or not self.alpha_leader.isActive():
			self.state = "LANE"
			return
			
		leader_pos = self.alpha_leader.getTransform().worldPosition
		dist = (leader_pos - self.transf.worldPosition).length()
		
		if dist > 6.0:
			self.move_to(leader_pos)
		else:
			# Stay near but check for lane pushing
			self.follow_lane(scene)

	def think_strategy(self, scene, hp_pct):
		"""Phase 60: Tactical Thinking with Threat & Economic Awareness."""
		game_time = scene.getElapsedSceneTime()
		is_late_game = game_time > 720 or (self.pc and self.pc.leveling.level >= 11)
		danger_score = self.get_danger_score(scene)

		# A. Emergency Survival (Weighted by Personality)
		retreat_thresh = 0.15
		if self.personality == MobaCommon.AIPersonality.FARMER: retreat_thresh = 0.30
		elif self.personality == MobaCommon.AIPersonality.BULLY: retreat_thresh = 0.08
		
		if hp_pct < retreat_thresh: 
			self.state = "RETREAT"
			return

		# B. Economic / Resource Reset (Smart Basing)
		if self.check_economic_reset(scene, hp_pct, danger_score):
			self.state = "RETREAT"
			return

		# C. Late Game Grouping
		if is_late_game and self.state not in ["RETREAT", "RECALLING", "COMBAT"]:
			if self.find_alpha_leader(scene):
				self.state = "FOLLOW"
				return

		# D. Role-Based Prioritization
		if self.role == "jungle":
			v_gank = self.get_gank_value(scene)
			v_farm = 0.5
			if self.target and self.target.hasTag("monster"):
				t_hp = self.target.getProperties().get("health", 0) / self.target.getProperties().get("maxHealth", 1)
				if t_hp < 0.2: v_farm = 1.0 
				
			if v_gank > v_farm:
				self.state = "GANK"
			else:
				self.state = "JUNGLE"
		else:
			# Laners: Combat vs Lane vs Objective
			if self.find_enemy_hero(scene):
				# Personality-driven engagement
				nearby_enemies = self.get_nearby_enemy_count(scene)
				nearby_allies = self.get_nearby_ally_count(scene)
				
				is_brave = self.personality in [MobaCommon.AIPersonality.BULLY, MobaCommon.AIPersonality.ASSASSIN]
				is_cautious = self.personality == MobaCommon.AIPersonality.FARMER
				
				# Engage condition
				should_fight = (nearby_allies >= nearby_enemies) or (is_brave and hp_pct > 0.4)
				if is_cautious and nearby_enemies > 0: should_fight = False
				
				if should_fight:
					self.state = "COMBAT"
				else:
					self.state = "LANE"
			else:
				# Objective Check
				if self.check_objective_priority(scene) or self.personality == MobaCommon.AIPersonality.TACTICIAN:
					self.state = "COMBAT"
				else:
					self.state = "LANE"


	def get_danger_score(self, scene):
		"""Evaluates the risk of being dove or ganked."""
		# Phase 70: Use EntityRegistry
		enemyTag = "teamA" if self.team == "teamB" else "teamB"
		enemies = MobaCommon.EntityRegistry.get_team_entities(enemyTag, "player")
		
		# 1. Direct Threat (Enemies visible and nearby)
		nearby = [e for e in enemies if (e.getTransform().worldPosition - self.transf.worldPosition).length() < 25.0]
		if nearby: return 1.0
		
		# 2. Fog Threat (Enemies missing)
		# TODO: Integration with VisionManager for true missing-ping logic
		return 0.2 # Baseline caution

	def check_economic_reset(self, scene, hp_pct, danger):
		"""Determines if the bot should base for items or health."""
		gold = self.pc.leveling.gold if self.pc else 0
		mana_pct = (self.pc.mana / self.pc.maxMana) if self.pc else 1.0
		
		# Condition 1: High Danger while low resources
		if danger > 0.8 and (hp_pct < 0.3 or mana_pct < 0.1):
			return True
			
		# Condition 2: High Gold Opportunity (Enough for a major item)
		if gold >= 1300 and self.is_wave_pushed(scene):
			return True
			
		# Condition 3: Safe but Low (HP < 40%)
		if hp_pct < 0.4 and self.is_wave_pushed(scene):
			return True
			
		return False

	def is_wave_pushed(self, scene):
		"""Returns True if no enemy minions remain within 15 units."""
		enemy_team = "teamA" if self.team == "teamB" else "teamB"
		nearby_ents = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, 15.0)
		for e in nearby_ents:
			if e.hasTag("minion") and e.hasTag(enemy_team):
				return False
		return True

	def get_gank_value(self, scene):
		"""Phase 59: Dynamic gank weighting."""
		val = 0.0
		enemyTag = "teamA" if self.team == "teamB" else "teamB"
		# Phase 70: Use EntityRegistry
		enemies = MobaCommon.EntityRegistry.get_team_entities(enemyTag, "player")
		
		for e in enemies:
			if not MobaCommon.is_target_visible(self.entity, e): continue
			
			dist = (e.getTransform().worldPosition - self.transf.worldPosition).length()
			if dist > 35.0: continue # Too far
			
			e_hp = e.getProperties().get("health", 0) / e.getProperties().get("maxHealth", 1)
			
			# Score Components
			# 1. Killability (Higher if low HP)
			k_score = (1.0 - e_hp) * 1.5
			
			# 2. Overextension (Higher if far from tower)
			o_score = self.get_overextension_multiplier(scene, e)
			
			current_val = (k_score + o_score) / 2.0
			val = max(val, current_val)
			if val >= 0.8: self.target = e # Lock target if high value
			
		return val

	def get_overextension_multiplier(self, scene, enemy):
		# Improved safety: Get team from tags if property is missing
		enemy_team = enemy.getProperties().get("team")
		if not enemy_team:
			enemy_team = "teamA" if enemy.hasTag("teamA") else ("teamB" if enemy.hasTag("teamB") else None)
			
		if not enemy_team: return 1.0
		
		turrets = MobaCommon.EntityRegistry.get_team_entities(enemy_team, "turret")
		if not turrets: return 1.2 # Fully overextended if no turrets left
		
		closest_d = 999.0
		for t in turrets:
			if not t.isActive(): continue
			d = (t.getTransform().worldPosition - enemy.getTransform().worldPosition).length()
			closest_d = min(closest_d, d)
			
		if closest_d > 20.0: return 1.2
		if closest_d > 12.0: return 0.8
		return 0.2 # Safe under tower

	def find_alpha_leader(self, scene):
		"""Phase 59: Finds the best ally to follow in Late Game."""
		allies = [e for e in MobaCommon.EntityRegistry.get_team_entities(self.team, "player") if e != self.entity]
		if not allies: return False
		
		# Proximity check (Don't group if they are miles away)
		valid_leas = []
		for a in allies:
			dist = (a.getTransform().worldPosition - self.transf.worldPosition).length()
			if dist < 40.0:
				valid_leas.append(a)
		
		if not valid_leas: return False
		
		# Alpha is the Highest Level (or Player)
		valid_leas.sort(key=lambda x: x.getProperties().get("level", 1), reverse=True)
		self.alpha_leader = valid_leas[0]
		return True

	def check_objective_priority(self, scene):
		"""Checks if Drake or Baron should be prioritized."""
		objs = [e for e in scene.getEntitiesWithTag("monster") if e.isActive() and (e.hasTag("dragon") or e.hasTag("baron"))]
		for o in objs:
			# Priority if low health or allies are attacking
			o_hp = o.getProperties().get("health", 0) / o.getProperties().get("maxHealth", 1)
			dist = (o.getTransform().worldPosition - self.transf.worldPosition).length()
			if (o_hp < 0.5 and dist < 20.0) or dist < 8.0:
				self.target = o
				return True
		return False

	def find_enemy_hero(self, scene):
		"""Phase 60: Tactical target selection with squishy prioritization."""
		enemyTag = "teamA" if self.team == "teamB" else "teamB"
		# Phase 70: Use EntityRegistry
		enemies = MobaCommon.EntityRegistry.get_team_entities(enemyTag, "player")
		in_turret = self.is_in_turret_range(scene)
		
		best_e = None
		best_score = -999.0
		
		for e in enemies:
			if not MobaCommon.is_target_visible(self.entity, e): continue
			
			dist = (e.getTransform().worldPosition - self.transf.worldPosition).length()
			if dist > 25.0: continue # Target too far
			
			# Base Score = Proximity
			score = 10.0 - (dist / 2.5)
			
			# HP Score (Prioritize low HP)
			e_hp_pct = e.getProperties().get("health", 0) / e.getProperties().get("maxHealth", 1)
			score += (1.0 - e_hp_pct) * 15.0
			
			# Squishy/Archetype Score (If under tower, focus paper enemies)
			if in_turret:
				e_pc = e.getPy("PlayerController")
				if e_pc and hasattr(e_pc, "heroData"):
					e_role = e_pc.heroData.get("role", "top")
					if e_role in ["mid", "adc", "support"]:
						score += 20.0 # High priority on paper targets
						
			if score > best_score:
				best_score = score
				best_e = e
		
		self.target = best_e
		return best_e is not None

	def move_to(self, target_pos):
		# Optimization (Phase 69): Skip calculation if target_pos is essentially current pos
		diff = target_pos - self.transf.worldPosition
		if (diff.x * diff.x + diff.y * diff.y + diff.z * diff.z) < 0.25: # 0.5m threshold
			# Phase 70: Fixed API misuse — CharacterComponent has no getLinearVelocity()
			if self.character:
				self.character.setWalkDirection(0, 0, 0)
			return

		dir = diff.normalized()
		
		# --- Professional Polish: Unjam Jitter ---
		if self.unjam_timer > 0:
			self.unjam_timer -= cave.getDeltaTime()
			# Blend target direction with unjam jitter (60/40 split for heroes)
			dir = (dir * 0.6 + self.unjam_dir * 0.4).normalized()

		speed = self.entity.getProperties().get("moveSpeed", 335) * MobaCommon.SPEED_RATIO
		tr = self.entity.getProperties().get("turnRate", 540)
		dt = cave.getDeltaTime()
		MobaCommon.rotate_towards(self.transf, dir, dt, tr)
		
		if self.character:
			dt = cave.getDeltaTime()
			self.character.setWalkDirection(0, 0, speed * dt)
			
		if self.animator:
			try: self.animator.playByName("Walk", 0.2, loop=True)
			except: pass

	def move_to_base(self, scene):
		# Move to team fountain
		team = self.team
		fountain = MobaCommon.EntityRegistry.get(team + "_fountain")
		if fountain:
			self.move_to(fountain[0].getTransform().worldPosition)

	def handle_retreat(self, scene):
		"""Phase 59: Strategic Survival & Reset logic."""
		hp_pct = self.entity.getProperties().get("health", 0) / self.entity.getProperties().get("maxHealth", 1)
		team = self.team
		fountains = MobaCommon.EntityRegistry.get(team + "_fountain")
		fountain = fountains[0] if fountains else None
		
		# 1. Survival Check: If HP is full, reset to lane/jungle
		if hp_pct > 0.95:
			if self.role == "jungle":
				self.state = "JUNGLE"
			else:
				self.state = "LANE"
			return

		# 2. Path to Fountain or Safe Spot
		if fountain:
			dist = (fountain.getTransform().worldPosition - self.transf.worldPosition).length()
			if dist < 8.0:
				# We are safe in base
				self.character.setWalkDirection(0, 0, 0)
				self.handle_shopping_logic(scene) # Phase 62: Shop while healing
				return
				
			target_pos = fountain.getTransform().worldPosition
			self.move_to(target_pos)
		
		# 3. Emergency Recall (If out of tower range and HP low)
		if not self.is_in_turret_range(scene) and hp_pct < 0.3:
			# Check for nearby enemies
			enemies = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, 12.0)
			has_threat = any(MobaCommon.get_entity_team(e) != self.team and e.isActive() for e in enemies)
			
			if not has_threat and not cave.getGlobalDict().get("IsARAM"):
				self.pc.executeRecall()
				self.state = "RECALLING"

	def follow_lane(self, scene):
		# Phase 34: Prioritize Turrets > Heroes in lane state
		enemy_team = "teamA" if self.team == "teamB" else "teamB"
		turrets = MobaCommon.EntityRegistry.get_team_entities(enemy_team, "turret")
		
		# Find the closest turret to target
		target_turret = None
		best_dist = 40.0 # Aggro range for towers
		for t in turrets:
			d = (t.getTransform().worldPosition - self.transf.worldPosition).length()
			if d < best_dist:
				best_dist = d
				target_turret = t
				
		if target_turret:
			dist = (target_turret.getTransform().worldPosition - self.transf.worldPosition).length()
			if dist <= 8.0: # Basic attack range for most bots
				self.character.setWalkDirection(0, 0, 0)
				# TODO: Standard basic attack logic in PC
			else:
				self.move_to(target_turret.getTransform().worldPosition)
			return

		# Follow allied minions or push toward enemy base
		allies = MobaCommon.EntityRegistry.get_team_entities(self.team, "minion")
		if allies:
			# Stay slightly behind minions
			lead_minion = allies[0]
			self.move_to(lead_minion.getTransform().worldPosition)
		else:
			nexus = MobaCommon.EntityRegistry.get(enemy_team + "_nexus")
			if nexus:
				self.move_to(nexus[0].getTransform().worldPosition)

	def handle_combat(self, scene, dt):
		if not self.target or not self.target.isActive():
			self.state = "LANE"
			self.chase_timer = 0.0
			self.dive_intent = False
			return
		
		dist = (self.target.getTransform().worldPosition - self.transf.worldPosition).length()
		atk_range = self.entity.getProperties().get("attackRange", 5.0)
		arch = self.get_archetype()
		
		# --- SEQUENCED DIVE (Phase 60) ---
		if self.is_in_turret_range(scene):
			self.dive_intent = True
			if not (arch in ["diver", "burst"]): # Non-tanks wait for lead
				if not self.is_any_ally_taking_turret_aggro(scene):
					# Wait at edge
					self.move_to(self.transf.worldPosition) # Hold position
					return
		else:
			self.dive_intent = False

		# --- Anti-Overchase & Leash ---
		dist_from_anchor = (self.transf.worldPosition - self.anchor_pos).length()
		if dist_from_anchor > 28.0: # Leash limit
			self.state = "RETREAT"
			self.target = None
			return

		if dist > atk_range + 2.0:
			self.chase_timer += dt
			if self.chase_timer > 6.0:
				self.state = "LANE"
				self.chase_timer = 0.0
				return
		else:
			self.chase_timer = 0.0
		
		# Archetype-Specific Positioning
		target_dist = atk_range
		if arch == "caster": target_dist = atk_range * 0.8 
		elif arch == "diver": target_dist = 2.5 
		
		# Movement vs Attack
		if dist > target_dist + 1.0:
			self.move_to(self.target.getTransform().worldPosition)
		elif dist < target_dist - 1.0 and arch == "caster":
			dir_away = (self.transf.worldPosition - self.target.getTransform().worldPosition).normalized()
			self.move_to(self.transf.worldPosition + dir_away * 5.0)
		else:
			self.character.setWalkDirection(0, 0, 0)
			self.skill_timer -= dt
			if self.skill_timer <= 0:
				self.skill_timer = 1.8 
				self.handle_combo()

	def handle_combo(self):
		"""Executes an ability combo sequence based on archetype and difficulty."""
		if not self.pc: return
		arch = self.get_archetype()
		
		# Phase 128: Virtual Cursor for AI Aiming
		if self.difficulty == MobaCommon.AIDifficulty.PRO and self.target:
			aim_pos = self.predict_target_pos(self.target)
		elif self.target:
			aim_pos = self.target.getTransform().worldPosition
		else:
			aim_pos = self.transf.worldPosition
			
		self.pc.virtualCursorPos = aim_pos
		
		# Flash Offensive (PRO Only)
		if self.difficulty == MobaCommon.AIDifficulty.PRO and self.target:
			dist = (self.target.getTransform().worldPosition - self.transf.worldPosition).length()
			t_hp = self.target.getProperties().get("health", 0) / self.target.getProperties().get("maxHealth", 1)
			if dist > 8.0 and dist < 13.0 and t_hp < 0.2:
				# Flash for the kill!
				self.pc.tryCast("D") # Assuming Flash is on D
		
		# Priority: R > Q > W > E (if off cooldown)
		if arch == "burst":
			# Assassins: R > E > Q > W
			for key in ["R", "E", "Q", "W"]:
				if self.pc.tryCast(key): return
		else:
			# Default: Q > W > E > R
			for key in ["Q", "W", "E", "R"]:
				if self.pc.tryCast(key): return
		
		# Fallback: Basic Attack via input buffer
		if self.target:
			self.pc.inputBuffer = ("ATTACK", self.target)

	def predict_target_pos(self, target, proj_speed=22.0):
		"""Linear prediction for skillshots."""
		t_char = target.get("Character")
		if not t_char: return target.getTransform().worldPosition
		
		vel = t_char.getWalkDirection() * 6.5 # Approx speed
		dist = (target.getTransform().worldPosition - self.transf.worldPosition).length()
		travel_time = dist / proj_speed
		return target.getTransform().worldPosition + vel * travel_time

	def handle_dodging(self, scene):
		"""PRO bots scan for and avoid skillshots."""
		if self.difficulty != MobaCommon.AIDifficulty.PRO: return False
		
		# Simple proxy: scan for entities with 'projectile' tag nearby
		projs = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, 6.0)
		for p in projs:
			if p.hasTag("projectile"):
				# Move perpendicular to projectile path
				p_trans = p.getTransform()
				p_dir = p_trans.getForwardVector(True)  # Cave API: getForwardVector(world=True)
				perp = cave.Vector3(-p_dir.z, 0, p_dir.x)
				self.character.setWalkDirection(perp.x * 0.8, 0, perp.z * 0.8)  # World-space dodge
				return True
		return False

	def is_any_ally_taking_turret_aggro(self, scene):
		allies = [e for e in MobaCommon.EntityRegistry.get_team_entities(self.team, "player") if e != self.entity]
		for a in allies:
			if self.is_being_targeted_by_turret(scene, a):
				return True
		return False

	def is_being_targeted_by_turret(self, scene, subject=None):
		# Cave Engine implementation: Turrets target the first entity in range
		if subject is None: subject = self.entity
		enemy_team = "teamA" if self.team == "teamB" else "teamB"
		turrets = MobaCommon.EntityRegistry.get_team_entities(enemy_team, "turret")
		for t in turrets:
			# Mocking aggro detection via proximity and team-priority
			dist = (t.getTransform().worldPosition - subject.getTransform().worldPosition).length()
			if dist < 12.0: return True
		return False

	def is_ally_attacking_target(self, scene):
		allies = [e for e in MobaCommon.EntityRegistry.get_team_entities(self.team, "player") if e != self.entity]
		for a in allies:
			dist = (a.getTransform().worldPosition - self.target.getTransform().worldPosition).length()
			if dist < 10.0: return True
		return False

	def get_nearby_enemy_count(self, scene):
		enemyTag = "teamA" if self.team == "teamB" else "teamB"
		# Phase 70: Use EntityRegistry
		enemies = MobaCommon.EntityRegistry.get_team_entities(enemyTag, "player")
		return len([e for e in enemies if (e.getTransform().worldPosition - self.transf.worldPosition).length() < 20.0])

	def get_nearby_ally_count(self, scene):
		# Phase 70: Use EntityRegistry
		allies = MobaCommon.EntityRegistry.get_team_entities(self.team, "player")
		return len([e for e in allies if (e.getTransform().worldPosition - self.transf.worldPosition).length() < 20.0])

	def get_archetype(self):
		"""Phase 58: Map roles and hero names to tactical archetypes."""
		if not self.pc or not hasattr(self.pc, "heroData"): return "diver"
		
		# 1. Direct Role Mapping
		if self.role == "adc" or self.role == "mid": return "caster"
		if self.role == "support": return "support"
		
		# 2. Hero Name Overrides (Specialized logic)
		name = self.pc.heroName
		if name in ["Borum", "Ignis", "Ragnar", "Krix"]: return "diver"
		if name in ["Zora", "Umbra"]: return "burst"
		
		return "diver"

	def find_gank_opportunity(self, scene):
		"""Phase 58: Search for overextended or vulnerable enemies (Throttled)."""
		# Phase 70: Use EntityRegistry
		enemyTag = "teamA" if self.team == "teamB" else "teamB"
		enemies = MobaCommon.EntityRegistry.get_team_entities(enemyTag, "player")
		
		for e in enemies:
			if not MobaCommon.is_target_visible(self.entity, e): continue
			
			dist_to_enemy = (e.getTransform().worldPosition - self.transf.worldPosition).length()
			if dist_to_enemy > 25.0: continue # Too far to gank
			
			hp_pct = e.getProperties().get("health", 0) / e.getProperties().get("maxHealth", 1)
			
			# Gank Trigger 1: Enemy is low HP
			if hp_pct < 0.4:
				self.target = e
				return True
			
			# Gank Trigger 2: Enemy is overextended (Distance from their turret)
			# FIX: Use EntityRegistry instead of raw getEntitiesWithTag
			turrets = MobaCommon.EntityRegistry.get_team_entities(enemyTag, "turret")
			closest_turret_dist = 999
			for t in turrets:
				if t.isActive():
					d = (t.getTransform().worldPosition - e.getTransform().worldPosition).length()
					closest_turret_dist = min(closest_turret_dist, d)
			
			if closest_turret_dist > 15.0: # 15 units from tower is overextended
				self.target = e
				return True
				
		return False

	def handle_jungle_loop(self, scene, dt):
		"""Moves through a systemic clear route and fights camps."""
		# 1. Combat check (if already fighting)
		if self.target and self.target.isActive() and self.target.hasTag("monster"):
			dist = (self.target.getTransform().worldPosition - self.transf.worldPosition).length()
			if dist > 3.0:
				self.move_to(self.target.getTransform().worldPosition)
			else:
				self.character.setWalkDirection(0, 0, 0)
				self.skill_timer -= dt
				if self.skill_timer <= 0:
					self.skill_timer = 1.2
					self.pc.tryCast("Q")
					# Basic kiting: step back slightly between autos
					self.unjam_timer = 0.3
					self.unjam_dir = (self.transf.worldPosition - self.target.getTransform().worldPosition).normalized()
			return

		# 2. Sequence Pathing
		camp_name = self.jungle_path[self.jungle_route_index % len(self.jungle_path)]
		target_camp_id = f"{self.team}_{camp_name}"
		
		# Find the monster(s) belonging to this camp
		monsters = []
		for e in MobaCommon.EntityRegistry.get("monster"):
			if not e.isActive(): continue
			j_comp = e.getPy("JungleMonsterComponent")
			if j_comp and j_comp.campID == target_camp_id:
				monsters.append(e)
		
		if monsters:
			# Camp is alive, go there
			self.target = monsters[0]
			self.move_to(monsters[0].getTransform().worldPosition)
		else:
			# Camp is dead/missing, move to next!
			self.jungle_route_index += 1
			# Safety break to avoid infinite loops if all camps dead
			if self.jungle_route_index > 20: 
				self.state = "LANE"
				self.jungle_route_index = 0

	def handle_gank_execution(self, scene, dt):
		"""Moves toward and engages the gank target."""
		if not self.target or not self.target.isActive():
			self.state = "JUNGLE"
			return
			
		dist = (self.target.getTransform().worldPosition - self.transf.worldPosition).length()
		if dist < 8.0:
			self.state = "COMBAT" # Close enough to enter combat logic
		else:
			self.move_to(self.target.getTransform().worldPosition)
