import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class Templates:
	"""Phase 24: Centralized Asset Registry to prevent string hallucinations."""
	# Minions
	MINION_MELEE   = "Minion_Melee"
	MINION_RANGED  = "Minion_Ranged"
	MINION_CANNON  = "Minion_Cannon"
	
	# Projectiles
	PROJ_BASIC     = "Projectile_Basic"
	PROJ_MINION    = "Projectile_Minion"
	PROJ_TURRET    = "TurretProjectile" # Direct mapping for stability
	
	# VFX
	VFX_ATTACK_HIT = "VFX_Blood_Burst"
	VFX_TURRET_HIT = "VFX_TurretHit"
	VFX_TURRET_EXP = "VFX_Turret_Explosion"
	VFX_DEATH      = "VFX_Generic_Death"
	VFX_LEVEL_UP   = "VFX_LevelUp_Gold"
	
	# SFX
	SFX_TURRET_FIRE = "SFX_Turret_Fire"
	SFX_MINION_ATK  = "SFX_Minion_Attack"
	SFX_JUNGLE_ATK  = "SFX_Jungle_Attack"
	SFX_RECALL_START = "SFX_Recall_Start"
	SFX_RECALL_FINISH = "SFX_Recall_Finish"
	SFX_VICTORY     = "SFX_Victory"
	SFX_DEFEAT      = "SFX_Defeat"
	SFX_KILL        = "SFX_Kill_Announcement"
	SFX_DOUBLE_KILL  = "SFX_DoubleKill"
	SFX_TRIPLE_KILL  = "SFX_TripleKill"
	SFX_QUADRA_KILL  = "SFX_QuadraKill"
	SFX_PENTA_KILL   = "SFX_PentaKill"
	SFX_STREAK_3     = "SFX_KillingSpree"
	SFX_STREAK_4     = "SFX_Rampage"
	SFX_STREAK_5     = "SFX_Unstoppable"
	SFX_STREAK_6     = "SFX_Dominating"
	SFX_STREAK_7     = "SFX_Godlike"
	SFX_STREAK_8     = "SFX_Legendary"
	SFX_ACE          = "SFX_Ace"
	MINIMAP_HERO   = "Icon_Hero"
	MINIMAP_BASIC  = "Icon_Simple"
	
	# Phase 35: FCT & UI Feedback
	FCT_TEMPLATE   = "UI_FloatingText"
	ICON_EMPTY     = "Icon_Empty"
	ICON_COOLDOWN  = "Icon_Overlay_CD"
	
	# Phase 36: Contextual Impacts & Ambience
	SFX_IMPACT_UNIT = "SFX_Impact_Organic"
	SFX_IMPACT_HERO = "SFX_Impact_Hero_Grunt"
	SFX_IMPACT_TURRET = "SFX_Impact_Metallic"
	SFX_UI_CLICK = "SFX_UI_Standard_Click"
	SFX_SHOP_PURCHASE = "SFX_Shop_Coins"
	SFX_ANNOUNCEMENT = "SFX_Global_Clarion"
	
	BGM_SUMMONERS_RIFT = "Ambience_SR_Forest"
	BGM_ARAM = "Ambience_ARAM_Bridge"
	
	# VFX & Vision (Phase 65)
	VFX_RECALL     = "VFX_Recall_Circle"
	VFX_WARD_STEALTH = "VFX_Ward_Stealth"
	VFX_WARD_BLUE    = "VFX_Ward_Blue"
	VFX_ORACLE_SWEEP = "VFX_Oracle_Sweep"
	
	# Default Hero Icons (Fallbacks)
	ICON_SKILL_Q   = "Icon_Skill_Q"
	ICON_SKILL_W   = "Icon_Skill_W"
	ICON_SKILL_E   = "Icon_Skill_E"
	ICON_SKILL_R   = "Icon_Skill_R"
	ICON_PASSIVE   = "Icon_Passive"
	
	# Default Item Icons
	ICON_ITEM_DEFAULT = "Icon_Item_Box"

	# Specialized Summon Templates (Phase 42)
	GHOUL          = "GhoulTemplate"
	GARGOYLE       = "GargoyleTemplate"
	WALL           = "WallTemplate"
	SENTRY         = "SentryTemplate"
	PROJ_SKILL     = "ProjectileTemplate"
	MINION_SUPER   = "Minion_Super"
	WARD_TEMPLATE  = "WardTemplate"
	VFX_BUFF_GREEN = "VFX_Buff_Green"
	SFX_SNOWBALL   = "SFX_Snowball_Hit"
	SFX_IMPACT_HEAVY = "SFX_Impact_Heavy"
	PROJ_RUNAANS   = "Projectile_Runaans"
	
	# Structures
	INHIBITOR      = "Inhibitor_Basic"
	NEXUS          = "Nexus_Central"
	
	# Missing Icon Fallback
	ICON_EMPTY     = "Icon_Empty"
	
	# Announcer SFX (Phase 132: Kill Announcements)
	SFX_KILL         = "SFX_Announcer_Kill"
	SFX_DOUBLE_KILL  = "SFX_Announcer_DoubleKill"
	SFX_TRIPLE_KILL  = "SFX_Announcer_TripleKill"
	SFX_QUADRA_KILL  = "SFX_Announcer_QuadraKill"
	SFX_PENTA_KILL   = "SFX_Announcer_PentaKill"
	SFX_STREAK_3     = "SFX_Announcer_KillingSpree"
	SFX_STREAK_4     = "SFX_Announcer_Rampage"
	SFX_STREAK_5     = "SFX_Announcer_Unstoppable"
	SFX_STREAK_6     = "SFX_Announcer_Dominating"
	SFX_STREAK_7     = "SFX_Announcer_Godlike"
	SFX_STREAK_8     = "SFX_Announcer_Legendary"

# get_entity_team() moved before FountainComponent (forward-reference fix)
# See definition above EffectFlags
