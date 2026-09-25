import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Enums.DamageType import DamageType
from Enums.EffectFlags import EffectFlags



class StatusEffect:
	"""Internal object to track an active effect on a player."""
	def __init__(self, id, duration, flags=0, magnitude=0.0, source=None, tick_rate=1.0, dmg_type=DamageType.MAGIC):
		self.id = id
		self.duration = duration
		self.flags = flags
		self.magnitude = magnitude
		self.source = source # Entity that applied the effect
		self.tick_rate = tick_rate
		self.dmg_type = dmg_type
		self.next_tick = tick_rate # Time until next damage tick
		
	def tick(self, dt):
		"""Returns True if the effect has expired."""
		self.duration -= dt
		return self.duration <= 0

	def is_cc(self):
		"""Returns True if this effect contains hard crowd control."""
		hard_cc = EffectFlags.STUN | EffectFlags.ROOT | EffectFlags.SILENCE | EffectFlags.FEAR | EffectFlags.CHARM
		return (self.flags & hard_cc) != 0
