import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core.MobaCommon import GameTick, broadcast_event

class GlobalObjectiveManager:
	"""Phase 105: Tracks global buff stacks and active neutral objective respawns."""
	dragon_stacks = {"teamA": 0, "teamB": 0}
	respawn_timers = {} # { "SPIRE_AMPLIFIED": time_float, ... }
	
	@staticmethod
	def start_respawn(obj_id, delay):
		now = GameTick.get_time_minutes() * 60.0
		GlobalObjectiveManager.respawn_timers[obj_id] = now + delay
		
	@staticmethod
	def get_timer(obj_id):
		now = GameTick.get_time_minutes() * 60.0
		rem = GlobalObjectiveManager.respawn_timers.get(obj_id, 0) - now
		return max(0, rem)
	baron_active = {"teamA": False, "teamB": False}
	

	@staticmethod
	def add_dragon(team):
		GlobalObjectiveManager.dragon_stacks[team] += 1
		broadcast_event(f"{team.upper()} has slain the Dragon! (Stacks: {GlobalObjectiveManager.dragon_stacks[team]})")

	@staticmethod
	def get_dragon_mult(team, stat_type):
		"""Returns the multiplier based on number of dragon kills."""
		stacks = GlobalObjectiveManager.dragon_stacks.get(team, 0)
		if stat_type == "ADAP": return 1.0 + (stacks * 0.04) # 4% per stack
		if stat_type == "RESIST": return 1.0 + (stacks * 0.05) # 5% per stack
		return 1.0
		
	@staticmethod
	def reset():
		GlobalObjectiveManager.dragon_stacks = {"teamA": 0, "teamB": 0}
		GlobalObjectiveManager.baron_active = {"teamA": False, "teamB": False}
