import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Static Game State
is_match_over = False
SPEED_RATIO = 1.0 / 56.6 # Standard MOBA-to-World-Units ratio
GOLD_XP_SPLIT_PERCENT = 0.5 # Phase 42: Centralized reward constant
_PROJECTILE_POOLS = {} # {template_name: EntityPool}

# --- Phase 105: Global Objective Tracking ---
class GlobalObjectiveManager:
	"""Phase 105: Tracks global buff stacks and active neutral objective respawns."""
	dragon_stacks = {"teamA": 0, "teamB": 0}
	respawn_timers = {} # { "SPIRE_AMPLIFIED": time_float, ... }
	
	@staticmethod
	def start_respawn(obj_id, delay):
		now = GameTick.get_time_minutes() * 60.0
		GlobalObjectiveManager.respawn_timers[obj_id] = now + delay
		
	@staticmethod
	def get_timer(obj_id):
		now = GameTick.get_time_minutes() * 60.0
		rem = GlobalObjectiveManager.respawn_timers.get(obj_id, 0) - now
		return max(0, rem)
	baron_active = {"teamA": False, "teamB": False}
	

	@staticmethod
	def add_dragon(team):
		GlobalObjectiveManager.dragon_stacks[team] += 1
		broadcast_event(f"{team.upper()} has slain the Dragon! (Stacks: {GlobalObjectiveManager.dragon_stacks[team]})")

	@staticmethod
	def get_dragon_mult(team, stat_type):
		"""Returns the multiplier based on number of dragon kills."""
		stacks = GlobalObjectiveManager.dragon_stacks.get(team, 0)
		if stat_type == "ADAP": return 1.0 + (stacks * 0.04) # 4% per stack
		if stat_type == "RESIST": return 1.0 + (stacks * 0.05) # 5% per stack
		return 1.0
		
	@staticmethod
	def reset():
		GlobalObjectiveManager.dragon_stacks = {"teamA": 0, "teamB": 0}
		GlobalObjectiveManager.baron_active = {"teamA": False, "teamB": False}

def dist_to_segment(p, a, b):
	"""Returns the shortest distance between point p and line segment ab."""
	ap = p - a
	ab = b - a
	t = max(0, min(1, ap.dot(ab) / ab.dot(ab)))
	projection = a + ab * t
	return (p - projection).length()

def spawn_delayed_aoe(scene, pos, radius, damage, delay=1.0, vfx="VFX_Circle_Warning", attacker=None):
	"""Spawns an AOE that deals damage after a delay."""
	warning = scene.addFromTemplate(vfx, pos)
	if warning:
		warning.getTransform().setScale(radius, 1.0, radius)
		warning.scheduleKill(delay + 0.5)
	
	import cave
	# We use a SceneTimer from the attacker if provided, or global
	def trigger():
		apply_circular_aoe(pos, radius, damage, DamageType.MAGIC, attacker=attacker)
		spawn_vfx(scene, "VFX_Impact_Standard", pos)
	
	# Since we don't have a global task scheduler in the proto, 
	# we usually use a LifetimeComponent with on_kill callback or similar.
	# For now, we'll assume the engine handles it via persistent VFX logic in specific templates.
	pass

class VisionManager:
	"""Phase 39/69/70: Caches allied vision data. Uses EntityRegistry. Throttled."""
	_cache = {} # {team: [{"pos": Vector3, "range": float, "brush": id, "true_sight": bool}]}
	_last_tick = -1
	_throttle_ticks = 4 # Update every 4 ticks (~7.5 FPS)

	@staticmethod
	def update(scene):
		now = GameTick._current_tick
		if now - VisionManager._last_tick < VisionManager._throttle_ticks: return
		VisionManager._last_tick = now
		VisionManager._cache = {"teamA": [], "teamB": []}
		
		# Phase 70: Use EntityRegistry instead of per-tag getEntitiesWithTag
		for tag in ["player", "minion", "turret", "ward"]:
			for e in EntityRegistry.get(tag):
				if not e.isActive(): continue
				props = e.getProperties()
				team = get_entity_team(e)
				if team not in VisionManager._cache: continue
				VisionManager._cache[team].append({
					"pos": e.getTransform().worldPosition,
					"range": props.get("visionRange", 15.0),
					"brush": props.get("in_brush_id"),
					"true_sight": props.get("hasTrueSight", False) or e.hasTag("turret") or e.hasTag("ward")
				})

	@staticmethod
	def is_in_river(scene, pos):
		"""Returns True if position is over a 'river' tagged floor."""
		ray_start = pos + cave.Vector3(0, 5.0, 0)
		ray_end = pos + cave.Vector3(0, -5.0, 0)
		hits = scene.rayCastAll(ray_start, ray_end)
		for h in hits:
			if h.entity.hasTag("river") or h.entity.hasTag("water"):
				return True
		return False

	@staticmethod
	def get_allied_vision(team):
		return VisionManager._cache.get(team, [])

	@staticmethod
	def reset():
		VisionManager._cache = {}
		VisionManager._last_tick = -1

class MatchStatsManager:
	"""Phase 38: Centralized tracking for session performance."""
	stats = {} # {uid: {"kills":0, "deaths":0, "assists":0, "cs":0, "gold":0, "damage":0, "damage_taken":0, "healing":0, "items":[], "level": 1}}
	vision_cache = {} # {uid: last_known_stats_dict}
	start_time = 0.0

	@staticmethod
	def init(scene):
		# Phase 70: Initialization Guard to prevent redundant wipes from multiple actors
		if hasattr(MatchStatsManager, "_initialized_frame") and MatchStatsManager._initialized_frame == GameTick._current_tick:
			return
		MatchStatsManager._initialized_frame = GameTick._current_tick
		MatchStatsManager.stats = {}
		MatchStatsManager.vision_cache = {}
		MatchStatsManager.start_time = scene.getElapsedSceneTime()

	@staticmethod
	def _get_stats(uid):
		if uid not in MatchStatsManager.stats:
			MatchStatsManager.stats[uid] = {
				"kills":0, "deaths":0, "assists":0, "cs":0, "gold":0, 
				"damage":0, "damage_taken":0, "healing":0, "items":[], "level": 1,
				"visionScore": 0, "objectiveDamage": 0
			}
		return MatchStatsManager.stats[uid]

	@staticmethod
	def track_damage(attacker_uid, amount):
		s = MatchStatsManager._get_stats(attacker_uid)
		s["damage"] += amount

	@staticmethod
	def track_damage_taken(victim_uid, amount):
		s = MatchStatsManager._get_stats(victim_uid)
		s["damage_taken"] += amount

	@staticmethod
	def track_healing(uid, amount):
		s = MatchStatsManager._get_stats(uid)
		s["healing"] += amount

	@staticmethod
	def track_kill(killer_uid):
		"""Phase 132: Tracks kills with multi-kill and streak detection."""
		s = MatchStatsManager._get_stats(killer_uid)
		s["kills"] += 1
		
		# 1. Multi-kill Detection (10s window)
		now = cave.getScene().getElapsedSceneTime() if cave.getScene() else time.time()
		last_kill_time = s.get("_last_kill_time", 0.0)
		multi = s.get("multi_kill_count", 0)
		
		if now - last_kill_time < 10.0:
			multi += 1
		else:
			multi = 1
			
		s["_last_kill_time"] = now
		s["multi_kill_count"] = multi
		
		# 2. Streak Detection
		s["current_streak"] = s.get("current_streak", 0) + 1
		
		return {"multi": multi, "streak": s["current_streak"]}

	@staticmethod
	def track_death(victim_uid):
		s = MatchStatsManager._get_stats(victim_uid)
		s["deaths"] += 1
		# Reset streaks on death
		s["current_streak"] = 0
		s["multi_kill_count"] = 0

	@staticmethod
	def track_gold(uid, amount):
		s = MatchStatsManager._get_stats(uid)
		s["gold"] += amount

	@staticmethod
	def track_cs(uid):
		s = MatchStatsManager._get_stats(uid)
		s["cs"] += 1
		
	@staticmethod
	def track_vision(uid, amount=1):
		s = MatchStatsManager._get_stats(uid)
		s["visionScore"] += amount
		
	@staticmethod
	def track_objective_damage(uid, amount):
		s = MatchStatsManager._get_stats(uid)
		s["objectiveDamage"] += amount

	@staticmethod
	def track_items(uid, items):
		s = MatchStatsManager._get_stats(uid)
		s["items"] = items

	@staticmethod
	def track_level(uid, level):
		s = MatchStatsManager._get_stats(uid)
		s["level"] = level

	@staticmethod
	def update_vision_snapshot(uid, current_stats):
		"""Phase 56: Snapshots current stats for the scoreboard vision cache."""
		# Deep copy items list to prevent reference issues
		snapshot = current_stats.copy()
		snapshot["items"] = list(current_stats.get("items", []))
		MatchStatsManager.vision_cache[uid] = snapshot

	@staticmethod
	def snapshot_hero(entity):
		"""Phase 56: Systemic stat capture for both live and vision-locked tracking."""
		if not entity or not entity.isActive(): return
		
		pc = entity.getPy("PlayerController")
		if not pc: return
		
		uid = entity.name
		stats = MatchStatsManager._get_stats(uid)
		
		# 1. Update Live Stats
		stats["level"] = pc.leveling.level
		stats["kills"] = pc.leveling.kills
		stats["deaths"] = pc.leveling.deaths
		stats["assists"] = pc.leveling.assists
		stats["items"] = list(pc.inventory_mgr.items)
		
		# 2. Update Vision Cache if applicable (Player's team can see)
		# Note: We assume the local player is always on teamA for vision checks
		# In a real setup, we'd check against the 'local_player' variable
		if entity.hasTag("teamA") or is_target_visible(cave.getScene().get("Player_Root") if cave.getScene() else None, entity):
			MatchStatsManager.update_vision_snapshot(uid, stats)

	@staticmethod
	def get_summary(uid):
		return MatchStatsManager._get_stats(uid)

	@staticmethod
	def get_all_stats():
		"""Returns all tracked stats for end-game summary."""
		return MatchStatsManager.stats

class GameTick:
	"""Static framework for deterministic logic synchronization (Phase 18)."""
	_tick_rate = 30.0 # 30Hz Logic
	_tick_timer = 0.0
	_current_tick = 0
	_callbacks = []
	_hit_stop_timer = 0.0
	_time_scale = 1.0  # Custom time multiplier (Cave Engine has no setTimeScale)

	@staticmethod
	def update(dt, scene=None):
		GameTick._tick_timer += dt
		while GameTick._tick_timer >= (1.0 / GameTick._tick_rate):
			GameTick._tick_timer -= (1.0 / GameTick._tick_rate)
			GameTick._current_tick += 1
			# Phase 70: Update EntityRegistry at tick boundary
			if scene:
				EntityRegistry.tick(scene)
			for cb in GameTick._callbacks:
				cb()
		
		# Phase 127: Hit-Stop Reset logic
		# NOTE: cave.setTimeScale() does not exist in Cave Engine API.
		# Hit-stop is implemented via a custom time multiplier instead.
		if GameTick._hit_stop_timer > 0:
			GameTick._hit_stop_timer -= dt
			if GameTick._hit_stop_timer <= 0:
				GameTick._time_scale = 1.0

	@staticmethod
	def is_tick_frame():
		"""Returns True if the current frame falls within a logic tick boundary."""
		return GameTick._tick_timer < (1.0 / GameTick._tick_rate)

	@staticmethod
	def get_scaled_dt():
		"""Returns delta time adjusted by the custom hit-stop time scale."""
		return cave.getDeltaTime() * GameTick._time_scale

	@staticmethod
	def trigger_hit_stop(duration):
		"""Phase 127: Brief time freeze for impact feel.
		Uses custom time multiplier since Cave Engine has no setTimeScale()."""
		GameTick._time_scale = 0.01  # Near freeze
		GameTick._hit_stop_timer = duration

	@staticmethod
	def get_time_minutes():
		"""Returns the current elapsed game time in minutes."""
		return GameTick._current_tick / (GameTick._tick_rate * 60.0)

	@staticmethod
	def get_game_phase():
		"""Phase 77: Returns EARLY (0-14), MID (14-25), or LATE (25+)."""
		mins = GameTick.get_time_minutes()
		if mins < 14.0: return "EARLY"
		if mins < 25.0: return "MID"
		return "LATE"

	@staticmethod
	def get_temporal_scaling():
		"""Phase 31/77: Returns a multiplier for NPC growth. 
		Early: 1.0 + 5%/min. Late (25+): 1.0 + 8%/min (Accelerated)."""
		mins = GameTick.get_time_minutes()
		if mins < 25.0:
			return 1.0 + (mins * 0.05)
		else:
			# Accelerated curve for Late Game push
			return 1.0 + (25.0 * 0.05) + ((mins - 25.0) * 0.10)

	@staticmethod
	def subscribe(callback):
		if callback not in GameTick._callbacks:
			GameTick._callbacks.append(callback)
			
	@staticmethod
	def unsubscribe(callback):
		if callback in GameTick._callbacks:
			GameTick._callbacks.remove(callback)

	@staticmethod
	def reset():
		"""Phase 23: Complete reset for scene transitions to prevent callback leaks."""
		GameTick._callbacks = []
		GameTick._tick_timer = 0.0
		GameTick._current_tick = 0
		GameTick._hit_stop_timer = 0.0
		GameTick._time_scale = 1.0
		
		# Phase 82: Match Lifecycle Reset
		global is_match_over
		is_match_over = False
		
		# Phase 36/39/70: Static Manager Cleanup
		stop_managed_ambience()
		VisionManager.reset()
		EntityRegistry.reset()
		SpatialGrid.reset()
		InhibitorRegistry.reset()

# ──────────────────────────────────────────────
# Phase 70: Centralized Entity Registry & Spatial Grid
# Replaces scattered getEntitiesWithTag() calls
# ──────────────────────────────────────────────

