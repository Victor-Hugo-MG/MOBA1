import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class MatchState:
	"""Phase 119: Lifecycle of a match."""
	PRE_DRAFT = "PRE_DRAFT"
	DRAFT = "DRAFT"
	LOADING = "LOADING"
	GATES_CLOSED = "GATES_CLOSED" # 0:00 - 0:15
	ACTIVE = "ACTIVE"
	FINISHED = "FINISHED"
