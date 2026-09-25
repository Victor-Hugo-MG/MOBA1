import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class Team:
	NEUTRAL = "neutral"
	TEAM_A  = "teamA"
	TEAM_B  = "teamB"

	@staticmethod
	def get_enemy(team):
		if team == Team.TEAM_A: return Team.TEAM_B
		if team == Team.TEAM_B: return Team.TEAM_A
		return Team.NEUTRAL

	# Phase 24: Team Color Mapping for VFX/UI consistency
	COLORS = {
		"teamA":  cave.Vector4(0.2, 0.4, 1.0, 1.0), # Blue
		"teamB":  cave.Vector4(1.0, 0.2, 0.2, 1.0), # Red
		"neutral": cave.Vector4(0.8, 0.8, 0.2, 1.0)  # Yellow/Gold
	}
