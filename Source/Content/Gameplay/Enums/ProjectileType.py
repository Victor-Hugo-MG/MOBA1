import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class ProjectileType:
	PHYSICAL = 0
	MAGICAL  = 1
	BOTH     = 2
