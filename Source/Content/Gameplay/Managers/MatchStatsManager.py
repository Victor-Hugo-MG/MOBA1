import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core.MobaCommon import GameTick, is_target_visible

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
