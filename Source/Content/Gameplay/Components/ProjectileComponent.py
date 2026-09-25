import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core.MobaCommon import *

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
		self.hit_entities = set()
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
			if e.name in self.hit_entities: continue
			
			if e.hasTag(enemyTag) and (e.hasTag("player") or e.hasTag("minion") or e.hasTag("monster")):
				self.hit_entities.add(e.name)
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
