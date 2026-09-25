import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core.MobaCommon import apply_damage, DamageType, apply_heal

class RuneManager:
	"""Phase 102: Manages the active keystone rune for a PlayerController."""
	def __init__(self, pc, rune_id):
		self.pc = pc
		self.rune_id = rune_id
		self.stacks = 0
		self.cooldown = 0.0
		self.proc_ready = True
		
	def update(self, dt):
		"""Tick cooldown."""
		if self.cooldown > 0:
			self.cooldown -= dt
			if self.cooldown <= 0:
				self.proc_ready = True
				
	def on_hit(self, target, is_ability=False):
		"""Called when the owner damages a target."""
		if not self.proc_ready:
			return
			
		if self.rune_id == "LETHAL_TEMPO":
			self.stacks = min(6, self.stacks + 1)
		elif self.rune_id == "CONQUEROR":
			self.stacks = min(12, self.stacks + (2 if is_ability else 1))
			if self.stacks >= 12:
				# Heal 8% of damage dealt
				self.pc.bonusAD += 2.0  # Minor AD per proc
		elif self.rune_id == "ELECTROCUTE":
			self.stacks += 1
			if self.stacks >= 3 and self.proc_ready:
				# Proc burst damage
				bonus_dmg = 30 + (self.pc.level * 8) + (self.pc.ap * 0.25)
				apply_damage(target, bonus_dmg, DamageType.MAGIC, attacker=self.pc.entity)
				self.stacks = 0
				self.proc_ready = False
				self.cooldown = 25.0
		elif self.rune_id == "GRASP_OF_THE_UNDYING":
			self.stacks += 1
			if self.stacks >= 4 and self.proc_ready:
				heal_amt = self.pc.maxHP * 0.03
				apply_heal(self.pc.entity, heal_amt)
				self.stacks = 0
				self.proc_ready = False
				self.cooldown = 4.0

	def reset_stacks(self):
		"""Reset stacks (e.g. out of combat)."""
		self.stacks = 0
