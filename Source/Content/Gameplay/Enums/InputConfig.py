import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Enums.CastingMode import CastingMode



class InputConfig:
	"""Phase 116: Centralized Keybinds and Input Preferences."""
	# Modifiers
	KEY_TARGET_HEROES_ONLY = cave.event.KEY_BACKQUOTE # Tilde/Grave
	
	# Action Keys
	KEY_ATTACK_MOVE = cave.event.KEY_A
	KEY_RECALL = cave.event.KEY_B
	KEY_STOP = cave.event.KEY_S
	KEY_LOCK_CAM = cave.event.KEY_Y
	KEY_SHOP = cave.event.KEY_P
	KEY_CENTER_CAM = cave.event.KEY_SPACE
	KEY_PING_GENERIC = cave.event.KEY_G
	KEY_PING_DANGER = cave.event.KEY_V
	
	# Casting Preferences
	SMART_CAST_BY_DEFAULT = True 
	CLAMP_CAST_AT_MAX_RANGE = True 
	AUTO_ATTACK_ENABLED = False 
	ATTACK_MOVE_ON_LEFT_CLICK = False # High-level setting
	TREAT_TARGET_HEROES_ONLY_AS_TOGGLE = False 
	
	# Per-Slot Casting Modes
	SLOT_CASTING_MODES = {
		"Q": CastingMode.QUICK,
		"W": CastingMode.QUICK,
		"E": CastingMode.QUICK,
		"R": CastingMode.QUICK_WITH_INDICATOR, # Default Ult to indicator for safety
		"D": CastingMode.QUICK,
		"F": CastingMode.QUICK
	}
