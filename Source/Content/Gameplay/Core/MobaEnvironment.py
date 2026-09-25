import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core import MobaCommon

class BushComponent(cave.Component):
	"""Hides entities inside from aquellos outside."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.radius = 3.5
		self.update_timer = 0.0
		# Unique ID for this bush instance to correlate with entity 'inside' status
		self.bush_id = f"bush_{self.entity.getUniqueName()}"
		
	def update(self):
		# Throttling to 10Hz (Bible Constraint: Optimization for non-spatial environmental logic)
		self.update_timer -= cave.getDeltaTime()
		if self.update_timer > 0: return
		self.update_timer = 0.1

		scene = self.entity.getScene()
		ents = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, self.radius)
		
		for e in ents:
			if e.hasTag("player") or e.hasTag("minion"):
				# Register entity as being inside THIS specific bush
				e.getProperties()["current_bush"] = self.bush_id
				e.getProperties()["last_bush_time"] = scene.getElapsedSceneTime()

class LifetimeComponent(cave.Component):
	"""Generic self-destruct timer."""
	duration = 5.0
	
	def start(self, scene):
		self.entity.scheduleKill(self.duration)
		
	def update(self):
		pass

class PlantComponent(cave.Component):
	"""Phase 100: Hit-based environmental object (Honeyfruit)."""
	def start(self, scene):
		self.hits = 3
		self.entity.getProperties()["health"] = 3
		self.entity.getProperties()["maxHealth"] = 3
		self.entity.addTag("plant")
		MobaCommon.setup_combat_feedback(self.entity)
		
	def update(self):
		if self.entity.getProperties().get("health", 0) <= 0:
			self.on_destroy()
			
	def on_destroy(self):
		scene = self.entity.getScene()
		pos = self.entity.getTransform().worldPosition
		# Spawn 5 small healing fruits in a spread
		import random
		for _ in range(5):
			offset = cave.Vector3(random.uniform(-2, 2), 0.5, random.uniform(-2, 2))
			fruit = scene.addFromTemplate("HealingFruitTemplate", pos + offset)
			if fruit:
				fruit.add("FruitPickupComponent")
		
		MobaCommon.play_sfx(self.entity, "SFX_Plant_Destroy")
		self.entity.kill()

class FruitPickupComponent(cave.Component):
	"""Phase 100: Small pickup that heals player on contact."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.radius = 1.5
		self.heal_amount = 60 # Balanced per pickup
		
	def update(self):
		scene = self.entity.getScene()
		# Search only for players in a small radius
		ents = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, self.radius)
		for e in ents:
			if e.hasTag("player") and e.isActive():
				self.on_pickup(e)
				break
				
	def on_pickup(self, player):
		MobaCommon.apply_heal(player, self.heal_amount)
		MobaCommon.play_sfx(player, "SFX_Fruit_Pickup", pitch_var=0.2)
		# Optional: Spawn tiny sparkle VFX
		self.entity.kill()
