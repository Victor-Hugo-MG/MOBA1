import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class VisionConstants:
	"""Phase 123: Vision Control."""
	WARD_DURATION = 90.0 # 1.5 mins
	WARD_SIGHT_RADIUS = 12.0
	ORACLE_DURATION = 10.0
	ORACLE_RADIUS = 8.0
