import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class EffectFlags:
	NONE        = 0
	STUN        = 1 << 0
	ROOT        = 1 << 1
	SILENCE     = 1 << 2
	DISARM      = 1 << 3
	INVULNERABLE = 1 << 4
	UNTARGETABLE = 1 << 5
	SHIELD      = 1 << 6
	SLOW        = 1 << 7
	TAUNT       = 1 << 8
	CHARM       = 1 << 9
	FEAR        = 1 << 10
	GROUNDED    = 1 << 11
	BLEED       = 1 << 12
	CREST_FIRE  = 1 << 13 # Red Buff
	CREST_INSIGHT = 1 << 14 # Blue Buff
	BARON_BUFF  = 1 << 15
	REVEALED    = 1 << 16
	CONTINUOUS  = 1 << 17 # Used for DoTs to suppress redundant FX
	CHANNELING  = 1 << 18
	RECALLING   = 1 << 19
	HIDDEN      = 1 << 20 # Phase 30: Invisible while in brush
	DEFLECT_PHYS  = 1 << 21 # Phase 70: Physical projectile deflection
	DEFLECT_MAGIC = 1 << 22 # Phase 70: Magical projectile deflection
	DEFLECT_MAGICAL = DEFLECT_MAGIC # Phase 70: Compatibility alias
	BASIC_ATTACK  = 1 << 23 # Phase 100: Distinguishes AAs from Spells
	CAMOUFLAGE    = 1 << 24 # Phase 101: Glass-shade + Untargetable + Hidden UI
	GHOST         = 1 << 25 # Phase 110: Ignore unit collision
	CC            = 1 << 26 # Generic CC marker for item interactions
	BUFF          = 1 << 27 # Positive buff marker (prevents cleanse removal)
