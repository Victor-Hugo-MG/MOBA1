ANIMATION_REGISTRY = {
	# ===================== GLOBAL DEFAULTS =====================
	"GLOBAL_DEFAULT": {
		"idle":   "p-idle",
		"walk":   "p-walk",
		"run":    "p-run",
		"attack": "p-attack",
		"skill_q": "p-ability",
		"skill_w": "p-ability",
		"skill_e": "p-ability",
		"skill_r": "p-ultimate",
		"passive": "p-passive",
		"death":  "p-death",
		"recall": "p-recall"
	},

	# ===================== HERO SPECIFIC MAPS =====================
	# Standardized Spec: [HeroName]_[Action]
	"Warrior": { "idle": "Warrior_Idle", "run": "Warrior_Run", "attack": "Warrior_Attack", "skill_q": "Warrior_Q", "skill_w": "Warrior_W", "skill_e": "Warrior_E", "skill_r": "Warrior_R", "death": "Warrior_Death" },
	"Techno Knight": { "idle": "Techno_Idle", "run": "Techno_Run", "attack": "Techno_Attack", "skill_q": "Techno_Q", "skill_w": "Techno_W", "skill_e": "Techno_E", "skill_r": "Techno_R", "death": "Techno_Death" },
	"Ironclad": { "idle": "Ironclad_Idle", "run": "Ironclad_Run", "attack": "Ironclad_Attack", "skill_q": "Ironclad_Q", "skill_w": "Ironclad_W", "skill_e": "Ironclad_E", "skill_r": "Ironclad_R", "death": "Ironclad_Death" },
	"Shadow": { "idle": "Shadow_Idle", "run": "Shadow_Run", "attack": "Shadow_Attack", "skill_q": "Shadow_Q", "skill_w": "Shadow_W", "skill_e": "Shadow_E", "skill_r": "Shadow_R", "death": "Shadow_Death" },
	"Frost Nova": { "idle": "Frost_Idle", "run": "Frost_Run", "attack": "Frost_Attack", "skill_q": "Frost_Q", "skill_w": "Frost_W", "skill_e": "Frost_E", "skill_r": "Frost_R", "death": "Frost_Death" },
	"Pyre": { "idle": "Pyre_Idle", "run": "Pyre_Run", "attack": "Pyre_Attack", "skill_q": "Pyre_Q", "skill_w": "Pyre_W", "skill_e": "Pyre_E", "skill_r": "Pyre_R", "death": "Pyre_Death" },
	"StormWeaver": { "idle": "Storm_Idle", "run": "Storm_Run", "attack": "Storm_Attack", "skill_q": "Storm_Q", "skill_w": "Storm_W", "skill_e": "Storm_E", "skill_r": "Storm_R", "death": "Storm_Death" },
	"GraveyardKing": { "idle": "King_Idle", "run": "King_Run", "attack": "King_Attack", "skill_q": "King_Q", "skill_w": "King_W", "skill_e": "King_E", "skill_r": "King_R", "death": "King_Death" },
	"WindWalker": { "idle": "Walker_Idle", "run": "Walker_Run", "attack": "Walker_Attack", "skill_q": "Walker_Q", "skill_w": "Walker_W", "skill_e": "Walker_E", "skill_r": "Walker_R", "death": "Walker_Death" },
	"Slayer": { "idle": "Slayer_Idle", "run": "Slayer_Run", "attack": "Slayer_Attack", "skill_q": "Slayer_Q", "skill_w": "Slayer_W", "skill_e": "Slayer_E", "skill_r": "Slayer_R", "death": "Slayer_Death" },
	"Guardian": { "idle": "Guardian_Idle", "run": "Guardian_Run", "attack": "Guardian_Attack", "skill_q": "Guardian_Q", "skill_w": "Guardian_W", "skill_e": "Guardian_E", "skill_r": "Guardian_R", "death": "Guardian_Death" },
	"Berserker": { "idle": "Berserker_Idle", "run": "Berserker_Run", "attack": "Berserker_Attack", "skill_q": "Berserker_Q", "skill_w": "Berserker_W", "skill_e": "Berserker_E", "skill_r": "Berserker_R", "death": "Berserker_Death" },
	"ShadowStalker": { "idle": "Stalker_Idle", "run": "Stalker_Run", "attack": "Stalker_Attack", "skill_q": "Stalker_Q", "skill_w": "Stalker_W", "skill_e": "Stalker_E", "skill_r": "Stalker_R", "death": "Stalker_Death" },
	"ArcaneSlinger": { "idle": "Slinger_Idle", "run": "Slinger_Run", "attack": "Slinger_Attack", "skill_q": "Slinger_Q", "skill_w": "Slinger_W", "skill_e": "Slinger_E", "skill_r": "Slinger_R", "death": "Slinger_Death" },
	"WindGuardian": { "idle": "WindG_Idle", "run": "WindG_Run", "attack": "WindG_Attack", "skill_q": "WindG_Q", "skill_w": "WindG_W", "skill_e": "WindG_E", "skill_r": "WindG_R", "death": "WindG_Death" },
	"DarkinApostle": { "idle": "Darkin_Idle", "run": "Darkin_Run", "attack": "Darkin_Attack", "skill_q": "Darkin_Q", "skill_w": "Darkin_W", "skill_e": "Darkin_E", "skill_r": "Darkin_R", "death": "Darkin_Death" },
	"NatureGuardian": { "idle": "Nature_Idle", "run": "Nature_Run", "attack": "Nature_Attack", "skill_q": "Nature_Q", "skill_w": "Nature_W", "skill_e": "Nature_E", "skill_r": "Nature_R", "death": "Nature_Death" },
	"SpiritForm": { "idle": "Spirit_Idle", "run": "Spirit_Run", "attack": "Spirit_Attack", "skill_q": "Spirit_Q", "skill_w": "Spirit_W", "skill_e": "Spirit_E", "skill_r": "Spirit_R", "death": "Spirit_Death" },
	"FlashFencer": { "idle": "Fencer_Idle", "run": "Fencer_Run", "attack": "Fencer_Attack", "skill_q": "Fencer_Q", "skill_w": "Fencer_W", "skill_e": "Fencer_E", "skill_r": "Fencer_R", "death": "Fencer_Death" },
	"Nighthawk": { "idle": "Hawk_Idle", "run": "Hawk_Run", "attack": "Hawk_Attack", "skill_q": "Hawk_Q", "skill_w": "Hawk_W", "skill_e": "Hawk_E", "skill_r": "Hawk_R", "death": "Hawk_Death" },
	"Embermage": { "idle": "Ember_Idle", "run": "Ember_Run", "attack": "Ember_Attack", "skill_q": "Ember_Q", "skill_w": "Ember_W", "skill_e": "Ember_E", "skill_r": "Ember_R", "death": "Ember_Death" },
	"Thornfang": { "idle": "Thorn_Idle", "run": "Thorn_Run", "attack": "Thorn_Attack", "skill_q": "Thorn_Q", "skill_w": "Thorn_W", "skill_e": "Thorn_E", "skill_r": "Thorn_R", "death": "Thorn_Death" },
	"Tidecaller": { "idle": "Tide_Idle", "run": "Tide_Run", "attack": "Tide_Attack", "skill_q": "Tide_Q", "skill_w": "Tide_W", "skill_e": "Tide_E", "skill_r": "Tide_R", "death": "Tide_Death" },

	# ===================== MINIONS & MONSTERS =====================
	"Minion_Melee": { "walk": "Walk_Loop", "attack": "Attack_Slash", "death": "Death" },
	"Minion_Ranged": { "walk": "Walk_Loop", "attack": "Attack_Shoot", "death": "Death" }
}

def get_anim(actor_name, anim_key, fallback="GLOBAL_DEFAULT"):
	"""
	Retrieves the clip name for a specific actor and action.
	Priority: Actor Map -> Global Default -> Hardcoded Fallback.
	"""
	# 1. Check for specific actor map
	actor_map = ANIMATION_REGISTRY.get(actor_name)
	if actor_map and anim_key in actor_map:
		return actor_map[anim_key]
	
	# 2. Fallback to Global Default
	default_map = ANIMATION_REGISTRY.get(fallback, ANIMATION_REGISTRY["GLOBAL_DEFAULT"])
	return default_map.get(anim_key, "p-idle")