class EntityRegistry:
	"""Phase 70: Updated once per GameTick. All queries read from cache.
	Replaces O(N) getEntitiesWithTag() calls with O(1) dict lookups."""
	_data = {}        # {tag: [entity, ...]}
	_last_tick = -1
	_tracked_tags = ["player", "minion", "monster", "turret", "inhibitor", "nexus", "ward",
	                  "teamA", "teamB", "neutral", "teamA_ward", "teamB_ward",
	                  "teamA_fountain", "teamB_fountain", "dragon", "baron",
	                  "teamA_nexus", "teamB_nexus", "lane_node", "JungleManager"]

	@staticmethod
	def tick(scene):
		"""Call once per GameTick (30Hz). Rebuilds tag cache."""
		if GameTick._current_tick == EntityRegistry._last_tick:
			return
		EntityRegistry._last_tick = GameTick._current_tick
		EntityRegistry._data.clear()
		
		# Single pass: query each tracked tag once
		for tag in EntityRegistry._tracked_tags:
			EntityRegistry._data[tag] = scene.getEntitiesWithTag(tag)
		
		# Also update SpatialGrid
		SpatialGrid.rebuild()

	@staticmethod
	def get(tag):
		"""Returns cached entity list for a tag. O(1)."""
		return EntityRegistry._data.get(tag, [])

	@staticmethod
	def get_active(tag):
		"""Returns only active entities for a tag."""
		return [e for e in EntityRegistry._data.get(tag, []) if e.isActive()]

	@staticmethod
	def get_team_entities(team, *required_tags):
		"""Returns entities that belong to a team AND have all required tags."""
		results = []
		for e in EntityRegistry.get(team):
			if not e.isActive(): continue
			if all(e.hasTag(t) for t in required_tags):
				results.append(e)
		return results

	@staticmethod
	def reset():
		EntityRegistry._data.clear()
		EntityRegistry._last_tick = -1

class InhibitorRegistry:
	"""Phase 77: Global state for inhibitors.
	_status: {(team, laneID): destroyed_until_timestamp}
	"""
	_status = {}

	@staticmethod
	def set_destroyed(team, lane_id, respawn_time):
		InhibitorRegistry._status[(team, lane_id)] = respawn_time

	@staticmethod
	def is_down(team, lane_id, current_time):
		# If team/lane is in registry and ready_at > current_time, it's DOWN
		limit = InhibitorRegistry._status.get((team, lane_id), 0)
		return limit > current_time

	@staticmethod
	def reset():
		InhibitorRegistry._status = {}

class RuneManager:
	"""Phase 102: Manages the active keystone rune for a PlayerController."""
	def __init__(self, pc, rune_id):
		self.pc = pc
		self.rune_id = rune_id
		self.stacks = 0
		self.cooldown = 0.0
		self.proc_ready = True
		
	def update(self, dt):
		"""Tick cooldown."""
		if self.cooldown > 0:
			self.cooldown -= dt
			if self.cooldown <= 0:
				self.proc_ready = True
				
	def on_hit(self, target, is_ability=False):
		"""Called when the owner damages a target."""
		if not self.proc_ready:
			return
			
		if self.rune_id == "LETHAL_TEMPO":
			self.stacks = min(6, self.stacks + 1)
		elif self.rune_id == "CONQUEROR":
			self.stacks = min(12, self.stacks + (2 if is_ability else 1))
			if self.stacks >= 12:
				# Heal 8% of damage dealt
				self.pc.bonusAD += 2.0  # Minor AD per proc
		elif self.rune_id == "ELECTROCUTE":
			self.stacks += 1
			if self.stacks >= 3 and self.proc_ready:
				# Proc burst damage
				bonus_dmg = 30 + (self.pc.level * 8) + (self.pc.ap * 0.25)
				apply_damage(target, bonus_dmg, DamageType.MAGIC, attacker=self.pc.entity)
				self.stacks = 0
				self.proc_ready = False
				self.cooldown = 25.0
		elif self.rune_id == "GRASP_OF_THE_UNDYING":
			self.stacks += 1
			if self.stacks >= 4 and self.proc_ready:
				heal_amt = self.pc.maxHP * 0.03
				apply_heal(self.pc.entity, heal_amt)
				self.stacks = 0
				self.proc_ready = False
				self.cooldown = 4.0

	def reset_stacks(self):
		"""Reset stacks (e.g. out of combat)."""
		self.stacks = 0


