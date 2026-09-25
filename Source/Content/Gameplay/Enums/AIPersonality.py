import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class AIPersonality:
	"""Phase 126: Advanced AI Personalities."""
	BULLY      = "BULLY"      # Aggressive trades, tower dives
	FARMER     = "FARMER"     # Safe play, high CS priority
	TACTICIAN  = "TACTICIAN"  # Objective focus (Spires/Colossus)
	SUPPORTIVE = "SUPPORTIVE" # Stays near allies, focuses on peel
	ASSASSIN   = "ASSASSIN"   # Flanks, focuses squishy targets
