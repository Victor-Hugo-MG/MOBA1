import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class DamageType:
	PHYSICAL = 0
	MAGIC = 1
	TRUE = 2
	PURE = 3 # Ignores shields
	HEAL = 4
	GOLD = 5 # Phase 35: Visual only
