import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class ResonanceSpireType:
	AMPLIFIED = "AMPLIFIED" # Red - AD/AP
	HARMONIZED = "HARMONIZED" # Blue - Resists
	GLITCH = "GLITCH" # Orange - MS
	CHAOTIC = "CHAOTIC" # Purple - Haste