class SpatialGrid:
	"""Phase 70: O(1) spatial queries via cell-based hashing.
	Updated once per GameTick via EntityRegistry."""
	_cell_size = 10.0
	_grid = {}  # {(cx, cz): [entity, ...]}
	_TRACKED_TAGS = ["player", "minion", "monster", "turret", "inhibitor", "nexus", "ward"]

	@staticmethod
	def _key(pos):
		return (int(pos.x // SpatialGrid._cell_size), int(pos.z // SpatialGrid._cell_size))

	@staticmethod
	def rebuild():
		"""Rebuild grid from EntityRegistry data. Called by EntityRegistry.tick()."""
		SpatialGrid._grid.clear()
		seen = set()  # Avoid duplicates across tags
		
		for tag in SpatialGrid._TRACKED_TAGS:
			for e in EntityRegistry.get(tag):
				uid = id(e) # Use Python id for uniqueness
				if uid in seen or not e.isActive():
					continue
				seen.add(uid)
				k = SpatialGrid._key(e.getTransform().worldPosition)
				if k not in SpatialGrid._grid:
					SpatialGrid._grid[k] = []
				SpatialGrid._grid[k].append(e)

	@staticmethod
	def query_radius(center, radius):
		"""Returns all active entities within radius using grid cells. O(1) average."""
		results = []
		r_sq = radius * radius
		r_cells = int(radius // SpatialGrid._cell_size) + 1
		cx, cz = SpatialGrid._key(center)
		
		for dx in range(-r_cells, r_cells + 1):
			for dz in range(-r_cells, r_cells + 1):
				cell = SpatialGrid._grid.get((cx + dx, cz + dz))
				if not cell:
					continue
				for e in cell:
					if not e.isActive():
						continue
					diff = e.getTransform().worldPosition - center
					if (diff.x * diff.x + diff.y * diff.y + diff.z * diff.z) <= r_sq:
						results.append(e)
		return results

	@staticmethod
	def reset():
		SpatialGrid._grid.clear()

# ──────────────────────────────────────────────
# Phase 70: Entity Pool (deactivate/activate pattern)
# ──────────────────────────────────────────────

class EntityPool:
	"""Reuses deactivated entities instead of constant addFromTemplate/kill cycles."""
	
	def __init__(self, scene, template_name, initial_size=0):
		self.scene = scene
		self.template = template_name
		self.pool = []
		
		# Pre-warm pool
		for _ in range(initial_size):
			e = scene.addFromTemplate(template_name)
			if e:
				e.deactivate(scene)
				self.pool.append(e)
	
	def acquire(self, position):
		"""Get an entity from the pool or create a new one."""
		for e in self.pool:
			if not e.isActive():
				e.getTransform().setPosition(position.x, position.y, position.z)
				e.activate(self.scene)
				return e
		
		# Pool exhausted — grow
		e = self.scene.addFromTemplate(self.template, position)
		if e:
			self.pool.append(e)
		return e
	
	def release(self, entity):
		"""Return entity to the pool instead of killing it."""
		if not entity: return
		entity.getTransform().setPosition(0, -999, 0) # Move far out of sight
		entity.deactivate(self.scene)

def release_entity(entity):
	"""
	Final Logic Seal: Returns an entity to its respective pool based on its template.
	"""
	if not entity: return
	template = entity.getProperties().get("pool_template")
	if template and template in _PROJECTILE_POOLS:
		_PROJECTILE_POOLS[template].release(entity)
	else:
		# Fallback for non-pooled or orphaned entities
		entity.kill()

# ──────────────────────────────────────────────
# Phase 70: BitMask Collision Layer Constants
# ──────────────────────────────────────────────

LAYER_TEAM_A     = 0   # Bit 0
LAYER_TEAM_B     = 1   # Bit 1
LAYER_TERRAIN    = 2   # Bit 2
LAYER_PROJECTILE = 3   # Bit 3
LAYER_NEUTRAL    = 4   # Bit 4

def create_enemy_mask(caster_team):
	"""Creates a BitMask that ONLY hits enemy units.
	Cave API: BitMask() default constructor, then enable specific layers."""
	mask = cave.BitMask(False)  # Explicitly disable all bits (default enables first 8)
	if caster_team == Team.TEAM_A:
		mask.enable(LAYER_TEAM_B)
	else:
		mask.enable(LAYER_TEAM_A)
	mask.enable(LAYER_NEUTRAL)  # Monsters are hittable by both teams
	return mask

# --- Phase 36: AudioManager ---
_active_ambient = None  # AudioTrackInstance or None

def play_managed_ambience(path, volume=0.5):
	"""Phase 36: Plays a looped ambient sound and tracks it for cleanup."""
	global _active_ambient
	stop_managed_ambience()  # Stop any existing ambient first
	
	try:
		scene = cave.getScene()
	except:
		return None
	
	handler = play_sfx(scene, path, volume=volume, loop=True)
	if handler:
		_active_ambient = handler  # Store AudioTrackInstance directly
	return handler

def stop_managed_ambience():
	"""Stops any currently playing ambient loop.
	Cave API: AudioTrackInstance is returned by play_sfx/AudioTrack.play().
	Call .stop() directly on the instance. Scene has no getAudioDevice()."""
	global _active_ambient
	if _active_ambient:
		try:
			# _active_ambient stores the AudioTrackInstance directly
			instance = _active_ambient
			if instance and hasattr(instance, 'stop'):
				instance.stop()
		except:
			pass
		_active_ambient = None

# ──────────────────────────────────────────────
# Team & Enums (Must be defined before FountainComponent)
# ──────────────────────────────────────────────

class Team:
	NEUTRAL = "neutral"
	TEAM_A  = "teamA"
	TEAM_B  = "teamB"

	@staticmethod
	def get_enemy(team):
		if team == Team.TEAM_A: return Team.TEAM_B
		if team == Team.TEAM_B: return Team.TEAM_A
		return Team.NEUTRAL

	# Phase 24: Team Color Mapping for VFX/UI consistency
	COLORS = {
		"teamA":  cave.Vector4(0.2, 0.4, 1.0, 1.0), # Blue
		"teamB":  cave.Vector4(1.0, 0.2, 0.2, 1.0), # Red
		"neutral": cave.Vector4(0.8, 0.8, 0.2, 1.0)  # Yellow/Gold
	}

def get_entity_team(entity):
	if not entity: return Team.NEUTRAL
	if entity.hasTag(Team.TEAM_A): return Team.TEAM_A
	if entity.hasTag(Team.TEAM_B): return Team.TEAM_B
	return Team.NEUTRAL

class EffectFlags:
	NONE        = 0
	STUN        = 1 << 0
	ROOT        = 1 << 1
	SILENCE     = 1 << 2
	DISARM      = 1 << 3
	INVULNERABLE = 1 << 4
	UNTARGETABLE = 1 << 5
	SHIELD      = 1 << 6
	SLOW        = 1 << 7
	TAUNT       = 1 << 8
	CHARM       = 1 << 9
	FEAR        = 1 << 10
	GROUNDED    = 1 << 11
	BLEED       = 1 << 12
	CREST_FIRE  = 1 << 13 # Red Buff
	CREST_INSIGHT = 1 << 14 # Blue Buff
	BARON_BUFF  = 1 << 15
	REVEALED    = 1 << 16
	CONTINUOUS  = 1 << 17 # Used for DoTs to suppress redundant FX
	CHANNELING  = 1 << 18
	RECALLING   = 1 << 19
	HIDDEN      = 1 << 20 # Phase 30: Invisible while in brush
	DEFLECT_PHYS  = 1 << 21 # Phase 70: Physical projectile deflection
	DEFLECT_MAGIC = 1 << 22 # Phase 70: Magical projectile deflection
	DEFLECT_MAGICAL = DEFLECT_MAGIC # Phase 70: Compatibility alias
	BASIC_ATTACK  = 1 << 23 # Phase 100: Distinguishes AAs from Spells
	CAMOUFLAGE    = 1 << 24 # Phase 101: Glass-shade + Untargetable + Hidden UI
	GHOST         = 1 << 25 # Phase 110: Ignore unit collision
	CC            = 1 << 26 # Generic CC marker for item interactions
	BUFF          = 1 << 27 # Positive buff marker (prevents cleanse removal)
	
class FountainComponent(cave.Component):
	"""Phase 28: Base area that enables shopping and rapid recovery."""
	team = Team.NEUTRAL
	radius = 12.0
	
	def update(self):
		scene = self.entity.getScene()
		pos = self.entity.getTransform().worldPosition
		
		# Find entities in radius
		ents = get_entities_in_radius(scene, pos, self.radius)
		in_range = set()
		for e in ents:
			if e.hasTag(self.team) and e.hasTag("player"):
				in_range.add(id(e))
				# Enable shopping
				e.getProperties()["canShop"] = True
				e.getProperties()["fountTick"] = GameTick._current_tick
				
				# Rapid Recovery (10% max health/mana per tick)
				if GameTick.is_tick_frame():
					max_hp = e.getProperties().get("maxHealth", 100)
					apply_heal(e, max_hp * 0.1, source=self.entity)
					
					pc = e.getPy("PlayerController")
					if pc:
						pc.mana = min(pc.maxMana, pc.mana + (pc.maxMana * 0.1))
		
		# NOTE: Cave Engine has no trigger callbacks (on_trigger_enter/exit).
		# We must manually reset canShop for players who left the radius.
		for e in EntityRegistry.get_team_entities(self.team, "player"):
			if id(e) not in in_range:
				e.getProperties()["canShop"] = False

class BrushComponent(cave.Component):
	"""Phase 30: Hide units and provide team-wide vision sharing."""
	brush_id = "brush_0" # Unique ID for each brush cluster
	
	def start(self, scene):
		self.actors = set() # Entities currently in this brush
		
	def cleanup(self):
		for actor in self.actors:
			if actor.isActive():
				actor.getProperties()["in_brush_id"] = None
				eff = actor.getPy("EffectComponent")
				if eff: eff.remove_flag(EffectFlags.HIDDEN)
		self.actors.clear()

	def update(self):
		"""Cave Engine has no trigger callbacks. Proximity is checked manually."""
		pos = self.entity.getTransform().worldPosition
		brush_radius = self.entity.getProperties().get("brushRadius", 3.0)
		
		current_contacts = set()
		for e in SpatialGrid.query_radius(pos, brush_radius):
			if not e.isActive(): continue
			if e.hasTag("player") or e.hasTag("minion") or e.hasTag("monster"):
				current_contacts.add(e)
				if e not in self.actors:
					# Enter brush
					e.getProperties()["in_brush_id"] = self.brush_id
					eff = e.getPy("EffectComponent")
					if eff:
						eff.add_flag(EffectFlags.HIDDEN)
		
		# Handle entities that left the brush
		exited = self.actors - current_contacts
		for e in exited:
			if e.isActive():
				e.getProperties()["in_brush_id"] = None
				eff = e.getPy("EffectComponent")
				if eff:
					eff.remove_flag(EffectFlags.HIDDEN)
		self.actors = current_contacts

class WardComponent(cave.Component):
	"""Phase 31: Provides vision in a radius and reveals brushes."""
	duration = 90.0
	vision_radius = 12.0
	team = "teamA"
	
	def start(self, scene):
		# Optimized Pattern: scheduleKill is more efficient than manual update ticking
		self.entity.scheduleKill(self.duration)
		self.entity.getProperties()["visionRange"] = self.vision_radius
		self.entity.getProperties()["team"] = self.team
		self.entity.addTag(f"{self.team}_ward")
		self.entity.addTag("ward")
		self.actors = set()
		
	def update(self):
		pass # Vision logic handled via VisionManager; lifetime handled by scheduleKill

def reveal_unit(entity, duration=3.5):
	"""Phase 30: Grant REVEALED flag to ignore HIDDEN status."""
	eff = entity.getPy("EffectComponent")
	if eff:
		eff.apply("REVEALED", duration, flags=EffectFlags.REVEALED)

# Team class moved before FountainComponent (forward-reference fix)
# See definition above EffectFlags

class Templates:
	"""Phase 24: Centralized Asset Registry to prevent string hallucinations."""
	# Minions
	MINION_MELEE   = "Minion_Melee"
	MINION_RANGED  = "Minion_Ranged"
	MINION_CANNON  = "Minion_Cannon"
	
	# Projectiles
	PROJ_BASIC     = "Projectile_Basic"
	PROJ_MINION    = "Projectile_Minion"
	PROJ_TURRET    = "TurretProjectile" # Direct mapping for stability
	
	# VFX
	VFX_ATTACK_HIT = "VFX_Blood_Burst"
	VFX_TURRET_HIT = "VFX_TurretHit"
	VFX_TURRET_EXP = "VFX_Turret_Explosion"
	VFX_DEATH      = "VFX_Generic_Death"
	VFX_LEVEL_UP   = "VFX_LevelUp_Gold"
	
	# SFX
	SFX_TURRET_FIRE = "SFX_Turret_Fire"
	SFX_MINION_ATK  = "SFX_Minion_Attack"
	SFX_JUNGLE_ATK  = "SFX_Jungle_Attack"
	SFX_RECALL_START = "SFX_Recall_Start"
	SFX_RECALL_FINISH = "SFX_Recall_Finish"
	SFX_VICTORY     = "SFX_Victory"
	SFX_DEFEAT      = "SFX_Defeat"
	SFX_KILL        = "SFX_Kill_Announcement"
	SFX_DOUBLE_KILL  = "SFX_DoubleKill"
	SFX_TRIPLE_KILL  = "SFX_TripleKill"
	SFX_QUADRA_KILL  = "SFX_QuadraKill"
	SFX_PENTA_KILL   = "SFX_PentaKill"
	SFX_STREAK_3     = "SFX_KillingSpree"
	SFX_STREAK_4     = "SFX_Rampage"
	SFX_STREAK_5     = "SFX_Unstoppable"
	SFX_STREAK_6     = "SFX_Dominating"
	SFX_STREAK_7     = "SFX_Godlike"
	SFX_STREAK_8     = "SFX_Legendary"
	SFX_ACE          = "SFX_Ace"
	MINIMAP_HERO   = "Icon_Hero"
	MINIMAP_BASIC  = "Icon_Simple"
	
	# Phase 35: FCT & UI Feedback
	FCT_TEMPLATE   = "UI_FloatingText"
	ICON_EMPTY     = "Icon_Empty"
	ICON_COOLDOWN  = "Icon_Overlay_CD"
	
	# Phase 36: Contextual Impacts & Ambience
	SFX_IMPACT_UNIT = "SFX_Impact_Organic"
	SFX_IMPACT_HERO = "SFX_Impact_Hero_Grunt"
	SFX_IMPACT_TURRET = "SFX_Impact_Metallic"
	SFX_UI_CLICK = "SFX_UI_Standard_Click"
	SFX_SHOP_PURCHASE = "SFX_Shop_Coins"
	SFX_ANNOUNCEMENT = "SFX_Global_Clarion"
	
	BGM_SUMMONERS_RIFT = "Ambience_SR_Forest"
	BGM_ARAM = "Ambience_ARAM_Bridge"
	
	# VFX & Vision (Phase 65)
	VFX_RECALL     = "VFX_Recall_Circle"
	VFX_WARD_STEALTH = "VFX_Ward_Stealth"
	VFX_WARD_BLUE    = "VFX_Ward_Blue"
	VFX_ORACLE_SWEEP = "VFX_Oracle_Sweep"
	
	# Default Hero Icons (Fallbacks)
	ICON_SKILL_Q   = "Icon_Skill_Q"
	ICON_SKILL_W   = "Icon_Skill_W"
	ICON_SKILL_E   = "Icon_Skill_E"
	ICON_SKILL_R   = "Icon_Skill_R"
	ICON_PASSIVE   = "Icon_Passive"
	
	# Default Item Icons
	ICON_ITEM_DEFAULT = "Icon_Item_Box"

	# Specialized Summon Templates (Phase 42)
	GHOUL          = "GhoulTemplate"
	GARGOYLE       = "GargoyleTemplate"
	WALL           = "WallTemplate"
	SENTRY         = "SentryTemplate"
	PROJ_SKILL     = "ProjectileTemplate"
	MINION_SUPER   = "Minion_Super"
	WARD_TEMPLATE  = "WardTemplate"
	VFX_BUFF_GREEN = "VFX_Buff_Green"
	SFX_SNOWBALL   = "SFX_Snowball_Hit"
	SFX_IMPACT_HEAVY = "SFX_Impact_Heavy"
	PROJ_RUNAANS   = "Projectile_Runaans"
	
	# Structures
	INHIBITOR      = "Inhibitor_Basic"
	NEXUS          = "Nexus_Central"
	
	# Missing Icon Fallback
	ICON_EMPTY     = "Icon_Empty"
	
	# Announcer SFX (Phase 132: Kill Announcements)
	SFX_KILL         = "SFX_Announcer_Kill"
	SFX_DOUBLE_KILL  = "SFX_Announcer_DoubleKill"
	SFX_TRIPLE_KILL  = "SFX_Announcer_TripleKill"
	SFX_QUADRA_KILL  = "SFX_Announcer_QuadraKill"
	SFX_PENTA_KILL   = "SFX_Announcer_PentaKill"
	SFX_STREAK_3     = "SFX_Announcer_KillingSpree"
	SFX_STREAK_4     = "SFX_Announcer_Rampage"
	SFX_STREAK_5     = "SFX_Announcer_Unstoppable"
	SFX_STREAK_6     = "SFX_Announcer_Dominating"
	SFX_STREAK_7     = "SFX_Announcer_Godlike"
	SFX_STREAK_8     = "SFX_Announcer_Legendary"

# get_entity_team() moved before FountainComponent (forward-reference fix)
# See definition above EffectFlags

class CastingMode:
	NORMAL = 0
	QUICK = 1
	QUICK_WITH_INDICATOR = 2

class InputConfig:
	"""Phase 116: Centralized Keybinds and Input Preferences."""
	# Modifiers
	KEY_TARGET_HEROES_ONLY = cave.event.KEY_BACKQUOTE # Tilde/Grave
	
	# Action Keys
	KEY_ATTACK_MOVE = cave.event.KEY_A
	KEY_RECALL = cave.event.KEY_B
	KEY_STOP = cave.event.KEY_S
	KEY_LOCK_CAM = cave.event.KEY_Y
	KEY_SHOP = cave.event.KEY_P
	KEY_CENTER_CAM = cave.event.KEY_SPACE
	KEY_PING_GENERIC = cave.event.KEY_G
	KEY_PING_DANGER = cave.event.KEY_V
	
	# Casting Preferences
	SMART_CAST_BY_DEFAULT = True 
	CLAMP_CAST_AT_MAX_RANGE = True 
	AUTO_ATTACK_ENABLED = False 
	ATTACK_MOVE_ON_LEFT_CLICK = False # High-level setting
	TREAT_TARGET_HEROES_ONLY_AS_TOGGLE = False 
	
	# Per-Slot Casting Modes
	SLOT_CASTING_MODES = {
		"Q": CastingMode.QUICK,
		"W": CastingMode.QUICK,
		"E": CastingMode.QUICK,
		"R": CastingMode.QUICK_WITH_INDICATOR, # Default Ult to indicator for safety
		"D": CastingMode.QUICK,
		"F": CastingMode.QUICK
	}

class IndicatorType:
	CIRCLE = 0
	LINE = 1
	CONE = 2
	RECTANGLE = 3

class DamageType:
	PHYSICAL = 0
	MAGIC = 1
	TRUE = 2
	PURE = 3 # Ignores shields
	HEAL = 4
	GOLD = 5 # Phase 35: Visual only

class DamageFlags:
	"""Bitflags for damage context (critical, basic attack, etc)."""
	NONE = 0
	CRITICAL = 1
	BASIC_ATTACK = 2
	AOE = 4


class ProjectileType:
	PHYSICAL = 0
	MAGICAL  = 1
	BOTH     = 2

class EffectComponent(cave.Component):
	"""Handles CC timers and active status effects on an entity."""
	def start(self, scene):
		self.active_effects = {} # {id: StatusEffect}
		self.combined_flags = 0
		self.pc = self.entity.getPy("PlayerController")
		self.needs_recalc = False # Final Phase Optimization
		
	def remove_negative_effects(self):
		"""Cleanses all crowd control and harmful debuffs."""
		neg_flags = EffectFlags.STUN | EffectFlags.ROOT | EffectFlags.SILENCE | \
					EffectFlags.DISARM | EffectFlags.SLOW | EffectFlags.TAUNT | \
					EffectFlags.CHARM | EffectFlags.FEAR | EffectFlags.GROUNDED | \
					EffectFlags.BLEED
					
		to_remove = []
		for eid, eff in self.active_effects.items():
			if eff.flags & neg_flags:
				to_remove.append(eid)
				
		for eid in to_remove:
			del self.active_effects[eid]
			
		if to_remove:
			self._recalculate_flags()
			self.needs_recalc = True
		
	def apply(self, effect_id, duration, flags=EffectFlags.NONE, magnitude=0.0, dmg_type=DamageType.MAGIC, source=None):
		self.active_effects[effect_id] = StatusEffect(effect_id, duration, flags, magnitude, source=source, dmg_type=dmg_type)
		self._recalculate_flags()
		# Optimized: Mark for recalc next frame or end of logic
		self.needs_recalc = True 
		# If it's a critical CC, refresh immediately for AI responsiveness
		if flags & (EffectFlags.STUN | EffectFlags.ROOT | EffectFlags.SILENCE):
			refresh_stats(self.entity)
			self.needs_recalc = False
		
	def add_flag(self, flag):
		"""Directly enables a bitmask flag on the combined_flags (for persistent toggles)."""
		self.combined_flags |= flag
		
	def remove_flag(self, flag):
		"""Directly removes a bitmask flag from combined_flags."""
		self.combined_flags &= ~flag
		
	def _recalculate_flags(self):
		self.combined_flags = 0
		for e in self.active_effects.values():
			self.combined_flags |= e.flags

	def has_flag(self, flag):
		return (self.combined_flags & flag) != 0

	def is_cced(self):
		"""Returns True if any hard crowd control is active (Stun, Fear, Charm)."""
		hard_cc = EffectFlags.STUN | EffectFlags.FEAR | EffectFlags.CHARM
		return self.has_flag(hard_cc)

	def is_stunned(self):
		return self.has_flag(EffectFlags.STUN)

	def is_rooted(self):
		return self.has_flag(EffectFlags.ROOT)

	def is_silenced(self):
		return self.has_flag(EffectFlags.SILENCE)

	def is_invulnerable(self):
		return self.has_flag(EffectFlags.INVULNERABLE)

	def is_untargetable(self):
		return self.has_flag(EffectFlags.UNTARGETABLE)

	def get_magnitude(self, effect_id):
		eff = self.active_effects.get(effect_id)
		# Phase 72 FIX: Use object property '.magnitude' instead of dict subscript
		return eff.magnitude if eff else 0.0

	def update(self):
		dt = cave.getDeltaTime()
		to_remove = []
		for eid, eff in self.active_effects.items():
			# Logic for Damage over Time (DoT)
			# DoTs are identified by the name "DOT_" or "BLEED"
			is_dot = "DOT_" in eid or "BLEED" in eid or "HEMORRHAGE" in eid
			if is_dot:
				eff.next_tick -= dt
				if eff.next_tick <= 0:
					eff.next_tick = eff.tick_rate
					# Apply damage using standardized applicator
					# magnitude used as damage per tick
					apply_damage(self.entity, eff.magnitude, eff.dmg_type, attacker=eff.source)

			if eff.tick(dt):
				to_remove.append(eid)
		
		if to_remove:
			for eid in to_remove:
				del self.active_effects[eid]
			self._recalculate_flags()
			self.needs_recalc = True
			
		if self.needs_recalc:
			refresh_stats(self.entity)
			self.needs_recalc = False

class ProjectileComponent(cave.Component):
	"""Moving entity that triggers an effect on contact."""
	speed = 20.0
	range = 15.0
	damage = 50.0
	team = "teamA"
	trail_template = None
	hit_vfx = None
	
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.spawn_pos = self.transf.worldPosition.copy()
		self.direction = self.transf.getForwardVector(True)
		self.hit_count = 0
		self.max_hits = 1
		self.prev_pos = self.transf.worldPosition.copy()
		
		# Persistent Trail VFX
		self.trail_vfx = None
		if self.trail_template:
			self.trail_vfx = spawn_vfx(scene, self.trail_template, self.transf.worldPosition, duration=-1, parent=self.entity)
		
	def update(self):
		dt = cave.getDeltaTime()
		scene = self.entity.getScene()
		
		# Movement
		curr_pos = self.transf.worldPosition
		move_step = self.direction * self.speed * dt
		next_pos = curr_pos + move_step
		
		# Swept-Collision (Phase 18 Fix): Prevents tunneling at high speed
		team = self.entity.getProperties().get("team", self.team)
		enemyTag = Team.get_enemy(team)
		
		# Use sphereCast to detect everything between last and current frame
		cast_radius = self.entity.getProperties().get("collisionRadius", 1.0)
		hits = scene.sphereCastAll(curr_pos, next_pos, cast_radius)
		
		# Sort hits by distance manually if necessary (sphereCastAll returns list)
		for hit in hits:
			e = hit.entity
			if not e or not e.isActive(): continue
			if e.hasTag(enemyTag) and (e.hasTag("player") or e.hasTag("minion") or e.hasTag("monster")):
				self.on_hit(e)
				self.hit_count += 1
				if self.hit_count >= self.max_hits:
					self.cleanup()
					return # Stop processing
					
		# Finalize move
		self.transf.applyMovement(move_step)
		
		# Range Check
		dist = (self.transf.worldPosition - self.spawn_pos).length()
		if dist > self.range:
			self.cleanup()
			return

	def cleanup(self):
		"""Ensures trails are destroyed before the projectile entity returns to the pool."""
		if hasattr(self, "trail_vfx") and self.trail_vfx:
			self.trail_vfx.kill()
		release_entity(self.entity)

	def on_hit(self, target):
		scene = self.entity.getScene()
		# Trigger hit VFX at target position
		if self.hit_vfx:
			spawn_vfx(scene, self.hit_vfx, target.getTransform().worldPosition, duration=0.5)
		
		# Generic damage applicator (assuming self.attacker exists or passed via property)
		attacker = self.entity.getProperties().get("attacker")
		apply_damage(target, self.damage, DamageType.PHYSICAL, attacker=attacker)
		self.cleanup()

class HomingProjectileComponent(cave.Component):
	"""Projectile that tracks a specific target entity."""
	speed = 25.0
	damage = 50.0
	attacker = None
	target = None
	hit_vfx = None
	is_basic = False
	
	def start(self, scene):
		self.transf = self.entity.getTransform()

	def update(self):
		if not self.target or not self.target.isActive():
			release_entity(self.entity)
			return
			
		dt = cave.getDeltaTime()
		t_transf = self.target.getTransform()
		# Aim for chest height (approx 1m up)
		target_pos = t_transf.worldPosition + cave.Vector3(0, 1.0, 0)
		
		# Move toward target
		curr_pos = self.transf.worldPosition
		diff = target_pos - curr_pos
		dist = diff.length()
		
		if dist < 0.5:
			self.on_hit()
			return
			
		dir = diff.normalized()
		self.transf.applyMovement(dir * self.speed * dt)
		self.transf.lookAtPosition(target_pos)

	def on_hit(self):
		scene = self.entity.getScene()
		if self.target and self.target.isActive():
			if self.hit_vfx:
				spawn_vfx(scene, self.hit_vfx, self.target.getTransform().worldPosition)
			
			# Trigger On-Hit Passives if attacker is a player and still active
			if self.attacker and self.attacker.isActive():
				a_pc = self.attacker.getPy("PlayerController")
				if a_pc:
					from Core import MobaItems
					flags = MobaCommon.EffectFlags.BASIC_ATTACK if self.is_basic else 0
					MobaItems.ItemEffectManager.process_on_hit(a_pc, self.target, is_ability=False, flags=flags)
			
			flags = MobaCommon.EffectFlags.BASIC_ATTACK if self.is_basic else 0
			apply_damage(self.target, self.damage, DamageType.PHYSICAL, attacker=self.attacker, flags=flags)
		
		release_entity(self.entity)

class BoomerangComponent(cave.Component):
	"""Projectile that travels to a point and returns to the owner."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.owner = self.entity.getProperties().get("owner")
		self.target_pos = self.entity.getProperties().get("targetPos")
		self.speed = self.entity.getProperties().get("speed", 25.0)
		self.phase = "outgoing"
		self.hit_list = [] # Reset on phase change
		
	def update(self):
		if not self.owner or not self.owner.isActive():
			release_entity(self.entity)
			return
			
		dt = cave.getDeltaTime()
		scene = self.entity.getScene()
		curr_pos = self.transf.worldPosition

		if self.phase == "outgoing":
			diff = self.target_pos - curr_pos
			dist = diff.length()
			if dist < 0.5:
				self.phase = "returning"
				self.hit_list = [] # Allow re-hitting on return
				return
			dir = diff.normalized()
		else:
			# returning phase
			diff = self.owner.getTransform().worldPosition - curr_pos
			dist = diff.length()
			if dist < 1.0:
				release_entity(self.entity)
				return
			dir = diff.normalized()
			
		self.transf.applyMovement(dir * self.speed * dt)
		self.transf.lookAtPosition(curr_pos + dir)
		
		# Collision
		from Core import MobaCommon
		team = self.entity.getProperties().get("team", "teamA")
		enemyTag = "teamB" if team == "teamA" else "teamA"
		width = self.entity.getProperties().get("width", 2.0)
		ents = MobaCommon.get_entities_in_radius(scene, curr_pos, width)
		
		for e in ents:
			if e.isActive() and e.hasTag(enemyTag) and e not in self.hit_list:
				if e.hasTag("player") or e.hasTag("minion") or e.hasTag("monster"):
					# Removed nested apply_damage mess
					props = self.entity.getProperties()
					dmg = props.get("outDamage" if self.phase == "outgoing" else "returnDamage", 50.0)
					p_type = props.get("outDamageType" if self.phase == "outgoing" else "returnDamageType", MobaCommon.DamageType.MAGIC)
					MobaCommon.apply_damage(e, dmg, p_type, attacker=self.owner)
					MobaCommon.spawn_vfx(scene, "VFX_Impact_Standard", e.getTransform().worldPosition, duration=0.5)
					self.hit_list.append(e)


_damage_depth = 0
MAX_DAMAGE_RECURSION = 3

def apply_damage(target, raw_dmg, dmg_type, attacker=None, situational_mult=1.0, flags=0):
	"""
	General purpose damage applicator.
	Redirects to PlayerController.takeDamage if target is a hero.
	Otherwise calculates reduction for minions/monsters.
	Phase 127: Added Hit-Stop and Screen Shake triggers.
	"""
	if not target or not target.isActive(): return 0
	
	global _damage_depth
	if _damage_depth >= MAX_DAMAGE_RECURSION: return 0
	
	try:
		_damage_depth += 1
		
		# Phase 101: Ability Monster Effectiveness (e.g. 1.5x on specific skills)
		if target.hasTag("monster") and attacker:
			a_pc = attacker.getPy("PlayerController") if hasattr(attacker, "getPy") else None
			if a_pc and hasattr(a_pc, "current_skill_data"):
				raw_dmg *= a_pc.current_skill_data.get("isMonsterEffective", 1.0)
		
		# --- Phase 101: Turret Fortification (Anti-Rush) ---
		# Mid and Top lane turrets take 50% reduced flat damage for the first 5 minutes.
		mins = GameTick.get_time_minutes()
		if mins < 5.0 and target.hasTag("turret"):
			if target.hasTag("mid") or target.hasTag("top"):
				raw_dmg *= 0.5
				
		# Phase 125: Objective Damage Tracking
		if attacker and (target.hasTag("turret") or target.hasTag("monster")):
			MatchStatsManager.track_objective_damage(attacker.name, raw_dmg)
		# Phase 121: Tactical Plant Interaction
		if target.hasTag("plant"):
			# Find the specific plant component
			for comp_name in ["PlantBase", "BlastCone", "VitalityBloom", "FluxSeeker"]:
				plant = target.getPy(comp_name)
				if plant:
					plant.take_damage(attacker)
					return 0
		
		# 0. Invulnerability/Untargetability Check (for non-players)
		currentHP = target.getProperties().get("health", 0)
		if currentHP <= 0: return 0 # Overkill Guard: Target is already dead
		
		eff = target.getPy("EffectComponent") if hasattr(target, "getPy") else None
		if eff:
			if eff.is_invulnerable(): return 0
			if eff.is_untargetable() and dmg_type != DamageType.TRUE: return 0

		# 1. PC/Hero Check (Heroes handle their own mitigation to avoid double-reduction)
		pc = target.getPy("PlayerController") if hasattr(target, "getPy") else None
		turret = target.getPy("TurretComponent") if hasattr(target, "getPy") else None
		
		# Phase 100: Lyra's Harmonic Healing
		if attacker:
			a_pc = attacker.getPy("PlayerController") if hasattr(attacker, "getPy") else None
			if a_pc and a_pc.heroName == "Lyra":
				target_team = get_entity_team(target)
				attacker_team = get_entity_team(attacker)
				if target_team == attacker_team and target.hasTag("player"):
					# Heal allies instead of damaging
					# 15 base + 50% "damage" as heal
					heal_amt = (raw_dmg * 0.5) + 15
					apply_heal(target, heal_amt, source=attacker)
					return 0
		
		# --- Phase 63: Jungle Gating & Scaling ---
		is_monster = target.hasTag("monster")
		if attacker and is_monster:
			a_pc = attacker.getPy("PlayerController") if hasattr(attacker, "getPy") else None
			if a_pc:
				has_jungle_item = False
				for item_id in a_pc.inventory_mgr.items:
					if "Resolve" in item_id: # Hunter's, Goliath's, Slayer's, Arcane
						has_jungle_item = True
						break
				
				match_time = target.getScene().getElapsedSceneTime()
				if not has_jungle_item and match_time < 600.0: # Before 10 minutes
					raw_dmg *= 0.5 # 50% damage penalty for non-junglers
				elif has_jungle_item:
					raw_dmg *= 1.25 # 25% Bonus to monsters
					# Omni-vamp sustain
					apply_heal(attacker, raw_dmg * 0.1, source=target)

		# Phase 102: Rune Proc Hook
		if attacker:
			a_pc = attacker.getPy("PlayerController") if hasattr(attacker, "getPy") else None
			if a_pc and hasattr(a_pc, "rune_mgr"):
				# Determine if this was an ability (from current_skill_data context)
				is_spell = hasattr(a_pc, "current_skill_data")
				a_pc.rune_mgr.on_hit(target, is_ability=is_spell)

		if pc and hasattr(pc, "takeDamage"):
			# Pass RAW damage; the controller will call calculate_damage once and apply to HP/Shield.
			final_dmg = pc.takeDamage(raw_dmg, dmg_type, attacker=attacker)
			# Phase 115: Track Damage Taken for summary
			MatchStatsManager.track_damage_taken(target.name, final_dmg)
		elif turret and hasattr(turret, "take_damage"):
			# Phase 100: Turret TakeDamage (for Plating detection)
			final_dmg = calculate_damage(raw_dmg, dmg_type, attacker=attacker, defender=target, situational_mult=situational_mult)
			final_dmg = turret.take_damage(final_dmg, attacker)
		else:
			# 2. Fallback for simple entities (minions, monsters)
			final_dmg = calculate_damage(raw_dmg, dmg_type, attacker=attacker, defender=target, situational_mult=situational_mult)
			
			props = target.getProperties()
			currentHP = props.get("health", 0)
			props["health"] = currentHP - final_dmg
			
			# --- Phase 105: Hand of Baron Empowerment ---
			# If this is a minion and an allied hero with Baron buff is nearby, it becomes a siege unit.
			if target.hasTag("minion") and not target.hasTag("super"):
				team = get_entity_team(target)
				nearby_allies = get_entities_in_radius(target.getScene(), target.getTransform().worldPosition, 12.0)
				is_empowered = False
				for a in nearby_allies:
					if a.hasTag(team) and a.hasTag("player") and a.getProperties().get("hasBaronBuff", False):
						is_empowered = True
						break
				
				if is_empowered:
					target.getProperties()["isEmpowered"] = True
					# Visual indicator (can be used by Shaders/FCT)
					target.getProperties()["range"] = 10.0 # Huge range boost for sieging
				else:
					target.getProperties()["isEmpowered"] = False
			
			# Track Contribution for Rewards
			if attacker:
				scene_time = target.getScene().getElapsedSceneTime()
				target.getProperties()["lastAttacker"] = attacker
				contribs = target.getProperties().get("contributions", {})
				contribs[attacker.name] = (scene_time, attacker) # Phase 39: Consistent (Time, Entity) tuple
				target.getProperties()["contributions"] = contribs
		
		# --- Systemic Feedback Loop (Phase 20) ---
		# 1. Trigger Visual Damage Blink (Red Flash)
		target_pc = target.getPy("PlayerController") if hasattr(target, "getPy") else None
		
		# Phase 101: Break Camouflage on taking damage
		eff = target.getPy("EffectComponent") if hasattr(target, "getPy") else None
		if final_dmg > 0 and eff and eff.has_flag(EffectFlags.CAMOUFLAGE):
			# Force removal of CAMOUFLAGE from both bitmask and effect list
			to_remove = [k for k, v in eff.active_effects.items() if (v.flags & EffectFlags.CAMOUFLAGE)]
			for k in to_remove: del eff.active_effects[k]
			eff._recalculate_flags()
			if target_pc: target_pc.recalculate_stats() # Force refresh visuals
			
		if target_pc:
			if hasattr(target_pc, "trigger_damage_blink"):
				target_pc.trigger_damage_blink()
			
			# Phase 100: Trigger Passive on Hit Taken
			if hasattr(target_pc, "passive_mgr"):
				target_pc.passive_mgr.on_hit_taken(attacker, final_dmg)
			
			# Combat Activity Tracking (support passives)
			target_pc.lastCombatTime = target.getScene().getElapsedSceneTime()
			from Core import MobaItems
			MobaItems.ItemEffectManager.process_taking_damage(target_pc, attacker, dmg_type, final_dmg)
		
		# 2. Trigger Floating Combat Text (FCT)
		# Continuous check: uses flags arg OR attacker status
		is_continuous = (flags & EffectFlags.CONTINUOUS) != 0
		if attacker and not is_continuous:
			a_pc = attacker.getPy("PlayerController") if hasattr(attacker, "getPy") else None
			if a_pc and (a_pc.flags & EffectFlags.CONTINUOUS):
				is_continuous = True

		# Phase 38: Track Damage Stats
		if attacker and final_dmg > 0:
			MatchStatsManager.track_damage(attacker.name, final_dmg)

		# ── Wave 35/76: Floating Combat Text Hook ───────────────────────────
		if final_dmg > 1.0:
			from UI import MobaUI
			fct_color = cave.Vector4(1, 1, 1, 1) # Default True
			if dmg_type == DamageType.PHYSICAL: fct_color = cave.Vector4(1.0, 0.4, 0.4, 1)
			elif dmg_type == DamageType.MAGIC:  fct_color = cave.Vector4(0.4, 0.7, 1.0, 1)
			
			MobaUI.spawn_fct(target.getScene(), target.getTransform().worldPosition, f"{int(final_dmg)}", fct_color)

			# Phase 127: Impact Overhaul
			is_heavy = (dmg_type in [DamageType.PHYSICAL, DamageType.MAGIC] and final_dmg > 100) or (flags & 1)
			if is_heavy and attacker and target:
				GameTick.trigger_hit_stop(0.06)
				MobaUI.trigger_screen_shake(target.getTransform().worldPosition, 0.2)
				MobaUI.trigger_mesh_flash(target)
				spawn_vfx(target.getScene(), Templates.SFX_IMPACT_HEAVY, target.getTransform().worldPosition)

		# Phase 30: Vision Reveal on Combat
		if final_dmg > 0:
			reveal_unit(target, 3.5)
			if attacker:
				reveal_unit(attacker, 3.5)

		# 3. Trigger Lifesteal if attacker is a player
		if attacker and dmg_type == DamageType.PHYSICAL:
			a_pc = attacker.getPy("PlayerController") if hasattr(attacker, "getPy") else None
			if a_pc:
				lifeSteal = attacker.getProperties().get("lifeSteal", 0.0)
				if lifeSteal > 0:
					apply_heal(attacker, final_dmg * lifeSteal)
					
				is_basic = False 
				a_pc.passive_mgr.on_hit_target(target, final_dmg, is_basic_attack=is_basic)
				
				# Combat Activity Tracking
				a_pc.lastCombatTime = target.getScene().getElapsedSceneTime()
		
		# Phase 36: Contextual Impact SFX
		if final_dmg > 0 and not is_continuous:
			impact_sfx = Templates.SFX_IMPACT_UNIT
			if target.hasTag("turret") or target.hasTag("inhibitor") or target.hasTag("nexus"):
				impact_sfx = Templates.SFX_IMPACT_TURRET
			play_sfx(target, impact_sfx, pitch_var=0.1)
		
		# Phase 131: Last-Hit Gold Pop (Feature 7)
		if final_dmg > 0 and target.hasTag("minion"):
			t_hp = target.getProperties().get("health", 0)
			if t_hp <= 0 and attacker and attacker.hasTag("player"):
				gold_val = target.getProperties().get("goldValue", 21)
				a_pc = attacker.getPy("PlayerController") if hasattr(attacker, "getPy") else None
				if a_pc:
					a_pc.gold = getattr(a_pc, 'gold', 0) + gold_val
					MatchStatsManager.track_cs(attacker.name)
					MobaUI.spawn_fct(target.getScene(), target.getTransform().worldPosition,
						f"+{gold_val}g", cave.Vector4(1.0, 0.85, 0.1, 1.0))
		
		# Phase 131: Turret Plating (Feature 6) - Mid lane only
		# Plates only activate when the defending mid laner has been away for 5+ seconds
		if final_dmg > 0 and target.hasTag("turret") and target.hasTag("mid") and attacker:
			t_props = target.getProperties()
			turret_team = get_entity_team(target)
			turret_pos = target.getTransform().worldPosition
			
			# Check if defending mid laner is nearby
			defender_nearby = False
			allies = EntityRegistry.get_team_entities(turret_team, "player")
			for ally in allies:
				a_pc = ally.getPy("PlayerController")
				if a_pc and hasattr(a_pc, "heroData") and a_pc.heroData.get("role") == "mid":
					dist = (ally.getTransform().worldPosition - turret_pos).length()
					if dist < 15.0:
						defender_nearby = True
						# Phase 131 Fix: Store the tick when the defender was last seen
						t_props["_mid_last_seen_tick"] = GameTick._current_tick
					break
			
			# Calculate away time based on tick difference
			last_seen = t_props.get("_mid_last_seen_tick", GameTick._current_tick)
			away_seconds = (GameTick._current_tick - last_seen) / GameTick._tick_rate
			
			# Only apply plating if mid has been gone for 5+ seconds
			plates = t_props.get("plates", TurretPlatingConfig.PLATES)
			mins = GameTick.get_time_minutes()
			mid_away = away_seconds >= 5.0
			
			if plates > 0 and mins < TurretPlatingConfig.FALL_OFF_TIME and mid_away:
				plate_hp = t_props.get("plateHP", TurretPlatingConfig.HP_PER_PLATE)
				plate_hp -= final_dmg
				if plate_hp <= 0:
					# Plate broken!
					plates -= 1
					t_props["plates"] = plates
					t_props["plateHP"] = TurretPlatingConfig.HP_PER_PLATE
					a_pc = attacker.getPy("PlayerController") if hasattr(attacker, "getPy") else None
					if a_pc:
						a_pc.gold = getattr(a_pc, 'gold', 0) + TurretPlatingConfig.GOLD_PER_PLATE
						MobaUI.spawn_fct(target.getScene(), turret_pos,
							f"+{TurretPlatingConfig.GOLD_PER_PLATE}g PLATE", cave.Vector4(1, 0.7, 0.2, 1))
					play_sfx(target, Templates.SFX_IMPACT_TURRET)
				else:
					t_props["plateHP"] = plate_hp
					
		return final_dmg
	except Exception as e:
		print(f"CRITICAL ERROR in apply_damage: {e}")
		return 0
	finally:
		_damage_depth -= 1



def apply_heal(entity, amount, source=None):
	"""Standardized healing logic with Grievous Wounds check."""
	p = entity.getProperties()
	current = p.get("health", 0)
	max_hp = p.get("maxHealth", 0)
	
	# Phase 71: Grievous Wounds (Healing Reduction)
	eff = entity.getPy("EffectComponent")
	# EffectFlags.BLEED is used as the bitmask for healing reduction
	if eff and eff.has_flag(EffectFlags.BLEED): 
		amount *= 0.6 # 40% Reduction
	
	new_hp = min(max_hp, current + amount)
	p["health"] = new_hp
	
	# Phase 100: Overheal (Bloodthirster)
	excess = (current + amount) - max_hp
	if excess > 0:
		pc_comp = entity.getPy("PlayerController")
		if pc_comp:
			from Core import MobaItems
			if MobaItems.ItemEffectManager.has_item_effect(pc_comp, "onTick", "OVERHEAL_SHIELD"):
				current_shield = p.get("shieldHP", 0)
				# Cap shield at 15% of max health
				p["shieldHP"] = min(max_hp * 0.15, current_shield + excess)
	
	if amount > 0:
		MatchStatsManager.track_healing(source.name if source else entity.name, amount)
		
	# ── Wave 35: Floating Combat Text Hook (Heal) ────────────────────
	if amount > 1.0:
		from UI import MobaUI
		MobaUI.spawn_fct(entity.getScene(), entity.getTransform().worldPosition, f"{int(amount)}", cave.Vector4(0.4, 1.0, 0.4, 1.0))
	
	return amount


def calculate_damage(raw_dmg, dmg_type=DamageType.PHYSICAL, attacker=None, defender=None, target_controller=None, situational_mult=1.0, flags=0):
	"""
	Calculates final damage after armor/mr reduction.
	Supports situational_mult (e.g. Lord Dominik's % bonus dmg).
	Supports flat and percent penetration.
	"""
	target = defender if defender else (target_controller.entity if target_controller else None)
	if not target or not target.isActive(): return raw_dmg * situational_mult
	
	# Phase 30: Backdoor Protection (Structure-Only)
	backdoor = target.getProperties().get("backdoor_reduction", 1.0)
	situational_mult *= backdoor

	# Phase 101: Attacker Passive Multipliers (Expansion)
	if attacker and attacker.isActive():
		a_pc = attacker.getPy("PlayerController") if hasattr(attacker, "getPy") else None
		if a_pc:
			if a_pc.heroName == "Aether" and dmg_type == DamageType.MAGIC:
				# Arcane Resonance
				situational_mult *= 1.15
			elif a_pc.heroName == "Kage" and dmg_type == DamageType.PHYSICAL:
				# Shadow Mark: Bonus vs low HP
				tar_hp = target.getProperties().get("health", 100)
				tar_max = target.getProperties().get("maxHealth", 100)
				if tar_hp / tar_max < 0.4:
					situational_mult *= 1.25

	if dmg_type == DamageType.TRUE:
		return raw_dmg * situational_mult
		
	props = target.getProperties()
	armor = props.get("armor", props.get("armorStat", 30))
	mr = props.get("magicResist", props.get("mrStat", 30))
	
	# Apply SHRED (Armor/MR reduction) from status effects
	pc = target.getPy("PlayerController") if hasattr(target, "getPy") else None
	total_shred = 0.0
	if pc and hasattr(pc, "activeEffects"):
		for eff in pc.activeEffects:
			if eff.id == "SHRED": total_shred += eff.magnitude
	else:
		eff_comp = target.getPy("EffectComponent") if hasattr(target, "getPy") else None
		if eff_comp:
			shred_data = getattr(eff_comp, "active_effects", {}).get("SHRED")
			# FIX: StatusEffect is an object with .magnitude attribute, not a dict
			if shred_data: total_shred = shred_data.magnitude if hasattr(shred_data, "magnitude") else 0.0
			
	if total_shred > 0:
		armor *= (1.0 - total_shred)
		mr *= (1.0 - total_shred)
	
	# Phase 101: Jungle Hunter Bypass (Jungler ignores 50% monster armor)
	if target.hasTag("monster") and attacker:
		a_pc = attacker.getPy("PlayerController") if hasattr(attacker, "getPy") else None
		if a_pc and hasattr(a_pc, "inventory_mgr") and a_pc.inventory_mgr.has_item_effect("onTick", "JUNGLE_HUNTER"):
			armor *= 0.5
			mr *= 0.5
	
	# Attacker Penetration stats
	flat_pen = 0.0
	percent_pen = 0.0
	
	if attacker and attacker.isActive():
		a_props = attacker.getProperties()
		if dmg_type == DamageType.PHYSICAL:
			flat_pen = a_props.get("lethality", 0.0)
			percent_pen = a_props.get("armorPenPercent", 0.0)
		elif dmg_type == DamageType.MAGIC:
			flat_pen = a_props.get("magicPenFlat", 0.0)
			percent_pen = a_props.get("magicPenPercent", 0.0)

	# Reduction Calculation
	def get_reduced_stat(stat, flat, percent):
		# Order: % Pen -> Flat Pen
		val = stat * (1.0 - percent)
		return val - flat

	if dmg_type == DamageType.PHYSICAL:
		effective_stat = get_reduced_stat(armor, flat_pen, percent_pen)
	elif dmg_type == DamageType.MAGIC:
		effective_stat = get_reduced_stat(mr, flat_pen, percent_pen)
	else:
		return raw_dmg * situational_mult

	# MOBA Damage Formula (LoL Style)
	if effective_stat >= 0:
		multiplier = 100.0 / (100.0 + effective_stat)
	else:
		# Amplification for negative resist: 2 - 100 / (100 - effective_stat)
		multiplier = 2.0 - (100.0 / (100.0 - effective_stat))
		
	# Phase 101: Crit Resilience (Randuin's Omen)
	# Reduces final crit damage by 30%
	if flags & DamageFlags.CRITICAL:
		# Check for persistence gating (humility/crit_resilience)
		# We check target.getProperties() or EffectComponent
		if target.getProperties().get("hasCritResilience", False):
			situational_mult *= 0.7
		
	# Phase 23 Safety: Never return negative damage (prevents unintended healing)
	final = max(0.0, raw_dmg * situational_mult * multiplier)
	
	# --- Phase 105: Baron Minion AOE Resilience ---
	# Baron-empowered minions take 70% reduced damage from non-True damage (AOE resistance simulation).
	if defender and defender.hasTag("minion") and defender.getProperties().get("isEmpowered") and dmg_type != DamageType.TRUE:
		final *= 0.3
		
	return final

class StatusEffect:
	"""Internal object to track an active effect on a player."""
	def __init__(self, id, duration, flags=0, magnitude=0.0, source=None, tick_rate=1.0, dmg_type=DamageType.MAGIC):
		self.id = id
		self.duration = duration
		self.flags = flags
		self.magnitude = magnitude
		self.source = source # Entity that applied the effect
		self.tick_rate = tick_rate
		self.dmg_type = dmg_type
		self.next_tick = tick_rate # Time until next damage tick
		
	def tick(self, dt):
		"""Returns True if the effect has expired."""
		self.duration -= dt
		return self.duration <= 0

	def is_cc(self):
		"""Returns True if this effect contains hard crowd control."""
		hard_cc = EffectFlags.STUN | EffectFlags.ROOT | EffectFlags.SILENCE | EffectFlags.FEAR | EffectFlags.CHARM
		return (self.flags & hard_cc) != 0

def refresh_stats(entity, base_stats=None):
	"""
	Phase 40: Centralized stat calculator.
	Sums: Base Stats + Item Bonuses + Active Effect Magnitudes.
	'base_stats' is an optional dict (for heroes), otherwise uses entity properties.
	"""
	p = entity.getProperties()
	
	# 1. Base Values (from argument or existing property)
	final_stats = {}
	fields = ["ad", "ap", "armor", "magicResist", "moveSpeed", "attackSpeed", "maxHealth", "maxMana", "turnRate"]
	
	for f in fields:
		# Phase 71: Clean-Read Pattern. Non-hero units (minions/monsters) use 'base_' properties 
		# as their source of truth to prevent recursive stat-bleeding from status effects.
		prop_key = f if f != "attackSpeed" else "baseAS"
		base_val = p.get(f"base_{prop_key}", p.get(prop_key, 0))
		final_stats[f] = base_stats.get(f, base_val) if base_stats else base_val

	# 2. Add Active Effects (StatusEffect magnitudes)
	eff_comp = entity.getPy("EffectComponent")
	# If it's a Hero, they use .activeEffects list
	pc = entity.getPy("PlayerController")
	# Phase 73: Use a unified source for active effects (EffectComponent is primary)
	active_list = []
	if eff_comp:
		active_list = eff_comp.active_effects.values()
	elif pc:
		active_list = pc.activeEffects

	for eff in active_list:
		if eff.id == "ARMOR_BOOST": final_stats["armor"] += eff.magnitude
		elif eff.id == "MS_BOOST": final_stats["moveSpeed"] += eff.magnitude
		elif eff.id == "STAT_MOD": 
			# Generic stat mod if magnitude is a dict or if we standardise it
			pass 
		elif eff.id == "SHRED": final_stats["armor"] -= eff.magnitude
		elif eff.id == "STEAL_PENALTY": final_stats["moveSpeed"] -= eff.magnitude
		elif eff.id == "BARON_BUFF":
			# Multiplicative bonuses (LoL style: +AD, +AP, +Minion Buffs)
			final_stats["ad"] *= 1.2
			final_stats["ap"] *= 1.2
		elif eff.id == "ELIXIR_OF_POWER":
			final_stats["ap"] += eff.magnitude
		elif eff.id == "VOID_BORN_RESILIENCE":
			# Jak'Sho: Rewards tanks for staying in the fight
			# pc.combat_timer is updated in the Controller
			if pc and getattr(pc, "combat_timer", 0) >= 5.0:
				# Apply 30% bonus to total resistances
				final_stats["armor"] *= 1.3
				final_stats["magicResist"] *= 1.3

	# 3. Synchronize back to Unity/Engine properties
	# Phase 81: Professional Balancing (Caps & Diminishing Returns)
	
	# Attack Speed Cap (Standard: 2.5)
	final_stats["attackSpeed"] = min(2.5, final_stats["attackSpeed"])
	
	# Movement Speed Soft-Caps (LoL Standard)
	raw_ms = final_stats["moveSpeed"]
	if raw_ms > 490:
		final_stats["moveSpeed"] = 490 + (raw_ms - 490) * 0.5
	elif raw_ms > 415:
		final_stats["moveSpeed"] = 415 + (raw_ms - 415) * 0.8
		
	# Special handling for names mapping (e.g. magicResist vs mr)
	p["armor"] = final_stats["armor"]
	p["magicResist"] = final_stats["magicResist"]
	p["attackDamage"] = final_stats["ad"]
	p["ap"] = final_stats["ap"]
	p["moveSpeed"] = final_stats["moveSpeed"]
	p["speed"] = final_stats["moveSpeed"] # Sync for AI
	p["maxHealth"] = final_stats["maxHealth"]
	p["maxMana"] = final_stats["maxMana"]
	p["turnRate"] = final_stats["turnRate"]
	p["attackSpeed"] = final_stats["attackSpeed"]
	
	return final_stats

def play_sfx(target, path, volume=1.0, loop=False, pitch_var=0.0):
	"""
	High-fidelity sound player. 
	'target' can be a Scene (for global), Entity (for 3D audio), or Vector3 (for position).
	Phase 70: Uses Cave AudioTrack.play() API — the simplest documented path.
	
	Cave API reference:
	  AudioTrack(filename: str) — loads an audio file
	  AudioTrack.play(volume, loop, pitch, startPaused) — plays and returns handler int
	  AudioDevice.setSource3D(handlerID, entityID, distance)
	  AudioDevice.setPitch(handlerID, pitch)
	"""
	if not path: return None
	
	scene = None
	pos = None
	entity = None
	
	# Determine context from target
	if isinstance(target, cave.Scene):
		scene = target
	elif isinstance(target, cave.Entity):
		scene = target.getScene()
		entity = target
	elif isinstance(target, cave.Vector3):
		try: scene = cave.getScene()
		except: pass
		pos = target
	
	if not scene: return None
	
	try:
		# Cave API: AudioTrack(filename).play(volume, loop, pitch, startPaused)
		# loop: True = loop infinitely, False = play once
		loop_val = 999999 if loop else 0  # Cave API: loop is int (number of repeats, 0 = play once)
		track = cave.AudioTrack(path)
		
		# Calculate pitch with variance
		final_pitch = 1.0
		if pitch_var > 0:
			import random as _rand
			final_pitch = _rand.uniform(1.0 - pitch_var, 1.0 + pitch_var)
		
		# play() returns an AudioTrackInstance (1.5.0+)
		instance = track.play(volume, loop_val, final_pitch)
		
		# 3D audio positioning via AudioTrackInstance methods (Phase 80: Engine 1.5.0 Upgrade)
		if instance and (entity or pos):
			try:
				if entity:
					# 1.5.0 pattern: instance.setSource3D(entity, maxDistance)
					instance.setSource3D(entity, 20.0)
				elif pos:
					# 1.5.0 pattern: instance.calculate3D(vector, maxDistance)
					instance.calculate3D(pos, 20.0)
			except: pass
		
		return instance
	except Exception:
		return None

def apply_cc(target, type_str, duration, magnitude=0.0, source=None):
	"""Helper to apply CC flags to an entity's EffectComponent or PlayerController."""
	if not target: return
	# 1. Try Hero/PlayerController first
	pc = target.getPy("PlayerController") if hasattr(target, "getPy") else target
	if hasattr(pc, "applyEffect"):
		pc.applyEffect(type_str, duration, magnitude=magnitude, source=source)
		
		# Phase 131: CC Duration Bar (Feature 2)
		cc_bar = target.getPy("CCStatusBarController") if hasattr(target, "getPy") else None
		if cc_bar:
			cc_bar.show(type_str, duration)
		
		# Phase 100: Support Item CC Hook (Solstice Sleigh)
		if source:
			s_pc = source.getPy("PlayerController") if hasattr(source, "getPy") else None
			if s_pc:
				MobaItems.ItemEffectManager.on_cc_landed(s_pc, target)
		return

	# 2. Fallback to generic EffectComponent (Minions/Monsters)
	eff = target.getPy("EffectComponent") if hasattr(target, "getPy") else None
	if not eff: return
	
	cc_map = {
		"STUN": EffectFlags.STUN,
		"ROOT": EffectFlags.ROOT,
		"SILENCE": EffectFlags.SILENCE,
		"DISARM": EffectFlags.DISARM,
		"SLOW": EffectFlags.SLOW,
		"FEAR": EffectFlags.FEAR,
		"CHARM": EffectFlags.CHARM,
		"TAUNT": EffectFlags.TAUNT,
		"GROUNDED": EffectFlags.GROUNDED,
		"UNTARGETABLE": EffectFlags.UNTARGETABLE,
		"INVULNERABLE": EffectFlags.INVULNERABLE
	}
	
	flag = cc_map.get(type_str.upper(), EffectFlags.NONE)
	eff.apply(type_str + "_CC", duration, flags=flag, magnitude=magnitude, source=source)
	# Redundant but safe: ensure refresh_stats is called
	refresh_stats(target)

def apply_dot(target, damage_per_tick, duration, tick_rate=1.0, source=None, dmg_type=DamageType.MAGIC):
	"""
	Phase 40: Systematic DoT (Damage over Time).
	Applies damage at set intervals.
	"""
	if not target or not target.isActive(): return
	
	eff = target.getPy("EffectComponent")
	if eff:
		dot_id = f"DOT_{str(hash(source))}_{dmg_type}"
		eff.active_effects[dot_id] = StatusEffect(dot_id, duration, magnitude=damage_per_tick, source=source, tick_rate=tick_rate, dmg_type=dmg_type)

def spawn_projectile(scene, attacker, template, speed, damage, proj_range, proj_type=ProjectileType.PHYSICAL, trail=None, hit_vfx=None):
	"""
	Universal projectile spawner. Reuses or creates a pooled entity.
	"""
	global _PROJECTILE_POOLS
	if template not in _PROJECTILE_POOLS:
		_PROJECTILE_POOLS[template] = EntityPool(scene, template)
	
	spawn_pos = attacker.getTransform().worldPosition + attacker.getTransform().getForwardVector(True) * 1.5
	proj = _PROJECTILE_POOLS[template].acquire(spawn_pos)
	
	if proj:
		proj.getTransform().lookAtPosition(spawn_pos + attacker.getTransform().getForwardVector(True))
		
		comp = proj.getPy("ProjectileComponent")
		if not comp: comp = proj.add("ProjectileComponent")
		
		if comp:
			comp.speed = speed
			comp.damage = damage
			comp.range = proj_range
			comp.team = get_entity_team(attacker)
			comp.trail_template = trail
			comp.hit_vfx = hit_vfx
			comp.is_dead = False # Reset pooled state
			
		# Tag for pooling logic
		proj.getProperties()["pool_template"] = template
		return proj
	return None

def spawn_homing_projectile(scene, attacker, target, template, speed, damage, hit_vfx=None, is_basic=False):
	"""
	Phase 12: Homing Projectile. Reuses or creates a pooled entity.
	"""
	global _PROJECTILE_POOLS
	if template not in _PROJECTILE_POOLS:
		_PROJECTILE_POOLS[template] = EntityPool(scene, template)
	
	spawn_pos = attacker.getTransform().worldPosition + cave.Vector3(0, 1.5, 0)
	proj = _PROJECTILE_POOLS[template].acquire(spawn_pos)
	
	if proj:
		comp = proj.getPy("HomingProjectileComponent")
		if not comp: comp = proj.add("HomingProjectileComponent")
		
		if comp:
			comp.target = target
			comp.attacker = attacker
			comp.speed = speed
			comp.damage = damage
			comp.hit_vfx = hit_vfx
			comp.is_basic = is_basic
			comp.team = get_entity_team(attacker)
			comp.is_dead = False # Reset pooled state
			
		# Tag for pooling logic
		proj.getProperties()["pool_template"] = template
		return proj
	return None

def cleanup_entity_state(entity):
	"""
	Final Logic Seal: Cleans up all per-instance MOBA state.
	Ensures vision flags, shop status, and effects don't 'bleed' into respawns.
	"""
	if not entity: return
	props = entity.getProperties()
	props["in_brush_id"] = None
	props["canShop"] = False
	props["shieldHP"] = 0
	
	eff = entity.getPy("EffectComponent")
	if eff:
		eff.combined_flags = EffectFlags.NONE
		eff.active_effects.clear()
	
	pc = entity.getPy("PlayerController")
	if pc:
		pc.flags = EffectFlags.NONE
		if hasattr(pc, "activeEffects"): pc.activeEffects.clear()
		if hasattr(pc, "activeToggles"): pc.activeToggles.clear()
		if hasattr(pc, "cooldowns"):
			for k in pc.cooldowns: pc.cooldowns[k].reset()
		pc.mana = pc.maxMana # Reset resources correctly

def spawn_vfx(scene, template_name, pos, duration=2.0, parent=None):
	"""
	Spawns a visual effect template.
	If parent is provided, the VFX will follow that entity (useful for auras).
	Phase 70: Fixed localPosition API misuse → setPosition.
	"""
	if not template_name: return None
	vfx = scene.addFromTemplate(template_name, pos)
	if vfx:
		if parent:
			# Cave API: Entity.setParent(parent: Entity) — NOT Transform.setParent
			vfx.setParent(parent)
			vfx.getTransform().setPosition(0, 0, 0) # Center on parent
		
		# Auto-cleanup
		if vfx and duration > 0:
			vfx.scheduleKill(duration)
	return vfx

def broadcast_event(message, is_banner=False):
	"""Phase 115: Proxy to MobaUI.broadcast_event for convenience."""
	from UI import MobaUI
	MobaUI.broadcast_event(message)

def apply_circular_aoe(scene, center, radius, damage, dmg_type=DamageType.MAGIC, attacker=None, vfx_hit=None, cc_type=None, cc_dur=0.0):
	"""Applies damage and optional CC to all enemies in a radius."""
	ents = get_entities_in_radius(scene, center, radius)
	team = attacker.getProperties().get("team", Team.TEAM_A) if attacker else Team.TEAM_A
	enemyTag = Team.get_enemy(team)
	
	count = 0
	for e in ents:
		if not e.isActive(): continue
		if e.hasTag(enemyTag) and (e.hasTag("player") or e.hasTag("minion") or e.hasTag("monster")):
			apply_damage(e, damage, dmg_type, attacker=attacker)
			if cc_type:
				# apply_cc expects an entity, not a PlayerController
				apply_cc(e, cc_type, cc_dur, source=attacker)
			
			if vfx_hit:
				spawn_vfx(scene, vfx_hit, e.getTransform().worldPosition)
			count += 1
	return count
class RewardManager:
	"""Handles Gold and XP distribution upon death."""
	@staticmethod
	def distribute(victim, killer):
		if not victim: return
		
		# Base Rewards
		gold_val = 0
		xp_val = 0
		
		# Phase 77: Dynamic Reward Scaling
		mins = GameTick.get_time_minutes()
		scaling = 1.0 + (mins * 0.02) # Rewards grow by 2% per minute
		
		if victim.hasTag("player"):
			gold_val = BountyConfig.BASE_KILL_GOLD
			xp_val = 500
			
			# Phase 122: Bounty Payout
			v_pc = victim.getPy("PlayerController")
			if v_pc:
				gold_val += v_pc.bounty
				v_pc.bounty = 0
				v_pc.killStreak = 0
				# Reset Multi-kill window on death
				v_pc.multiKillCount = 0
		elif victim.hasTag("minion"):
			# Minion gold caps at 2.0x base
			m_scaling = min(2.0, 1.0 + (mins * 0.03))
			gold_val = int(20 * m_scaling)
			xp_val = int(60 * m_scaling)
		elif victim.hasTag("monster"):
			gold_val = int(victim.getProperties().get("goldReward", 50) * scaling)
			xp_val = int(victim.getProperties().get("xpReward", 100) * scaling)
			
		# Give gold to killer
		if killer:
			k_pc = killer.getPy("PlayerController")
			if k_pc:
				# Phase 101: Monster Hunter Penalty (Junglers take -50% CS Gold/XP early)
				reward_mult = 1.0
				if victim.hasTag("minion") and mins < 14.0:
					if k_pc.inventory_mgr.has_item_effect("onTick", "JUNGLE_HUNTER"):
						reward_mult = 0.5
				
				final_gold = int(gold_val * reward_mult)
				final_xp = int(xp_val * reward_mult)
				
				k_pc.leveling.gold += final_gold
				k_pc.add_exp(final_xp)
				MatchStatsManager.track_gold(killer.name, final_gold) # Phase 38
				
				# Phase 122: Update Killer Streak & Multi-Kill
				if victim.hasTag("player"):
					k_pc.handleKillStreak(victim)
				
				# Phase 35: Gold Popup
				if gold_val > 0:
					fct = victim.getPy("FloatingCombatTextComponent")
					if fct and hasattr(fct, "setup"):
						fct.setup(gold_val, DamageType.GOLD)

				# Phase 100: Support Economy (Gold Sharing)
				# 50% Gold to nearby allies with Support items (until 20 mins)
				mins = GameTick.get_time_minutes()
				if victim.hasTag("minion") and mins < 20:
					scene = victim.getScene()
					v_pos = victim.getTransform().worldPosition
					team = killer.getProperties().get("team")
					
					allies = [e for e in get_entities_in_radius(scene, v_pos, 14.0) 
							 if e.hasTag("player") and e.hasTag(team) and e != killer]
					
					for ally in allies:
						a_pc = ally.getPy("PlayerController")
						# Check if ally has Support item (SUPPORT_GOLD effect)
						if a_pc and a_pc.inventory_mgr.has_item_effect("onTick", "SUPPORT_GOLD"):
							share = int(gold_val * 0.5)
							a_pc.leveling.gold += share
							# Track for Evolution
							a_pc.quest_gold = getattr(a_pc, "quest_gold", 0) + share
							# Show popup for the support too
							MobaUI.spawn_fct(scene, ally.getTransform().worldPosition, f"+{share}G", cave.Vector4(0.8, 0.8, 0.0, 1.0))
				
				# Phase 32: Shutdown Bounty Logic
				if victim.hasTag("player"):
					v_pc = victim.getPy("PlayerController")
					
					# Track Kill/Death in stats
					MatchStatsManager.track_kill(killer.name)
					MatchStatsManager.track_death(victim.name)
					
					# --- Phase 115: Assist Tracking ---
					contribs = victim.getProperties().get("contributions", {})
					scene_time = victim.getScene().getElapsedSceneTime()
					for name, data in contribs.items():
						# data[0] is time, data[1] is entity
						c_time, c_ent = data
						if name != killer.name and (scene_time - c_time) < 10.0:
							# Valid Assist
							MatchStatsManager._get_stats(name)["assists"] += 1
							c_pc = c_ent.getPy("PlayerController")
							if c_pc: c_pc.leveling.assists += 1
					
					if v_pc and hasattr(v_pc, "killing_spree") and v_pc.killing_spree >= 3:
						# Bounty: 150G base + 50G per kill above 3
						bounty = 150 + ((v_pc.killing_spree - 3) * 50)
						k_pc.leveling.gold += bounty
						AnnouncerManager.announce_shutdown(killer, victim, bounty)
						v_pc.killing_spree = 0 # Reset victim spree
					
					# Report kill to Announcer for Multi-Kills
					AnnouncerManager.on_hero_kill(killer, victim)
				
				# Phase 31: XP Sharing Logic
				# Distribute XP pool among ALL allied heroes in radius
				scene = victim.getScene()
				v_pos = victim.getTransform().worldPosition
				team = killer.getProperties().get("team")
				
				allies = [e for e in get_entities_in_radius(scene, v_pos, 14.0) 
						 if e.hasTag("player") and e.hasTag(team) and e != killer]
				
				if allies:
					# Split XP: 100% to killer, 50% split among allies
					shared_xp = xp_val * GOLD_XP_SPLIT_PERCENT / len(allies)
					for ally in allies:
						# Phase 74: Check if ally is alive and NOT in fountain (invulnerability)
						a_pc = ally.getPy("PlayerController")
						if a_pc and not (a_pc.flags & EffectFlags.INVULNERABLE):
							if a_pc.respawnTimer <= 0:
								a_pc.add_exp(shared_xp)
				
				# Phase 28: Update Meta-Stats
				if victim.hasTag("player"):
					k_pc.leveling.kills += 1
				elif victim.hasTag("minion") or victim.hasTag("monster"):
					k_pc.leveling.cs += 1
					
				# Phase 101: Jungle Quest (Large Monsters)
				if victim.hasTag("monster") and victim.getProperties().get("isLarge", True):
					k_pc.large_monsters_killed = getattr(k_pc, "large_monsters_killed", 0) + 1
					if k_pc.large_monsters_killed == 20:
						MobaCommon.broadcast_event(f"The Jungle has Evolved! {killer.name}'s Smite is now PRIMAL.", is_banner=True)
						MobaCommon.play_sfx(killer, "SFX_Evolution")
				
				# Phase 100: Trigger Passive on Kill
				if hasattr(k_pc, "passive_mgr"):
					k_pc.passive_mgr.on_kill(victim)
					

		# Phase 28: Victim Death Increment
		v_pc = victim.getPy("PlayerController")
		if v_pc:
			v_pc.leveling.deaths += 1
		
		# Assist Logic (LoL Parity: 50% Gold/XP Pool split among contributors)
		contribs = victim.getProperties().get("contributions", {}) # {name: (time, ent)}
		now = victim.getScene().getElapsedSceneTime()
		
		valid_assistants = []
		for ent_name, data in contribs.items():
			last_hit_time = data[0]
			entity = data[1]
			# 10s Window for assists, must be active and not the killer
			if entity and entity.isActive() and entity != killer and (now - last_hit_time) <= 10.0:
				valid_assistants.append(entity)
				
		if valid_assistants:
			pool_gold = int(gold_val * GOLD_XP_SPLIT_PERCENT)
			pool_xp = int(xp_val * GOLD_XP_SPLIT_PERCENT)
			
			# Phase 100: Dredge's "Cut" (Global Share)
			# If killer is Dredge, the most recent assister gets FULL gold regardless of range
			is_dredge_ulti = False
			if killer:
				k_pc = killer.getPy("PlayerController")
				if k_pc and k_pc.heroName == "Dredge":
					# Only if killed with R (flag set in executeAbilityEffect)
					if getattr(k_pc, "last_kill_is_execute", False):
						is_dredge_ulti = True
						k_pc.last_kill_is_execute = False # Reset
			
			share_gold = int(pool_gold / len(valid_assistants))
			if is_dredge_ulti:
				# Most recent assistant gets 100% of the gold pool, others split
				# For simplicity: just give the whole pool to the first valid one if Dredge R'd
				# (Matches LoL Pyke's "Your Cut")
				share_gold = gold_val # Full base kill gold to the assistant!
				
			share_xp = int(pool_xp / len(valid_assistants))
			
			for ass in valid_assistants:
				a_pc = ass.getPy("PlayerController")
				if a_pc:
					a_pc.leveling.gold += share_gold
					a_pc.add_exp(share_xp)
					if victim.hasTag("player"): a_pc.leveling.assists += 1

def setup_combat_feedback(entity):
	"""Phase 35: Systemic attachment of FCT and Health Juice to units."""
	if not entity.getPy("FloatingCombatTextComponent"):
		entity.add("FloatingCombatTextComponent")
	if not entity.getPy("HealthJuiceComponent"):
		entity.add("HealthJuiceComponent")

def spawn_combat_text(entity, text, color=(1.0, 1.0, 1.0)):
	"""Phase 35: Convenience wrapper to show floating text above an entity."""
	fct = entity.getPy("FloatingCombatTextComponent") if entity else None
	if fct and hasattr(fct, "show_text"):
		try: fct.show_text(text, color)
		except: pass

class AnnouncerManager:
	"""Phase 32: Tracks killing sprees, multi-kill windows, and global broadcasts."""
	_multi_kill_window = 10.0 # Standard MOBA 10s window
	_spree_thresholds = {
		3: "Killing Spree", 4: "Rampage", 5: "Unstoppable", 
		6: "Dominating", 7: "Godlike", 8: "LEGENDARY"
	}
	_multi_labels = {
		2: ("Double Kill", "DOUBLE"), 
		3: ("Triple Kill", "TRIPLE"), 
		4: ("Quadra Kill", "DEFAULT"), # No quadra-specific art yet
		5: ("PENTAKILL!", "PENTA")
	}
	
	@staticmethod
	def on_hero_kill(killer, victim):
		k_pc = killer.getPy("PlayerController")
		if not k_pc: return
		
		# Phase 38: Stats
		MatchStatsManager.track_kill(killer.name)
		MatchStatsManager.track_death(victim.name)
		
		dt = cave.getDeltaTime()
		now = killer.getScene().getElapsedSceneTime()
		
		# 1. Killing Spree Logic
		k_pc.killing_spree = getattr(k_pc, "killing_spree", 0) + 1
		msg = AnnouncerManager._spree_thresholds.get(k_pc.killing_spree)
		if msg:
			AnnouncerManager.broadcast_global(f"{killer.name} is {msg.upper()}!", is_banner=True)
			
		# 2. Multi-Kill Logic
		last_kill_time = getattr(k_pc, "last_kill_time", 0.0)
		if (now - last_kill_time) <= AnnouncerManager._multi_kill_window:
			k_pc.multi_kill_count = getattr(k_pc, "multi_kill_count", 0) + 1
		else:
			k_pc.multi_kill_count = 1
			
		k_pc.last_kill_time = now
		
		multi_data = AnnouncerManager._multi_labels.get(k_pc.multi_kill_count)
		if multi_data:
			label, b_type = multi_data
			AnnouncerManager.broadcast_global(label.upper(), is_banner=True, source=killer, banner_type=b_type)
			
		# 3. Static Kill Feed Entry
		from UI import MobaUI
		MobaUI.add_kill_feed(killer, victim)
		
		# 4. Gold Popup FCT
		f_color = cave.Vector4(1.0, 0.8, 0.0, 1.0) # Gold
		MobaUI.spawn_fct(killer.getScene(), victim.getTransform().worldPosition, "+300G", f_color)

	@staticmethod
	def announce_shutdown(killer, victim, bounty):
		AnnouncerManager.broadcast_global(f"SHUT DOWN! {killer.name} ended {victim.name}'s spree (+{bounty}G)", is_banner=True)

	@staticmethod
	def broadcast_global(text, is_banner=False, source=None, banner_type="DEFAULT"):
		from UI import MobaUI
		# Feedback (Visual & Audio)
		if is_banner:
			MobaUI.show_announcement(text, banner_type=banner_type)
			if source: 
				scene = source.getScene()
				play_sfx(scene, Templates.SFX_ANNOUNCEMENT) 
		else:
			MobaUI.broadcast_event(text)

# ──────────────────────────────────────────────
# ROTATION HELPERS (Phase 76: Constant Turn Rate)
# ──────────────────────────────────────────────

def rotate_towards(transf, target_dir, dt, turn_rate):
	"""
	Smoothly rotates transf toward target_dir at a constant turn_rate (deg/s).
	Replaces instant lookAtSmooth for better tactical weight.
	"""
	if not target_dir or target_dir.length() < 0.001: return
	
	# Cave Engine API: lookAt is instant. 
	# To get constant rate, we lerp between current forward and target 
	# but limit the step size.
	
	current_fwd = transf.getForwardVector(True)
	target_fwd = target_dir.normalized()
	
	# Dot product for angle (Cave API .dot() or standard python)
	dot = current_fwd.x * target_fwd.x + current_fwd.z * target_fwd.z
	dot = max(-1.0, min(1.0, dot))
	
	angle_diff = math.degrees(math.acos(dot))
	
	if angle_diff < 0.1:
		transf.lookAt(target_fwd) # Snap if close
		return

	# Max rotation this frame
	max_rot = turn_rate * dt
	
	# Determine if we should snap or lerp
	# interpolation factor = max_rot / angle_diff
	factor = min(1.0, max_rot / angle_diff)
	
	# Use Cave's lookAtSmooth as the underlying lerp mechanism
	transf.lookAtSmooth(target_fwd, factor)

# ──────────────────────────────────────────────
# HELPER FUNCTIONS (Phase 70: Refactored to use SpatialGrid/EntityRegistry)
# ──────────────────────────────────────────────

def get_entities_in_radius(scene, center, radius):
	"""
	Returns all active entities within radius.
	Phase 70: Uses SpatialGrid for O(1) average spatial queries.
	"""
	# Optimized: EntityRegistry.tick(scene) now handled exclusively by GameTick
	return SpatialGrid.query_radius(center, radius)

def is_target_visible(attacker, target):
	"""
	Standardized Vision Check (Phase 39): Uses VisionManager cache.
	"""
	if not attacker or not target or not target.isActive():
		return False
		
	# --- Phase 65: Ward Stealth Gating ---
	if target.hasTag("ward"):
		# Check if it belongs to the same team
		if get_entity_team(attacker) == get_entity_team(target):
			return True
		
		# If it's a stealth ward on the enemy team, it MUST be revealed to be seen
		if target.getProperties().get("isStealthWard", False):
			eff = target.getPy("EffectComponent")
			if eff and eff.has_flag(EffectFlags.REVEALED): 
				return True
			return False # Hidden by default
		
		# Farsight wards (not stealth) are visible like normal units
	
	# 1. Revealed Status
	eff = target.getPy("EffectComponent")
	if eff and eff.has_flag(EffectFlags.REVEALED): return True
	
	# 2. Team Vision Cache
	team = attacker.getProperties().get("team")
	if not team: return True
	
	scene = attacker.getScene()
	VisionManager.update(scene) # Updates once per logic tick
	
	t_pos = target.getTransform().worldPosition
	t_brush = target.getProperties().get("in_brush_id")
	
	for v in VisionManager.get_allied_vision(team):
		diff = t_pos - v["pos"]
		dist = diff.length()
		if dist <= v["range"]:
			# --- Phase 81: Line-of-Sight Wall Occlusion ---
			# We only perform raycast if the target isn't already revealed by Brush logic
			is_in_same_brush = t_brush and (v["brush"] == t_brush or v["true_sight"])
			
			if t_brush and not is_in_same_brush:
				continue # Hidden in a different brush
				
			# Perform Line-of-Sight check for static geometry (Walls)
			# Start slightly above ground (1.5m) to avoid hitting the floor
			ray_start = v["pos"] + cave.Vector3(0, 1.5, 0)
			ray_end = t_pos + cave.Vector3(0, 1.5, 0)
			
			# Cave API: scene.rayCastAll returns hits sorted by distance
			hits = scene.rayCastAll(ray_start, ray_end)
			is_occluded = False
			for hit in hits:
				if hit.entity == target: break # Reached target safely
				# If we hit a static object or an indestructible wall before the target
				if hit.entity.hasTag("static") or hit.entity.hasTag("wall"):
					is_occluded = True
					break
			
			if not is_occluded:
				return True
				
	return False

def get_closest_target(center, radius, attacker=None):
	"""
	Returns the closest active visible enemy within radius of center.
	"""
	if attacker is None:
		return None
		
	scene = attacker.getScene()
	team = Team.TEAM_A if attacker.hasTag(Team.TEAM_A) else Team.TEAM_B
	enemy_tag = Team.get_enemy(team)

	best = None
	best_dist = float("inf")
	for e in get_entities_in_radius(scene, center, radius):
		if e.hasTag(enemy_tag) and is_target_visible(attacker, e):
			d = (e.getTransform().worldPosition - center).length()
			if d < best_dist:
				best_dist = d
				best = e
	return best

def apply_dot_hero(target_pc, dps, duration, source=None):
	"""
	Applies a damage-over-time (BLEED) effect to a PlayerController.
	The effect is tracked via applyEffect and ticked in PlayerController.update.
	"""
	if not target_pc: return
	target_pc.applyEffect("BLEED", duration, magnitude=dps, source=source)

def apply_execute_multiplier(damage, current_hp, max_hp):
	"""
	Scales execute damage up based on how much HP the target is missing.
	Returns 1x–2x multiplied damage (2x at 0 HP).
	"""
	if max_hp <= 0: return damage
	missing_pct = max(0.0, min(1.0, 1.0 - (current_hp / max_hp)))
	return damage * (1.0 + missing_pct)

def push_target(target, direction, distance):
	"""
	Applies instant knockback to an entity along direction.
	Uses Transform.applyMovement (correct Cave API for incremental position change).
	"""
	if not target or not target.isActive(): return
	move = direction.normalized() * distance
	target.getTransform().applyMovement(move)
	# Brief stun so pushback feels impactful
	# FIX: apply_cc expects an Entity, not a PlayerController
	apply_cc(target, "STUN", 0.3)

def pull_target(target, destination):
	"""
	Pulls an entity toward destination (hook/grab effect).
	Uses Transform.applyMovement for the displacement.
	"""
	if not target or not target.isActive(): return
	t_pos = target.getTransform().worldPosition
	diff = destination - t_pos
	target.getTransform().applyMovement(diff * 0.8)
	# FIX: apply_cc expects an Entity, not a PlayerController
	apply_cc(target, "STUN", 0.3)  # CC solidity: prevent fighting back during pull
	apply_cc(target, "ROOT", 0.5)

def spawn_hawkshot(controller):
	"""
	Spawns a scouting projectile (e.g. Ashe Hawkshot) toward mouse cursor.
	Grants vision at landing via VFX.
	"""
	scene = controller.entity.getScene()
	target_pos = getattr(controller, "clampedTargetPos", None)
	if not target_pos:
		out = scene.getDataOverMousePosition()
		if out.hit: target_pos = out.position
		
	if not target_pos: return
	spawn_projectile(
		scene, controller.entity,
		"HawkshotProjectile",
		speed=40.0, damage=0,
		proj_range=50.0,
		hit_vfx="VFX_Hawkshot_Land"
	)

def spawn_volley(controller, count, spread_deg, proj_range):
	scene = controller.entity.getScene()
	forward = controller.transf.getForwardVector(True)
	half = spread_deg / 2.0
	step = spread_deg / max(1, count - 1) if count > 1 else 0.0

	for i in range(count):
		angle_rad = math.radians(-half + step * i)
		cos_a = math.cos(angle_rad)
		sin_a = math.sin(angle_rad)
		# Correct 2D rotation for Z-forward/X-right space
		dir_x = forward.x * cos_a - forward.z * sin_a
		dir_z = forward.x * sin_a + forward.z * cos_a
		shot_dir = cave.Vector3(dir_x, 0.0, dir_z).normalized()
		
		# Offset slightly forward so it doesn't collide with the caster immediately
		spawn_pos = controller.transf.worldPosition + shot_dir * 1.8
		ad_val = getattr(controller, "ad", 15)
		
		proj = spawn_projectile(
			scene, controller.entity, 
			"Projectile_Basic", 
			speed=35.0, 
			damage=ad_val * 0.5, 
			proj_range=proj_range,
			hit_vfx=Templates.VFX_ATTACK_HIT
		)
		if proj:
			proj.getTransform().lookAt(shot_dir)


def save_match_result(winner_team, match_stats):
	"""
	Saves the final results of a match to a local JSON file.
	match_stats: List of dicts [{"hero": "Garen", "k": 10, "d": 2, "a": 5, "cs": 150}, ...]
	"""
	filepath = "match_history.json"
	history = []
	
	# Load existing history
	if os.path.exists(filepath):
		try:
			with open(filepath, "r") as f:
				history = json.load(f)
		except:
			history = []
			
	# Add new entry
	entry = {
		"date": time.strftime("%Y-%m-%d %H:%M:%S"),
		"winner": winner_team,
		"stats": match_stats
	}
	history.append(entry)
	
	# Keep only last 20 matches for performance
	if len(history) > 20:
		history = history[-20:]
		
	# Save back
	try:
		with open(filepath, "w") as f:
			json.dump(history, f, indent=4)
	except Exception as e:
		print(f"Failed to save match history: {e}")

def save_data(filename, data):
	"""Generic JSON saver."""
	import json
	try:
		with open(filename, "w") as f:
			json.dump(data, f, indent=4)
	except Exception as e:
		print(f"Failed to save {filename}: {e}")

def load_data(filename):
	"""Generic JSON loader."""
	import json
	import os
	if not os.path.exists(filename): return None
	try:
		with open(filename, "r") as f:
			return json.load(f)
	except:
		return None

def get_respawn_timer(level, scene_time):
	"""Phase 77: Professional Respawn Timer calculation.
	LoL-inspired: Base + Level scaling + Time scaling.
	"""
	mins = scene_time / 60.0
	# Base 6s + 2s per level (lvl18 = 42s)
	timer = 6.0 + (level * 2.0)
	
	# After 15 mins, timer increases by 1% per minute to force game resolution
	if mins > 15.0:
		timer *= (1.0 + (mins - 15.0) * 0.01)
		
	# Cap for prototype sanity
	return min(75.0, timer)

class ResonanceSpireType:
	AMPLIFIED = "AMPLIFIED" # Red - AD/AP
	HARMONIZED = "HARMONIZED" # Blue - Resists
	GLITCH = "GLITCH" # Orange - MS
	CHAOTIC = "CHAOTIC" # Purple - Haste

class ObjectiveBuffs:
	"""Phase 118: Strategic Buff Storage."""
	SPIRE_STACKS = { "teamA": {}, "teamB": {} } # team: { spireType: count }
	COLOSSUS_ACTIVE = { "teamA": 0.0, "teamB": 0.0 } # team: time_remaining
	
	@staticmethod
	def apply_spire(team, spire_type):
		stacks = ObjectiveBuffs.SPIRE_STACKS[team]
		stacks[spire_type] = stacks.get(spire_type, 0) + 1
		MobaUI.broadcast_event(f"TEAM {team[-1].upper()} captured a {spire_type} Resonance Spire!")

	@staticmethod
	def apply_colossus(team, duration=180.0):
		"""Phase 118 Fix: Orchestrate the global team buff."""
		ObjectiveBuffs.COLOSSUS_ACTIVE[team] = duration
		
		# 1. Global UI & Audio
		MobaUI.show_announcement(f"TEAM {team[-1].upper()} HAS SLAIN THE CRYSTALLINE COLOSSUS!", banner_type="PENTA")
		MobaCommon.play_sfx(cave.getScene(), MobaCommon.Templates.SFX_ACE)
		
		# 2. Apply Effect to all living teammates
		# This triggers the minion empowerment logic in MobaMinions.py
		players = EntityRegistry.get_team_entities(team, "player")
		for p in players:
			ec = p.getPy("EffectComponent")
			if ec:
				ec.apply("BARON_BUFF", duration)
				# 3. Visual Aura for the hero
				MobaCommon.spawn_vfx(p.getScene(), "VFX_Baron_Aura", p.getTransform().worldPosition, parent=p)

class MatchState:
	"""Phase 119: Lifecycle of a match."""
	PRE_DRAFT = "PRE_DRAFT"
	DRAFT = "DRAFT"
	LOADING = "LOADING"
	GATES_CLOSED = "GATES_CLOSED" # 0:00 - 0:15
	ACTIVE = "ACTIVE"
	FINISHED = "FINISHED"

class PingType:
	"""Phase 120: Tactical communication."""
	GENERIC = "GENERIC"
	OMW = "OMW"
	MIA = "MIA"
	DANGER = "DANGER"
	ASSIST = "ASSIST"

class CombatIntensity:
	"""Phase 120: Dynamic music levels."""
	IDLE = 0
	FARMING = 1
	COMBAT = 2
	BOSS = 3

class PlantType:
	"""Phase 121: Tactical Flora."""
	BLAST_CONE = "BLAST_CONE"
	VITALITY_BLOOM = "VITALITY_BLOOM"
	FLUX_SEEKER = "FLUX_SEEKER"

class MultiKillType:
	"""Phase 122: Hype & Bounties."""
	DOUBLE = "DOUBLE KILL"
	TRIPLE = "TRIPLE KILL"
	QUADRA = "QUADRA KILL"
	PENTA = "PENTA KILL"

class BountyConfig:
	"""Phase 122: Kill streaks and shutdowns."""
	MAX_BOUNTY = 700 # Balanced: Not too high, not too low
	STREAK_STEP = 50 # Every kill adds 50g bounty
	BASE_KILL_GOLD = 300

class VisionConstants:
	"""Phase 123: Vision Control."""
	WARD_DURATION = 90.0 # 1.5 mins
	WARD_SIGHT_RADIUS = 12.0
	ORACLE_DURATION = 10.0
	ORACLE_RADIUS = 8.0

class AIPersonality:
	"""Phase 126: Advanced AI Personalities."""
	BULLY      = "BULLY"      # Aggressive trades, tower dives
	FARMER     = "FARMER"     # Safe play, high CS priority
	TACTICIAN  = "TACTICIAN"  # Objective focus (Spires/Colossus)
	SUPPORTIVE = "SUPPORTIVE" # Stays near allies, focuses on peel
	ASSASSIN   = "ASSASSIN"   # Flanks, focuses squishy targets

class AIDifficulty:
	"""Phase 128: Global AI skill levels."""
	NORMAL = "NORMAL"
	PRO    = "PRO"

class TurretPlatingConfig:
	"""Phase 131: Turret Plating (Feature 6)."""
	PLATES = 5
	GOLD_PER_PLATE = 160
	HP_PER_PLATE = 1000 # Each plate adds 1000 HP to the turret
	FALL_OFF_TIME = 14.0 # Minutes - plates fall off at 14 min

class QuickCastConfig:
	"""Phase 131: Quick Cast settings (Feature 10)."""
	ENABLED_BY_DEFAULT = False

class VisionConstants2:
	"""Phase 123: Vision Control (continued)."""
	ORACLE_DURATION = 10.0
	ORACLE_RADIUS = 8.0

def get_mouse_position_ui():
	"""Phase 116: Returns the current mouse position in UI/Screen space.
	Cave API: cave.getMousePositionUI() returns UI-space coords."""
	return cave.getMousePositionUI()

def play_announcer(scene, line_key):
	"""Phase 119: Global announcer system."""
	# 1. Text Broadcast
	clean_text = line_key.upper().replace("_", " ")
	MobaUI.broadcast_event(f"[ANNOUNCER]: {clean_text}")
	# 2. Audio Trigger (In a full build, this plays specific .wav)
	# cave.playSound(f"Announcer_{line_key}")

def resolve_unit_overlap(entity, radius=1.0):
	"""Phase 117: Soft Collision. Prevents units from overlapping by applying a gentle push."""
	scene = entity.getScene()
	pos = entity.getTransform().worldPosition
	# Query nearby units
	contacts = scene.checkContactSphere(pos, radius * 1.5)
	push_vec = cave.Vector3(0, 0, 0)
	for c in contacts:
		if c.entity == entity: continue
		if not (c.entity.hasTag("player") or c.entity.hasTag("minion")): continue
		
		other_pos = c.entity.getTransform().worldPosition
		diff = pos - other_pos
		dist = diff.length()
		if dist < radius:
			# Apply push force proportional to overlap
			push_vec += diff.normalized() * (radius - dist) * 0.1
	
	if push_vec.length() > 0.01:
		# Cave API: Transform.move(x, y, z, local=False) for world-space movement
		entity.getTransform().move(push_vec.x, 0, push_vec.z, False)

def get_faction_shader_params(faction):
	"""Phase 117: Returns a dict of shader uniform names/values for each faction."""
	t = cave.getScene().getElapsedSceneTime() if cave.getScene() else 0.0
	if faction == "Rich Families":
		return {
			"u_crystallineIntensity": 0.5 + cave.math.sin(t * 2.0) * 0.2,
			"u_refractionScale": 0.1,
			"u_specularPulse": cave.math.cos(t) * 0.5 + 0.5
		}
	elif faction == "Imperium":
		return {
			"u_glitchFrequency": 15.0 if cave.math.sin(t * 10.0) > 0.8 else 0.0,
			"u_scanlineOffset": t % 1.0,
			"u_amplifiedTech": 1.0
		}
	elif faction == "Monster":
		return {
			"u_chaosDistortion": 0.2,
			"u_mutantHue": cave.math.sin(t * 0.5) * 0.1
		}
	elif faction == "Nomade":
		return {
			"u_heatHaze": 0.05,
			"u_organicGlow": 0.3
		}
	elif faction == "The Front":
		return {
			"u_interferenceAlpha": 0.4 if cave.math.sin(t * 20.0) > 0.5 else 0.1
		}
	return {}

# ──────────────────────────────────────────────
# AUDIT: Duplicate class definitions that previously existed here have been
# REMOVED. They were silently overwriting the earlier, more complete versions:
#   - MatchState (duplicate of line 2667)
#   - PingType (duplicate of line 2676)
#   - CombatIntensity (duplicate of line 2684)
#   - IndicatorType (duplicate of line 946)
#   - InhibitorRegistry (duplicate of line 416 — was MISSING reset(), broke GameTick.reset())
#   - GlobalObjectiveManager (duplicate of line 18 — was MISSING dragon/baron logic)
#   - play_announcer (duplicate of line 2751)
#   - reveal_unit (duplicate of line 790)
# ──────────────────────────────────────────────
