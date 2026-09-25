import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class PlantType:
	"""Phase 121: Tactical Flora."""
	BLAST_CONE = "BLAST_CONE"
	VITALITY_BLOOM = "VITALITY_BLOOM"
	FLUX_SEEKER = "FLUX_SEEKER"
