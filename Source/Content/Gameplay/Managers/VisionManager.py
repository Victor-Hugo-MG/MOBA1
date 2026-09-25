import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core.MobaCommon import GameTick, EntityRegistry, get_entity_team

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
