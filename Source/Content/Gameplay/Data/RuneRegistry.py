# RuneRegistry.py
# Phase 102: Pre-game strategy layer for hero customization.

RUNE_TREE = {
	"PRECISION": {
		"color": [1.0, 0.8, 0.2, 1.0], # Gold
		"keystones": {
			"LETHAL_TEMPO": {
				"id": "LETHAL_TEMPO",
				"name": "Lethal Tempo",
				"description": "Attacking an enemy hero grants 10% Attack Speed for 6s, stacking up to 6 times. At max stacks, gain +2 range.",
				"as_per_stack": 0.10,
				"max_stacks": 6,
				"bonus_range": 2.0,
				"icon": "Icon_Rune_LethalTempo"
			},
			"CONQUEROR": {
				"id": "CONQUEROR",
				"name": "Conqueror",
				"description": "Attacks and abilities grant stacks of Adaptive AD/AP. At 12 stacks, heal for 8% of damage dealt to heroes.",
				"max_stacks": 12,
				"heal_percent": 0.08,
				"icon": "Icon_Rune_Conqueror"
			}
		}
	},
	"SORCERY": {
		"color": [0.4, 0.4, 1.0, 1.0], # Blue
		"keystones": {
			"ARCANE_COMET": {
				"id": "ARCANE_COMET",
				"name": "Arcane Comet",
				"description": "Damaging a hero with an ability hurls a comet at them, dealing magic damage in an area.",
				"base_damage": 30,
				"scaling": 0.35, # AP scaling
				"cooldown": 20.0,
				"icon": "Icon_Rune_ArcaneComet"
			},
			"PHASE_RUSH": {
				"id": "PHASE_RUSH",
				"name": "Phase Rush",
				"description": "Hitting a hero with 3 unique attacks/abilities within 3s grants 30-60% MS and 75% Slow Resist.",
				"duration": 3.0,
				"cooldown": 30.0,
				"icon": "Icon_Rune_PhaseRush"
			}
		}
	},
	"RESOLVE": {
		"color": [0.2, 1.0, 0.2, 1.0], # Green
		"keystones": {
			"GRASP_OF_THE_UNDYING": {
				"id": "GRASP_OF_THE_UNDYING",
				"name": "Grasp of the Undying",
				"description": "Every 4s in combat, your next attack on a hero deals 3% Max HP magic damage and heals you for 2% Max HP.",
				"charge_time": 4.0,
				"damage_hp_ratio": 0.03,
				"heal_hp_ratio": 0.02,
				"icon": "Icon_Rune_Grasp"
			},
			"AFTERSHOCK": {
				"id": "AFTERSHOCK",
				"name": "Aftershock",
				"description": "After immobilizing an enemy, gain +35 Armor/MR for 2.5s, then explode for magic damage nearby.",
				"duration": 2.5,
				"cooldown": 20.0,
				"icon": "Icon_Rune_Aftershock"
			}
		}
	},
	"DOMINATION": {
		"color": [1.0, 0.2, 0.2, 1.0], # Red
		"keystones": {
			"ELECTROCUTE": {
				"id": "ELECTROCUTE",
				"name": "Electrocute",
				"description": "Hitting a hero with 3 unique attacks/abilities within 3s deals 30-180 bonus Adaptive Damage.",
				"base": 30, "per_level": 8.0, "cooldown": 25.0, "icon": "Icon_Rune_Electrocute"
			},
			"DARK_HARVEST": {
				"id": "DARK_HARVEST",
				"name": "Dark Harvest",
				"description": "Damaging a hero below 50% HP deals bonus damage and harvests 5 soul essence (+5 damage per soul).",
				"threshold": 0.5, "base": 20, "per_soul": 5.0, "cooldown": 45.0, "icon": "Icon_Rune_DarkHarvest"
			}
		},
		"minor_runes": {
			"EYEBALL_COLLECTION": {"ad": 10, "ap": 15},
			"SUDDEN_IMPACT": {"lethality": 8, "magicPenFlat": 6, "trigger": "AFTER_DASH"}
		}
	}
}

# Add minor runes to the other trees as well
RUNE_TREE["PRECISION"]["minor_runes"] = {
	"LEGEND_ALACRITY": {"as": 0.10},
	"LEGEND_TENACITY": {"tenacity": 0.10}
}
RUNE_TREE["SORCERY"]["minor_runes"] = {
	"MANAFLOW_BAND": {"maxMana": 250},
	"TRANSCENDENCE": {"cdr": 0.10}
}
RUNE_TREE["RESOLVE"]["minor_runes"] = {
	"OVERGROWTH": {"maxHP": 150},
	"SECOND_WIND": {"hpRegen": 3.0}
}

def get_rune_data(rune_id):
	"""Returns the data block for a specific rune ID."""
	for tree in RUNE_TREE.values():
		if rune_id in tree["keystones"]:
			return tree["keystones"][rune_id]
	return None
