import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class BountyConfig:
	"""Phase 122: Kill streaks and shutdowns."""
	MAX_BOUNTY = 700 # Balanced: Not too high, not too low
	STREAK_STEP = 50 # Every kill adds 50g bounty
	BASE_KILL_GOLD = 300
