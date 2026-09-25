# MonsterRegistry.py
# Phase 101: Centralized data-source for Jungle Camps and Epic Bosses.

MONSTER_REGISTRY = {
	"BLUE_BUFF": {
		"name": "Crest of Insight",
		"hp": 2400, "ad": 80, "armor": 20, "mr": 20,
		"gold": 100, "xp": 180,
		"category": "LARGE", "buff": "CREST_INSIGHT", "icon": "Icon_Monster_Blue"
	},
	"RED_BUFF": {
		"name": "Crest of Cinders",
		"hp": 2400, "ad": 80, "armor": 20, "mr": 20,
		"gold": 100, "xp": 180,
		"category": "LARGE", "buff": "CREST_FIRE", "icon": "Icon_Monster_Red"
	},
	"GROMP": {
		"name": "Gromp",
		"hp": 2200, "ad": 100, "armor": 0, "mr": 20,
		"gold": 80, "xp": 135,
		"category": "LARGE", "icon": "Icon_Monster_Gromp"
	},
	"GREATER_WOLF": {
		"name": "Greater Murk Wolf",
		"hp": 1600, "ad": 45, "armor": 20, "mr": 20,
		"gold": 55, "xp": 100,
		"category": "LARGE", "icon": "Icon_Monster_Wolf_Big"
	},
	"GREATER_KRUG": {
		"name": "Ancient Krug",
		"hp": 1200, "ad": 60, "armor": 40, "mr": 10,
		"gold": 70, "xp": 120,
		"category": "LARGE", "icon": "Icon_Monster_Krug_Big"
	},
	"GREATER_RAPTOR": {
		"name": "Crimson Raptor",
		"hp": 1100, "ad": 25, "armor": 30, "mr": 10,
		"gold": 45, "xp": 90,
		"category": "LARGE", "icon": "Icon_Monster_Raptor_Big"
	},
	"SCUTTLE": {
		"name": "Rift Scuttler",
		"hp": 1200, "ad": 0, "armor": 60, "mr": 60,
		"gold": 60, "xp": 115,
		"category": "SMALL", "icon": "Icon_Monster_Scuttle"
	},
	"SMALL_MINION": {
		"name": "Griphen", # Generic small monster name
		"hp": 500, "ad": 15, "armor": 10, "mr": 0,
		"gold": 10, "xp": 25,
		"category": "SMALL"
	},
	"DRAGON": {
		"name": "The Dragon",
		"hp": 5500, "ad": 150, "armor": 50, "mr": 50,
		"gold": 150, "xp": 300, "global_gold": 100,
		"category": "EPIC", "icon": "Icon_Monster_Dragon"
	},
	"BARON": {
		"name": "Baron Nashor",
		"hp": 12600, "ad": 350, "armor": 120, "mr": 120,
		"gold": 300, "xp": 600, "global_gold": 300,
		"category": "EPIC", "icon": "Icon_Monster_Baron"
	}
}

def get_scaled_stats(monster_id, minutes):
	"""Returns stats with periodic growth (LoL style: +5% HP/min, +3% AD/min)."""
	base = MONSTER_REGISTRY.get(monster_id)
	if not base: return None
	
	factor = min(20, int(minutes)) # Cap scaling at 20 mins
	hp_mult = 1.0 + (factor * 0.05)
	ad_mult = 1.0 + (factor * 0.03)
	
	scaled = base.copy()
	scaled["hp"] = int(base["hp"] * hp_mult)
	scaled["ad"] = int(base["ad"] * ad_mult)
	return scaled
