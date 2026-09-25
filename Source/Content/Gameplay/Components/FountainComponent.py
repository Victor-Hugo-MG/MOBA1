import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core.MobaCommon import *


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
