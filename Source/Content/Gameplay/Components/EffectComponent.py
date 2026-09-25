import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core.MobaCommon import *


class EffectComponent(cave.Component):
	"""Handles CC timers and active status effects on an entity."""
	def start(self, scene):
		self.active_effects = {} # {id: StatusEffect}
		self.combined_flags = 0
		self.pc = self.entity.getPy("PlayerController")
		self.needs_recalc = False # Final Phase Optimization
		
	def remove_negative_effects(self):
		"""Cleanses all crowd control and harmful debuffs."""
		neg_flags = EffectFlags.STUN | EffectFlags.ROOT | EffectFlags.SILENCE | \
					EffectFlags.DISARM | EffectFlags.SLOW | EffectFlags.TAUNT | \
					EffectFlags.CHARM | EffectFlags.FEAR | EffectFlags.GROUNDED | \
					EffectFlags.BLEED
					
		to_remove = []
		for eid, eff in self.active_effects.items():
			if eff.flags & neg_flags:
				to_remove.append(eid)
				
		for eid in to_remove:
			del self.active_effects[eid]
			
		if to_remove:
			self._recalculate_flags()
			self.needs_recalc = True
		
	def apply(self, effect_id, duration, flags=EffectFlags.NONE, magnitude=0.0, dmg_type=DamageType.MAGIC, source=None):
		self.active_effects[effect_id] = StatusEffect(effect_id, duration, flags, magnitude, source=source, dmg_type=dmg_type)
		self._recalculate_flags()
		# Optimized: Mark for recalc next frame or end of logic
		self.needs_recalc = True 
		# If it's a critical CC, refresh immediately for AI responsiveness
		if flags & (EffectFlags.STUN | EffectFlags.ROOT | EffectFlags.SILENCE):
			refresh_stats(self.entity)
			self.needs_recalc = False
		
	def add_flag(self, flag):
		"""Directly enables a bitmask flag on the combined_flags (for persistent toggles)."""
		self.combined_flags |= flag
		
	def remove_flag(self, flag):
		"""Directly removes a bitmask flag from combined_flags."""
		self.combined_flags &= ~flag
		
	def _recalculate_flags(self):
		self.combined_flags = 0
		for e in self.active_effects.values():
			self.combined_flags |= e.flags

	def has_flag(self, flag):
		return (self.combined_flags & flag) != 0

	def is_cced(self):
		"""Returns True if any hard crowd control is active (Stun, Fear, Charm)."""
		hard_cc = EffectFlags.STUN | EffectFlags.FEAR | EffectFlags.CHARM
		return self.has_flag(hard_cc)

	def is_stunned(self):
		return self.has_flag(EffectFlags.STUN)

	def is_rooted(self):
		return self.has_flag(EffectFlags.ROOT)

	def is_silenced(self):
		return self.has_flag(EffectFlags.SILENCE)

	def is_invulnerable(self):
		return self.has_flag(EffectFlags.INVULNERABLE)

	def is_untargetable(self):
		return self.has_flag(EffectFlags.UNTARGETABLE)

	def get_magnitude(self, effect_id):
		eff = self.active_effects.get(effect_id)
		# Phase 72 FIX: Use object property '.magnitude' instead of dict subscript
		return eff.magnitude if eff else 0.0

	def update(self):
		dt = cave.getDeltaTime()
		to_remove = []
		for eid, eff in self.active_effects.items():
			# Logic for Damage over Time (DoT)
			# DoTs are identified by the name "DOT_" or "BLEED"
			is_dot = "DOT_" in eid or "BLEED" in eid or "HEMORRHAGE" in eid
			if is_dot:
				eff.next_tick -= dt
				if eff.next_tick <= 0:
					eff.next_tick = eff.tick_rate
					# Apply damage using standardized applicator
					# magnitude used as damage per tick
					apply_damage(self.entity, eff.magnitude, eff.dmg_type, attacker=eff.source)

			if eff.tick(dt):
				to_remove.append(eid)
		
		if to_remove:
			for eid in to_remove:
				del self.active_effects[eid]
			self._recalculate_flags()
			self.needs_recalc = True
			
		if self.needs_recalc:
			refresh_stats(self.entity)
			self.needs_recalc = False
