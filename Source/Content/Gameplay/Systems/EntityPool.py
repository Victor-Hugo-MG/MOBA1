import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



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
