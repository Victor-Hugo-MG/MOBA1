import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core.MobaCommon import GameTick, SpatialGrid

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
