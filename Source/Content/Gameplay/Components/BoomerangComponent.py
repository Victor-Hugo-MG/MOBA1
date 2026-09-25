import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core import MobaCommon

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
			MobaCommon.release_entity(self.entity)
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
				MobaCommon.release_entity(self.entity)
				return
			dir = diff.normalized()
			
		self.transf.applyMovement(dir * self.speed * dt)
		self.transf.lookAtPosition(curr_pos + dir)
		
		# Collision
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
