import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class DamageFlags:
	"""Bitflags for damage context (critical, basic attack, etc)."""
	NONE = 0
	CRITICAL = 1
	BASIC_ATTACK = 2
	AOE = 4
