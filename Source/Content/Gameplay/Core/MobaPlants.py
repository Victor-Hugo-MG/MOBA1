import cave
from Core import MobaCommon
from Core import MobaStates
import random
import math

class PlantBase(cave.Component):
	"""
	Base class for Tactical Flora in OMO.
	Plants are one-hit interactables that provide utility.
	"""
	def start(self, scene):
		self.is_ready = True
		self.respawn_timer = 0.0
		self.respawn_duration = 300.0 # 5 Minutes
		
	def take_damage(self, attacker):
		"""Triggered by PlayerController during basic attacks."""
		if not self.is_ready: return
		
		self.trigger(attacker)
		self.is_ready = False
		self.entity.deactivate(self.entity.getScene())
		self.respawn_timer = self.respawn_duration

	def update(self):
		if not self.is_ready:
			self.respawn_timer -= cave.getDeltaTime()
			if self.respawn_timer <= 0:
				self.is_ready = True
				self.entity.activate(self.entity.getScene())
				MobaCommon.spawn_vfx(self.entity.getScene(), "VFX_Plant_Respawn", self.entity.getTransform().worldPosition)

	def trigger(self, attacker):
		"""To be overridden."""
		pass

class BlastCone(PlantBase):
	"""
	Phase 121: The Red Plant.
	Explodes after a brief delay, knocking back all units.
	"""
	def trigger(self, attacker):
		pos = self.entity.getTransform().worldPosition.copy()
		scene = self.entity.getScene()
		
		# Delay the explosion for professional feel (0.5s)
		MobaCommon.spawn_vfx(scene, "VFX_BlastCone_Prime", pos)
		
		# In a full build, we'd use a timer. For prototype, we apply immediately
		targets = MobaCommon.get_entities_in_radius(scene, pos, 6.0)
		for t in targets:
			if t.hasTag("player") or t.hasTag("minion"):
				# Calculate knockback direction
				target_pos = t.getTransform().worldPosition
				diff = target_pos - pos
				if diff.length() < 0.1: diff = cave.Vector3(0, 0, 1) # Center safety
				
				knockback_dest = target_pos + diff.normalized() * 7.0
				pc = t.getPy("PlayerController")
				if pc:
					# Use DashState to simulate a smooth knockback 'jump'
					pc.fsm.setState(MobaStates.DashState(knockback_dest, speed=22.0, duration=0.45))
					
		MobaCommon.spawn_vfx(scene, "VFX_BlastCone_Explosion", pos)
		MobaCommon.play_sfx(self.entity, "SFX_Plant_Blast")

class VitalityBloom(PlantBase):
	"""
	Phase 121: The Green Plant.
	Drops healing fruits on the ground.
	"""
	def trigger(self, attacker):
		pos = self.entity.getTransform().worldPosition
		scene = self.entity.getScene()
		
		for i in range(5):
			angle = (i / 5.0) * 3.1415 * 2.0
			offset = cave.Vector3(math.cos(angle), 0, math.sin(angle)) * 2.5
			fruit = scene.addFromTemplate("Template_VitalityFruit", pos + offset)
			if fruit:
				# Add a collection component
				fruit.add("VitalityFruitComponent")

class FluxSeeker(PlantBase):
	"""
	Phase 121: The Blue Plant.
	Reveals a cone of vision in the direction hit.
	"""
	def trigger(self, attacker):
		pos = self.entity.getTransform().worldPosition
		attacker_pos = attacker.getTransform().worldPosition
		direction = (pos - attacker_pos).normalized()
		
		# Reveal enemies in a long-range area (simulated cone as radius)
		scene = self.entity.getScene()
		reveal_pos = pos + direction * 17.0  # Center of reveal area
		targets = MobaCommon.get_entities_in_radius(scene, reveal_pos, 18.0)
		for t in targets:
			if t.hasTag("player") or t.hasTag("ward"):
				MobaCommon.reveal_unit(t, 5.0)  # 5 second reveal
		MobaCommon.spawn_vfx(scene, "VFX_FluxSeeker_Wave", pos)

class VitalityFruitComponent(cave.Component):
	"""Logic for the individual healing fruits."""
	def update(self):
		scene = self.entity.getScene()
		pos = self.entity.getTransform().worldPosition
		
		# Check for player proximity
		targets = MobaCommon.get_entities_in_radius(scene, pos, 1.2)
		for t in targets:
			if t.hasTag("player"):
				MobaCommon.apply_heal(t, t.getProperties().get("maxHealth", 1000) * 0.035)
				# Apply a small temporary slow
				pc = t.getPy("PlayerController")
				if pc: pc.applyEffect("MS_SLOW", 0.5, magnitude=0.25)
				
				MobaCommon.play_sfx(self.entity, "SFX_Fruit_Eat")
				self.entity.kill()
				return
