HERO_REGISTRY = {
	# ===================== FALLBACK HERO =====================
	"Kael": {
		"role": "top",
		"stats": {
			"maxHP": 580, "recovery": 2.0, "armor": 38, "mr": 26, # High Armor, Low MR
			"speed": 315, "range": 2.2, "isRanged": False, "turnRate": 540,
			"maxMana": 400, "manaRegen": 1.5, "ad": 55, "ap": 0, "baseAS": 0.625,
		},
		"growthStats": {"hp": 105, "armor": 4.5, "mr": 1.2, "ad": 5.0},
		"passive": {"id": "CLEAVE_HEAL", "name": "Fortress Will", "healPercent": 0.05, "desc": "Passive: Basic attacks harmonize with the earth, healing for 5% of damage dealt.", "icon": "Icons/Kael_Passive.png"},
		"splash": "Heroes/Warrior/Textures/Splash/Splash.png",
		"skills": {
			"Q": {"name": "Gratewall Bash", "effect": "STUN_AOE", "duration": 1.0, "radius": 4.0, "cd": [12, 11, 10, 9, 8], "mana": 60, "icon": "Icons/Kael_Q.png"},
			"W": {"name": "Harmonic Bulwark", "effect": "STAT_MOD", "duration": 4.0, "modifiers": {"armor": 40, "mr": 20}, "cd": [18, 16, 14], "mana": 70, "icon": "Icons/Kael_W.png"},
			"E": {"name": "Seismic Charge", "effect": "DASH", "speed": 30.0, "duration": 0.25, "cd": [14, 13, 12, 11, 10], "mana": 50, "icon": "Icons/Kael_E.png"},
			"R": {"name": "Gilded Judgment", "effect": "EXECUTE_TRUE", "baseDamage": [150, 250, 350], "range": 3.0, "cd": [120, 100, 80], "mana": 100, "icon": "Icons/Kael_R.png"},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0, "icon": "Icons/Trinket_Yellow.png"}
		},
		"faction": "Gratewalls"
	},

	"Cyrus": { # Was Techno Knight
		"faction": "Imperium",
		"role": "jungle",
		"stats": {
			"maxHP": 620, "recovery": 2.2, "armor": 34, "mr": 32,
			"speed": 315, "range": 2.5, "isRanged": False, "turnRate": 600,
			"maxMana": 400, "manaRegen": 1.5, "ad": 60, "ap": 0, "baseAS": 0.625,
		},
		"growthStats": {"hp": 98, "armor": 4.2, "mr": 1.8, "ad": 5.0},
		"passive": {"id": "ADAPTIVE_BARRIER", "name": "Amplified Barrier", "value": 80, "cooldown": 12.0, "icon": "Heroes/TechnoKnight/Textures/Icons/Passive.png"},
		"splash": "Heroes/TechnoKnight/Textures/Splash/Splash.png",
		"sfx_attack": "SFX_Techno_Atk",
		"vfx_attack_cast": "VFX_Techno_Muzzle",
		"vfx_attack_hit": "VFX_Techno_Spark",
		"skills": {
			"Q": {
				"name": "Amplified Edge", "effect": "EMPOWERED_AA", "bonusDamage": [40, 70, 100, 130, 160],
				"cd": [8, 7.5, 7, 6.5, 6], "mana": 50, "icon": "Heroes/TechnoKnight/Textures/Icons/Q.png",
				"vfx_cast": "VFX_Techno_Spark", "sfx_cast": "SFX_Techno_Q"
			},
			"W": {
				"name": "Resonance Plating", "effect": "HP_SCALED_SHIELD", "value": [80, 110, 140, 170, 200],
				"duration": 4.0, "cd": [15, 14, 13, 12, 11], "mana": 65, "icon": "Heroes/TechnoKnight/Textures/Icons/W.png",
				"vfx_cast": "VFX_Techno_Shield", "sfx_cast": "SFX_Techno_W"
			},
			"E": {
				"name": "Imperium Dash", "effect": "DASH", "speed": 45.0, "duration": 0.3,
				"cd": [14, 13, 12, 11, 10], "mana": 60, "icon": "Heroes/TechnoKnight/Textures/Icons/E.png",
				"vfx_cast": "VFX_Techno_Trail", "sfx_cast": "SFX_Techno_E"
			},
			"R": {
				"name": "Imperium Overclock", "effect": "CIRCULAR_AOE", "range": 6.0, "damage": [200, 325, 450],
				"cd": [120, 100, 80], "mana": 100, "icon": "Heroes/TechnoKnight/Textures/Icons/R.png",
				"vfx_cast": "VFX_Techno_Explosion", "sfx_cast": "SFX_Techno_Ultimate"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},

	"Borum": { # Was Ironclad
		"faction": "Gratewalls",
		"role": "top", 
		"stats": {
			"maxHP": 680, "recovery": 2.5, "armor": 30, "mr": 45, 
			"speed": 310, "range": 2.2, "isRanged": False, "turnRate": 630
		},
		"vfx_attack_hit": "VFX_Metal_Clash",
		"growthStats": {"hp": 105, "armor": 4.5, "mr": 2.0, "ad": 5.2},
		"passive": {"id": "TENACITY", "name": "Borum's Resolve", "tenacity": 0.3, "icon": "Heroes/Ironclad/Textures/Icons/Passive.png"},
		"splash": "Heroes/Ironclad/Textures/Splash/Splash.png",
		"sfx_attack": "SFX_Ironclad_Atk",
		"vfx_attack_cast": "VFX_Metal_Clash_Muzzle",
		"skills": {
			"Q": {
				"name": "Gratewall Haste", "effect": "EMPOWERED_MS_AA", "msBoost": 0.35, "duration": 4.0, 
				"cd": [10, 9, 8, 7, 6], "mana": 40, "icon": "Heroes/Ironclad/Textures/Icons/Q.png",
				"vfx_cast": "VFX_Ironclad_Empower", "sfx_cast": "SFX_Ironclad_Q"
			},
			"W": {
				"name": "Fortress Shield", "effect": "HP_SCALED_SHIELD", "value": [60, 90, 120, 150, 180], 
				"duration": 3.0, "cd": [16, 14, 12, 10, 8], "mana": 60, "icon": "Heroes/Ironclad/Textures/Icons/W.png",
				"vfx_cast": "VFX_Ironclad_Shield", "sfx_cast": "SFX_Ironclad_W"
			},
			"E": {
				"name": "Brute Slam", "effect": "STUN", "duration": 1.25, "range": 3.5, 
				"cd": [12, 11, 10, 9, 8], "mana": 50, "icon": "Heroes/Ironclad/Textures/Icons/E.png",
				"vfx_cast": "VFX_Ironclad_GroundSlam", "sfx_cast": "SFX_Ironclad_E"
			},
			"R": {
				"name": "Bastion Execution", "effect": "EXECUTE_TRUE", "range": 3.0, "baseDamage": [150, 250, 350], 
				"cd": [120, 100, 80], "mana": 100, "isBlocking": True,
				"icon": "Heroes/Ironclad/Textures/Icons/R.png",
				"vfx_cast": "VFX_Ironclad_Execute", "vfx_hit": "VFX_Blood_Burst", "sfx_cast": "SFX_Ironclad_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Zora": { # Was Shadow
		"faction": "Jun Hu",
		"role": "mid",
		"stats": {
			"maxHP": 540, "recovery": 1.8, "armor": 24, "mr": 30, 
			"speed": 355, "range": 1.8, "isRanged": False, "turnRate": 630
		},
		"vfx_attack_hit": "VFX_Shadow_Slash",
		"growthStats": {"hp": 80, "armor": 3.0, "mr": 1.25, "ad": 4.5},
		"passive": {"id": "NIGHTFALL", "name": "Harmonized Strike", "bonusDamage": 40, "icon": "Heroes/Shadow/Textures/Icons/Passive.png"},
		"splash": "Heroes/Shadow/Textures/Splash/Splash.png",
		"sfx_attack": "SFX_Shadow_Atk",
		"vfx_attack_cast": "VFX_Shadow_Muzzle",
		"skills": {
			"Q": {
				"name": "Harmonized Dart", "effect": "LINEAR_PROJECTILE", "speed": 35.0, "range": 12.0, 
				"damage": [80, 115, 150, 185, 220], "cd": [6, 5, 4, 3, 2.5], "mana": 50, "icon": "Heroes/Shadow/Textures/Icons/Q.png",
				"vfx_cast": "VFX_Shadow_Cast", "vfx_trail": "VFX_Shadow_Trail", "vfx_hit": "VFX_Shadow_Impact", "sfx_cast": "SFX_Shadow_Q"
			},
			"W": {
				"name": "Prism Blink", "effect": "BLINK", "range": 6.5, "cd": [18, 16, 14, 12, 10], "mana": 70, "icon": "Heroes/Shadow/Textures/Icons/W.png",
				"vfx_cast": "VFX_Shadow_Smoke_Start", "vfx_hit": "VFX_Shadow_Smoke_End", "sfx_cast": "SFX_Shadow_W"
			},
			"E": {
				"name": "Geometric Shroud", "effect": "ACTIVE_STEALTH", "duration": 2.5, "cd": [20, 18, 16, 14, 12], "mana": 60, "icon": "Heroes/Shadow/Textures/Icons/E.png",
				"vfx_cast": "VFX_Shadow_Stealth_Smoke", "sfx_cast": "SFX_Shadow_E"
			},
			"R": {
				"name": "Crystalline Execution", "effect": "DASH", "speed": 40.0, "duration": 0.25, "damage": [200, 350, 500], "icon": "Heroes/Shadow/Textures/Icons/R.png",
				"cd": [100, 85, 70], "mana": 100,
				"vfx_cast": "VFX_Shadow_Dash_Shadows", "sfx_cast": "SFX_Shadow_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Eira": { # Was Frost Nova
		"faction": "Jun Hu",
		"role": "mid",
		"stats": {"maxHP": 520, "recovery": 1.5, "armor": 22, "mr": 35, "speed": 335, "range": 7.5, "isRanged": True, "turnRate": 450},
		"attackProjectile": "VFX_Ice_Shard", "attackProjSpeed": 28.0, "vfx_attack_hit": "VFX_Ice_Shatter",
		"growthStats": {"hp": 75, "ad": 2.2, "mana": 50},
		"passive": {"id": "CHILLING_AURA", "name": "Perfect Chill", "slow": 0.15, "icon": "Heroes/FrostNova/Textures/Icons/Passive.png"},
		"splash": "Heroes/FrostNova/Textures/Icons/Passive.png",
		"sfx_attack": "SFX_Frost_Atk",
		"vfx_attack_cast": "VFX_Frost_Muzzle",
		"skills": {
			"Q": {
				"name": "Harmonized Shard", "effect": "LINEAR_PROJECTILE", "speed": 28.0, "range": 14.0, "damage": [80, 120, 160, 200, 240], "cd": [7, 6, 5, 4, 3], "mana": 50, "icon": "Heroes/FrostNova/Textures/Icons/Q.png",
				"vfx_trail": "VFX_Ice_Shard_Trail", "vfx_hit": "VFX_Ice_Shatter", "sfx_cast": "SFX_Frost_Cast_Small"
			},
			"W": {
				"name": "Crystalline Slide", "effect": "DASH", "speed": 25.0, "duration": 0.3, "cd": [12, 11, 10, 9, 8], "mana": 60, "icon": "Heroes/FrostNova/Textures/Icons/W.png",
				"vfx_cast": "VFX_Frost_Slide_Ground", "sfx_cast": "SFX_Frost_Slide"
			},
			"E": {
				"name": "Geometric Frost", "effect": "STUN", "duration": 1.5, "range": 8.0, "cd": [18, 16, 14, 12, 10], "mana": 70, "icon": "Heroes/FrostNova/Textures/Icons/E.png",
				"vfx_cast": "VFX_Ice_Ring_Spawn", "vfx_hit": "VFX_Ice_Freeze", "sfx_cast": "SFX_Frost_Freeze"
			},
			"R": {
				"name": "Prismatic Blizzard", "effect": "SUSTAINED_ZONE", "radius": 7.0, "dps": [100, 150, 200], "cd": [120, 100, 80], "mana": 100, "isChannel": True, "icon": "Heroes/FrostNova/Textures/Icons/R.png",
				"vfx_cast": "VFX_Blizzard_Aura", "vfx_persistent": True, "sfx_cast": "SFX_Frost_Ult_Storm"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Ignis": { # Was Pyre
		"faction": "Armhold",
		"role": "top",
		"stats": {"maxHP": 650, "recovery": 3.0, "armor": 35, "mr": 30, "speed": 325, "range": 2.5, "isRanged": False, "turnRate": 630},
		"vfx_attack_hit": "VFX_Fire_Burst",
		"growthStats": {"hp": 100, "armor": 4.8, "ad": 5.0},
		"passive": {"id": "IGNITE", "name": "Furnace Soul", "dot": 15, "duration": 3.0, "icon": "Heroes/Pyre/Textures/Icons/Passive.png"},
		"splash": "Heroes/Pyre/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Industrial Scorch", "effect": "EMPOWERED_MS_AA", "msBoost": 0.3, "duration": 3.5, "cd": [9, 8, 7, 6, 5], "mana": 45, "icon": "Heroes/Pyre/Textures/Icons/Q.png",
				"vfx_cast": "VFX_Flaming_Sword", "vfx_persistent": True, "sfx_cast": "SFX_Pyre_Q"
			},
			"W": {
				"name": "Boiler Plating", "effect": "HP_SCALED_SHIELD", "value": [80, 110, 140, 170, 200], "duration": 2.5, "cd": [15, 13, 11, 9, 7], "mana": 60, "icon": "Heroes/Pyre/Textures/Icons/W.png",
				"vfx_cast": "VFX_Magma_Shield", "vfx_persistent": True, "sfx_cast": "SFX_Pyre_W"
			},
			"E": {
				"name": "Steam Burst", "effect": "PUSH_STUN", "range": 4.0, "distance": 6.0, "cd": [14, 13, 12, 11, 10], "mana": 50, "icon": "Heroes/Pyre/Textures/Icons/E.png",
				"vfx_cast": "VFX_Fire_Dash_Burst", "sfx_cast": "SFX_Pyre_E"
			},
			"R": {
				"name": "Armhold Impact", "effect": "EXECUTE_TRUE", "range": 4.0, "baseDamage": [200, 350, 500], "cd": [110, 95, 80], "mana": 100, "isBlocking": True, "icon": "Heroes/Pyre/Textures/Icons/R.png",
				"vfx_cast": "VFX_Volcanic_Impact", "vfx_hit": "VFX_Lava_Splash", "sfx_cast": "SFX_Pyre_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Zarek": { # Was StormWeaver
		"faction": "Armhold",
		"role": "mid",
		"stats": {"maxHP": 540, "recovery": 1.6, "armor": 22, "mr": 30, "speed": 335, "range": 8.0, "isRanged": True, "turnRate": 450},
		"attackProjectile": "VFX_Lightning_Bolt", "attackProjSpeed": 40.0, "vfx_attack_hit": "VFX_Electric_Pop",
		"growthStats": {"hp": 82, "ad": 2.8, "mana": 42},
		"passive": {"id": "STATIC_CHARGE", "name": "Power Surge", "bonusDmgEveryAAs": 3, "icon": "Heroes/StormWeaver/Textures/Icons/Passive.png"},
		"splash": "Heroes/StormWeaver/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Industrial Shock", "effect": "APPLY_MARK", "range": 10.0, "duration": 6.0, "cd": [7, 6.5, 6, 5.5, 5], "mana": 40, "icon": "Heroes/StormWeaver/Textures/Icons/Q.png",
				"vfx_cast": "VFX_Lightning_Arc", "vfx_hit": "VFX_Mark_Spark", "sfx_cast": "SFX_Storm_Q"
			},
			"W": {
				"name": "Resonance Dash", "effect": "THUNDER_DASH", "speed": 38.0, "duration": 0.25, "cd": [12, 11, 10, 9, 8], "mana": 60, "icon": "Heroes/StormWeaver/Textures/Icons/W.png",
				"vfx_cast": "VFX_Thunder_Step", "sfx_cast": "SFX_Storm_W"
			},
			"E": {
				"name": "Grid Discharge", "effect": "DETONATE", "range": 12.0, "damage": [100, 140, 180, 220, 260], "cd": [14, 13, 12, 11, 10], "mana": 70, "icon": "Heroes/StormWeaver/Textures/Icons/E.png",
				"vfx_cast": "VFX_Tesla_Burst", "vfx_hit": "VFX_Electric_Pop", "sfx_cast": "SFX_Storm_E"
			},
			"R": {
				"name": "Armhold Coil", "effect": "SUMMON_SENTRY", "duration": 12.0, "cd": [120, 110, 100], "mana": 100, "icon": "Heroes/StormWeaver/Textures/Icons/R.png",
				"vfx_cast": "VFX_Storm_Totem_Summon", "sfx_cast": "SFX_Storm_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Mortis": { # Was GraveyardKing
		"faction": "Monsters",
		"role": "top",
		"stats": {"maxHP": 600, "recovery": 2.2, "armor": 32, "mr": 32, "speed": 315, "range": 2.5, "isRanged": False, "turnRate": 630},
		"growthStats": {"hp": 95, "armor": 4.2, "ad": 5.2},
		"passive": {"id": "SOUL_HARVEST", "name": "Chaotic Harvest", "healOnKill": 0.05, "icon": "Heroes/GraveyardKing/Textures/Icons/Passive.png"},
		"splash": "Heroes/GraveyardKing/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Void Skull", "effect": "LINEAR_PROJECTILE", "speed": 22.0, "range": 11.0, "damage": [70, 105, 140, 175, 210], "cd": [8, 7, 6, 5, 4], "mana": 45, "icon": "Heroes/GraveyardKing/Textures/Icons/Q.png",
				"vfx_trail": "VFX_Spectral_Skull_Trail", "vfx_hit": "VFX_Soul_Shatter", "sfx_cast": "SFX_King_Q"
			},
			"W": {
				"name": "Warped Husk", "effect": "SUMMON_ENTITY", "template": "GhoulTemplate", "cd": [16, 14, 12, 10, 8], "mana": 60, "icon": "Heroes/GraveyardKing/Textures/Icons/W.png",
				"vfx_cast": "VFX_Grave_Burst", "sfx_cast": "SFX_King_W"
			},
			"E": {
				"name": "Chaotic Grasp", "effect": "STUN", "duration": 1.25, "range": 7.5, "cd": [14, 13, 12, 11, 10], "mana": 60, "icon": "Heroes/GraveyardKing/Textures/Icons/E.png",
				"vfx_cast": "VFX_Spectral_Hand_Cast", "vfx_hit": "VFX_Grave_Grasp_Root", "sfx_cast": "SFX_King_E"
			},
			"R": {
				"name": "Eldritch Harbinger", "effect": "SUMMON_ENTITY", "template": "GargoyleTemplate", "duration": 20.0, "cd": [140, 120, 100], "mana": 100, "icon": "Heroes/GraveyardKing/Textures/Icons/R.png",
				"vfx_cast": "VFX_Soul_Storm", "vfx_persistent": True, "sfx_cast": "SFX_King_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Sora": {
		"faction": "Nomade's",
		"role": "top",
		"stats": {"maxHP": 540, "recovery": 1.8, "armor": 32, "mr": 28, "speed": 330, "range": 1.8, "isRanged": False, "turnRate": 630, "maxMana": 350, "manaRegen": 1.5},
		"growthStats": {"hp": 90, "ad": 4.5, "armor": 3.5},
		"passive": {"id": "FLOW", "name": "Wind Shield", "shieldAtMaxFlow": 100, "manaPerStep": 0.5},
		"skills": {
			"Q": {
				"name": "Steel Tempest", "effect": "STRIKE_SINGLE", "range": 4.5, "damage": [60, 90, 120, 150, 180], "cd": [4, 3, 2], "mana": 30,
				"vfx_cast": "VFX_Wind_Blade"
			},
			"W": {
				"name": "Wind Wall", "effect": "DEFLECT_PROJECTILE", "duration": 3.5, "cd": [24, 20, 16], "mana": 80,
				"vfx_cast": "VFX_Wind_Wall"
			},
			"E": {
				"name": "Sweeping Blade", "effect": "DASH_TARGETED", "speed": 35.0, "duration": 0.25, "cd": [0.5, 0.4, 0.3], "mana": 40,
				"vfx_cast": "VFX_Wind_Trail"
			},
			"R": {
				"name": "Last Breath", "effect": "SUSPEND_STUN", "duration": 1.5, "damage": [200, 350, 500], "cd": [100, 80, 60], "mana": 100
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Krix": { # Was Slayer
		"faction": "The Front",
		"role": "jungle",
		"stats": {"maxHP": 580, "recovery": 2.0, "armor": 32, "mr": 28, "speed": 355, "range": 2.0, "isRanged": False, "turnRate": 630},
		"growthStats": {"hp": 85, "ad": 4.8, "armor": 3.2},
		"passive": {"id": "HUNT", "name": "Glitch Mark", "bonusDmg": 0.1, "icon": "Heroes/Slayer/Textures/Icons/Passive.png"},
		"splash": "Heroes/Slayer/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Scavenged Slash", "effect": "CONE_VOLLEY", "count": 3, "range": 6.0, "damage": [70, 110, 150], "cd": [8, 7, 6], "mana": 45, "icon": "Heroes/Slayer/Textures/Icons/Q.png",
				"vfx_cast": "VFX_Blade_Slash", "sfx_cast": "SFX_Slayer_Q"
			},
			"W": {
				"name": "Glitch Dash", "effect": "DASH", "speed": 35.0, "duration": 0.2, "cd": [14, 12, 10], "mana": 50, "icon": "Heroes/Slayer/Textures/Icons/W.png",
				"vfx_cast": "VFX_Shadow_Step", "sfx_cast": "SFX_Slayer_W"
			},
			"E": {
				"name": "Signal Grapple", "effect": "BLEED_PULL", "range": 8.0, "dps": 20, "duration": 3.0, "cd": [20, 18, 16], "mana": 60, "icon": "Heroes/Slayer/Textures/Icons/E.png",
				"vfx_cast": "VFX_Grapple_Chain", "vfx_hit": "VFX_Blood_Spray", "sfx_cast": "SFX_Slayer_E"
			},
			"R": {
				"name": "System Shock", "effect": "EXECUTE_TRUE", "range": 4.0, "baseDamage": [150, 250, 350], "cd": [120, 100, 80], "mana": 100, "icon": "Heroes/Slayer/Textures/Icons/R.png",
				"vfx_hit": "VFX_Execute_Impact", "sfx_cast": "SFX_Slayer_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Orix": { # Was Guardian
		"faction": "Gratewalls",
		"role": "support",
		"stats": {"maxHP": 640, "recovery": 2.8, "armor": 45, "mr": 40, "speed": 310, "range": 2.2, "isRanged": False, "turnRate": 630},
		"growthStats": {"hp": 110, "armor": 5.5, "mr": 4.5},
		"passive": {"id": "STONE_SKIN", "name": "Harmonic Aura", "armorPerAlly": 8, "radius": 8.0, "icon": "Heroes/Guardian/Textures/Icons/Passive.png"},
		"splash": "Heroes/Guardian/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Fortress Bash", "cd": [14, 12, 10], "mana": 60, "icon": "Heroes/Guardian/Textures/Icons/Q.png",
				"stages": [
					{"effect": "CONE_VOLLEY", "count": 2, "range": 5.0, "damage": 50},
					{"effect": "CONE_VOLLEY", "count": 2, "range": 5.0, "damage": 50},
					{"effect": "STUN", "duration": 1.5, "range": 4.0}
				],
				"stageWindow": 4.0, "vfx_cast": "VFX_Shield_Bash", "sfx_cast": "SFX_Guardian_Q"
			},
			"W": {
				"name": "Resonance Shield", "effect": "HP_SHIELD", "value": [100, 150, 200], "duration": 4.0, "cd": [18, 16, 14], "mana": 70, "icon": "Heroes/Guardian/Textures/Icons/W.png",
				"vfx_cast": "VFX_Spirit_Shield", "vfx_persistent": True, "sfx_cast": "SFX_Guardian_W"
			},
			"E": {
				"name": "Gilded Shatter", "effect": "AOE_STUN", "radius": 5.0, "duration": 1.0, "damage": [60, 90, 120, 150, 180], "cd": [16, 15, 14, 13, 12], "mana": 65, "icon": "Heroes/Guardian/Textures/Icons/E.png",
				"vfx_cast": "VFX_Earth_Shatter", "sfx_cast": "SFX_Guardian_E"
			},
			"R": {
				"name": "Imperial Ascension", "effect": "INVULNERABLE", "duration": 2.5, "cd": [150, 130, 110], "mana": 100, "icon": "Heroes/Guardian/Textures/Icons/R.png",
				"vfx_cast": "VFX_Holy_Ascension", "vfx_persistent": True, "sfx_cast": "SFX_Guardian_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Bastian": { # The Iron Sentinel
		"faction": "Imperium",
		"role": "jungle",
		"stats": {
			"maxHP": 680, "recovery": 3.5, "armor": 45, "mr": 35, 
			"speed": 315, # Slow tank speed
			"range": 2.5, "isRanged": False, "turnRate": 550,
			"maxMana": 350, "manaRegen": 1.5, "ad": 65, "ap": 0
		},
		"growthStats": {"hp": 115, "armor": 5.2, "ad": 4.5},
		"passive": {"id": "SHIELD_BLOCK", "name": "Amplified Aegis", "blockChance": 0.2, "dr": 0.15, "desc": "Passive: 20% chance to block 15% of incoming damage via resonance."},
		"skills": {
			"Q": {
				"name": "Amplified Pulse", "effect": "CIRCULAR_AOE", "radius": 5.0, "damage": [70, 110, 150, 190, 230], 
				"cd": [9, 8, 7, 6, 5], "mana": 50, "isMonsterEffective": 1.5, # 1.5x to monsters
				"vfx_cast": "VFX_Seismic_Impact", "sfx_cast": "SFX_Bastian_Q"
			},
			"W": {
				"name": "Resonance Barrier", "effect": "STAT_MOD", "duration": 3.0, "modifiers": {"damageReduction": 0.35}, 
				"cd": [18, 16, 14, 12, 10], "mana": 60, "vfx_cast": "VFX_Shield_Harden"
			},
			"E": {
				"name": "Imperium Charge", "effect": "DASH_STUN", "speed": 30.0, "duration": 0.4, "range": 6.0,
				"cd": [16, 15, 14, 13, 12], "mana": 70, "vfx_cast": "VFX_Iron_Charge"
			},
			"R": {
				"name": "Imperium Arena", "effect": "GROUNDED_ZONE", "radius": 8.0, "duration": 5.0,
				"cd": [120, 105, 90], "mana": 100, "vfx_cast": "VFX_Fortress_Arena", "sfx_cast": "SFX_Bastian_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Ragnar": {
		"faction": "The Front",
		"role": "top",
		"stats": {
			"maxHP": 600, "recovery": 3.0, "armor": 35, "mr": 26, # Fighter Resist Gating
			"speed": 320, "range": 2.5, "isRanged": False, "turnRate": 630,
			"maxMana": 300, "manaRegen": 1.0, "ad": 62, "ap": 0
		},
		"growthStats": {"hp": 110, "ad": 5.5, "armor": 4.5},
		"passive": {"id": "LIFE_DRINKER", "name": "Rust Hunger", "lifesteal": 0.1, "desc": "Passive: Gains 10% Life Steal through scavenged tech."},
		"skills": {
			"Q": {
				"name": "Scrap Storm", "effect": "CIRCULAR_AOE", "radius": 5.5, "damage": [80, 120, 160], "cd": [8, 7, 6], "mana": 60,
				"healOnHit": 0.08, "vfx_cast": "VFX_Whirlwind"
			},
			"W": {
				"name": "Jitter Plating", "effect": "HP_SCALED_SHIELD", "value": [100, 150, 200], "duration": 3.0, "cd": [16, 14, 12], "mana": 65
			},
			"E": {
				"name": "Glitch Leap", "effect": "DASH", "speed": 35.0, "duration": 0.3, "cd": [18, 16, 14], "mana": 50
			},
			"R": {
				"name": "System Redline", "effect": "STAT_MOD", "duration": 8.0, "modifiers": {"ad": 40, "as": 0.5, "speed": 60}, "cd": [110, 95, 80], "mana": 100
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Umbra": { # Was ShadowStalker
		"faction": "The Front",
		"role": "jungle",
		"stats": {"maxHP": 520, "recovery": 1.5, "armor": 24, "mr": 30, "speed": 355, "range": 1.8, "isRanged": False, "turnRate": 630},
		"growthStats": {"hp": 75, "ad": 5.2, "armor": 2.8},
		"passive": {"id": "MARK_ON_HIT", "name": "Hunter's Mark", "bonusDmg": 30, "icon": "Heroes/ShadowStalker/Textures/Icons/Passive.png"},
		"splash": "Heroes/ShadowStalker/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Shadow Veil", "effect": "ACTIVE_STEALTH", "duration": 4.0, "cd": [18, 16, 14], "mana": 60, "icon": "Heroes/ShadowStalker/Textures/Icons/Q.png",
				"vfx_cast": "VFX_Shadow_Veil", "sfx_cast": "SFX_Stalker_Q"
			},
			"W": {
				"name": "Terror Pulse", "effect": "FEAR", "duration": 1.5, "range": 5.0, "cd": [15, 14, 13], "mana": 50, "icon": "Heroes/ShadowStalker/Textures/Icons/W.png",
				"vfx_cast": "VFX_Nightmare_Pulse", "vfx_hit": "VFX_Terror_Sparks", "sfx_cast": "SFX_Stalker_W"
			},
			"E": {
				"name": "Essence Drain", "effect": "STAT_STEAL", "magnitude": 20, "duration": 4.0, "range": 6.0, "cd": [12, 11, 10], "mana": 50, "icon": "Heroes/ShadowStalker/Textures/Icons/E.png",
				"vfx_cast": "VFX_Essence_Drain", "sfx_hit": "SFX_Stalker_E"
			},
			"R": {
				"name": "Assassination", "cd": [110, 95, 80], "mana": 100, "icon": "Heroes/ShadowStalker/Textures/Icons/R.png",
				"stages": [
					{"effect": "DASH", "speed": 40, "duration": 0.2},
					{"effect": "EXECUTE_TRUE", "range": 3.0, "baseDamage": 200}
				],
				"stageWindow": 2.0, "vfx_cast": "VFX_Shadow_Assassination", "sfx_cast": "SFX_Stalker_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Ezra": { # Was ArcaneSlinger
		"faction": "Imperium",
		"role": "adc",
		"stats": {"maxHP": 530, "recovery": 1.5, "armor": 25, "mr": 30, "speed": 345, "range": 12.0, "isRanged": True, "turnRate": 450},
		"attackProjectile": "VFX_Arcane_Bolt", "attackProjSpeed": 35.0, "vfx_attack_hit": "VFX_Arcane_Burst",
		"growthStats": {"hp": 80, "ad": 4.0, "as": 0.03},
		"passive": {"id": "AS_FLOW", "name": "Amplified Focus", "asPerStack": 0.05, "maxStacks": 5, "icon": "Heroes/ArcaneSlinger/Textures/Icons/Passive.png"},
		"splash": "Heroes/ArcaneSlinger/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Amplified Bolt", "effect": "LINEAR_PROJECTILE", "speed": 35.0, "range": 18.0, "damage": [60, 100, 140], "cd": [4, 3.5, 3], "mana": 40, "icon": "Heroes/ArcaneSlinger/Textures/Icons/Q.png",
				"vfx_trail": "VFX_Arcane_Bolt_Trail", "vfx_hit": "VFX_Arcane_Burst", "sfx_cast": "SFX_Slinger_Q"
			},
			"W": {
				"name": "Resonance Shift", "effect": "BLINK", "range": 5.5, "cd": [16, 14, 12], "mana": 70, "icon": "Heroes/ArcaneSlinger/Textures/Icons/W.png",
				"vfx_cast": "VFX_Arcane_Shift", "sfx_cast": "SFX_Slinger_W"
			},
			"E": {
				"name": "Concussive Flare", "effect": "APPLY_MARK", "range": 10.0, "duration": 5.0, "cd": [12, 11, 10], "mana": 50, "icon": "Heroes/ArcaneSlinger/Textures/Icons/E.png",
				"vfx_cast": "VFX_Essence_Flare", "sfx_cast": "SFX_Slinger_E"
			},
			"R": {
				"name": "Imperium Barrage", "effect": "SUSTAINED_ZONE", "radius": 10.0, "dps": [80, 120, 160], "manaPerSec": 30, "cd": 2.0, "icon": "Heroes/ArcaneSlinger/Textures/Icons/R.png",
				"vfx_cast": "VFX_Arcane_Barrage", "vfx_persistent": True, "sfx_cast": "SFX_Slinger_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Kenji": {
		"faction": "Jun Hu",
		"role": "jungle",
		"stats": {"maxHP": 560, "recovery": 2.0, "armor": 30, "mr": 28, "speed": 330, "range": 2.2, "isRanged": False, "turnRate": 630, "maxMana": 380, "manaRegen": 1.8},
		"growthStats": {"hp": 88, "ad": 4.8, "armor": 3.2},
		"passive": {"id": "PRECISION_STRIKE", "name": "Harmonized Blade", "bonusASPerHit": 0.1, "maxStacks": 4, "desc": "Passive: Basic attacks synchronize with the target, gaining speed."},
		"skills": {
			"Q": {
				"name": "Crystalline Flash", "effect": "DASH_STRIKE", "speed": 40, "damage": [70, 110, 150], "cd": [10, 9, 8], "mana": 50,
				"vfx_cast": "VFX_Thunder_Flash"
			},
			"W": {
				"name": "Geometric Parry", "effect": "PARRY", "duration": 1.0, "cd": [20, 18, 16], "mana": 70,
				"vfx_cast": "VFX_Blade_Parry"
			},
			"E": {
				"name": "Resonance Hunt", "effect": "STAT_MOD", "duration": 4.0, "modifiers": {"speed": 40, "armorPen": 0.15}, "cd": [14, 12, 10], "mana": 45
			},
			"R": {
				"name": "Prismatic Omni-Strike", "effect": "MULTI_STRIKE", "count": 5, "damage": [50, 75, 100], "cd": [120, 100, 80], "mana": 100
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Arath": { # Was DarkinApostle
		"faction": "Monsters",
		"role": "top",
		"stats": {"maxHP": 580, "recovery": 3.0, "armor": 38, "mr": 30, "speed": 325, "range": 2.5, "isRanged": False, "turnRate": 630},
		"growthStats": {"hp": 95, "ad": 5.5, "armor": 3.8},
		"passive": {"id": "LIFE_STEAL", "name": "Chaotic Thirst", "vamp": 0.1, "icon": "Heroes/DarkinApostle/Textures/Icons/Passive.png"},
		"splash": "Heroes/DarkinApostle/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Void Slam", "cd": [14, 12, 10, 8, 6], "icon": "Heroes/DarkinApostle/Textures/Icons/Q.png",
				"stages": [
					{"effect": "RECT_SWEETSPOT", "width": 4, "length": 10, "sweetLength": 2.5},
					{"effect": "RECT_SWEETSPOT", "width": 6, "length": 8, "sweetLength": 3.0},
					{"effect": "RECT_SWEETSPOT", "width": 8, "length": 8, "sweetLength": 8.0}
				],
				"stageWindow": 4.0, "damage": [20, 40, 60, 80, 100], "bonusDamage": [40, 80, 120, 160, 200],
				"vfx_cast": "VFX_Darkin_Blade_Slam", "sfx_cast": "SFX_Darkin_Q"
			},
			"W": {
				"name": "Chaotic Chains", "effect": "PUSH_STUN", "range": 4.0, "distance": 6.0, "cd": [15, 13, 11], "mana": 0, "icon": "Heroes/DarkinApostle/Textures/Icons/W.png",
				"vfx_cast": "VFX_Darkin_Chain", "sfx_cast": "SFX_Darkin_W"
			},
			"E": {
				"name": "Warp Dash", "effect": "DASH", "speed": 30.0, "duration": 0.25, "cd": [9, 8, 7, 6, 5], "mana": 0, "combos": {"allowedEffects": ["all"]}, "icon": "Heroes/DarkinApostle/Textures/Icons/E.png",
				"vfx_cast": "VFX_Darkin_Dash", "sfx_cast": "SFX_Darkin_E"
			},
			"R": {
				"name": "Eldritch Ascension", "effect": "STAT_MOD", "duration": 10.0, "modifiers": {"ad": 50, "speed": 80}, "cd": [120, 100, 80], "mana": 0, "icon": "Heroes/DarkinApostle/Textures/Icons/R.png",
				"vfx_cast": "VFX_Darkin_Ascension", "vfx_persistent": True, "sfx_cast": "SFX_Darkin_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Thorne": { # The Verdant Warden
		"faction": "Nomade's",
		"role": "support",
		"stats": {
			"maxHP": 620, "recovery": 3.0, "armor": 38, "mr": 36,
			"speed": 315, "range": 2.2, "isRanged": False, "turnRate": 600, # Heavy tank speed
			"maxMana": 380, "manaRegen": 1.8, "ad": 61, "ap": 0
		},
		"growthStats": {"hp": 95, "armor": 4.2, "mr": 4.2},
		"passive": {"id": "BRAMBLE_THORNS", "name": "Organic Spikes", "reflectPercent": 0.15, "desc": "Passive: Reflects 15% of magic damage via organic resonance."},
		"skills": {
			"Q": {
				"name": "Organic Vines", "effect": "GRAB_PULL", "range": 8.0, "cd": [16, 14, 12, 10, 8], "mana": 65,
				"vfx_cast": "VFX_Thorne_Hook", "sfx_cast": "SFX_Thorne_Q"
			},
			"W": {
				"name": "Nature’s Shield", "effect": "SHIELD_TENACITY", "value": [80, 120, 160, 200, 240], 
				"duration": 3.5, "cd": [20, 18, 16], "mana": 80, "vfx_cast": "VFX_Thorne_Shield"
			},
			"E": {
				"name": "Rooted Dash", "effect": "DASH_KNOCKUP", "speed": 25.0, "duration": 0.45, "radius": 4.0,
				"cd": [18, 16, 14, 12, 10], "mana": 70, "vfx_cast": "VFX_Thorne_Leap"
			},
			"R": {
				"name": "Nomade Bloom", "effect": "GROUNDED_AURA", "radius": 10.0, "duration": 6.5,
				"cd": [130, 115, 100], "mana": 100, "vfx_persistent": True, "vfx_cast": "VFX_Thorne_TreeForm", "sfx_cast": "SFX_Thorne_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Silvan": { # The Nature Guardian (Human Form)
		"faction": "Nomade's",
		"role": "support",
		"stats": {
			"maxHP": 540, "recovery": 2.2, "armor": 26, "mr": 30,
			"speed": 330, "range": 8.0, "isRanged": True, "turnRate": 450,
			"maxMana": 400, "manaRegen": 2.5, "ad": 48, "ap": 0
		},
		"attackProjectile": "VFX_Leaf_Dart", "attackProjSpeed": 30.0,
		"growthStats": {"hp": 82, "ap": 4.5, "mana": 50},
		"passive": {"id": "NATURE_TOUCH", "name": "Guardian's Presence", "regenAura": 8, "desc": "Passive: Nearby allies gain 8 HP/5s Regen."},
		"skills": {
			"Q": {
				"name": "Nature's Grasp", "effect": "GRAB_PULL", "range": 10.0, "cd": [16, 14, 12], "mana": 60,
				"vfx_cast": "VFX_Vine_Pull", "sfx_cast": "SFX_Silvan_Q"
			},
			"W": {
				"name": "Healing Bloom", "effect": "HEAL_TARGETED", "heal": [80, 120, 160], "range": 8.0,
				"cd": [12, 11, 10], "mana": 65, "vfx_cast": "VFX_Nature_Heal"
			},
			"E": {
				"name": "Seeded Trap", "effect": "ROOT", "duration": 1.25, "radius": 4.0, "cd": [18, 16, 14], "mana": 70,
				"vfx_cast": "VFX_Seed_Explosion"
			},
			"R": {
				"name": "Spirit Shift", "effect": "TRANSFORM", "targetHero": "Spirit", "cd": 6.0,
				"vfx_cast": "VFX_Spirit_Transformation", "sfx_cast": "SFX_Spirit_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Spirit": { # Was SpiritForm (Cougar Form)
		"faction": "Nomade's",
		"role": "support",
		"stats": {"maxHP": 570, "recovery": 4.0, "armor": 30, "mr": 30, "speed": 345, "range": 2.5, "isRanged": False, "turnRate": 630},
		"growthStats": {"hp": 85, "ad": 4.5, "speed": 5},
		"passive": {"id": "SPIRIT_SPEED", "name": "Ethereal Speed", "msFlat": 25, "icon": "Heroes/SpiritForm/Textures/Icons/Passive.png"},
		"splash": "Heroes/SpiritForm/Textures/Splash/Splash.png",
		"startWithR": True,
		"skills": {
			"Q": {
				"name": "Pounce", "effect": "DASH", "speed": 40, "duration": 0.2, "cd": [6, 5, 4], "mana": 30, "icon": "Heroes/SpiritForm/Textures/Icons/Q.png",
				"vfx_cast": "VFX_Spirit_Pounce", "sfx_cast": "SFX_Spirit_Q"
			},
			"W": {
				"name": "Spirit Howl", "effect": "FEAR", "duration": 1.0, "range": 4.0, "cd": [16, 14, 12], "mana": 50, "icon": "Heroes/SpiritForm/Textures/Icons/W.png",
				"vfx_cast": "VFX_Spirit_Howl", "sfx_cast": "SFX_Spirit_W"
			},
			"E": {
				"name": "Nature Burst", "effect": "CIRCLE_AOE", "radius": 4.5, "damage": [50, 80, 110], "cd": [10, 9, 8], "mana": 45, "icon": "Heroes/SpiritForm/Textures/Icons/E.png",
				"vfx_cast": "VFX_Spirit_Burst"
			},
			"R": {
				"name": "Revert", "effect": "TRANSFORM", "targetHero": "Silvan", "cd": 6.0, "icon": "Heroes/SpiritForm/Textures/Icons/R.png",
				"vfx_cast": "VFX_Spirit_Transformation", "sfx_cast": "SFX_Spirit_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Fiore": {
		"faction": "Jun Hu",
		"role": "top",
		"stats": {"maxHP": 530, "recovery": 1.8, "armor": 30, "mr": 26, "speed": 325, "range": 2.2, "isRanged": False, "turnRate": 630, "maxMana": 320, "manaRegen": 1.2},
		"growthStats": {"hp": 82, "ad": 5.2, "armor": 3.2},
		"passive": {"id": "DUELIST_VITAL", "name": "Fencer's Will", "trueDmgPercent": 0.03, "healFlat": 25, "desc": "Passive: Basic attacks on the 'vital' side deal % true damage and heal."},
		"skills": {
			"Q": {
				"name": "Lunge", "effect": "DASH_STRIKE", "speed": 35.0, "damage": [60, 90, 120], "cd": [12, 10, 8], "mana": 45,
				"cd_reset_on_hit": 0.6, "vfx_cast": "VFX_Fiore_Lunge"
			},
			"W": {
				"name": "Riposte", "effect": "PARRY_STUN", "duration": 0.75, "cd": [24, 20, 16], "mana": 75,
				"vfx_cast": "VFX_Fiore_Riposte"
			},
			"E": {
				"name": "Blademanship", "effect": "EMPOWERED_AA", "critOnSecond": True, "cd": [11, 10, 9], "mana": 40
			},
			"R": {
				"name": "Grand Challenge", "effect": "MARK_VITALS", "duration": 8.0, "cd": [110, 95, 80], "mana": 100
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Nyx": { # Was Nighthawk
		"faction": "The Front",
		"role": "adc",
		"stats": {"maxHP": 510, "recovery": 1.2, "armor": 22, "mr": 28, "speed": 345, "range": 10.0, "isRanged": True, "turnRate": 450},
		"attackProjectile": "VFX_Arrow_Silver", "attackProjSpeed": 40.0, "vfx_attack_hit": "VFX_Arrow_Impact",
		"growthStats": {"hp": 78, "ad": 3.8, "as": 0.04, "armor": 2.5},
		"passive": {"id": "LONG_SHOT", "name": "Signal Eye", "rangeFlat": 1.5, "icon": "Heroes/Nighthawk/Textures/Icons/Passive.png"},
		"splash": "Heroes/Nighthawk/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Glitch Arrow", "effect": "LINEAR_PROJECTILE", "speed": 45.0, "range": 20.0, "damage": [50, 90, 130, 170, 210],
				"cd": [8, 7, 6, 5, 4], "mana": 35, "icon": "Heroes/Nighthawk/Textures/Icons/Q.png",
				"vfx_trail": "VFX_Hawk_Arrow_Trail", "vfx_hit": "VFX_Hawk_Arrow_Impact", "sfx_cast": "SFX_Hawk_Q"
			},
			"W": {
				"name": "Jitter Focus", "effect": "STAT_MOD", "duration": 5.0, "modifiers": {"as": 0.40, "speed": 30},
				"cd": [18, 16, 14, 12, 10], "mana": 60, "icon": "Heroes/Nighthawk/Textures/Icons/W.png",
				"vfx_cast": "VFX_Hawk_Focus", "sfx_cast": "SFX_Hawk_W"
			},
			"E": {
				"name": "Signal Roll", "effect": "DASH", "speed": 35.0, "duration": 0.25, "cd": [16, 14, 12, 10, 8], "mana": 50, "icon": "Heroes/Nighthawk/Textures/Icons/E.png",
				"vfx_cast": "VFX_Hawk_Roll", "sfx_cast": "SFX_Hawk_E"
			},
			"R": {
				"name": "Scavenged Bolt", "effect": "LINEAR_PROJECTILE", "speed": 50.0, "range": 50.0, "damage": [200, 350, 500],
				"cd": [100, 85, 70], "mana": 100, "isGlobal": True, "icon": "Heroes/Nighthawk/Textures/Icons/R.png",
				"vfx_trail": "VFX_Hawk_Ult_Trail", "vfx_hit": "VFX_Hawk_Ult_Explosion", "sfx_cast": "SFX_Hawk_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Sol": { # Was Embermage
		"faction": "Monsters",
		"role": "apc",
		"stats": {"maxHP": 500, "recovery": 1.4, "armor": 20, "mr": 30, "speed": 340, "range": 8.5, "isRanged": True, "turnRate": 450},
		"attackProjectile": "VFX_Ember_Orb", "attackProjSpeed": 28.0, "vfx_attack_hit": "VFX_Ember_Pop",
		"growthStats": {"hp": 72, "ad": 2.0, "mana": 55, "ap": 3.0},
		"passive": {"id": "BURN", "name": "Chaotic Flare", "burnDmg": 10, "duration": 4.0, "icon": "Heroes/Embermage/Textures/Icons/Passive.png"},
		"splash": "Heroes/Embermage/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Void Orb", "effect": "LINEAR_PROJECTILE", "speed": 32.0, "range": 14.0, "damage": [70, 115, 160, 205, 250],
				"cd": [6, 5.5, 5, 4.5, 4], "mana": 45, "icon": "Heroes/Embermage/Textures/Icons/Q.png",
				"vfx_trail": "VFX_Fireball_Trail", "vfx_hit": "VFX_Fireball_Burst", "sfx_cast": "SFX_Ember_Q"
			},
			"W": {
				"name": "Void Pool", "effect": "SUSTAINED_ZONE", "radius": 5.5, "dps": [50, 80, 110, 140, 170],
				"duration": 3.0, "cd": [14, 13, 12, 11, 10], "mana": 70, "icon": "Heroes/Embermage/Textures/Icons/W.png",
				"vfx_cast": "VFX_Ember_Pool", "vfx_persistent": True, "sfx_cast": "SFX_Ember_W"
			},
			"E": {
				"name": "Chaotic Snare", "effect": "STUN", "duration": 1.25, "range": 9.0, "cd": [16, 14, 12, 10, 8], "mana": 60, "icon": "Heroes/Embermage/Textures/Icons/E.png",
				"vfx_cast": "VFX_Ember_Snare", "vfx_hit": "VFX_Ember_Stun", "sfx_cast": "SFX_Ember_E"
			},
			"R": {
				"name": "Chaotic Storm", "effect": "SUSTAINED_ZONE", "radius": 8.0, "dps": [150, 225, 300],
				"cd": [130, 110, 90], "mana": 100, "isChannel": True, "duration": 3.0, "icon": "Heroes/Embermage/Textures/Icons/R.png",
				"vfx_cast": "VFX_Inferno_Storm", "vfx_persistent": True, "sfx_cast": "SFX_Ember_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Vern": { # Was Thornfang
		"faction": "Nomade's",
		"role": "jungle",
		"stats": {"maxHP": 560, "recovery": 2.0, "armor": 30, "mr": 30, "speed": 355, "range": 2.2, "isRanged": False, "turnRate": 630},
		"growthStats": {"hp": 82, "ad": 4.2, "armor": 3.0},
		"passive": {"id": "BLEED_AA", "name": "Organic Thorns", "dps": 12, "duration": 3.0, "icon": "Heroes/Thornfang/Textures/Icons/Passive.png"},
		"splash": "Heroes/Thornfang/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Organic Strike", "effect": "EMPOWERED_MS_AA", "msBoost": 0.20, "duration": 3.0,
				"cd": [7, 6, 5, 4, 3], "mana": 35, "icon": "Heroes/Thornfang/Textures/Icons/Q.png",
				"vfx_cast": "VFX_Thorn_Strike", "sfx_cast": "SFX_Thorn_Q"
			},
			"W": {
				"name": "Root Lunge", "effect": "DASH", "speed": 38.0, "duration": 0.25, "damage": [60, 90, 120, 150, 180],
				"cd": [12, 11, 10, 9, 8], "mana": 50, "icon": "Heroes/Thornfang/Textures/Icons/W.png",
				"vfx_cast": "VFX_Thorn_Lunge", "sfx_cast": "SFX_Thorn_W"
			},
			"E": {
				"name": "Organic Grasp", "effect": "ROOT", "duration": 1.0, "range": 6.0, "cd": [14, 13, 12, 11, 10], "mana": 55, "icon": "Heroes/Thornfang/Textures/Icons/E.png",
				"vfx_cast": "VFX_Vine_Grasp", "vfx_hit": "VFX_Vine_Root", "sfx_cast": "SFX_Thorn_E"
			},
			"R": {
				"name": "Nomade Rage", "effect": "STAT_MOD", "duration": 8.0,
				"modifiers": {"ad": 40, "speed": 60, "armor": 20, "mr": 20},
				"cd": [120, 100, 80], "mana": 100, "icon": "Heroes/Thornfang/Textures/Icons/R.png",
				"vfx_cast": "VFX_Thorn_Rage", "vfx_persistent": True, "sfx_cast": "SFX_Thorn_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Mara": { # Was Tidecaller
		"faction": "Nomade's",
		"role": "support",
		"stats": {"maxHP": 550, "recovery": 2.5, "armor": 30, "mr": 38, "speed": 335, "range": 7.0, "isRanged": True, "turnRate": 450},
		"attackProjectile": "VFX_Water_Orb", "attackProjSpeed": 25.0, "vfx_attack_hit": "VFX_Water_Splash",
		"growthStats": {"hp": 80, "armor": 3.5, "mr": 3.5},
		"passive": {"id": "HEAL_AA", "name": "Nomade Wave", "healFlat": 20, "icon": "Heroes/Tidecaller/Textures/Icons/Passive.png"},
		"splash": "Heroes/Tidecaller/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Organic Wave", "effect": "LINEAR_PROJECTILE", "speed": 25.0, "range": 12.0, "damage": [60, 100, 140, 180, 220],
				"cd": [10, 9, 8, 7, 6], "mana": 50, "icon": "Heroes/Tidecaller/Textures/Icons/Q.png",
				"vfx_trail": "VFX_Tidal_Wave_Trail", "vfx_hit": "VFX_Tidal_Wave_Stun", "sfx_cast": "SFX_Tide_Q",
				"onHit": "STUN", "stunDuration": 1.0
			},
			"W": {
				"name": "Nature's Mist", "effect": "HEAL_PERCENT", "percent": 0.12, "cd": [10, 9, 8, 7, 6], "mana": 60, "icon": "Heroes/Tidecaller/Textures/Icons/W.png",
				"vfx_cast": "VFX_Tidal_Heal", "sfx_cast": "SFX_Tide_W"
			},
			"E": {
				"name": "Fluid Shield", "effect": "HP_SCALED_SHIELD", "value": [60, 90, 120, 150, 180], "duration": 3.0,
				"cd": [14, 13, 12, 11, 10], "mana": 65, "icon": "Heroes/Tidecaller/Textures/Icons/E.png",
				"vfx_cast": "VFX_Water_Shield", "sfx_cast": "SFX_Tide_E"
			},
			"R": {
				"name": "Resonance Tsunami", "effect": "LINEAR_PROJECTILE", "speed": 20.0, "range": 40.0,
				"damage": [150, 250, 350], "cd": [140, 120, 100], "mana": 100, "icon": "Heroes/Tidecaller/Textures/Icons/R.png",
				"onHit": "STUN", "stunDuration": 1.5,
				"vfx_trail": "VFX_Tsunami_Trail", "vfx_hit": "Vsunami_Impact", "sfx_cast": "SFX_Tide_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},

	# ===================== NEW SUPPORT HEROES =====================

	"Dredge": {
		"faction": "The Front",
		"role": "support",
		"stats": {"maxHP": 560, "recovery": 1.8, "armor": 28, "mr": 32, "speed": 325, "range": 2.2, "isRanged": False, "turnRate": 630},
		"growthStats": {"hp": 85, "ad": 4.2, "armor": 3.0},
		"passive": {"id": "DROWNED_GIFT", "name": "Scavenged Bounty", "adPerHP": 0.1, "icon": "Heroes/Dredge/Textures/Icons/Passive.png"},
		"splash": "Heroes/Dredge/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Rust Skewer", "effect": "LINEAR_PROJECTILE", "speed": 50.0, "range": 12.0, "damage": [80, 120, 160], 
				"onHit": "GRAB_PULL", "cd": [14, 12, 10], "mana": 60, "icon": "Heroes/Dredge/Textures/Icons/Q.png",
				"vfx_trail": "VFX_Harpoon_Chain", "vfx_hit": "VFX_Water_Explosion", "sfx_cast": "SFX_Dredge_Q"
			},
			"W": {
				"name": "Signal Undertow", "effect": "DASH", "speed": 40.0, "duration": 0.3, "onFinish": "AO_STUN", "radius": 3.0,
				"cd": [15, 13, 11], "mana": 50, "icon": "Heroes/Dredge/Textures/Icons/W.png",
				"vfx_cast": "VFX_Dredge_GhostWater", "sfx_cast": "SFX_Dredge_W"
			},
			"E": {
				"name": "Glitch Water", "effect": "ACTIVE_STEALTH", "duration": 5.0, "msBoost": 0.3, "cd": [20, 18, 16], "mana": 60, "icon": "Heroes/Dredge/Textures/Icons/E.png"
			},
			"R": {
				"name": "Depth Execution", "effect": "EXECUTE_TRUE", "range": 3.5, "baseDamage": [250, 400, 550], "cd": [120, 100, 80],
				"isGlobalShare": True, "icon": "Heroes/Dredge/Textures/Icons/R.png", "vfx_cast": "VFX_Dredge_XStrike", "sfx_cast": "SFX_Dredge_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},

	"Vento": {
		"faction": "Jun Hu",
		"role": "support",
		"stats": {"maxHP": 540, "recovery": 1.6, "armor": 24, "mr": 30, "speed": 340, "range": 8.0, "isRanged": True, "turnRate": 450},
		"attackProjectile": "VFX_Wind_Blast", "attackProjSpeed": 35.0,
		"growthStats": {"hp": 80, "armor": 3.0, "mr": 3.0},
		"passive": {"id": "SONIC_AURA", "name": "Harmonized Aura", "range": 10.0, "icon": "Heroes/Vento/Textures/Icons/Passive.png"},
		"splash": "Heroes/Vento/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Harmonized Pulse", "effect": "LINEAR_PROJECTILE", "speed": 45.0, "range": 14.0, "onHit": "STUN", "stunDuration": 1.0,
				"cd": [12, 11, 10], "mana": 50, "icon": "Heroes/Vento/Textures/Icons/Q.png", "vfx_trail": "VFX_Vento_Tornado", "sfx_cast": "SFX_Vento_Q"
			},
			"W": {
				"name": "Sync Surge", "effect": "AURA_TOGGLE", "isAutoSwap": True, "cd": 1.0, "mana": 0, "icon": "Heroes/Vento/Textures/Icons/W.png"
			},
			"E": {
				"name": "Resonance Boost", "effect": "STAT_MOD_AURA", "duration": 3.0, "cd": [15, 14, 13], "mana": 80, "icon": "Heroes/Vento/Textures/Icons/E.png"
			},
			"R": {
				"name": "Prismatic Barrier", "effect": "AOE_SHIELD", "radius": 12.0, "value": [500, 750, 1000], "duration": 5.0,
				"cd": [140, 120, 100], "mana": 100, "icon": "Heroes/Vento/Textures/Icons/R.png", "vfx_cast": "VFX_Vento_Barrier", "sfx_cast": "SFX_Vento_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},

	"Lyra": {
		"faction": "Imperium",
		"role": "support",
		"stats": {"maxHP": 520, "recovery": 1.4, "armor": 22, "mr": 30, "speed": 330, "range": 12.0, "isRanged": True, "turnRate": 450},
		"attackProjectile": "VFX_Med_Bolt", "attackProjSpeed": 50.0,
		"growthStats": {"hp": 75, "armor": 2.5, "mr": 2.5},
		"passive": {"id": "OPTIC_STINGER", "name": "Amplified Care", "healBase": 15, "icon": "Heroes/Lyra/Textures/Icons/Passive.png"},
		"splash": "Heroes/Lyra/Textures/Splash/Splash.png",
		"skills": {
			"Q": {
				"name": "Resonance Dart", "effect": "STUN", "duration": 2.5, "range": 18.0, "speed": 55.0,
				"cd": [18, 16, 14], "mana": 75, "icon": "Heroes/Lyra/Textures/Icons/Q.png", "vfx_trail": "VFX_Ana_Dart", "sfx_cast": "SFX_Ana_Q"
			},
			"W": {
				"name": "Amplified Burst", "effect": "AOE_HEAL_AMP", "radius": 5.0, "duration": 5.0, "cd": [14, 13, 12], "mana": 60, "icon": "Heroes/Lyra/Textures/Icons/W.png"
			},
			"E": {
				"name": "Pix Overclock", "effect": "BUFF_ALLY", "asBoost": 0.4, "cd": [16, 15, 14], "mana": 70, "icon": "Heroes/Lyra/Textures/Icons/E.png"
			},
			"R": {
				"name": "Imperium Surge", "effect": "BUFF_ALLY", "dr": 0.5, "ad": 50, "ap": 50, "duration": 8.0, 
				"cd": [120, 110, 100], "mana": 100, "icon": "Heroes/Lyra/Textures/Icons/R.png", "vfx_cast": "VFX_Ana_Nano", "sfx_cast": "SFX_Ana_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Kage": {
		"faction": "Jun Hu",
		"role": "mid",
		"stats": {"maxHP": 540, "recovery": 1.6, "armor": 26, "mr": 30, "speed": 355, "range": 2.0, "isRanged": False, "turnRate": 630},
		"growthStats": {"hp": 82, "ad": 4.0, "armor": 3.0},
		"passive": {"id": "SHADOW_MARK", "name": "Harmonized Mark", "bonusTrueDmg": 40, "threshold": 0.4},
		"splash": "Heroes/Kage/Textures/Splash/Splash.png",
		"skills": {
			"Q": {"name": "Crystalline Strike", "effect": "DASH_STRIKE", "speed": 35.0, "damage": [60, 95, 130, 165, 200], "cd": [9, 8, 7, 6, 5], "mana": 50},
			"W": {"name": "Prism Obscure", "effect": "ACTIVE_STEALTH", "duration": 2.5, "cd": [20, 18, 16, 14, 12], "mana": 65},
			"E": {"name": "Geometric Blades", "effect": "CIRCULAR_AOE", "radius": 4.5, "damage": [70, 100, 130, 160, 190], "cd": [12, 11, 10, 9, 8], "mana": 55},
			"R": {"name": "Perfect Execution", "effect": "BLINK_EXECUTE", "range": 7.0, "damage": [250, 400, 550], "cd": [120, 100, 80], "mana": 100},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Aether": {
		"faction": "Jun Hu",
		"role": "mid",
		"stats": {"maxHP": 520, "recovery": 1.4, "armor": 22, "mr": 30, "speed": 335, "range": 8.5, "isRanged": True},
		"growthStats": {"hp": 75, "ap": 4.0, "mana": 60},
		"passive": {"id": "ARCANE_LINK", "name": "Harmonized Link", "damageAmp": 0.15},
		"skills": {
			"Q": {"name": "Place Prism", "effect": "SUMMON_OBJECT", "template": "ArcaneConduit", "cd": [12, 11, 10, 9, 8], "maxCount": 2, "mana": 70},
			"W": {"name": "Geometric Shield", "effect": "SHIELD_SELF", "value": [80, 120, 160, 200, 240], "duration": 3.0, "cd": [16, 15, 14, 13, 12], "mana": 60},
			"E": {"name": "Resonance Pull", "effect": "PULL_TO_OBJECTS", "range": 10.0, "cd": [18, 16, 14, 12, 10], "mana": 80},
			"R": {"name": "Sync Singularity", "effect": "OBJECT_EXPLOSION", "damage": [200, 325, 450], "cd": [120, 105, 90], "mana": 100},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Icarus": {
		"faction": "The Front",
		"role": "mid",
		"stats": {"maxHP": 550, "recovery": 2.0, "armor": 25, "mr": 30, "speed": 340, "range": 2.5, "isRanged": False},
		"growthStats": {"hp": 85, "ad": 3.8, "speed": 4.0},
		"passive": {"id": "SOARING_WILL", "name": "Scavenged Grace", "bonusSpeedRiver": 45},
		"skills": {
			"Q": {"name": "Signal Blade", "effect": "LINEAR_PROJECTILE", "speed": 35.0, "damage": [70, 110, 150, 190, 230], "cd": [8, 7, 6, 5, 4], "mana": 50},
			"W": {"name": "Glitch Takeoff", "effect": "DASH", "speed": 30.0, "duration": 0.2, "cd": [14, 13, 12, 11, 10], "mana": 60},
			"E": {"name": "Jitter Spear", "effect": "STUN", "duration": 1.25, "range": 6.0, "cd": [16, 15, 14, 13, 12], "mana": 75},
			"R": {"name": "Glitch Flight", "effect": "GLOBAL_DASH", "speed": 55.0, "range": 65.0, "damage": [150, 250, 350], "cd": [140, 120, 100], "mana": 100},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Nova": {
		"faction": "Imperium",
		"role": "mid",
		"stats": {"maxHP": 500, "recovery": 1.2, "armor": 18, "mr": 30, "speed": 335, "range": 10.0, "isRanged": True},
		"growthStats": {"hp": 70, "ap": 5.0, "mana": 70},
		"passive": {"id": "STARLIGHT", "name": "Amplified Stacks", "explosiveDamage": 100, "stacksRequired": 3},
		"skills": {
			"Q": {"name": "Resonance Beam", "effect": "LINEAR_BEAM", "damage": [80, 130, 180, 230, 280], "range": 22.0, "cd": [9, 8, 7, 6, 5], "mana": 60},
			"W": {"name": "Amplified Suns", "effect": "ORBITAL_SHIELD", "damagePerSec": [20, 35, 50, 65, 80], "duration": 4.0, "cd": [18, 17, 16, 15, 14], "mana": 70},
			"E": {"name": "Gravity Well", "effect": "SUSTAINED_ZONE", "radius": 6.0, "slow": 0.40, "duration": 3.0, "cd": [16, 14, 12, 10, 8], "mana": 80},
			"R": {"name": "Imperium Supernova", "effect": "GLOBAL_AOE", "damage": [250, 400, 550], "range": 70.0, "cd": [160, 140, 120], "mana": 100},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Vex": {
		"faction": "Monsters",
		"role": "mid",
		"stats": {"maxHP": 560, "recovery": 1.8, "armor": 30, "mr": 34, "speed": 340, "range": 2.2, "isRanged": False},
		"growthStats": {"hp": 90, "ad": 2.5, "ap": 3.5},
		"passive": {"id": "SOUL_HARVEST", "name": "Chaotic Gluttony", "apPerKill": 2, "maxStacks": 50},
		"skills": {
			"Q": {"name": "Void Orb", "effect": "LINEAR_PROJECTILE", "speed": 28.0, "damage": [90, 140, 190, 240, 290], "cd": [10, 9, 8, 7, 6], "mana": 60},
			"W": {"name": "Chaotic Tether", "effect": "TETHER_DRAIN", "dps": [30, 50, 70, 90, 110], "duration": 3.5, "range": 6.5, "cd": [14, 13, 12, 11, 10], "mana": 70},
			"E": {"name": "Void Phantasm", "effect": "BLINK_DECOY", "range": 5.0, "duration": 1.5, "cd": [18, 16, 14, 12, 10], "mana": 80},
			"R": {"name": "Eldritch Feast", "effect": "AOE_DRAIN", "radius": 7.5, "damage": [150, 250, 350], "healPercent": 0.5, "cd": [140, 120, 100], "mana": 100},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	},
	"Cinder": { # The Magma Warden
		"faction": "Armhold",
		"role": "support",
		"stats": {
			"maxHP": 650, "recovery": 3.2, "armor": 42, "mr": 38,
			"speed": 310, "range": 2.2, "isRanged": False, "turnRate": 550,
			"maxMana": 400, "manaRegen": 2.0, "ad": 58, "ap": 0
		},
		"growthStats": {"hp": 105, "armor": 5.0, "mr": 4.8},
		"passive": {"id": "MELTDOWN", "name": "Industrial Aura", "armorShred": 5, "desc": "Passive: Shreds 5 Armor/MR via industrial resonance every 1s."},
		"skills": {
			"Q": {
				"name": "Armhold Hook", "effect": "GRAB_PULL", "range": 8.5, "cd": [18, 16, 14, 12, 10], "mana": 70,
				"vfx_cast": "VFX_Cinder_Hook", "sfx_cast": "SFX_Cinder_Q"
			},
			"W": {
				"name": "Steam Wave", "effect": "CIRCULAR_AOE", "radius": 5.5, "damage": [60, 90, 120, 150, 180], 
				"cd": [12, 11, 10, 9, 8], "mana": 60, "vfx_cast": "VFX_Cinder_Wave"
			},
			"E": {
				"name": "Furnace Pool", "effect": "SUSTAINED_ZONE", "radius": 6.0, "slow": 0.35, "duration": 4.0,
				"cd": [16, 15, 14, 13, 12], "mana": 65, "vfx_cast": "VFX_Cinder_Pool", "vfx_persistent": True
			},
			"R": {
				"name": "Boiler Overload", "effect": "AOE_KNOCKUP", "radius": 8.0, "damage": [150, 250, 350],
				"cd": [130, 115, 100], "mana": 100, "vfx_cast": "VFX_Cinder_Eruption", "sfx_cast": "SFX_Cinder_R"
			},
			"TRINKET": {"effect": "SUMMON_WARD", "duration": 90.0, "cd": 120.0, "mana": 0}
		}
	}
}
HERO_REGISTRY["Warrior"] = HERO_REGISTRY["Kael"]

SUMMONER_REGISTRY = {
	"Flash": {
		"effect": "BLINK", "range": 6.5, "cd": 300,
		"combos": {"allowedEffects": ["all"]},
		"icon": "Icon_Spell_Flash"
	},
	"Ignite": {
		"effect": "BLEED", "dps": 20, "duration": 5.0, "range": 7.0, "cd": 180,
		"grievousWounds": 0.4,
		"icon": "Icon_Spell_Ignite"
	},
	"Smite": {
		"effect": "EXECUTE_TRUE", "range": 6.0, "damage": 900, "cd": 90,
		"healOnKill": 0.1,
		"icon": "Icon_Spell_Smite"
	},
	"Teleport": {
		"effect": "CHANNEL_TP", "channelTime": 4.0, "cd": 360,
		"icon": "Icon_Spell_Teleport"
	},
	"Ghost": {
		"effect": "SPEED_BUFF", "speedBonus": 0.28, "duration": 10.0, "cd": 210,
		"icon": "Icon_Spell_Ghost"
	},
	"Heal": {
		"effect": "HEAL_BURST", "healBase": 90, "healPerLevel": 15, "cd": 240,
		"speedBonus": 0.30, "speedDuration": 1.0,
		"icon": "Icon_Spell_Heal"
	},
	"Barrier": {
		"effect": "SHIELD", "shieldBase": 115, "shieldPerLevel": 10,
		"duration": 2.5, "cd": 180,
		"icon": "Icon_Spell_Barrier"
	},
	"Exhaust": {
		"effect": "EXHAUST", "slow": 0.30, "damageReduction": 0.40,
		"duration": 3.0, "range": 6.5, "cd": 210,
		"icon": "Icon_Spell_Exhaust"
	},
	"Cleanse": {
		"effect": "CLEANSE", "cd": 210,
		"icon": "Icon_Spell_Cleanse"
	}
}
