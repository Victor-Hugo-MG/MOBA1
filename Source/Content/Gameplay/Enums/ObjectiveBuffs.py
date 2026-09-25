import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core import MobaCommon
from Core.MobaCommon import EntityRegistry
from UI import MobaUI

class ObjectiveBuffs:
	"""Phase 118: Strategic Buff Storage."""
	SPIRE_STACKS = { "teamA": {}, "teamB": {} } # team: { spireType: count }
	COLOSSUS_ACTIVE = { "teamA": 0.0, "teamB": 0.0 } # team: time_remaining
	
	@staticmethod
	def apply_spire(team, spire_type):
		stacks = ObjectiveBuffs.SPIRE_STACKS[team]
		stacks[spire_type] = stacks.get(spire_type, 0) + 1
		MobaUI.broadcast_event(f"TEAM {team[-1].upper()} captured a {spire_type} Resonance Spire!")

	@staticmethod
	def apply_colossus(team, duration=180.0):
		"""Phase 118 Fix: Orchestrate the global team buff."""
		ObjectiveBuffs.COLOSSUS_ACTIVE[team] = duration
		
		# 1. Global UI & Audio
		MobaUI.show_announcement(f"TEAM {team[-1].upper()} HAS SLAIN THE CRYSTALLINE COLOSSUS!", banner_type="PENTA")
		MobaCommon.play_sfx(cave.getScene(), MobaCommon.Templates.SFX_ACE)
		
		# 2. Apply Effect to all living teammates
		# This triggers the minion empowerment logic in MobaMinions.py
		players = EntityRegistry.get_team_entities(team, "player")
		for p in players:
			ec = p.getPy("EffectComponent")
			if ec:
				ec.apply("BARON_BUFF", duration)
				# 3. Visual Aura for the hero
				MobaCommon.spawn_vfx(p.getScene(), "VFX_Baron_Aura", p.getTransform().worldPosition, parent=p)
