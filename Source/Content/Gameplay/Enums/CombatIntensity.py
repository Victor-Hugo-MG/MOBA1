import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class CombatIntensity:
	"""Phase 120: Dynamic music levels."""
	IDLE = 0
	FARMING = 1
	COMBAT = 2
	BOSS = 3
