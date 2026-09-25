import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core.MobaCommon import *


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
