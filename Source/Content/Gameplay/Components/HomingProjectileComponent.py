import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core import MobaCommon
from Core.MobaCommon import *

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
