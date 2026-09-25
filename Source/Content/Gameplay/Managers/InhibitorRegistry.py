import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class InhibitorRegistry:
	"""Phase 77: Global state for inhibitors.
	_status: {(team, laneID): destroyed_until_timestamp}
	"""
	_status = {}

	@staticmethod
	def set_destroyed(team, lane_id, respawn_time):
		InhibitorRegistry._status[(team, lane_id)] = respawn_time

	@staticmethod
	def is_down(team, lane_id, current_time):
		# If team/lane is in registry and ready_at > current_time, it's DOWN
		limit = InhibitorRegistry._status.get((team, lane_id), 0)
		return limit > current_time

	@staticmethod
	def reset():
		InhibitorRegistry._status = {}
