import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class PingType:
	"""Phase 120: Tactical communication."""
	GENERIC = "GENERIC"
	OMW = "OMW"
	MIA = "MIA"
	DANGER = "DANGER"
	ASSIST = "ASSIST"
