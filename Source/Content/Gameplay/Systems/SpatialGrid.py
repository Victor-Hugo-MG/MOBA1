import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core.MobaCommon import EntityRegistry

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
