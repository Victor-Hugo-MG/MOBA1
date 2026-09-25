import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class TurretPlatingConfig:
	"""Phase 131: Turret Plating (Feature 6)."""
	PLATES = 5
	GOLD_PER_PLATE = 160
	HP_PER_PLATE = 1000 # Each plate adds 1000 HP to the turret
	FALL_OFF_TIME = 14.0 # Minutes - plates fall off at 14 min
