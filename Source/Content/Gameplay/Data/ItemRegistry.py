ITEM_REGISTRY = {
	# =========================================================================
	# BASIC COMPONENTS (TIER 1)
	# =========================================================================
	"Long Sword": {"price": 350, "stats": {"ad": 10}, "icon": "Icon_Item_LongSword"},
	"Dagger": {"price": 300, "stats": {"as": 0.12}, "icon": "Icon_Item_Dagger"},
	"Ruby Crystal": {"price": 400, "stats": {"hp": 150}, "icon": "Icon_Item_RubyCrystal"},
	"Cloth Armor": {"price": 300, "stats": {"armor": 15}, "icon": "Icon_Item_ClothArmor"},
	"Null-Magic Mantle": {"price": 450, "stats": {"mr": 25}, "icon": "Icon_Item_NullMagicMantle"},
	"Amplifying Tome": {"price": 400, "stats": {"ap": 20}, "icon": "Icon_Item_AmplifyingTome"},
	"Sapphire Crystal": {"price": 350, "stats": {"mana": 250}, "icon": "Icon_Item_SapphireCrystal"},
	"Faerie Charm": {"price": 250, "stats": {"manaRegen": 0.5}, "icon": "Icon_Item_FaerieCharm"},
	"Rejuvenation Bead": {"price": 300, "stats": {"hpRegen": 0.5}, "icon": "Icon_Item_RejuvenationBead"},
	"Cloak of Agility": {"price": 600, "stats": {"crit": 0.15}, "icon": "Icon_Item_Cloak"},
	"Pickaxe": {"price": 875, "stats": {"ad": 25}, "icon": "Icon_Item_Pickaxe"},
	"B.F. Sword": {"price": 1300, "stats": {"ad": 40}, "icon": "Icon_Item_BFSword"},

	# =========================================================================
	# ADVANCED COMPONENTS (TIER 2)
	# =========================================================================
	"Chain Vest": {"price": 800, "recipe": ["Cloth Armor"], "stats": {"armor": 40}, "icon": "Icon_Item_ChainVest"},
	"Negatron Cloak": {"price": 900, "recipe": ["Null-Magic Mantle"], "stats": {"mr": 50}, "icon": "Icon_Item_NegatronCloak"},
	"Blasting Wand": {"price": 850, "stats": {"ap": 40}, "icon": "Icon_Item_BlastingWand"},
	"Fiendish Codex": {"price": 900, "recipe": ["Amplifying Tome"], "stats": {"ap": 35, "cdr": 0.1}, "icon": "Icon_Item_FiendishCodex"},
	"Giant's Belt": {"price": 900, "recipe": ["Ruby Crystal"], "stats": {"hp": 350}, "icon": "Icon_Item_GiantsBelt"},
	"Vampiric Scepter": {"price": 900, "recipe": ["Long Sword"], "stats": {"ad": 15, "lifeSteal": 0.1}, "icon": "Icon_Item_VampScepter"},
	"Recurve Bow": {"price": 700, "recipe": ["Dagger"], "stats": {"as": 0.15, "onHit": 15}, "icon": "Icon_Item_RecurveBow"},
	"Caulfield's Warhammer": {"price": 1100, "recipe": ["Long Sword", "Long Sword"], "stats": {"ad": 25, "cdr": 0.1}, "icon": "Icon_Item_Warhammer"},
	"Kircheis Shard": {"price": 700, "recipe": ["Dagger"], "stats": {"as": 0.1}, "effects": {"onTick": "ENERGIZED"}, "icon": "Icon_Item_Kircheis"},
	"Zeal": {"price": 1100, "recipe": ["Dagger", "Cloak of Agility"], "stats": {"as": 0.15, "crit": 0.15, "speed": 15}, "icon": "Icon_Item_Zeal"},
	"Sheen": {"price": 700, "stats": {"mana": 250}, "effects": {"onAbilityCast": "SPELLBLADE_READY"}, "uniquePassive": "SPELLBLADE", "icon": "Icon_Item_Sheen"},
	"Executioner's Calling": {"price": 800, "recipe": ["Long Sword"], "stats": {"ad": 15}, "effects": {"onHit": "GRIEVOUS_WOUNDS"}, "uniquePassive": "GRIEVOUS_WOUNDS", "icon": "Icon_Item_Executioners"},
	"Last Whisper": {"price": 1450, "recipe": ["Long Sword", "Long Sword"], "stats": {"ad": 20, "armorPenPercent": 0.15}, "icon": "Icon_Item_LastWhisper"},

	# =========================================================================
	# TANK ITEMS
	# =========================================================================
	"Sunfire Aegis": {
		"price": 2700, "recipe": ["Chain Vest", "Giant's Belt"], "combinePrice": 1000,
		"stats": {"hp": 500, "armor": 50}, "effects": {"onTick": "IMMOLATE"},
		"uniquePassive": "IMMOLATE", "icon": "Icon_Item_Sunfire"
	},
	"Thornmail": {
		"price": 2700, "recipe": ["Chain Vest", "Ruby Crystal"], "combinePrice": 1500,
		"stats": {"hp": 350, "armor": 70}, "effects": {"onTakeDamage": "THORNS"},
		"icon": "Icon_Item_Thornmail"
	},
	"Force of Nature": {
		"price": 2800, "recipe": ["Negatron Cloak", "Ruby Crystal"], "combinePrice": 1500,
		"stats": {"hp": 400, "mr": 60, "speed": 15}, "effects": {"onTakeMagicDamage": "STEADFAST"}
	},
	"Randuin's Omen": {
		"price": 2700, "recipe": ["Chain Vest", "Ruby Crystal"], "combinePrice": 1500,
		"stats": {"hp": 400, "armor": 55}, "effects": {"onTakeDamage": "CRIT_RESILIENCE"},
		"uniquePassive": "HUMILITY", "description": "Reduces damage from Critical Strikes by 30%.",
		"icon": "Icon_Item_Randuins"
	},
	"Jak'Sho, The Protean": {
		"price": 3200, "recipe": ["Chain Vest", "Negatron Cloak", "Ruby Crystal"], "combinePrice": 1200,
		"stats": {"hp": 300, "armor": 30, "mr": 30}, "effects": {"onTick": "VOID_BORN_RESILIENCE"},
		"uniquePassive": "VOID_RESILIENCE", "description": "After 5s in combat with heroes, increase total bonus Armor and MR by 30% until combat ends.",
		"icon": "Icon_Item_JakSho"
	},

	# =========================================================================
	# FIGHTER ITEMS
	# =========================================================================
	"Black Cleaver": {
		"price": 3100, "recipe": ["Caulfield's Warhammer", "Ruby Crystal"], "combinePrice": 1600,
		"stats": {"ad": 45, "hp": 400, "cdr": 0.2}, "effects": {"onHit": "CLEAVE_SHRED"}
	},
	"Sterak's Gage": {
		"price": 3000, "recipe": ["Long Sword", "Ruby Crystal"], "combinePrice": 2250,
		"stats": {"ad": 40, "hp": 450}, "effects": {"onTick": "LIFELINE_CHECK"},
		"uniquePassive": "LIFELINE"
	},
	"Death's Dance": {
		"price": 3200, "recipe": ["Caulfield's Warhammer", "Chain Vest", "Pickaxe"], "combinePrice": 1000,
		"stats": {"ad": 55, "armor": 45, "cdr": 0.15}, "effects": {"onTakeDamage": "IGNORE_PAIN"},
		"uniquePassive": "DEFIANCE", "icon": "Icon_Item_DeathsDance"
	},
	"Gore-Drinker": {
		"price": 3300, "recipe": ["Caulfield's Warhammer", "Giant's Belt", "Long Sword"], "combinePrice": 950,
		"stats": {"ad": 55, "hp": 400, "cdr": 0.20}, 
		"active_id": "THIRST_SLASH", "active_cd": 15, "description": "Active: Deals AOE damage and heals for 8% missing HP per enemy hit.",
		"icon": "Icon_Item_Goredrinker"
	},
	"Hullbreaker": {
		"price": 3000, "recipe": ["Pickaxe", "Ruby Crystal", "Cloth Armor"], "combinePrice": 1425,
		"stats": {"ad": 65, "hp": 350, "armor": 25}, "effects": {"onTick": "HULLBREAKER_CHECK"},
		"uniquePassive": "BOARDING_PARTY", "description": "Grants 35-60 bonus Armor and MR when no allies are nearby. Boosts turret damage.",
		"icon": "Icon_Item_Hullbreaker"
	},
	"Ravenous Hydra": {
		"price": 3300, "recipe": ["Pickaxe", "Vampiric Scepter", "Caulfield's Warhammer"], "combinePrice": 425,
		"stats": {"ad": 65, "lifeSteal": 0.12, "cdr": 0.20}, "effects": {"onHit": "RAVENOUS_CLEAVE"},
		"uniquePassive": "CLEAVE", "icon": "Icon_Item_Hydra"
	},
	"Divine Sunderer": {
		"price": 3300, "recipe": ["Sheen", "Caulfield's Warhammer", "Ruby Crystal"], "combinePrice": 800,
		"stats": {"ad": 40, "hp": 300, "cdr": 0.20}, "effects": {"onHit": "SPELLBLADE_HEAL"},
		"uniquePassive": "SPELLBLADE", "icon": "Icon_Item_Sunderer"
	},
	"Stridebreaker": {
		"price": 3300, "recipe": ["Pickaxe", "Dagger", "Ruby Crystal"], "combinePrice": 1100,
		"stats": {"ad": 50, "as": 0.2, "hp": 400, "cdr": 0.2}, 
		"active_id": "HALTING_SLASH", "active_cd": 15, "description": "Active: Deals AOE damage and slows enemies by 40%.",
		"icon": "Icon_Item_Stridebreaker"
	},
	"Spear of Shojin": {
		"price": 3300, "recipe": ["Caulfield's Warhammer", "B.F. Sword", "Ruby Crystal"], "combinePrice": 500,
		"stats": {"ad": 55, "hp": 300, "cdr": 0.20}, "effects": {"onTick": "DRAGON_FORCE"},
		"description": "Increases spell haste for basic abilities based on missing HP.", "icon": "Icon_Item_Shojin"
	},

	# =========================================================================
	# ASSASSIN ITEMS
	# =========================================================================
	"Youmuu's Ghostblade": {
		"price": 3000, "recipe": ["Caulfield's Warhammer", "Long Sword"], "combinePrice": 1550,
		"stats": {"ad": 55, "lethality": 18, "cdr": 0.15}, 
		"active_id": "GHOST_STEP", "active_cd": 45, "icon": "Icon_Item_Youmuus"
	},
	"Edge of Night": {
		"price": 3100, "recipe": ["Long Sword", "Ruby Crystal"], "combinePrice": 2150,
		"stats": {"ad": 55, "lethality": 18, "cdr": 0.15, "hp": 250}, "effects": {"onTick": "SPELL_SHIELD_REFRESH"},
		"icon": "Icon_Item_EdgeOfNight"
	},
	"Umbral Glaive": {
		"price": 2600, "recipe": ["Long Sword", "Long Sword"], "combinePrice": 1600,
		"stats": {"ad": 50, "lethality": 18, "cdr": 0.15}, "effects": {"onTick": "BLACKOUT_DETECT"},
		"icon": "Icon_Item_Umbral"
	},
	"The Collector": {
		"price": 3100, "recipe": ["Pickaxe", "Cloak of Agility"], "combinePrice": 1600,
		"stats": {"ad": 55, "lethality": 18, "crit": 0.20}, "effects": {"onHit": "EXECUTE_LOW_HP"},
		"icon": "Icon_Item_Collector"
	},
	"Axiom Arc": {
		"price": 3000, "recipe": ["Caulfield's Warhammer", "Long Sword"], "combinePrice": 1550,
		"stats": {"ad": 55, "lethality": 18, "cdr": 0.25}, "effects": {"onKill": "ULT_REFUND"},
		"icon": "Icon_Item_Axiom"
	},
	"Serylda's Grudge": {
		"price": 3200, "recipe": ["Caulfield's Warhammer", "Last Whisper"], "combinePrice": 650,
		"stats": {"ad": 55, "lethality": 18, "cdr": 0.20}, "effects": {"onAbilityHit": "ICY_SLOW"},
		"icon": "Icon_Item_Serylda"
	},

	# =========================================================================
	# AP ITEMS
	# =========================================================================
	"Luden's Tempest": {
		"price": 3200, "recipe": ["Lost Chapter", "Blasting Wand", "Amplifying Tome"], "combinePrice": 1050,
		"stats": {"ap": 90, "mana": 600, "cdr": 0.20}, "effects": {"onHit": "ECHO_PROC"},
		"uniquePassive": "ECHO", "icon": "Icon_Item_Ludens"
	},
	"Warden's Shroud": {
		"price": 3000, "recipe": ["Lost Chapter", "Ruby Crystal", "Amplifying Tome"], "combinePrice": 1200,
		"stats": {"ap": 70, "hp": 300, "mana": 400, "cdr": 0.15}, "effects": {"onHit": "SPECTRAL_CHAIN"},
		"uniquePassive": "GRAVITY_MARK", "description": "Dealing spell damage to a hero grounds them for 1.5s (12s CD).",
		"icon": "Icon_Item_WardensShroud"
	},
	"Rabadon's Deathcap": {
		"price": 3200, "recipe": ["Fiendish Codex", "Blasting Wand"], "combinePrice": 1450,
		"stats": {"ap": 75, "hp": 300, "mana": 600}, "effects": {"onHit": "TORMENT_BURN"}
	},
	"Zhonya's Hourglass": {
		"price": 3000, "recipe": ["Fiendish Codex", "Cloth Armor"], "combinePrice": 1800,
		"stats": {"ap": 80, "armor": 45, "cdr": 0.15}, 
		"active_id": "STASIS", "active_cd": 120, "icon": "Icon_Item_Zhonyas"
	},
	"Morellonomicon": {
		"price": 2500, "recipe": ["Blasting Wand", "Ruby Crystal"], "combinePrice": 1250,
		"stats": {"ap": 90, "hp": 300}, "effects": {"onHit": "GRIEVOUS_WOUNDS"}
	},
	"Shadowflame": {
		"price": 3200, "recipe": ["Blasting Wand", "Wand of Restoration"], "combinePrice": 1250,
		"stats": {"ap": 115, "magicPenFlat": 12}, "effects": {"onHit": "CINDERBLOOM_SHRED"},
		"description": "Ignores a portion of shields and crits low HP targets.", "icon": "Icon_Item_Shadowflame"
	},
	"Stormsurge": {
		"price": 2900, "recipe": ["Blasting Wand", "Aether Wisp"], "combinePrice": 1050,
		"stats": {"ap": 95, "magicPenFlat": 10, "speed": 15}, "effects": {"onKill": "SQUALL_STRIKE"},
		"description": "Dealing 35% of a hero's HP triggers a delayed lightning strike.", "icon": "Icon_Item_Stormsurge"
	},
	"Archangel's Staff": {
		"price": 3000, "recipe": ["Tear of the Goddess", "Blasting Wand"], "combinePrice": 1000,
		"stats": {"ap": 80, "mana": 600, "cdr": 0.2}, "effects": {"onTick": "AWE_MANA_CONVERSION"},
		"description": "Grants AP based on Max Mana. Transforms at max stacks.", "icon": "Icon_Item_Archangels"
	},
	"Rod of Ages": {
		"price": 2600, "recipe": ["Blasting Wand", "Ruby Crystal"], "combinePrice": 750,
		"stats": {"ap": 60, "hp": 400, "mana": 400}, "effects": {"onMinutePassed": "ETERNITY_GROWTH"},
		"description": "Gains HP, Mana, and AP every minute (up to 10 stacks).", "icon": "Icon_Item_ROA"
	},

	# =========================================================================
	# ICONIC LEGENDARY ITEMS (Elite Crit & Utility Path)
	# =========================================================================
	"Infinity Edge": {
		"price": 3400, "recipe": ["B.F. Sword", "Pickaxe", "Cloak of Agility"], "combinePrice": 625,
		"stats": {"ad": 80, "crit": 0.33}, "effects": {"critPower": "IE_PASSIVE"},
		"isCapstone": True, "uniquePassive": "CRIT_AMP", "as_logic": "CRIT_LIMITER", "icon": "Icon_Item_IE"
	},
	"Essence Reaver": {
		"price": 3200, "recipe": ["Caulfield's Warhammer", "Cloak of Agility", "Sheen"], "combinePrice": 400,
		"stats": {"ad": 65, "cdr": 0.2, "crit": 0.33}, "effects": {"onHit": "SPELLBLADE_MANA"},
		"isCapstone": True, "uniquePassive": "SPELLBLADE", "as_logic": "CRIT_LIMITER", "icon": "Icon_Item_ER"
	},
	"Stormrazor": {
		"price": 3100, "recipe": ["B.F. Sword", "Cloak of Agility", "Kircheis Shard"], "combinePrice": 500,
		"stats": {"ad": 60, "crit": 0.33}, "effects": {"onHit": "GALE_STRIKE"},
		"isCapstone": True, "uniquePassive": "ENERGIZED", "as_logic": "CRIT_LIMITER", "icon": "Icon_Item_Stormrazor"
	},
	"Navori Flickerblade": {
		"price": 3000, "recipe": ["Recurve Bow", "Cloak of Agility"], "combinePrice": 1000,
		"stats": {"as": 0.5, "crit": 0.33}, "effects": {"onHit": "FLICKER_CD"},
		"uniquePassive": "FLICKER", "icon": "Icon_Item_Navori"
	},
	"Phantom Dancer": {
		"price": 2800, "recipe": ["Hearthbound Axe", "Cloak of Agility"], "combinePrice": 600,
		"stats": {"as": 0.5, "crit": 0.33}, "effects": {"onHit": "PD_GHOSTING"},
		"uniquePassive": "SPECTRAL_WALTZ", "icon": "Icon_Item_PD"
	},
	"Runaan's Hurricane": {
		"price": 2800, "recipe": ["Recurve Bow", "Cloak of Agility"], "combinePrice": 1000,
		"stats": {"as": 0.5, "crit": 0.33}, "effects": {"onHit": "RUNAANS_BOLTS"},
		"uniquePassive": "WIND_FURY", "icon": "Icon_Item_Runaans"
	},
	"Rapid Firecannon": {
		"price": 3000, "recipe": ["Kircheis Shard", "Cloak of Agility"], "combinePrice": 850,
		"stats": {"as": 0.5, "crit": 0.33}, "effects": {"onHit": "FIRE_RANGE"},
		"uniquePassive": "ENERGIZED", "icon": "Icon_Item_RFC"
	},
	"Lord Dominik's Regards": {
		"price": 3200, "recipe": ["Last Whisper", "Cloak of Agility"], "combinePrice": 1000,
		"stats": {"ad": 40, "armorPenPercent": 0.3, "crit": 0.33}, "effects": {"situationalDamage": "GIANT_SLAYER"},
		"uniquePassive": "LAST_WHISPER", "icon": "Icon_Item_LDR"
	},
	"Mortal Reminder": {
		"price": 3200, "recipe": ["Executioner's Calling", "Last Whisper", "Cloak of Agility"], "combinePrice": 750,
		"stats": {"ad": 40, "armorPenPercent": 0.3, "crit": 0.33}, "effects": {"onHit": ["TRUE_SIGHT_REVEAL", "GRIEVOUS_WOUNDS"]},
		"uniquePassive": "LAST_WHISPER", "icon": "Icon_Item_Mortal"
	},
	"Bloodthirster": {
		"price": 3400, "recipe": ["B.F. Sword", "Vampiric Scepter"], "combinePrice": 1200,
		"stats": {"ad": 80, "lifeSteal": 0.18, "crit": 0.33}, "effects": {"onTick": "OVERHEAL_SHIELD"},
		"uniquePassive": "ICHOR", "icon": "Icon_Item_BT"
	},
	"Immortal Shieldbow": {
		"price": 3000, "recipe": ["Pickaxe", "Cloak of Agility", "Vampiric Scepter"], "combinePrice": 500,
		"stats": {"ad": 50, "as": 0.2, "lifeSteal": 0.1, "crit": 0.33}, "effects": {"onTakeDamage": "LIFELINE_SHIELD"},
		"uniquePassive": "LIFELINE", "icon": "Icon_Item_Shieldbow"
	},
	"Galeforce": {
		"price": 3300, "recipe": ["B.F. Sword", "Zeal"], "combinePrice": 800,
		"stats": {"ad": 60, "as": 0.2}, "active_id": "GALEFORCE_DASH", "active_cd": 60,
		"icon": "Icon_Item_Galeforce"
	},
	"Phase Shifter": {
		"price": 3000, "recipe": ["Caulfield's Warhammer", "Dagger"], "combinePrice": 1000,
		"stats": {"ad": 45, "as": 0.3}, "active_id": "PHASE_SHIFT", "active_cd": 90,
		"icon": "Icon_Item_PhaseShifter"
	},
	"Mercurial Scimitar": {
		"price": 3000, "recipe": ["Quicksilver Sash", "Pickaxe"], "combinePrice": 600,
		"stats": {"ad": 50, "mr": 40}, "active_id": "CLEANSE_CC", "active_cd": 90,
		"icon": "Icon_Item_Scimitar"
	},
	"Guardian Angel": {
		"price": 3000, "recipe": ["Caulfield's Warhammer", "Chain Vest"], "combinePrice": 1100,
		"stats": {"ad": 45, "armor": 40}, "effects": {"onLethal": "RESURRECT"},
		"uniquePassive": "RESURRECTION", "icon": "Icon_Item_GA"
	},
	"Wit's End": {
		"price": 3100, "recipe": ["Recurve Bow", "Null-Magic Mantle", "Ruby Crystal"], "combinePrice": 1050,
		"stats": {"as": 0.55, "mr": 40, "hp": 200}, "effects": {"onHit": "WITS_END_STING"},
		"uniquePassive": "FRAY", "is_onhit_spawner": True, "icon": "Icon_Item_WitsEnd"
	},
	"Rageblade": {
		"price": 3200, "recipe": ["Recurve Bow", "Amplifying Tome", "Long Sword"], "combinePrice": 2150,
		"stats": {"as": 0.3, "ad": 25, "ap": 25}, "effects": {"onHit": "PHANTOM_HIT"},
		"isCapstone": True, "as_logic": "GUINSOO_UNLIMITER", "uniquePassive": "SEETHING_STRIKE", "icon": "Icon_Item_Rageblade"
	},
	"Blade of the Ruined King": {
		"price": 3300, "recipe": ["Vampiric Scepter", "Recurve Bow", "Pickaxe"], "combinePrice": 800,
		"stats": {"ad": 40, "as": 0.55, "lifeSteal": 0.1, "hp": 200}, "effects": {"onHit": "BORK_SHRED"},
		"uniquePassive": "RUINED_KING", "is_onhit_spawner": True, "icon": "Icon_Item_Bork"
	},
	"Terminus": {
		"price": 3200, "recipe": ["Recurve Bow", "Pickaxe", "Cloth Armor"], "combinePrice": 1100,
		"stats": {"ad": 35, "as": 0.55, "hp": 200}, "effects": {"onHit": "JUXTAPOSITION"},
		"uniquePassive": "TERMINUS", "is_onhit_spawner": True, "icon": "Icon_Item_Terminus"
	},
	"Kraken Slayer": {
		"price": 3000, "recipe": ["Recurve Bow", "B.F. Sword"], "combinePrice": 1000,
		"stats": {"ad": 40, "as": 0.55, "hp": 200}, "effects": {"onHit": "BRING_IT_DOWN"},
		"uniquePassive": "KRAKEN", "is_onhit_spawner": True, "icon": "Icon_Item_Kraken"
	},

	# =========================================================================
	# SUPPORT ITEMS
	# =========================================================================
	"Moonstone Renewer": {
		"price": 2500, "recipe": ["Faerie Charm", "Ruby Crystal"], "combinePrice": 1950,
		"stats": {"hp": 250, "manaRegen": 1.0, "healAmp": 0.20}, "effects": {"onTick": "STARLIT_GRACE"},
		"icon": "Icon_Item_Moonstone"
	},
	"Redemption": {
		"price": 2300, "recipe": ["Ruby Crystal", "Faerie Charm"], "combinePrice": 1650,
		"stats": {"hp": 250, "manaRegen": 1.0, "healAmp": 0.15}, 
		"active_id": "INTERVENTION", "active_cd": 120, "icon": "Icon_Item_Redemption"
	},
	"Locket of Iron Solari": {
		"price": 2300, "recipe": ["Null-Magic Mantle", "Cloth Armor", "Ruby Crystal"], "combinePrice": 1100,
		"stats": {"hp": 200, "armor": 30, "mr": 30}, 
		"active_id": "DEVOTION", "active_cd": 90, "icon": "Icon_Item_Locket"
	},
	"Staff of Flowing Waters": {
		"price": 2300, "recipe": ["Faerie Charm", "Amplifying Tome"], "combinePrice": 1650,
		"stats": {"ap": 40, "manaRegen": 1.0, "healAmp": 0.15}, 
		"active_id": "TOTAL_CLEANSE", "active_cd": 120, "icon": "Icon_Item_StaffFlowing"
	},
	"Horizon Focus": {
		"price": 2400, "recipe": ["Blasting Wand", "Ruby Crystal"], "combinePrice": 1150,
		"stats": {"ap": 70, "hp": 200, "cdr": 0.15}, "effects": {"onAbilityHit": "REVEAL_SNIPE"},
		"active_id": "TACTICAL_BLINK", "active_cd": 240, "icon": "Icon_Item_Horizon"
	},
	"Shurelya's Battlesong": {
		"price": 2200, "recipe": ["Faerie Charm", "Ruby Crystal"], "combinePrice": 1550,
		"stats": {"hp": 300, "manaRegen": 1.0, "cdr": 0.15}, 
		"active_id": "BATTLE_CRY", "active_cd": 90, "icon": "Icon_Item_Shurelyas"
	},

	# =========================================================================
	# SUPPORT EVOLUTION STARTERS (400G - Role Locked)
	# ===================== Tier 1 =====================
	"Relic Shield": {
		"price": 400, "stats": {"hp": 100, "hpRegen": 0.5}, "effects": {"onTick": "SUPPORT_GOLD"},
		"role_lock": "support", "evolution_tier": 1, "next_tier": "Targon's Buckler", "icon": "Icon_Item_Relic1"
	},
	"Spellthief's Edge": {
		"price": 400, "stats": {"ap": 10, "manaRegen": 0.5}, "effects": {"onTick": "SUPPORT_GOLD"},
		"role_lock": "support", "evolution_tier": 1, "next_tier": "Frostfang", "icon": "Icon_Item_Spellthief1"
	},
	"Spectral Sickle": {
		"price": 400, "stats": {"ad": 8, "manaRegen": 0.5}, "effects": {"onTick": "SUPPORT_GOLD"},
		"role_lock": "support", "evolution_tier": 1, "next_tier": "Harrowing Crescent", "icon": "Icon_Item_Sickle1"
	},
	# ===================== Tier 2 (500G Quest) =====================
	"Targon's Buckler": {
		"price": 0, "stats": {"hp": 200, "hpRegen": 1.25}, "effects": {"onTick": "SUPPORT_GOLD"},
		"evolution_tier": 2, "icon": "Icon_Item_Relic2"
	},
	"Frostfang": {
		"price": 0, "stats": {"ap": 25, "manaRegen": 1.25}, "effects": {"onTick": "SUPPORT_GOLD"},
		"evolution_tier": 2, "icon": "Icon_Item_Spellthief2"
	},
	"Harrowing Crescent": {
		"price": 0, "stats": {"ad": 25, "manaRegen": 1.25}, "effects": {"onTick": "SUPPORT_GOLD"},
		"evolution_tier": 2, "icon": "Icon_Item_Sickle2"
	},
	# ===================== Tier 3 (1000G Quest - Choice) =====================
	"Celestial Opposition": {
		"price": 0, "stats": {"hp": 400, "hpRegen": 2.5, "armor": 30, "mr": 30},
		"quest_requirement": 1000, "evolution_tier": 3, "icon": "Icon_Item_Celestial",
		"effects": {"onTakeDamage": "CELESTIAL_SHIELD"}
	},
	"Zaz'Zak's Realmspike": {
		"price": 0, "stats": {"ap": 60, "manaRegen": 2.5, "hp": 200},
		"quest_requirement": 1000, "evolution_tier": 3, "icon": "Icon_Item_Zazzak",
		"effects": {"onAbilityHit": "REALMSPIKE_SHRED"}
	},
	"Solstice Sleigh": {
		"price": 0, "stats": {"hp": 300, "manaRegen": 2.5, "cdr": 0.20},
		"quest_requirement": 1000, "evolution_tier": 3, "icon": "Icon_Item_Solstice",
		"effects": {"onCC": "SOLSTICE_SLEIGH"}
	},
	"Bloodsong": {
		"price": 0, "stats": {"ad": 40, "manaRegen": 2.5, "hp": 200, "as": 0.1},
		"quest_requirement": 1000, "evolution_tier": 3, "icon": "Icon_Item_Bloodsong",
		"effects": {"onHit": "BLOODSONG_EXPOSE"}
	},

	# =========================================================================
	# JUNGLE ITEMS
	# =========================================================================
	"Hunter's Resolve": {
		"price": 450, "stats": {"hp": 50}, "isUnsellable": True,
		"effects": {"onMonsterCombat": "JUNGLE_HUNTER"},
		"icon": "Icon_Item_JungleStarter"
	},
	"Slayer's Resolve": {
		"price": 450, "stats": {"ad": 10, "omnivamp": 0.08}, "effects": {"onTick": ["JUNGLE_HUNTER", "STALK"]},
		"icon": "Icon_Item_Slayers_Resolve", "description": "Hunter: +40% dmg to monsters. Stalk: Next hit deals bonus dmg after 5s out of combat."
	},
	"Arcane Resolve": {
		"price": 450, "stats": {"ap": 20, "manaRegen": 2.5}, "effects": {"onTick": "JUNGLE_HUNTER", "onAbilityHit": "SOUL_HARVEST"},
		"icon": "Icon_Item_Arcane_Resolve", "description": "Hunter: +40% dmg to monsters. Harvest: Gain +1 AP per large monster kill."
	},
	"Goliath's Resolve": {
		"price": 450, "stats": {"hp": 150, "hpRegen": 3.0}, "effects": {"onTick": ["JUNGLE_HUNTER", "COLOSSAL_AURA"]},
		"icon": "Icon_Item_Goliaths_Resolve", "description": "Hunter: +40% dmg to monsters. Aura: Burns nearby monsters for magic damage."
	},

	# =========================================================================
	# TRINKETS (SLOT 7)
	# =========================================================================
	"Warding Totem": {
		"price": 0, "isTrinket": True, "icon": "Icon_Trinket_Yellow",
		"active_id": "PLACE_WARD", "active_cd": 180,
		"description": "Places a Stealth Ward that lasts 90s."
	},
	"Oracle Lens": {
		"price": 0, "isTrinket": True, "icon": "Icon_Trinket_Red",
		"active_id": "ORACLE_SWEEP", "active_cd": 90,
		"description": "Sweeps for 10s, revealing nearby enemy wards."
	},
	"Farsight Alteration": {
		"price": 0, "isTrinket": True, "icon": "Icon_Trinket_Blue",
		"active_id": "FARSIGHT_WARD", "active_cd": 120,
		"description": "Places a long-range visible ward at level 9+."
	},

	# =========================================================================
	# BOOTS (ONE PAIR LIMIT)
	# =========================================================================
	"Boots of Speed": {
		"price": 300, "stats": {"speed": 25}, "isBoots": True, 
		"icon": "Icon_Item_BootsOfSpeed"
	},
	"Plated Steelcaps": {
		"price": 1100, "recipe": ["Boots of Speed", "Cloth Armor"], "combinePrice": 500,
		"stats": {"speed": 45, "armor": 20}, "isBoots": True,
		"effects": {"onTakeDamage": "AA_REDUCTION"},
		"icon": "Icon_Item_PlatedSteelcaps"
	},
	"Mercury's Treads": {
		"price": 1100, "recipe": ["Boots of Speed", "Null-Magic Mantle"], "combinePrice": 350,
		"stats": {"speed": 45, "mr": 25, "tenacity": 0.3}, "isBoots": True,
		"icon": "Icon_Item_MercurysTreads"
	},
	"Sorcerer's Shoes": {
		"price": 1100, "recipe": ["Boots of Speed"], "combinePrice": 800,
		"stats": {"speed": 45, "magicPenFlat": 18}, "isBoots": True,
		"icon": "Icon_Item_Sorcs"
	},
	"Berserker's Greaves": {
		"price": 1100, "recipe": ["Boots of Speed", "Dagger"], "combinePrice": 500,
		"stats": {"speed": 45, "as": 0.35}, "isBoots": True,
		"icon": "Icon_Item_Berserkers"
	},
	"Ionian Boots of Lucidity": {
		"price": 950, "recipe": ["Boots of Speed"], "combinePrice": 650,
		"stats": {"speed": 45, "cdr": 0.15}, "isBoots": True,
		"icon": "Icon_Item_Lucidity"
	},
	"Boots of Swiftness": {
		"price": 900, "recipe": ["Boots of Speed"], "combinePrice": 600,
		"stats": {"speed": 60, "slowResist": 0.25}, "isBoots": True,
		"icon": "Icon_Item_Swiftness"
	},
	"Mobility Boots": {
		"price": 1000, "recipe": ["Boots of Speed"], "combinePrice": 700,
		"stats": {"speed": 25}, "isBoots": True, "special": "MOBILITY_PASSIVE",
		"icon": "Icon_Item_MobiBoots"
	}
}

def get_item_price(item_name, inventory=[]):
	"""Phase 61: Recursive pricing. Calculates price by subtracting value of owned components."""
	item = ITEM_REGISTRY.get(item_name)
	if not item: return 0
	
	total_cost = item["price"]
	if "recipe" not in item:
		return total_cost
		
	def get_component_reduction(recipe, current_inv):
		reduction = 0
		for component in recipe:
			if component in current_inv:
				reduction += ITEM_REGISTRY[component]["price"]
				current_inv.remove(component)
			else:
				comp_data = ITEM_REGISTRY.get(component)
				if comp_data and "recipe" in comp_data:
					reduction += get_component_reduction(comp_data["recipe"], current_inv)
		return reduction

	temp_inv = inventory[:]
	owned_value = get_component_reduction(item["recipe"], temp_inv)
	combine_floor = item.get("combinePrice", 0)
	return max(combine_floor, total_cost - owned_value)

def is_component_of(component_name, target_name):
	"""Phase 62: Recursively checks if item A is a component of item B."""
	target = ITEM_REGISTRY.get(target_name)
	if not target or "recipe" not in target: return False
	if component_name in target["recipe"]: return True
	for sub in target["recipe"]:
		if is_component_of(component_name, sub): return True
	return False
