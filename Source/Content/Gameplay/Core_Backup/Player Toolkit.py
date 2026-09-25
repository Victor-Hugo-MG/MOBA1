import cave
import cave.event
import cave.math
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Data import HeroRegistry
from Data import ItemRegistry
from Data import RuneRegistry
from Data import SkinRegistry
from Data import AnimationRegistry
from UI import MobaUI
from UI import MobaUIFX
from Core import MobaStates
from Core import MobaItems
from Core import MobaCommon
from Core.MobaPassives import MobaPassiveManager
import math
import random
import json


# ──────────────────────────────────────────────
# SimpleFSM: Lightweight Python FSM to replace non-existent cave.FSM
# Mirrors the cave.FSM interface: setState(), run()
# ──────────────────────────────────────────────
class SimpleFSM:
	"""Lightweight state machine that drives MobaStates."""
	def __init__(self, initial_state):
		self._state = initial_state
		self._controller = None

	def setState(self, new_state):
		self._state = new_state
		if self._controller and hasattr(self._state, 'start'):
			self._state.start(self._controller)

	def run(self):
		if self._state:
			next_state = self._state.run()
			if next_state is not None and next_state is not self._state:
				self._state = next_state
				if self._controller and hasattr(self._state, 'start'):
					self._state.start(self._controller)

	def bind(self, controller):
		"""Bind controller reference and start the initial state."""
		self._controller = controller
		if self._state and hasattr(self._state, 'start'):
			self._state.start(controller)



class LevelingManager:
	"""Phase 18: Decoupled XP and Gold logic."""
	def __init__(self, pc):
		self.pc = pc
		self.level = 1
		self.exp = 0
		self.gold = 500
		self.kills = 0
		self.deaths = 0
		self.assists = 0
		self.cs = 0
		self.skillPoints = 1
		self.skillLevels = {"Q": 0, "W": 0, "E": 0, "R": 0}
		self.expToNext = 280

	def add_exp(self, amount):
		self.exp += amount
		while self.exp >= self.expToNext and self.level < 18:
			self.level_up()

	def level_up(self):
		self.exp -= self.expToNext
		self.level += 1
		self.skillPoints += 1
		self.expToNext = int(self.expToNext * 1.15) + 100
		self.pc.recalculate_stats() # Force update on level up
		
		# ── Wave 35/37: Level Up Feedback ───────────────────────────
		from Core import MobaCommon
		from UI import MobaUI
		MobaCommon.play_sfx(self.pc.entity, MobaCommon.Templates.SFX_ANNOUNCEMENT)
		MobaCommon.spawn_vfx(self.pc.entity.getScene(), MobaCommon.Templates.VFX_LEVEL_UP, self.pc.entity.getTransform().worldPosition)
		
		f_color = cave.Vector4(1.0, 0.9, 0.2, 1.0) # Golden-Yellow
		MobaUI.spawn_fct(self.pc.entity.getScene(), self.pc.entity.getTransform().worldPosition, "LEVEL UP!", f_color)

class InventoryManager:
	"""Phase 18: Decoupled Item and Shop logic."""
	def __init__(self, pc):
		self.pc = pc
		self.items = [] # Max 6 items
		self.trinket = "Warding Totem" # Phase 65: Dedicated Trinket Slot
		self.isShopOpen = False
		self.lastTimeShopOpened = 0
		self.active_cooldowns = {} # {item_id: timestamp_ready} (Systemic)
		self.slot_cooldowns = [0.0] * 7 # [slot0...slot5, trinket] (HUD visualization)

	def update_support_quest(self):
		"""Phase 100: Check shared gold milestones and evolve support items."""
		now_gold = getattr(self.pc, "quest_gold", 0)
		for i, item_id in enumerate(self.items):
			data = ItemRegistry.ITEM_REGISTRY.get(item_id)
			if not data: continue
			
			tier = data.get("evolution_tier")
			if not tier: continue
			
			# Evolution Pick Logic: Auto-evolve only to Tier 2 (500G)
			# Tier 3 (1000G) is now a choice in the Shop.
			if tier == 1 and now_gold >= 500:
				# Derive next tier from the item's evolution chain
				next_tier = data.get("evolves_into", item_id + "_T2")
				self.items[i] = next_tier
				self.pc.recalculate_stats()
				MobaUI.broadcast_event(f"Support Item EVOLVED to {next_tier}!")
				MobaCommon.play_sfx(self.pc.entity, "SFX_Support_Upgrade")
				MobaCommon.spawn_vfx(self.pc.entity.getScene(), "VFX_Upgrade_Sparkle", self.pc.transf.worldPosition)
				return

	def buy_item(self, item_id):
		"""Phase 61/63: Recursive shop purchase & evolution logic."""
		if item_id in self.items or item_id == self.trinket: return False # Already owned
		item = ItemRegistry.ITEM_REGISTRY.get(item_id)
		if not item: return False
		
		# Role Lock Check
		role_lock = item.get("role_lock")
		if role_lock:
			my_role = self.pc.heroData.get("role", "warrior")
			if my_role.lower() != role_lock.lower():
				MobaUI.broadcast_event(f"This item is only for {role_lock} heroes!")
				return False
		
		# Quest Requirement Check (for Tier 3 Support Choice)
		quest_req = item.get("quest_requirement", 0)
		if quest_req > 0:
			now_gold = getattr(self.pc, "quest_gold", 0)
			if now_gold < quest_req:
				MobaUI.broadcast_event(f"Quest Gold too low! Need {quest_req}G.")
				return False
			
			# Prerequisite Check: Must have a Tier 2 Support item to swap
			has_tier2 = False
			for i, owned_id in enumerate(self.items):
				owned_data = ItemRegistry.ITEM_REGISTRY.get(owned_id)
				if owned_data and owned_data.get("evolution_tier") == 2:
					# Match found! Swap them.
					self.items[i] = item_id
					self.pc.recalculate_stats()
					MobaUI.broadcast_event(f"Path chosen: {item_id}!")
					MobaCommon.play_sfx(self.pc.entity, "SFX_Support_Ascend")
					return True
			
			MobaUI.broadcast_event("You need a Tier 2 Support item to upgrade!")
			return False
		
		# Phase 65: Trinket Swap (Free and separate slot)
		if item.get("isTrinket"):
			self.trinket = item_id
			self.pc.recalculate_stats()
			return True

		# Phase 66: Boots Restriction (One pair only)
		if item.get("isBoots"):
			existing_boot = None
			for owned in self.items:
				owned_data = ItemRegistry.ITEM_REGISTRY.get(owned)
				if owned_data and owned_data.get("isBoots"):
					existing_boot = owned
					break
			
			if existing_boot:
				# Check if this is an upgrade (is existing boot in recipe?)
				recipe = item.get("recipe", [])
				if existing_boot not in recipe:
					# Not an upgrade, and already has boots. Block.
					MobaUI.broadcast_event("You can only carry one pair of boots!")
					return False
		
		# Phase 100: Capstone Restriction (Unique Category Choice)
		if item.get("isCapstone"):
			for owned in self.items:
				owned_data = ItemRegistry.ITEM_REGISTRY.get(owned)
				if owned_data and owned_data.get("isCapstone"):
					MobaUI.broadcast_event("You can only carry one Capstone item!")
					return False

		# Phase 63: Automatic Evolution Swap
		if item.get("isEvolution"):
			return self.evolve_jungle_item(item_id.split("'")[0].upper()) # Guessing path from name
		
		price = ItemRegistry.get_item_price(item_id, self.items)
		
		# Inventory Logic: Check if we have space after consuming components
		def simulate_consumption(recipe, current_items):
			for comp in recipe:
				if comp in current_items:
					current_items.remove(comp)
				else:
					comp_data = ItemRegistry.ITEM_REGISTRY.get(comp)
					if comp_data and "recipe" in comp_data:
						simulate_consumption(comp_data["recipe"], current_items)
		
		temp_items = self.items[:]
		if "recipe" in item:
			simulate_consumption(item["recipe"], temp_items)
			
		if self.pc.leveling.gold >= price and len(temp_items) < 6:
			# Actual Consumption
			self.items = temp_items
			self.pc.leveling.gold -= price
			self.items.append(item_id)
			self.pc.recalculate_stats()
			return True
		return False

	def sell_item(self, slot_index):
		"""Phase 61: Sell item for 70% refund."""
		if 0 <= slot_index < len(self.items):
			item_id = self.items[slot_index]
			item = ItemRegistry.ITEM_REGISTRY.get(item_id)
			if item and (item.get("isUnsellable") or item.get("isTrinket")):
				return False # Phase 63/65: Soul-bound or Trinket
			
			self.items.pop(slot_index)
			if item:
				refund = int(item["price"] * 0.7)
				self.pc.leveling.gold += refund
				self.pc.recalculate_stats()
				return True
		return False

	def evolve_jungle_item(self, path="AD"):
		"""Phase 63: Evolves the jungle starter into a scaling legendary."""
		starter = "Hunter's Resolve"
		if starter not in self.items: return False
		
		# Swapping item in place
		idx = self.items.index(starter)
		evolution = "Slayer's Resolve" # Default AD
		
		path = path.upper()
		if "AP" in path or "ARCANE" in path: evolution = "Arcane Resolve"
		elif "TANK" in path or "GOLIATH" in path: evolution = "Goliath's Resolve"
		elif "AD" in path or "SLAYER" in path: evolution = "Slayer's Resolve"
		
		self.items[idx] = evolution
		self.pc.recalculate_stats()
		MobaUI.broadcast_event(f"{self.pc.heroName} has evolved their Resolve!")
		return True
		
	def trigger_active(self, slot_index):
		"""Phase 76: Manual execution of item actives with CD checks."""
		item_id = None
		is_trinket = slot_index == 6
		
		# 1. Resolve Item ID
		if is_trinket:
			item_id = self.trinket
		elif 0 <= slot_index < len(self.items):
			item_id = self.items[slot_index]
			
		if not item_id: return False
		
		# 2. Check Data for Active component
		data = ItemRegistry.ITEM_REGISTRY.get(item_id)
		active_id = data.get("active_id") if data else None
		if not active_id: return False
		
		# 3. Cooldown Check
		now = self.pc.entity.getScene().getElapsedSceneTime()
		if self.active_cooldowns.get(item_id, 0) > now:
			return False
			
		# 4. Execute Logic
		from Core import MobaItems
		MobaItems.ItemEffectManager.process_active(self.pc, active_id)
		
		# 5. Set Cooldowns
		cd_val = data.get("active_cd", 30)
		self.active_cooldowns[item_id] = now + cd_val
		self.slot_cooldowns[slot_index] = cd_val # For HUD display pulse
		
		return True

class PlayerController(cave.Component):
	damageCooldownTime = 1.0
	INPUT_BUFFER_TIME = 0.2 # Phase 73: Standard input buffer window
	
	# Property bridges — route pc.level/skillPoints/skillLevels to LevelingManager
	@property
	def level(self):
		return self.leveling.level if hasattr(self, 'leveling') else 1

	@property
	def skillPoints(self):
		return self.leveling.skillPoints if hasattr(self, 'leveling') else 0

	@skillPoints.setter
	def skillPoints(self, val):
		if hasattr(self, 'leveling'):
			self.leveling.skillPoints = val

	@property
	def skillLevels(self):
		return self.leveling.skillLevels if hasattr(self, 'leveling') else {"Q": 0, "W": 0, "E": 0, "R": 0}

	@skillLevels.setter
	def skillLevels(self, val):
		if hasattr(self, 'leveling'):
			self.leveling.skillLevels = val

	def on_crit_landed(self):
		"""Phase 100: Flickerblade / Navori logic."""
		if hasattr(self, "inventory_mgr") and MobaItems.ItemEffectManager.has_item_effect(self, "onHit", "FLICKER_CD"):
			for key in ["Q", "W", "E"]:
				if key in self.cooldowns:
					cd = self.cooldowns[key]
					# Reduce remaining time by 15%
					rem = cd.get()  # Cave API: SceneTimer.get()
					if rem > 0 and rem < 100: # Not a 'Reset' sentinel (usually 999)
						cd.set(rem * 0.85)  # Cave API: SceneTimer.set()

	def start(self, scene: cave.Scene):
		# Phase 38: Initialize Match Statistics
		from Core import MobaCommon
		MobaCommon.MatchStatsManager.init(scene)
		MobaCommon.is_match_over = False

		# Phase 23: Ensure GameTick lead with a clean state if this is the first actor
		if MobaCommon.GameTick._current_tick == 0:
			MobaCommon.GameTick.reset()
			
		# Core Components
		self.transf = self.entity.getTransform()
		self.character : cave.CharacterComponent = self.entity.get("Character")
		self.eff_comp = self.entity.getPy("EffectComponent") # Cached for performance
		self.mesh = self.entity.getChild("Mesh")
		
		# Safety: Ensure mesh and animator are valid
		self.animator = None
		if self.mesh:
			try: self.animator = self.mesh.get("Animation")
			except: pass
		
		# To control the Health:
		self.lifeBar = self.entity.getChild("Health Bar", False).getChild("Bar")
		self.lifeBarUI : cave.UIElementComponent = self.lifeBar.get("UIElement")
		
		# Phase 35: Health Juice / Shadow Bar
		self.shadowBar = self.entity.getChild("Health Bar", False).getChild("ShadowBar")
		self.shadowBarUI = self.shadowBar.get("UIElement") if self.shadowBar else None
		
		self.passiveGoldTimer = 1.0
		self.quest_gold = 0 # Support quest tracking
		
		self.passiveGoldTimer = 1.0
		self.quest_gold = 0
		self.wardCharges = 1
		self.wardMaxCharges = 1
		self.wardChargeTimer = cave.SceneTimer(0)
		self.lastCombatTime = -10.0 # Ready at start
		self.isCelestialActive = False
		self.vento_aura = 0 # Phase 100: For Vento's auto-aura
		self.last_kill_is_execute = False # Phase 100: For Dredge's gold share
		
		# Phase 101: Mid-lane Expansion States
		self.conduits = [] # Aether's conduits
		self.soul_stacks = 0 # Vex's passive stacks
		self.is_flying = False # Icarus ultimate state
		
		# Damage Cooldown (for environmental dmg)
		self.damageCooldown = cave.SceneTimer(999)
		self.damageCooldownTime = 1.0

		# --- Gameplay Variables ---
		self.item_cooldowns = {}
		self.deferred_damage = 0.0
		self.dd_bleed_timer = 0.0
		self.kraken_stacks = 0
		self.has_spellblade = False
		self.empoweredAA = None
		self.empoweredAATimer = 0
		self.isRecalling = False
		self.flags = 0 # Phase 73: Initialize flags to prevent AttributeError
		
		# --- Phase 116: Pro Configurations ---
		self.targetHeroesOnly = False
		self.cameraLocked = False
		self.autoAttack = MobaCommon.InputConfig.AUTO_ATTACK_ENABLED
		self.slotCastingModes = MobaCommon.InputConfig.SLOT_CASTING_MODES.copy()
		self.attackMoveOnLeftClick = MobaCommon.InputConfig.ATTACK_MOVE_ON_LEFT_CLICK
		self.attackMoveCursor = True
		self.stickyRangeIndicator = False
		self.lastTimeToggledHeroesOnly = 0
		
		# --- Phase 73: Input Buffering ---
		self.inputBuffer = None
		self.bufferTimer = 0.0
		self.stickyRangeIndicator = False
		
		# --- Phase 65: Trinkets & Vision ---
		self.trinket_cooldown = 0.0
		self.is_oracle_active = False
		self.oracle_timer = 0.0
		
		# --- Phase 30: Snowball (Mark/Dash) ---
		self.snowballMarkedTarget = None # The entity currently marked
		self.snowballMarkTimer = 0.0 # Duration remaining on mark
		
		# --- Phase 122: Hype & Bounties ---
		self.lastKillTime = 0.0
		self.multiKillCount = 0
		self.killStreak = 0
		self.bounty = 0
		
		# --- Phase 125: Primal Jungle ---
		self.jungleStacks = 0 # Grows on monster kills
		self.junglePetType = None # "GUSTWALKER", "MOSSTOMPER", "SCORCHCLAW"
		
		# --- Phase 131: Quick Cast & Virtual Cursor ---
		self.quickCastSettings = {"Q": False, "W": False, "E": False, "R": False}
		self.virtualCursorPos = None # Used by AI bots
		self.damageRecap = [] # Last N damage sources for death recap
		
		# --- Phase 63: Jungle Assignment ---
		self.heroData = HeroRegistry.HERO_REGISTRY.get(self.heroName, {})
		
		# --- Buff/FX System (Phase 20) ---
		if not self.entity.getPy("FloatingCombatTextComponent"):
			self.entity.add("FloatingCombatTextComponent")
		
		# --- Movement & Camera ---
		self.spawnPoint = self.transf.worldPosition.copy()
		self.respawnTimer = 0.0
		self.baseRespawnTime = 6.0
		
		# --- Ability States ---
		self.skillStages = {"Q": 0, "W": 0, "E": 0, "R": 0}
		self.activeToggles = {} # skillKey: bool
		self.skillStageTimers = {"Q": 0, "W": 0, "E": 0, "R": 0}
		self.cooldowns = {"Q": cave.SceneTimer(), "W": cave.SceneTimer(), "E": cave.SceneTimer(), "R": cave.SceneTimer()}
		self.cooldownDurations = {"Q": 0.0, "W": 0.0, "E": 0.0, "R": 0.0}
		# Initialize timers far in the past so abilities are ready
		for k in self.cooldowns: self.cooldowns[k].set(999)
		self.activeEffects = []
		
		# --- Leveling & Economy (Phase 18: Decoupled) ---
		self.leveling = LevelingManager(self)
		self.inventory_mgr = InventoryManager(self)
		
		# Phase 102: Rune System Initialization
		# Assign default rune if none provided (Matches User Role Vision)
		default_runes = {
			"jungle": "LETHAL_TEMPO",
			"support": "GRASP_OF_THE_UNDYING",
			"mid": "ELECTROCUTE",
			"adc": "LETHAL_TEMPO",
			"top": "CONQUEROR"
		}
		role = self.heroData.get("role", "warrior")
		self.rune_id = getattr(self, "selected_rune", default_runes.get(role, "LETHAL_TEMPO"))
		self.rune_mgr = MobaCommon.RuneManager(self, self.rune_id)
		
		# Phase 63: Jungle Assignment (must be after inventory_mgr is created)
		if self.heroData.get("role") == "jungle":
			self.inventory_mgr.items.append("Hunter's Resolve")
		
		self.passiveGoldTimer = 1.0
		self.outOfCombatTimer = cave.SceneTimer(999)
		
		# --- Phase 51: Rune System ---
		self.runeData = getattr(self, "runeData", None) # May be set by MatchOrchestrator
		
		# Bridge the naming discrepancy (Phase 52 Hardening)
		self.inventory = self.inventory_mgr.items 
		
		# Team Setup (Default to TeamA)
		if not (self.entity.hasTag("teamA") or self.entity.hasTag("teamB")):
			self.entity.addTag("teamA")
		
		# Load Hero Data
		self.initializeHero(self.heroName)

		# Phase 70: Optimized Component & Stat Initialization (Fixed per-frame leak)
		# These must only run once at start, not inside update_vision_tick
		if not self.entity.getPy("UIIndicatorComponent"):
			self.indicator = self.entity.add("UIIndicatorComponent")
		else:
			self.indicator = self.entity.getPy("UIIndicatorComponent")
			
		self.activeCastKey = None
		self.rangeActive = False
		self.castingMode = MobaCommon.CastingMode.QUICK_WITH_INDICATOR # Phase 116 Default
		self.eff_comp = self.entity.getPy("EffectComponent")
		MobaCommon.setup_combat_feedback(self.entity)
		self.recalculate_stats()

		# Shop UI Reference
		self.shopUI = None
		self.isARAM = cave.getGlobalDict().get("IsARAM", False)
		self.shopLocked = False # Always start unlocked in SR/ARAM Fountain
		
		shop_ent = scene.get("Shop")
		if shop_ent:
			self.shopUI = shop_ent.getPy("ShopComponent")

		# --- Phase 30: ARAM Lobby & Global Properties ---
		# Read hero from champion selection (set in MobaLobby.py)
		selected_hero = cave.getGlobalDict().get("SelectedHero", "")
		if selected_hero:
			self.heroName = selected_hero
		
		self.isARAM = cave.getGlobalDict().get("IsARAM", False)
		if self.isARAM:
			# ARAM Starting Rules: Lvl 3, 1400 Gold
			self.leveling.level = 3
			self.leveling.gold = 1400
			self.leveling.skillPoints = 3
			self.shopLocked = False # Initially open in fountain

		# FSM Initialization (State Driver)
		self.fsm = SimpleFSM(MobaStates.IdleState())
		self.fsm.bind(self)

		# Phase 100: Standardized Passive Manager
		self.passive_mgr = MobaPassiveManager(self)
		
		# Phase 100: Item Effect Cache (Optimized lookup)
		self.cached_item_effects = set()
		self.refresh_item_cache()
		
	def use_trinket(self, target_pos=None):
		"""Phase 65: Utility to activate the current trinket."""
		if self.trinket_cooldown > 0: return
		
		trinket_name = self.inventory_mgr.trinket
		scene = self.entity.getScene()
		
		if trinket_name == "Warding Totem":
			# Normal Ward: Stealth, 90s duration
			self._place_ward(scene, target_pos, duration=90.0, stealth=True)
			self.trinket_cooldown = 120.0
			
		elif trinket_name == "Oracle Lens":
			# Sweep: 10s duration
			self.is_oracle_active = True
			self.oracle_timer = 10.0
			self.trinket_cooldown = 90.0
			MobaCommon.play_sfx(self.entity, "SFX_Oracle_Start")
			
		elif trinket_name == "Farsight Alteration":
			# Blue Ward: Visible, Permanent (until destroyed), Long Range
			if self.leveling.level < 9: return # Level gate like League
			
			# Long range clamp (40 units)
			dist = (target_pos - self.transf.worldPosition).length()
			if dist > 40.0:
				target_pos = self.transf.worldPosition + (target_pos - self.transf.worldPosition).normalized() * 40.0
				
			self._place_ward(scene, target_pos, duration=-1, stealth=False, farsight=True)
			self.trinket_cooldown = 140.0

	def _place_ward(self, scene, pos, duration=90.0, stealth=True, farsight=False):
		if not pos: pos = self.transf.worldPosition + self.transf.getForwardVector() * 2.0
		
		ward = scene.addFromTemplate("WardTemplate", pos)
		if ward:
			comp = ward.getPy("WardComponent")
			if comp:
				comp.team = MobaCommon.get_entity_team(self.entity)
				comp.duration = duration
			
			# Vision Gating (Phase 65)
			ward.getProperties()["isStealthWard"] = stealth
			ward.getProperties()["isFarsight"] = farsight
			ward.getProperties()["health"] = 1 if farsight else 3 # Farsight is 1 hit
			
			MobaCommon.play_sfx(self.entity, "SFX_Ward_Place")

	def update_vision_tick(self, dt):
		"""Handles active vision tool logic."""
		if self.trinket_cooldown > 0:
			self.trinket_cooldown -= dt
			
		if self.is_oracle_active:
			self.oracle_timer -= dt
			# Oracle Sweep Logic: Reveal nearby enemy wards
			scene = self.entity.getScene()
			enemy_team = MobaCommon.Team.get_enemy(MobaCommon.get_entity_team(self.entity))
			wards = scene.getEntitiesWithTag("ward")
			for w in wards:
				if w.hasTag(enemy_team):
					dist = (w.getTransform().worldPosition - self.transf.worldPosition).length()
					if dist < 6.0: # Sweep radius
						MobaCommon.reveal_unit(w, 1.0) # Continuous reveal
						
			if self.oracle_timer <= 0:
				self.is_oracle_active = False

		# Unified Initialization
		# Moved to start() to prevent per-frame component leak and stat-recalc race
		pass

	def has_cooldown(self, tag):
		return self.item_cooldowns.get(tag, 0) > 0

	def set_cooldown(self, tag, duration):
		self.item_cooldowns[tag] = duration

	def recalculate_stats(self):
		"""Recalculates flat and percentage-based stats from base + items."""
		base = self.baseStats
		growth = self.heroData.get("growthStats", {})
		lvl_factor = self.level - 1
		
		# 1. Base + Per Level (Standardized to HeroRegistry keys)
		self.baseAD = base.get("ad", 50) + (growth.get("ad", 3.0) * lvl_factor)
		self.ad = self.baseAD
		self.ap = base.get("ap", 0) + (growth.get("ap", 0.0) * lvl_factor)
		self.armor = base.get("armor", 30) + (growth.get("armor", 4.0) * lvl_factor)
		self.mr = base.get("mr", 30) + (growth.get("mr", 1.5) * lvl_factor)
		self.maxHP = base.get("maxHP", 550) + (growth.get("hp", 90) * lvl_factor)
		self.maxMana = base.get("maxMana", 400) + (growth.get("mana", 40) * lvl_factor)
		self.speed = base.get("speed", 335)
		
		# Reset Passive-driven bonuses for clean recalculation
		self.bonusArmor = 0.0
		self.bonusAS = 0.0
		self.bonusAD = 0.0
		self.bonusMS = 0.0
		self.recoveryMod = 0.0
		
		# 4. Rune Bonuses
		if hasattr(self, "rune_mgr"):
			# Phase 100 Fix: Direct application to stat bridges instead of undefined helper
			if self.rune_id == "LETHAL_TEMPO":
				self.bonusAS += (self.rune_mgr.stacks * 0.10)
				if self.rune_mgr.stacks >= 6:
					self.range += 2.0
		
		# 5. Apply Minor Runes
		for m_id in getattr(self, "minor_runes", []):
			# Logic: Look up in registry and apply
			for tree in RuneRegistry.RUNE_TREE.values():
				if m_id in tree.get("minor_runes", {}):
					m_data = tree["minor_runes"][m_id]
					self.ad += m_data.get("ad", 0)
					self.ap += m_data.get("ap", 0)
					self.maxHP += m_data.get("maxHP", 0)
					self.maxMana += m_data.get("maxMana", 0)
					self.bonusAS += m_data.get("as", 0)
					self.tenacity += m_data.get("tenacity", 0)
					self.cdr += m_data.get("cdr", 0)
					self.hpRegen += m_data.get("hpRegen", 0)
		
		# Phase 118: Baron Buff Stats (Colossus Gaze)
		if self.hasEffect("BARON_BUFF"):
			self.ad += 40
			self.ap += 40
		
		
		# Recovery (Regen) - Must be reset BEFORE rune additions
		self.hpRegen = base.get("recovery", 1.5) + (growth.get("recovery", 0.2) * lvl_factor)
		self.manaRegen = base.get("manaRegen", 1.0) + (growth.get("manaRegen", 0.1) * lvl_factor)
		
		# Reset secondary stats that accumulate from items/runes
		self.critChance = 0.0
		self.critDamage = 0.0
		self.lifeSteal = 0.0
		self.cdr = 0.0
		self.lethality = 0.0
		self.tenacity = 0.0
		self.slowResist = 0.0
		self.magicPenFlat = 0.0
		self.range = base.get("range", 6.0)
		# Reset Dynamic Item Bonuses
		self.hullbreaker_bonus = getattr(self, "hullbreaker_bonus", 0)
		self.bonusCDR = 0.0
		
		# 2. Item Stats (Consolidated pass)
		self.bonusAS_items = 0.0
		self.onhit_spawner_count = 0
		self.as_logic_mode = "STANDARD" # "STANDARD", "CRIT", "ON_HIT"
		self.has_guinsoo = False
		self.has_ie = False
		self.has_ga = False
		
		armor_pen_opposite = 1.0
		magic_pen_opposite = 1.0
		
		for item_id in self.inventory:
			data = ItemRegistry.ITEM_REGISTRY.get(item_id)
			if not data: continue
			
			s = data.get("stats", {})
			# Flat Stats
			self.ad += s.get("ad", 0)
			self.ap += s.get("ap", 0)
			self.armor += s.get("armor", 0)
			self.mr += s.get("mr", 0)
			self.maxHP += s.get("hp", 0)
			self.maxMana += s.get("maxMana", s.get("mana", 0)) # Standardized lookup
			self.speed += s.get("speed", 0)
			
			# Secondary Stats
			self.bonusAS_items += s.get("as", 0)
			self.critChance += s.get("crit", 0)
			self.lifeSteal += s.get("lifeSteal", 0)
			self.cdr += s.get("cdr", 0)
			self.lethality += s.get("lethality", 0)
			self.hpRegen += s.get("hpRegen", 0)
			self.manaRegen += s.get("manaRegen", 0)
			self.tenacity += s.get("tenacity", 0.0)
			self.slowResist += s.get("slowResist", 0.0)
			self.magicPenFlat += s.get("magicPenFlat", 0.0)
			
			# Multiplicative Pen Stacking (Parity: LoL)
			armor_pen_opposite *= (1.0 - s.get("armorPenPercent", 0.0))
			magic_pen_opposite *= (1.0 - s.get("magicPenPercent", 0.0))
			
			# Logic & Special Passives
			if data.get("is_onhit_spawner"):
				self.onhit_spawner_count += 1
				
			logic = data.get("as_logic")
			if logic == "CRIT_LIMITER": self.as_logic_mode = "CRIT"
			elif logic == "GUINSOO_UNLIMITER": 
				self.as_logic_mode = "ON_HIT"
				self.has_guinsoo = True

			if item_id == "Infinity Edge":
				self.critDamage += 0.35
				self.has_ie = True
			elif item_id == "Guardian Angel":
				self.has_ga = True
			
			# Phase 66: Mobility Boots
			if data.get("special") == "MOBILITY_PASSIVE":
				if self.outOfCombatTimer.get() > 5.0:  # Cave API: Timer.get()
					self.speed += 90

		# Apply Hullbreaker / Dynamic Buffs
		self.armor += self.hullbreaker_bonus
		self.mr += self.hullbreaker_bonus

		# Phase 101: Heavy Character Mechanics (HP Penalty)
		# Squishies (HP < 1800) are unaffected. Tanks/Fighters get slower and hit slower.
		if self.maxHP > 1800:
			excess_hp = self.maxHP - 1800
			# Penalty: -0.5 MS per 100 HP, -1% AS Factor per 200 HP
			ms_penalty = (excess_hp / 100.0) * 0.5
			as_penalty_mult = 1.0 - (excess_hp / 200.0) * 0.015
			
			self.speed = max(280, self.speed - ms_penalty) # Floor at 280 MS
			self.totalAS_mult = max(0.4, as_penalty_mult) # Store multiplier for later AS calculation
		else:
			self.totalAS_mult = 1.0
			
		# Phase 101: Tank Damage Conversion (HP to AD)
		# Simulates 'Titan's Hydra' / Rune scaling for Heavy classes.
		if self.maxHP > 2500 and self.heroData.get("role") in ["top", "jungle"]:
			self.ad += (self.maxHP * 0.015)
		
		# Secondary Stats Initializers
		self.baseAS = base.get("baseAS", 0.625)
		# AS Growth is usually a percentage of base AS per level
		self.bonusAS = (growth.get("as", 0.0) * (self.level - 1)) + base.get("bonusAS", 0.0)



		# Phase 101: River Speed (Icarus Passive)
		if self.heroName == "Icarus":
			if MobaCommon.VisionManager.is_in_river(self.entity.getScene(), self.transf.worldPosition):
				self.speed += 45 # Flat river bonus

		# 3. Apply Tiered AS Caps & Final Logic
		has_as_boots = "Berserker's Greaves" in self.inventory
		self.is_limit_broken = (self.has_guinsoo and self.onhit_spawner_count >= 3 and has_as_boots)
		
		# --- Step A: Item-based AS (Passive) ---
		total_passive_bonus = self.bonusAS + self.bonusAS_items
		
		# Limit Break Surge: Instant leap to 3.0 AS when evolved
		if self.is_limit_broken:
			total_passive_bonus += 1.2 
			
		item_only_as = self.baseAS * (1.0 + total_passive_bonus)
		
		# Passive Item Cap
		item_cap = 2.0 if self.as_logic_mode == "CRIT" else 2.5
		if self.is_limit_broken: item_cap = 3.0 # Guinsoo Evolution Unlocks Cap
			
		self.totalAS_from_items = min(item_cap, item_only_as)
		
		# --- Step B: Skill-based AS (Active) ---
		self.bonusAS_skills = 0.0
		for eff in getattr(self, "activeEffects", []):
			if eff.id == "AS_BOOST":
				self.bonusAS_skills += eff.magnitude
				
		# --- Step C: Merge and Apply Global Hard Caps ---
		raw_total_as = self.totalAS_from_items + (self.baseAS * self.bonusAS_skills)
		
		# Standard world max (usually 2.5)
		absolute_max = 2.5 
		if self.as_logic_mode == "CRIT": absolute_max = 2.5 
		elif self.is_limit_broken: absolute_max = 3.0 
			
		# Apply Heavy penalty multiplier
		self.totalAS = min(absolute_max, raw_total_as) * getattr(self, "totalAS_mult", 1.0)
		
		# --- Step D: AS Overflow Conversion (Overdrive) ---
		# Only works if Limit Break is triggered
		if self.is_limit_broken:
			self.as_overflow = max(0, raw_total_as - 3.0)
		else:
			self.as_overflow = 0
		
		# Other stat finalization
		self.armorPenPercent = 1.0 - armor_pen_opposite
		self.magicPenPercent = 1.0 - magic_pen_opposite
		self.cdr = min(0.40, self.cdr)
		self.critChance = min(1.0, self.critChance)
		
		# --- Phase 100: Ward Capacity Scaling ---
		self.wardMaxCharges = 1 # Baseline
		for item in self.inventory:
			data = ItemRegistry.ITEM_REGISTRY.get(item)
			if data:
				tier = data.get("evolution_tier", 0)
				if tier == 1: self.wardMaxCharges = 1
				elif tier == 2: self.wardMaxCharges = 3
				elif tier == 3: self.wardMaxCharges = 4
		self.wardCharges = min(self.wardCharges, self.wardMaxCharges)
		
		# --- Phase 100: Lethality Sniper Range Scaling ---
		base_range = self.baseStats.get("range", 6.0)
		if getattr(self, "isRanged", False):
			# Sniper Bonus: +0.05 Range per 1 Lethality
			bonus_range = self.lethality * 0.05
			self.range = base_range + bonus_range
		else:
			self.range = base_range
			
		# Phase 73 FIX: Apply SPEED_RATIO to moveSpeed for engine compatibility
		self.speed *= MobaCommon.SPEED_RATIO
		
		# Phase 100: Hero-Specific Passives (Expansion)
		if self.heroName == "Dredge":
			actual_lvl_factor = self.level - 1
			base_max_hp = base.get("maxHP", 550) + (growth.get("hp", 90) * actual_lvl_factor)
			bonus_hp = max(0, self.maxHP - base_max_hp)
			self.ad += bonus_hp * 0.1 # 10% conversion
		
		elif self.heroName == "Vex":
			# Soul Harvest: 2 AP per stack
			self.ap += self.soul_stacks * 2
			
		elif self.heroName == "Nova":
			# Nova gains bonus Magic Pen based on Level
			self.magicPenFlat += self.level * 1.5
		
		# 4. Centralized Refresh (Phase 40)
		p = self.entity.getProperties()
		p["tenacity"] = min(0.6, self.tenacity) # Tenacity cap
		p["slowResist"] = self.slowResist
		
		# Update Item Cache for O(1) loop performance
		self.refresh_item_cache()
		
		# --- Phase 105: Dragon Soul Scaling ---
		team = MobaCommon.get_entity_team(self.entity)
		obj_mgr = MobaCommon.GlobalObjectiveManager
		ad_ap_mult = obj_mgr.get_dragon_mult(team, "ADAP")
		resist_mult = obj_mgr.get_dragon_mult(team, "RESIST")
		
		self.ad *= ad_ap_mult
		self.ap *= ad_ap_mult
		self.armor *= resist_mult
		self.mr *= resist_mult

		# Pass calculated base+item stats to refresh_stats to add active effects
		base_and_items = {
			"ad": self.ad, "ap": self.ap, "armor": self.armor, "magicResist": self.mr,
			"moveSpeed": self.speed, "attackSpeed": self.totalAS,
			"maxHealth": self.maxHP, "maxMana": self.maxMana,
			"attackRange": self.range
		}
		MobaCommon.refresh_stats(self.entity, base_and_items)
		
		# Synchronize local variables back from properties (since effects might have modified them)
		p = self.entity.getProperties()
		p["attackRange"] = self.range # Force sync for range logic
		self.ad = p["attackDamage"]
		self.armor = p["armor"]
		self.mr = p["magicResist"]
		self.speed = p["moveSpeed"]
		
		# Remaining UI/Logic props
		p["critChance"] = self.critChance
		p["lifeSteal"] = self.lifeSteal
		p["cdr"] = self.cdr
		p["lethality"] = self.lethality
		p["armorPenPercent"] = self.armorPenPercent
		p["magicPenPercent"] = self.magicPenPercent
		p["magicPenFlat"] = self.magicPenFlat
		
	def refresh_item_cache(self):
		"""Phase 100: Compiles all currently held item effect IDs into a flat set."""
		self.cached_item_effects.clear()
		for item_id in self.inventory:
			data = ItemRegistry.ITEM_REGISTRY.get(item_id)
			if data and "effects" in data:
				for evt, effect_id in data["effects"].items():
					self.cached_item_effects.add(effect_id)

	def takeDamage(self, raw_dmg, dmg_type, attacker=None):
		# 1. Invulnerability Check
		if hasattr(self, "flags") and (self.flags & MobaCommon.EffectFlags.INVULNERABLE):
			return 0

		# 2. Spell Shield Block
		blocked = False
		for eff in self.activeEffects:
			if eff.id == "SPELL_SHIELD":
				eff.duration = 0 # Consume
				blocked = True
				break
		if blocked: return 0
		
		# 3. Aggro Signaling (For Turrets)
		if attacker and attacker.hasTag("player"):
			attacker.getProperties()["last_hero_aggro_time"] = self.entity.getScene().getElapsedSceneTime()
			pass

		# 4. Situational Multipliers (LDR Giant Slayer, etc)
		situational_mult = 1.0
		if attacker:
			attacker_pc = attacker.getPy("PlayerController")
			if attacker_pc:
				situational_mult = MobaItems.ItemEffectManager.get_situational_multiplier(attacker_pc, self.entity)

		# 5. Item Defense Passives (Death's Dance, Thornmail, etc.)
		# process_on_take_damage returns adjusted raw damage
		raw_dmg = MobaItems.ItemEffectManager.process_on_take_damage(self, attacker, raw_dmg, dmg_type)
		
		# 6. Mitigation Calculation (Armor/MR + Penetration)
		# We call calculate_damage HERE. Raw dmg comes from MobaCommon.apply_damage or internal triggers.
		reduced_dmg = MobaCommon.calculate_damage(raw_dmg, dmg_type, attacker=attacker, defender=self.entity, situational_mult=situational_mult)
		
		# 7. Out of Combat status
		self.outOfCombatTimer.reset()
		
		# 8. Shield Handling (Skip for DamageType.PURE)
		shield = self.entity.getProperties().get("shieldHP", 0)
		if shield > 0 and dmg_type != MobaCommon.DamageType.PURE:
			# Damage absorbed by shield first
			absorbed = min(shield, reduced_dmg)
			self.entity.getProperties()["shieldHP"] = shield - absorbed
			reduced_dmg -= absorbed
			
		# 9. Apply to Health
		current_hp = self.entity.getProperties()["health"]
		if current_hp - reduced_dmg <= 0:
			# Lethal Damage Detected - Check for Resurrection
			if getattr(self, "has_ga", False) and not self.inventory_mgr.has_cooldown("Guardian Angel"):
				self.entity.getProperties()["health"] = 1.0
				self.trigger_resurrection()
				return 0 # Damage negated by GA proc
			
		self.entity.getProperties()["health"] -= reduced_dmg
		
		# 10. Recall Interruption (Phase 28)
		if reduced_dmg > 0 and self.isRecalling:
			self.cancelRecall("Damage Taken")
		
		# 10. Track Contribution for Rewards
		if attacker:
			scene_time = self.entity.getScene().getElapsedSceneTime()
			self.entity.getProperties()["lastAttacker"] = attacker
			contribs = self.entity.getProperties().get("contributions", {})
			contribs[attacker.name if hasattr(attacker, 'name') else str(attacker)] = (scene_time, attacker)
			self.entity.getProperties()["contributions"] = contribs
			
		
		# Phase 100: Trigger Passive on Damage Taken
		if hasattr(self, "passive_mgr"):
			self.passive_mgr.on_hit_taken(attacker, reduced_dmg)
			
		return reduced_dmg

	def trigger_resurrection(self):
		"""Phase 100: Guardian Angel - 4s Stasis followed by 50% Restore."""
		scene = self.entity.getScene()
		# 1. Apply Stasis
		self.applyEffect("STASIS", 4.0, flags=MobaCommon.EffectFlags.INVULNERABLE | MobaCommon.EffectFlags.UNTARGETABLE | MobaCommon.EffectFlags.STUN)
		
		# 2. Visuals: Golden Tint
		if self.mesh:
			m_comp = self.mesh.get("Mesh")
			if m_comp:
				mat = m_comp.getFinalMaterial()
				if mat: mat.uniforms.set("u_baseColor", cave.Vector4(1.0, 0.8, 0.2, 1.0))
		
		MobaCommon.spawn_vfx(scene, "VFX_GA_Proc", self.transf.worldPosition, duration=4.0)
		MobaCommon.play_sfx(self.entity, "SFX_GA_Proc")
		
		# 3. Set Cooldown (Standard LoL 300s)
		self.inventory_mgr.set_cooldown("Guardian Angel", 300.0)
		self.resurrection_timer = 4.0

	def buy_item(self, item_name):
		"""Attempt to purchase an item, handling recipes and gold (delegated to InventoryManager)."""
		return self.inventory_mgr.buy_item(item_name)

	def initializeHero(self, name):
		"""Standardized hero loader for start() and TRANSFORM effects."""
		self.heroName = name
		registry = HeroRegistry.HERO_REGISTRY
		self.heroData = registry.get(name, registry["Warrior"])
		
		# Phase 100: Restricted Support Initial Item
		if self.heroData.get("role") == "support":
			self.buy_item("Guardian's Compass")
		self.abilities = self.heroData["skills"]
		
		stats = self.heroData["stats"]
		self.baseStats = stats.copy()
		
		# Apply Stats to Entity Properties
		self.entity.getProperties()["maxHealth"] = stats["maxHP"]
		self.entity.getProperties()["health"] = stats["maxHP"]
		self.entity.getProperties()["armor"] = stats["armor"]
		self.entity.getProperties()["magicResist"] = stats["mr"]
		self.entity.getProperties()["isRanged"] = stats["isRanged"]
		self.isRanged = stats["isRanged"] # Cache for item logic
		self.entity.getProperties()["attackRange"] = stats["range"]
		
		# Movement speed conversion
		self.baseSpeed = stats["speed"] / 56.6
		self.mana = stats.get("maxMana", 100.0)
		self.maxMana = stats.get("maxMana", 100.0)
		self.manaRegen = 2.0
		
		# Cleanup existing toggles
		self.activeToggles.clear()
		
		# Ultimate learning at level 1 check
		if self.heroData.get("startWithR"):
			self.skillLevels["R"] = 1
			
		# Phase 51: Injection of pre-game Runes/Masteries
		if hasattr(self, "runeData") and self.runeData:
			self.applyRunes(self.runeData)
		
		pass

	def applyRunes(self, rune_data):
		"""Phase 51: Injects flat stat bonuses from RuneRegistry into base attributes."""
		stats = rune_data.get("stats", {})
		
		# Apply Flat AD
		if "ad_flat" in stats:
			self.baseStats["ad"] = self.baseStats.get("ad", 50) + stats["ad_flat"]
			
		# Apply Flat HP
		if "hp_flat" in stats:
			self.baseStats["maxHP"] += stats["hp_flat"]
			self.entity.getProperties()["maxHealth"] = self.baseStats["maxHP"]
			self.entity.getProperties()["health"] = self.baseStats["maxHP"]
			
		# Apply Flat Armor
		if "armor_flat" in stats:
			self.baseStats["armor"] = self.baseStats.get("armor", 30) + stats["armor_flat"]
			self.entity.getProperties()["armor"] = self.baseStats["armor"]

		# Apply Flat MR
		if "mr_flat" in stats:
			self.baseStats["mr"] = self.baseStats.get("mr", 30) + stats["mr_flat"]
			self.entity.getProperties()["magicResist"] = self.baseStats["mr"]

		# Apply AP (Ability Power)
		if "ap_flat" in stats:
			self.baseStats["ap"] = self.baseStats.get("ap", 0) + stats["ap_flat"]

		# Apply Percentage AS
		if "as_percent" in stats:
			# We store this to be picked up by recalculate_stats as a multiplier or addition
			self.baseStats["bonusAS"] = self.baseStats.get("bonusAS", 0) + stats["as_percent"]

		self.recalculate_stats()

	def add_exp(self, amount: int):
		"""Adds experience and handles leveling up (delegated to LevelingManager)."""
		self.leveling.add_exp(amount)

	def level_up(self):
		"""Handles stat growth logic for leveling up (delegated to LevelingManager)."""
		self.leveling.level_up()

	def upgrade_skill(self, key: str):
		if self.skillPoints > 0:
			current_level = self.skillLevels.get(key, 0)
			ability_data = self.abilities.get(key)
			
			if not ability_data:
				return

			max_level = ability_data.get("maxLevel", 5) # Default max level 5
			if key == "R": max_level = ability_data.get("maxLevel", 3) # Ultimate max level 3

			if current_level < max_level:
				# Check level requirement for ultimate
				if key == "R" and self.level < 6 and current_level == 0:
					return
				if key == "R" and self.level < 11 and current_level == 1:
					return
				if key == "R" and self.level < 16 and current_level == 2:
					return

				self.skillLevels[key] = current_level + 1
				self.skillPoints -= 1
			else:
				pass
		else:
			pass

	def track_camera_to(self, target_ent):
		"""Snaps the main camera to a target entity."""
		scene = self.entity.getScene()
		cam = scene.getCamera()
		if not cam or not target_ent: return
		
		targetPos = target_ent.getTransform().worldPosition
		camTrans = cam.getTransform()
		
		# Find relative offset from player to maintain perspective
		# This handles arbitrary camera angles/heights set in the editor
		offset = camTrans.worldPosition - self.transf.worldPosition
		new_cam_pos = targetPos + offset
		camTrans.setPosition(new_cam_pos.x, new_cam_pos.y, new_cam_pos.z)
		pass

	def track_camera_to_ally(self, index):
		"""Snaps camera to the Nth ally champion."""
		scene = self.entity.getScene()
		teamTag = "teamA" if self.entity.hasTag("teamA") else "teamB"
		# Get allies, exclude self, sort by ID for consistent F2-F5 mapping
		allies = [e for e in MobaCommon.EntityRegistry.get_team_entities(teamTag, "player") if e != self.entity]
		allies.sort(key=lambda x: x.entityID)
		
		if index < len(allies):
			self.track_camera_to(allies[index])

	def get_skill_value(self, key, param, default=0):
		"""Returns the value for a parameter based on the current skill level."""
		ability = self.abilities.get(key)
		if not ability: return default
		
		val = ability.get(param, default)
		if isinstance(val, list):
			lvl = self.skillLevels.get(key, 0)
			idx = max(0, min(lvl - 1, len(val) - 1))
			return val[idx]
		return val
		
	def hasEffect(self, effect_id):
		"""Returns True if the entity has an active effect with the given ID."""
		if not self.eff_comp:
			self.eff_comp = self.entity.getPy("EffectComponent")
		if self.eff_comp:
			return effect_id in self.eff_comp.active_effects
		return False

	def onAttackHit(self, target_ent, target_controller, damage_dealt):
		"""Called after each auto-attack lands. Handles on-hit passives and Jungle Buffs."""
		
		# --- JUNGLE BUFF ON-HIT ---
		if self.hasEffect("BUFF_RED") and target_controller:
			# Slow (15%) + Burn (small true damage)
			target_controller.applyEffect("SLOW", 2.0, flags=MobaCommon.EffectFlags.SLOW, magnitude=0.15)
			# Brief true damage burn
			MobaCommon.apply_damage(target_ent, 10 + (self.level * 2), MobaCommon.DamageType.TRUE, attacker=self.entity)
			pass

	def handleKillStreak(self, victim):
		"""Phase 122: Updates bounty and multi-kill status on enemy death."""
		scene = self.entity.getScene()
		now = scene.getElapsedSceneTime()
		
		# 1. Update Streak & Bounty
		self.killStreak += 1
		# Every kill adds STREAK_STEP, capped at MAX_BOUNTY
		self.bounty = min(MobaCommon.BountyConfig.MAX_BOUNTY, self.bounty + MobaCommon.BountyConfig.STREAK_STEP)
		
		# 2. Multi-Kill Logic (10s window)
		if (now - self.lastKillTime) < 10.0:
			self.multiKillCount += 1
		else:
			self.multiKillCount = 1
		self.lastKillTime = now
		
		# 3. Announce & Visual Hype
		kill_type = None
		if self.multiKillCount == 2: kill_type = MobaCommon.MultiKillType.DOUBLE
		elif self.multiKillCount == 3: kill_type = MobaCommon.MultiKillType.TRIPLE
		elif self.multiKillCount == 4: kill_type = MobaCommon.MultiKillType.QUADRA
		elif self.multiKillCount >= 5: kill_type = MobaCommon.MultiKillType.PENTA
		
		if kill_type:
			MobaCommon.play_announcer(scene, kill_type)
			MobaUI.broadcast_multi_kill(self.entity, kill_type)
		else:
			# Normal Kill
			MobaCommon.play_announcer(scene, "ENEMY_SLAIN")

		# Phase 100: Unified Passive Hit Processing
		if hasattr(self, "passive_mgr"):
			self.passive_mgr.on_hit_target(target_ent, damage_dealt, is_basic_attack=True)
			
		# Phase 101: Fighter/Duelist Item Hit Effects
		if hasattr(self, "inventory_mgr"):
			MobaItems.ItemEffectManager.process_on_hit(self, target_ent, is_ability=False)

	def getStacksOn(self, target_ent, stack_name):
		"""Returns the number of stacks of a given passive on a target."""
		stack_key = f"{stack_name}_{self.entity.name}"
		return target_ent.getProperties().get(stack_key, 0)

	def processInput(self):
		dt = cave.getDeltaTime()
		events = cave.getEvents()
		scene = self.entity.getScene()

		# Buffer Decay
		if self.bufferTimer > 0:
			self.bufferTimer -= dt
			if self.bufferTimer <= 0:
				self.inputBuffer = None

		# Key Mapping
		key_map = {
			cave.event.KEY_Q: "Q", cave.event.KEY_W: "W", cave.event.KEY_E: "E", cave.event.KEY_R: "R",
			cave.event.KEY_D: "D", cave.event.KEY_F: "F", cave.event.KEY_4: "TRINKET"
		}

		# --- 1. Keyboard Events — Using Cave's pressed()/released() API ---
		isCtrl = events.active(cave.event.KEY_LCTRL) or events.active(cave.event.KEY_RCTRL)
		
		# Phase 116: Target Heroes Only (~ Key)
		cfg = MobaCommon.InputConfig
		if cfg.TREAT_TARGET_HEROES_ONLY_AS_TOGGLE:
			if events.pressed(cfg.KEY_TARGET_HEROES_ONLY):
				self.targetHeroesOnly = not self.targetHeroesOnly
				MobaUI.broadcast_event(f"Target Heroes Only: {'ON' if self.targetHeroesOnly else 'OFF'}")
		else:
			self.targetHeroesOnly = events.active(cfg.KEY_TARGET_HEROES_ONLY)

		# Ability Upgrading (LoL: Ctrl+Q/W/E/R on key press)
		if isCtrl:
			for key_const, label in key_map.items():
				if label in ("Q", "W", "E", "R") and events.pressed(key_const):
					self.upgrade_skill(label)

		# Camera Centering (on press)
		if events.pressed(cfg.KEY_CENTER_CAM) or events.pressed(cave.event.KEY_F1):
			self.track_camera_to(self.entity)
		elif events.pressed(cave.event.KEY_F2): self.track_camera_to_ally(0)
		elif events.pressed(cave.event.KEY_F3): self.track_camera_to_ally(1)
		elif events.pressed(cave.event.KEY_F4): self.track_camera_to_ally(2)
		elif events.pressed(cave.event.KEY_F5): self.track_camera_to_ally(3)

		# Ability & Summoner Casting (skip if Ctrl held)
		if not isCtrl:
			for key_const, label in key_map.items():
				if events.pressed(key_const):
					self.handleSmartCast(label, isDown=True)
				elif events.released(key_const):
					self.handleSmartCast(label, isDown=False)

		# Recall (B key)
		if events.pressed(cfg.KEY_RECALL):
			self.executeRecall()

		# Stop (S key)
		if events.pressed(cfg.KEY_STOP):
			self.inputBuffer = None
			self.state = MobaStates.IdleState()
			self.state.start(self)
			if hasattr(self, "character"): self.character.setWalkDirection(0,0,0)
			
		# Camera Lock (Y key)
		if events.pressed(cfg.KEY_LOCK_CAM):
			self.cameraLocked = not self.cameraLocked
			MobaUI.broadcast_event(f"Camera Lock: {'ON' if self.cameraLocked else 'OFF'}")

		# Shop (P key)
		if events.pressed(cfg.KEY_SHOP):
			if self.entity.getProperties().get("canShop", False):
				# Phase 31: ARAM only locks shop after leaving fountain
				if self.isARAM and self.shopLocked:
					pass
					MobaUI.broadcast_event("The Dealer is gone! Die to shop.")
					return

				if self.shopUI:
					self.shopUI.toggle()
					self.isShopOpen = not self.isShopOpen
				else:
					pass
			else:
				pass

		# Ping System (Phase 120 Radial Wheel)
		if events.active(cave.event.KEY_LALT) or events.active(cave.event.KEY_RALT):
			if events.pressed(cave.event.MOUSE_LEFT):
				self.handlePing("GENERIC")
		
		# Generic Ping (G) - Hold for Wheel
		if events.pressed(cfg.KEY_PING_GENERIC):
			self.ping_hold_timer = 0.0
			self.ping_start_pos = MobaCommon.get_mouse_position_ui()
			
		if events.active(cfg.KEY_PING_GENERIC):
			self.ping_hold_timer += dt
			if self.ping_hold_timer > 0.25: # 250ms hold
				hud_list = scene.getEntitiesWithTag("HUD_Root")
				if hud_list:
					hud = hud_list[0].getPy("HUDController")
					if hud: hud.open_ping_wheel(self.ping_start_pos)
				
		if events.released(cfg.KEY_PING_GENERIC):
			hud_list = scene.getEntitiesWithTag("HUD_Root")
			if hud_list:
				hud = hud_list[0].getPy("HUDController")
				if hud and self.ping_hold_timer > 0.25:
					ping_type = hud.close_ping_wheel()
					self.handlePing(ping_type)
				elif self.ping_hold_timer <= 0.25:
					self.handlePing("GENERIC")
			self.ping_hold_timer = 0.0
			
		if events.pressed(cfg.KEY_PING_DANGER):
			self.handlePing("DANGER")

		# Attack-Move (A key)
		if events.pressed(cfg.KEY_ATTACK_MOVE):
			self.rangeActive = not self.rangeActive if self.stickyRangeIndicator else True
			if self.rangeActive:
				self.indicator.show(MobaCommon.IndicatorType.CIRCLE, {"range": self.entity.getProperties().get("attackRange", 5.0)})
		if events.released(cfg.KEY_ATTACK_MOVE) and not self.stickyRangeIndicator:
			self.rangeActive = False
			self.indicator.hide()

		# --- 2. Mouse Input ---
		if events.pressed(cave.event.MOUSE_RIGHT):
			# PHASE 116: Right-click cancel logic
			if self.activeCastKey or self.rangeActive:
				self.rangeActive = False
				if self.indicator: self.indicator.hide()
				self.activeCastKey = None
				return # Don't move on the frame you cancel
			
			# Movement cancels Recall
			if self.isRecalling:
				self.cancelRecall("Movement Input")
				
			out = scene.getDataOverMousePosition()
			if out.hit:
				if out.entity.hasTag("enemy"):
					# Phase 116: Target Heroes Only logic
					if self.targetHeroesOnly and not out.entity.hasTag("player"):
						# Skip minions/structures, treat as ground move
						self.inputBuffer = ("MOVE", out.position.copy())
					else:
						self.inputBuffer = ("ATTACK", out.entity)
					self.bufferTimer = self.INPUT_BUFFER_TIME
				else:
					self.inputBuffer = ("MOVE", out.position.copy())
					self.bufferTimer = self.INPUT_BUFFER_TIME

		if events.pressed(cave.event.MOUSE_LEFT):
			# Phase 116: Attack Move on Left Click
			if self.attackMoveOnLeftClick and not self.activeCastKey:
				out = scene.getDataOverMousePosition()
				if out.hit:
					self.executeAttackMove(out.position.copy())
					return

			if self.activeCastKey:
				self.tryCast(self.activeCastKey)
				self.activeCastKey = None
				self.indicator.hide()
			elif self.rangeActive:
				out = scene.getDataOverMousePosition()
				if out.hit:
					self.executeAttackMove(out.position.copy())
					self.rangeActive = False
					self.indicator.hide()


	def handleSmartCast(self, key, isDown):
		"""Logic for Normal vs Quick vs Quick+Indicator."""
		mode = self.slotCastingModes.get(key, MobaCommon.CastingMode.NORMAL)
		if isDown:
			if mode == MobaCommon.CastingMode.QUICK:
				self.tryCast(key)
			elif mode == MobaCommon.CastingMode.QUICK_WITH_INDICATOR:
				self.activeCastKey = key
				self.showAbilityIndicator(key)
			else: # NORMAL
				self.activeCastKey = key
				self.showAbilityIndicator(key)
		else: # Key Up
			if mode == MobaCommon.CastingMode.QUICK_WITH_INDICATOR:
				if self.activeCastKey == key:
					self.tryCast(key)
					self.activeCastKey = None
					if self.indicator: self.indicator.hide()

	def handlePing(self, type):
		"""Phase 116: Unified Ping Broadcaster."""
		scene = self.entity.getScene()
		out = scene.getDataOverMousePosition()
		if out.hit:
			msg = f"{self.heroName} signals {type} at {out.position.x:.1f}, {out.position.z:.1f}"
			MobaCommon.broadcast_event(msg)
			# Spawn VFX at location
			template = "VFX_Ping_Generic" if type == "GENERIC" else "VFX_Ping_Danger"
			MobaCommon.spawn_vfx(scene, template, out.position + cave.Vector3(0, 0.5, 0), duration=2.5)

	def showAbilityIndicator(self, key):
		ability = self.abilities.get(key)
		if not ability: return
		
		# Get data for current stage
		stages = ability.get("stages")
		data = stages[self.skillStages[key]] if stages else ability
		
		# Determine visual type
		eff = data.get("effect", "")
		itype = MobaCommon.IndicatorType.CIRCLE
		if "PROJECTILE" in eff: itype = MobaCommon.IndicatorType.LINE
		elif "RECT" in eff: itype = MobaCommon.IndicatorType.RECTANGLE
		
		self.indicator.show(itype, {
			"range": data.get("range", 10.0),
			"width": data.get("width", 2.0)
		})

	def executeAttackMove(self, target_pos):
		"""Logic for A-click: attack nearest enemy to cursor or player."""
		scene = self.entity.getScene()
		enemies = MobaCommon.EntityRegistry.get("enemy")
		if not enemies: return
		
		pivot = target_pos if self.attackMoveCursor else self.transf.worldPosition
		
		best_target = None
		min_dist = 999
		for e in enemies:
			if not e.isActive(): continue
			# Check if unit is targetable
			props = e.getProperties()
			if props.get("isUntargetable", False): continue
			
			# Phase 116: Target Heroes Only modifier for Attack Move
			# (Optional: LoL standard attack move usually doesn't respect it, but we'll add the check for custom feel)
			if self.targetHeroesOnly and not e.hasTag("player"): continue

			d = (e.getTransform().worldPosition - pivot).length()
			if d < min_dist:
				min_dist = d
				best_target = e
		
		if best_target:
			self.inputBuffer = ("ATTACK", best_target)
			self.bufferTimer = self.INPUT_BUFFER_TIME
		else:
			self.inputBuffer = ("MOVE", target_pos)
			self.bufferTimer = self.INPUT_BUFFER_TIME

	def get_skill_data(self, key):
		"""Returns the ability data dict for a given skill key, accounting for stages."""
		ability = self.abilities.get(key)
		if not ability: return None
		stages = ability.get("stages")
		if stages:
			stage_idx = self.skillStages.get(key, 0)
			return stages[min(stage_idx, len(stages) - 1)]
		return ability

	def tryCast(self, key):
		"""Entry point for casting. Transitions to AbilityState if valid. Returns True on success."""
		if key == "TRINKET":
			self.executeTrinket()
			return True

		# Phase 115: Summoner Spell Routing (D/F keys)
		if key in ("D", "F"):
			if hasattr(self, 'summoner_spell_mgr') and self.summoner_spell_mgr:
				return self.summoner_spell_mgr.try_cast(key)
			return False

		ability = self.get_skill_data(key)
		if not ability: return False
		
		# Phase 131: Quick Cast Toggle (Feature 10)
		is_quick = self.quickCastSettings.get(key, MobaCommon.QuickCastConfig.ENABLED_BY_DEFAULT)
		if is_quick:
			# Skip range indicator, cast immediately toward mouse/virtualCursor
			pass # Quick cast uses same path but skips indicator display
		
		# --- Phase 116: Clamp Cast at Max Range ---
		if MobaCommon.InputConfig.CLAMP_CAST_AT_MAX_RANGE:
			scene = self.entity.getScene()
			out = scene.getDataOverMousePosition()
			if out.hit:
				target_pos = out.position
				max_range = ability.get("range", 10.0)
				dist = (target_pos - self.transf.worldPosition).length()
				if dist > max_range:
					# Standard LoL behavior: fire at max range toward cursor
					dir = (target_pos - self.transf.worldPosition).normalized()
					# We override the mouse target for the upcoming AbilityState/execute
					self.clampedTargetPos = self.transf.worldPosition + dir * max_range
				else:
					self.clampedTargetPos = None
			else:
				self.clampedTargetPos = None

		# 0. Check CC Restrictions
		if self.flags & (MobaCommon.EffectFlags.STUN | MobaCommon.EffectFlags.SILENCE):
			return False
			
		# Grounded Restriction (Phase 101)
		if self.flags & MobaCommon.EffectFlags.GROUNDED:
			eff = ability.get("effect", "")
			if "DASH" in eff or "BLINK" in eff or "LEAP" in eff:
				from UI import MobaUI
				MobaUI.spawn_fct(self.entity.getScene(), self.transf.worldPosition, "CAN'T DASH!", cave.Vector4(0.8, 0.4, 1.0, 1.0))
				return False
			
		# 1. Check if Learned & Cooldowns
		lvl = self.skillLevels.get(key, 0)
		if lvl == 0: return False # Not learned
		timer = self.cooldowns.get(key)
		if timer and timer.get() < self.cooldownDurations.get(key, 0): return False
		
		mana_cost = self.get_skill_value(key, "mana", 0)
		if self.mana < mana_cost: return False
		
		# Toggles (e.g. Anivia R)
		if ability.get("isToggle"):
			if key in self.activeToggles:
				del self.activeToggles[key]
				pass
			else:
				self.activeToggles[key] = {
					"pivot": self.transf.worldPosition.copy(),
					"leash": ability.get("leashRange", 18.0)
				}
				pass
			return True

		# 2. Spellblade (Sheen) Trigger
		from Core import MobaItems
		if MobaItems.ItemEffectManager.has_item_effect(self, "onAbilityCast", "SPELLBLADE_READY"):
			if not self.has_cooldown("SPELLBLADE_CD"):
				self.has_spellblade = True
				self.set_cooldown("SPELLBLADE_CD", 1.5)

		# 2. Get Stage Data
		stages = ability.get("stages")
		stageData = ability
		currentStage = self.skillStages.get(key, 0)
		if stages:
			stageData = stages[currentStage]
			
		# 3. Transition to multi-phase AbilityState
		self.fsm.setState(MobaStates.AbilityState(key, ability, stageData))
		
		# 4. Consume Resources
		self.mana -= self.get_skill_value(key, "mana", 0)
		self.entity.getProperties()["mana"] = self.mana # Sync to props for UI
		
		# 5. Cooldown Logic — depends on whether this is a staged ability
		if stages:
			nextStage = currentStage + 1
			if nextStage >= len(stages):
				# Final stage reached → full cooldown, reset stage
				self.skillStages[key] = 0
				self.skillStageTimers[key] = 0
				self.cooldownDurations[key] = self.get_skill_value(key, "cd", 10.0)
				self.cooldowns[key].reset()
				pass
			else:
				# Mid-stage → short internal CD + recast window
				# Note: self.skillStages[key] increment is now handled exclusively in executeAbilityEffect
				self.cooldownDurations[key] = ability.get("stageWindow", 4.0)
				pass
		else:
			# Normal (non-staged) ability → standard cooldown
			self.cooldownDurations[key] = self.get_skill_value(key, "cd", 10.0)
			self.cooldowns[key].reset()
		
		# Phase 100: Bloodsong/Spellblade Priming
		if MobaItems.ItemEffectManager.has_item_effect(self, "onHit", "BLOODSONG_EXPOSE"):
			self.spellblade_primed = True
			
		# Phase 100: Vento Aura Auto-Swap
		if self.heroName == "Vento":
			self.vento_aura = 1 - self.vento_aura
			MobaCommon.spawn_vfx(self.entity.getScene(), "VFX_Vento_Swap", self.transf.worldPosition, duration=1.0)
			
		return True

	def executeAbilityEffect(self, key, stageData):
		"""Called by AbilityState once startup is complete."""
		scene = self.entity.getScene()
		ability = self.abilities.get(key)
		
		# --- Wave 11: Audio-Visual & Shader Feedback ---
		# 1. Trigger SFX (Cast Sound)
		sfx_cast = stageData.get("sfx_cast", stageData.get("sfx"))
		if sfx_cast: MobaCommon.play_sfx(self.entity, sfx_cast)
		
		# 2. Spawn VFX (Cast Visuals)
		vfx_cast = stageData.get("vfx_cast", stageData.get("vfx"))
		if vfx_cast:
			is_persistent = stageData.get("vfx_persistent", False)
			dur = -1 if is_persistent else stageData.get("vfx_duration", 1.5)
			MobaCommon.spawn_vfx(scene, vfx_cast, self.transf.worldPosition, duration=dur, parent=self.entity if is_persistent else None)
		
		# 3. Update Shader Uniforms (Material Effects)
		shader_params = stageData.get("shaderParams")
		if shader_params and self.mesh:
			mesh_cmp = self.mesh.get("Mesh")
			if mesh_cmp:
				for param, value in shader_params.items():
					try: mesh_cmp.uniformOverrides.set(param, value)
					except: pass
		
		# --- Original Logic ---
		effect_name = stageData.get("effect", "")
		if self.flags & MobaCommon.EffectFlags.GROUNDED:
			if effect_name in ["BLINK", "DASH", "THUNDER_DASH"]:
				return # Prevent effect execution if grounded

		# Manage stage increment or reset
		stages = ability.get("stages", [])
		if stages:
			self.skillStages[key] += 1
			if self.skillStages[key] >= len(stages):
				self.skillStages[key] = 0
				self.cooldownDurations[key] = self.get_skill_value(key, "cd", 10.0)
				self.cooldowns[key].reset()
				self.skillStageTimers[key] = 0
			else:
				# Short window to re-cast before CD starts
				self.skillStageTimers[key] = ability.get("stageWindow", 4.0)
				self.cooldownDurations[key] = ability.get("stageCD", 0.5) # Global internal CD between casts
				self.cooldowns[key].reset()
		else:
			self.cooldownDurations[key] = self.get_skill_value(key, "cd", 10.0)
			self.cooldowns[key].reset()

		# 3. Effect Dispatcher (Using stageData)
		self.current_skill_data = stageData
		effect = stageData.get("effect")
		
		if effect == "EMPOWERED_MS_AA":
			# MS Boost via status effect system
			ms_boost = self.get_skill_value(key, "msBoost", 0.3)
			duration = self.get_skill_value(key, "duration", 3.0)
			self.applyEffect("MS_BOOST", duration, magnitude=ms_boost)
			# Empowered AA buff (ID used for logic check in AttackState)
			self.applyEffect("EmpoweredAA", duration)
			
			# AA Reset check
			if isinstance(self.fsm.getState(), MobaStates.AttackState):
				self.fsm.setState(MobaStates.AttackState(reset=True))
		
		elif effect == "HP_SCALED_SHIELD":
			# Shield that is stronger at low HP
			missing_pct = 1.0 - (self.entity.getProperties()["health"] / self.entity.getProperties()["maxHealth"])
			base_val = self.get_skill_value(key, "value", 100)
			duration = self.get_skill_value(key, "duration", 2.5)
			
			final_val = base_val * (1.0 + missing_pct) # Up to 2x shield
			self.applyEffect("SHIELD", duration, magnitude=final_val)
			self.entity.getProperties()["shieldHP"] = final_val
			pass
			
		elif effect == "HP_SCALED_DAMAGE":
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData["range"])
			if target:
				missing_pct = 1.0 - (self.entity.getProperties()["health"] / self.entity.getProperties()["maxHealth"])
				base_dmg = stageData["damage"]
				final_dmg = base_dmg * (1.0 + (missing_pct * 2.0))
				
				# Use standardized damage applicator
				dmg_type = MobaCommon.DamageType.MAGIC if stageData.get("res_type") == "magical" else MobaCommon.DamageType.PHYSICAL
				reduced = MobaCommon.apply_damage(target, final_dmg, dmg_type, attacker=self.entity)
				pass

		elif effect in ["STUN", "ROOT", "SILENCE", "SLOW", "CHARM", "FEAR", "TAUNT"]:
			# Universal CC call
			cast_range = stageData.get("range", 10.0)
			target = MobaCommon.get_closest_target(self.transf.worldPosition, cast_range)
			if target:
				duration = self.get_skill_value(key, "duration", 1.0)
				magnitude = self.get_skill_value(key, "magnitude", 0.0)
				MobaCommon.apply_cc(target.getPy("PlayerController"), effect, duration, magnitude, source=self.entity)
				
				# Visual Feedback on Target
				vfx_hit = stageData.get("vfx_hit")
				if vfx_hit: MobaCommon.spawn_vfx(scene, vfx_hit, target.getTransform().worldPosition)

		elif effect == "EXECUTE_TRUE":
			cast_range = stageData.get("range", 10.0)
			target = MobaCommon.get_closest_target(self.transf.worldPosition, cast_range)
			if target:
				base_dmg = self.get_skill_value(key, "baseDamage", 50)
				# Calculate damage with True Damage and Execute multiplier
				t_pc = target.getPy("PlayerController")
				final = MobaCommon.calculate_damage(base_dmg, MobaCommon.DamageType.TRUE, attacker=self.entity, target_controller=t_pc)
				final = MobaCommon.apply_execute_multiplier(final, target.getProperties().get("health", 100), target.getProperties().get("maxHealth", 100))
				
				# Use standardized damage applicator
				# Phase 100: Set flag for Dredge's global gold share
				if self.heroName == "Dredge" and key == "R":
					self.last_kill_is_execute = True
					
				MobaCommon.apply_damage(target, final, MobaCommon.DamageType.TRUE, attacker=self.entity)
				pass
				
				# Visual Feedback on Target
				vfx_hit = stageData.get("vfx_hit")
				if vfx_hit: MobaCommon.spawn_vfx(scene, vfx_hit, target.getTransform().worldPosition)

		elif effect == "CONE_VOLLEY":
			MobaCommon.spawn_volley(self, stageData["count"], 45, stageData["range"])
			
		elif effect == "GRAB_PULL":
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData["range"])
			if target:
				MobaCommon.pull_target(target, self.transf.worldPosition)
				
		elif effect == "BLEED_PULL":
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData["range"])
			if target:
				# 1. Pull
				MobaCommon.pull_target(target, self.transf.worldPosition)
				# 2. Bleed
				MobaCommon.apply_dot_hero(target.getPy("PlayerController"), stageData["dps"], stageData["duration"], source=self.entity)
			
		elif effect == "BLEED":
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData.get("range", 7.0))
			if target:
				MobaCommon.apply_dot_hero(target.getPy("PlayerController"), stageData["dps"], stageData["duration"], source=self.entity)
			
		elif effect == "SCOUT_SHOT":
			# Utility Scout ability.
			MobaCommon.spawn_hawkshot(self)

		elif effect == "GROUNDED_ZONE":
			# Silvan's Nature Grasp: Slow + No Blink/Dash
			radius = stageData.get("radius", 6.0)
			duration = stageData.get("duration", 4.0)
			# Spawn a persistent trigger zone
			zone = scene.addFromTemplate("GroundZoneTemplate", self.transf.worldPosition)
			if zone:
				comp = zone.getPy("ZoneComponent")
				if comp:
					comp.setup(self.entity, radius, duration, effect_type="GROUNDED", slow=0.4)
				MobaCommon.spawn_vfx(scene, "VFX_Nature_Zone", self.transf.worldPosition, duration=duration)

		elif effect == "FROST_GUARD":
			# Composite: Shield + Resistances
			shield_val = stageData["value"]
			duration = stageData["duration"]
			self.applyEffect("SHIELD", duration, magnitude=shield_val)
			self.entity.getProperties()["shieldHP"] = shield_val
			
			# Add temporary armor boost (managed via status effect id check in update if needed, 
			# or just direct stat bump if we had a flat bonus list)
			# For now, we reuse the magnitude to represent the stat boost if we want.
			self.applyEffect("ARMOR_BOOST", duration, magnitude=stageData["armorBoost"])
			pass

		elif effect == "ICY_CHAINS":
			# Composite: Pull + Slow
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData["range"])
			if target:
				MobaCommon.pull_target(target, self.transf.worldPosition)
				MobaCommon.apply_cc(target.getPy("PlayerController"), "SLOW", stageData["slowDuration"], magnitude=0.4)
				pass
		
		elif effect == "BLINK":
			# Creative: Instant Teleport toward cursor
			out = scene.getDataOverMousePosition()
			if out.hit:
				target_pos = out.position
				current_pos = self.transf.worldPosition
				vec = target_pos - current_pos
				dist = vec.length()
				
				max_range = stageData.get("range", 10.0)
				clamped_dist = min(dist, max_range)
				final_pos = current_pos + (vec.normalized() * clamped_dist)
				
				# Geometry Safety: Maintain character's current Y height to prevent blinking into sky/terrain
				final_pos.y = current_pos.y
				
				# Teleport
				self.transf.setPosition(final_pos.x, final_pos.y, final_pos.z)
				pass

		elif effect == "PUSH_STUN":
			# Creative: Push enemies, stun on wall hit
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData["range"])
			if target:
				dir_push = (target.getTransform().worldPosition - self.transf.worldPosition).normalized()
				MobaCommon.push_target(target, dir_push, stageData.get("distance", 5.0))
				pass

		elif effect == "AURA_TOGGLE":
			# Refined: Uses the SUSTAINED_ZONE data-driven pattern
			# This allows older aura skills to benefit from the new persistent VFX/SFX system
			if key in self.activeToggles:
				data = self.activeToggles[key]
				if "vfx" in data: data["vfx"].kill()
				if "sfx" in data: data["sfx"].stop()
				del self.activeToggles[key]
			else:
				radius = self.get_skill_value(key, "radius", 5.0)
				dps = self.get_skill_value(key, "dps", 50.0)
				vfx_name = stageData.get("vfx_cast")
				sfx_name = stageData.get("sfx_cast")
				
				vfx = MobaCommon.spawn_vfx(scene, vfx_name, self.transf.worldPosition, duration=-1, parent=self.entity) if vfx_name else None
				sfx = MobaCommon.play_sfx(self.entity, sfx_name, loop=True) if sfx_name else None
				
				self.activeToggles[key] = {
					"radius": radius, "dps": dps, "vfx": vfx, "sfx": sfx, "timer": 0.0,
					"manaPerSec": stageData.get("manaPerSec", 10.0)
				}
				pass

		elif effect == "APPLY_MARK":
			# Creative: Mark a specific target
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData["range"])
			if target:
				t_pc = target.getPy("PlayerController")
				if t_pc:
					t_pc.applyEffect("Marked", stageData.get("duration", 6.0))
					pass

		elif effect == "DETONATE":
			# Damage all nearby marked targets on the enemy team
			scene = self.entity.getScene()
			enemyTag = "teamB" if self.entity.hasTag("teamA") else "teamA"
			targets = MobaCommon.EntityRegistry.get_active(enemyTag)
			
			dmg = self.get_skill_value(key, "damage", 100)
			cast_range = stageData.get("range", 12.0)
			
			for t in targets:
				if (t.getTransform().worldPosition - self.transf.worldPosition).length() <= cast_range:
					t_pc = t.getPy("PlayerController")
					if t_pc and t_pc.hasEffect("Marked"):
						# Apply damage
						final = MobaCommon.apply_damage(t, dmg, MobaCommon.DamageType.MAGIC, attacker=self.entity)
						
						# Visual Feedback on detonation
						vfx_hit = stageData.get("vfx_hit")
						if vfx_hit: MobaCommon.spawn_vfx(scene, vfx_hit, t.getTransform().worldPosition)
						
						t_pc.removeEffect("Marked") # Consume mark
			
			# Bonus: StormWeaver reset logic
			if self.heroName == "StormWeaver":
				self.cooldowns["Q"] = 0
				pass

		elif effect == "SUMMON_SENTRY":
			# Creative: Temporary AI turret
			template = stageData.get("template", self.heroData.get("sentryTemplate", "SentryTemplate"))
			sentry = scene.addFromTemplate(template, self.transf.worldPosition + self.transf.getForwardVector(True) * 3.0)
			if sentry:
				# Add team tag
				team = MobaCommon.get_entity_team(self.entity)
				sentry.addTag(team)
				sentry.getProperties()["team"] = team
				sentry.addTag("minion") # So it's not prioritized over heroes
				# Logic to self-destruct after duration
				sentry.getProperties()["lifetime"] = stageData.get("duration", 10.0)
				pass

		elif effect == "THUNDER_DASH":
			# Creative: Dash that resets if target is Marked
			target = MobaCommon.get_closest_target(self.transf.worldPosition, 6.0)
			if target:
				t_pc = target.getPy("PlayerController")
				if t_pc and t_pc.hasEffect("Marked"):
					self.cooldowns["W"] = 0 # Reset W instantly
					pass
			
			# Execute dash
			mouse_out = scene.getDataOverMousePosition()
			if mouse_out.hit:
				self.fsm.setState(MobaStates.DashState(mouse_out.position, speed=35.0, duration=0.3))

		elif effect == "TRANSFORM":
			# Creative: Switch form (data swap)
			new_form = stageData["targetHero"]
			hp_pct = self.entity.getProperties()["health"] / self.entity.getProperties()["maxHealth"]
			self.initializeHero(new_form)
			self.entity.getProperties()["health"] = self.entity.getProperties()["maxHealth"] * hp_pct
			
			# Bonus: Transformation Feedback
			MobaCommon.spawn_vfx(scene, stageData.get("vfx_hit"), self.transf.worldPosition)
			pass

		elif effect == "SUMMON_ENTITY":
			# Creative: Heimer Turret / Yorick Monster / King Ghouls
			out = scene.getDataOverMousePosition()
			if out.hit:
				template = stageData.get("template", self.heroData.get("summonTemplate", "SummonTemplate"))
				summon = scene.addFromTemplate(template, out.position)
				if summon:
					# Metadata for team and owner
					team = MobaCommon.get_entity_team(self.entity)
					summon.addTag(team)
					summon.getProperties()["owner"] = self.entity
					summon.getProperties()["team"] = team
					
					# Visual Feedback on Spawn
					vfx_hit = stageData.get("vfx_hit")
					if vfx_hit: MobaCommon.spawn_vfx(scene, vfx_hit, out.position)
					
					# Lifetime management
					dur = stageData.get("duration", 10.0)
					if dur > 0: summon.scheduleKill(dur)

		elif effect == "LINEAR_PROJECTILE":
			# Creative: Skillshot (Ezreal Q)
			out = scene.getDataOverMousePosition()
			if out.hit:
				dmg = self.get_skill_value(key, "damage", 100.0)
				speed = stageData.get("speed", 25.0)
				range_val = stageData.get("range", 20.0)
				p_type = stageData.get("projType", MobaCommon.ProjectileType.PHYSICAL)
				
				# Visual Context - Pull from hero-specific data if available
				template = stageData.get("template", self.heroData.get("projectileTemplate", MobaCommon.Templates.PROJ_BASIC))
				trail = stageData.get("vfx_trail")
				hit_vfx = stageData.get("vfx_hit", self.heroData.get("vfx_impact_standard"))
				
				MobaCommon.spawn_projectile(scene, self.entity, template, speed, dmg, range_val, p_type, trail=trail, hit_vfx=hit_vfx)

		elif effect == "SUMMON_WARD":
			# Creative: Place a vision ward
			out = scene.getDataOverMousePosition()
			if out.hit:
				template = stageData.get("template", self.heroData.get("wardTemplate", "WardTemplate"))
				ward = scene.addFromTemplate(template, out.position)
				if ward:
					team = MobaCommon.get_entity_team(self.entity)
					ward.addTag(team)
					ward.getProperties()["team"] = team
					ward_cmp = ward.getPy("WardComponent")
					if ward_cmp:
						ward_cmp.team = team
						# Ensure ward starts its lifecycle
						ward_cmp.start(scene)

		elif effect == "DEFLECT_PROJECTILE":
			# Creative: Physical or Magic deflection zone (Wind Wall / Samira W)
			duration = self.get_skill_value(key, "duration", 1.0)
			p_type = stageData.get("projType", MobaCommon.ProjectileType.BOTH)
			
			flags = MobaCommon.EffectFlags.NONE
			if p_type == MobaCommon.ProjectileType.PHYSICAL or p_type == MobaCommon.ProjectileType.BOTH:
				flags |= MobaCommon.EffectFlags.DEFLECT_PHYS
			if p_type == MobaCommon.ProjectileType.MAGICAL or p_type == MobaCommon.ProjectileType.BOTH:
				flags |= MobaCommon.EffectFlags.DEFLECT_MAGIC
				
			self.applyEffect("DEFLECTION", duration, flags=flags)
			
		elif effect == "STAT_MOD":
			# Temporary stat changes (Garen W armor or Berserker AD)
			duration = self.get_skill_value(key, "duration", 3.0)
			mods = stageData.get("modifiers", {}) # e.g. {"armor": 20, "ad": 30}
			self.applyEffect("STAT_MOD", duration, magnitude=mods)

		elif effect == "CREATE_WALL":
			# Creative: Spawn movement blocker
			out = scene.getDataOverMousePosition()
			if out.hit:
				template = stageData.get("template", self.heroData.get("wallTemplate", "WallTemplate"))
				wall = scene.addFromTemplate(template, out.position)
				if wall:
					wall.getProperties()["lifetime"] = stageData.get("duration", 5.0)
					wall.getProperties()["team"] = MobaCommon.get_entity_team(self.entity)

		elif effect == "GROUNDED_ZONE":
			# Creative: AoE that prevents dashes
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData["range"])
			if target:
				t_pc = target.getPy("PlayerController")
				if t_pc:
					MobaCommon.apply_cc(t_pc, "GROUNDED", stageData["duration"])
					pass

		elif effect == "ACTIVE_STEALTH":
			# Creative: Become untargetable and semi-transparent
			self.applyEffect("STEALTH", stageData["duration"], flags=MobaCommon.EffectFlags.UNTARGETABLE)
			pass

		elif effect == "DASH_STUN":
			# Bastian's E: Dash then Stun
			out = scene.getDataOverMousePosition()
			if out.hit:
				speed = stageData.get("speed", 30.0)
				duration = stageData.get("duration", 0.4)
				# Use a specialized DashState callback to stun on arrival
				stun_dur = stageData.get("stunDuration", 1.25)
				def on_hit_stun(target):
					MobaCommon.apply_cc(target, "STUN", stun_dur, source=self.entity)
					MobaCommon.spawn_vfx(scene, "VFX_Shield_Impact", target.getTransform().worldPosition)
				
				self.fsm.setState(MobaStates.DashState(out.position, speed=speed, duration=duration, onHitCallback=on_hit_stun))

		elif effect == "GROUNDED_AURA":
			# Thorne's R: Mobile suppression field
			radius = stageData.get("radius", 10.0)
			duration = stageData.get("duration", 6.5)
			# Pattern: Zone attached to caster via parentage
			zone = scene.addFromTemplate("GroundedZoneTemplate", self.transf.worldPosition)
			if zone:
				zone.setParent(self.entity)
				zone.getTransform().setPosition(0,0,0)
				comp = zone.getPy("ZoneComponent")
				if comp:
					comp.setup(self.entity, radius, duration, effect_type="GROUNDED")
				MobaCommon.spawn_vfx(scene, "VFX_Grounded_Ring", self.transf.worldPosition, duration=duration, parent=self.entity)

		elif effect == "SHIELD_TENACITY":
			# Thorne's W: Defense + CC resistance
			val = stageData.get("value", 100)
			dur = stageData.get("duration", 3.5)
			self.applyEffect("SHIELD", dur, magnitude=val)
			self.applyEffect("TENACITY", dur, magnitude=0.4) # +40% Tenacity

		elif effect == "DASH_KNOCKUP":
			# Thorne's E: Leap disruption
			out = scene.getDataOverMousePosition()
			if out.hit:
				speed = stageData.get("speed", 25.0)
				dur = stageData.get("duration", 0.4)
				rad = stageData.get("radius", 4.0)
				def on_land_impact(pos):
					MobaCommon.apply_circular_aoe(scene, pos, rad, 100, MobaCommon.DamageType.MAGIC, attacker=self.entity, cc_type="STUN", cc_dur=0.75)
					MobaCommon.spawn_vfx(scene, "VFX_Impact_Dust", pos)
					
				self.fsm.setState(MobaStates.DashState(out.position, speed=speed, duration=dur, onArrival=on_land_impact))

		elif effect == "STAT_STEAL":
			# Creative: Drain armor from target, grant to self
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData["range"])
			if target:
				amount = stageData["magnitude"]
				t_pc = target.getPy("PlayerController")
				if t_pc:
					t_pc.applyEffect("STEAL_PENALTY", stageData["duration"], magnitude=-amount)
					self.applyEffect("STEAL_BONUS", stageData["duration"], magnitude=amount)
					pass


		elif effect == "FEAR":
			# Creative: Targets run away for duration
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData["range"])
			if target:
				t_pc = target.getPy("PlayerController")
				if t_pc:
					MobaCommon.apply_cc(t_pc, "FEAR", stageData["duration"])
					# Visual Trigger
					vfx_hit = stageData.get("vfx_hit")
					if vfx_hit: MobaCommon.spawn_vfx(scene, vfx_hit, target.getTransform().worldPosition)

		elif effect == "BLEED_PULL":
			# Creative: Continuous damage + slight drag toward caster
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData["range"])
			if target:
				t_pc = target.getPy("PlayerController")
				if t_pc:
					self.applyEffect("BLEED", stageData["duration"], magnitude=stageData["dps"])
					# Drag logic would usually be in target's update or a status effect
					pass

		elif effect == "HP_SHIELD":
			# Simple flat shield
			val = self.get_skill_value(key, "value", 100)
			dur = stageData.get("duration", 3.0)
			self.applyEffect("SHIELD", dur, magnitude=val)
			self.entity.getProperties()["shieldHP"] = val

		elif effect == "INVULNERABLE":
			# Ultimate protection (Kayle/Taric R)
			dur = stageData.get("duration", 2.0)
			self.applyEffect("INVULNERABLE", dur, flags=MobaCommon.EffectFlags.INVULNERABLE)

		elif effect == "HEAL_PERCENT":
			# Heal based on max health
			pct = stageData.get("percent", 0.1)
			val = self.entity.getProperties()["maxHealth"] * pct
			self.entity.getProperties()["health"] = min(self.entity.getProperties()["maxHealth"], self.entity.getProperties()["health"] + val)
			# Floating Text
			if fct := self.entity.getPy("FloatingCombatTextComponent"):
				fct.setup(val, MobaCommon.DamageType.HEAL)

		elif effect == "DASH":
			# Creative: Smooth Dash toward cursor
			out = scene.getDataOverMousePosition()
			if out.hit:
				target_pos = out.position
				self.fsm.setState(MobaStates.DashState(target_pos, speed=stageData.get("speed", 30.0), duration=stageData.get("duration", 0.4)))
				pass
				
		elif effect == "RECT_SWEETSPOT":
			# Creative: Rectangle AoE with a 'Sweetspot' at the end (Aatrox Q)
			width = stageData.get("width", 4.0)
			length = stageData.get("length", 10.0)
			sweet_length = stageData.get("sweetLength", 2.0)
			
			# Logic: Box Check
			origin = self.transf.worldPosition
			forward = self.transf.getForwardVector(True)
			
			# Get all potential targets (allies of teamB if I'm teamA)
			enemyTag = "teamB" if self.entity.hasTag("teamA") else "teamA"
			potential = MobaCommon.EntityRegistry.get_active(enemyTag)
			
			base_dmg = self.get_skill_value(key, "damage", 100)
			bonus_dmg = self.get_skill_value(key, "bonusDamage", 150)
			
			for t in potential:
				t_pos = t.getTransform().worldPosition
				relative = t_pos - origin
				dist_fwd = relative.dot(forward)
				dist_side = abs(relative.dot(cave.math.Vector3(forward.z, 0, -forward.x))) # Perpendicular
				
				if 0 < dist_fwd < length and dist_side < width/2:
					# Impact!
					is_sweet = (length - dist_fwd) < sweet_length
					dmg = bonus_dmg if is_sweet else base_dmg
					
					dmg_type = stageData.get("damageType", MobaCommon.DamageType.PHYSICAL)
					MobaCommon.apply_damage(t, dmg, dmg_type, attacker=self.entity)
					
					# Visual Triggers
					vfx_hit = stageData.get("vfx_hit_sweet" if is_sweet else "vfx_hit", "VFX_Impact_Standard")
					MobaCommon.spawn_vfx(scene, vfx_hit, t_pos)
					
					if is_sweet: 
						t_pc = t.getPy("PlayerController")
						if t_pc: MobaCommon.apply_cc(t_pc, "STUN", 0.5)
					
			pass

		elif effect == "SUSTAINED_ZONE":
			# Toggle-based AoE (e.g. Anivia R / Fiddlesticks R relative to player)
			if key in self.activeToggles:
				# Deactivate
				data = self.activeToggles[key]
				if "vfx" in data and data["vfx"]: data["vfx"].kill()
				if "sfx" in data and data["sfx"]: data["sfx"].stop()
				del self.activeToggles[key]
				pass
			else:
				# Activate
				radius = self.get_skill_value(key, "radius", 5.0)
				dps = self.get_skill_value(key, "dps", 50.0)
				
				# Handle visuals via persistent tags
				vfx = None
				sfx = None
				vfx_name = stageData.get("vfx_cast")
				sfx_name = stageData.get("sfx_cast")
				
				if vfx_name:
					vfx = MobaCommon.spawn_vfx(scene, vfx_name, self.transf.worldPosition, duration=-1, parent=self.entity)
				if sfx_name:
					sfx = MobaCommon.play_sfx(self.entity, sfx_name, loop=True)
					
				self.activeToggles[key] = {
					"radius": radius,
					"dps": dps,
					"vfx": vfx,
					"sfx": sfx,
					"timer": 0.0 # For pulsing
				}
				pass

		elif effect == "HEAL_TARGET":
			# Heal closest ally hero within range
			ally_tag = "teamA" if self.entity.hasTag("teamA") else "teamB"
			allies = MobaCommon.EntityRegistry.get_active(ally_tag)
			best_ally = None
			best_dist = stageData.get("range", 8.0)
			for a in allies:
				if a == self.entity: continue
				d = (a.getTransform().worldPosition - self.transf.worldPosition).length()
				if d < best_dist:
					best_dist = d
					best_ally = a
			if best_ally:
				val = self.get_skill_value(key, "value", 100)
				MobaCommon.apply_heal(best_ally, val, source=self.entity)
				pass
			else:
				# Self-heal fallback
				val = self.get_skill_value(key, "value", 100)
				self.entity.getProperties()["health"] = min(self.entity.getProperties()["maxHealth"], self.entity.getProperties()["health"] + val)
			sfx = stageData.get("sfx")
			if sfx: MobaCommon.play_sfx(self.entity, sfx)

		elif effect == "SHIELD_TARGET":
			# Shield closest ally hero within range
			ally_tag = "teamA" if self.entity.hasTag("teamA") else "teamB"
			allies = MobaCommon.EntityRegistry.get_active(ally_tag)
			best_ally = None
			best_dist = stageData.get("range", 8.0)
			for a in allies:
				if a == self.entity: continue
				d = (a.getTransform().worldPosition - self.transf.worldPosition).length()
				if d < best_dist:
					best_dist = d
					best_ally = a
			target_ent = best_ally if best_ally else self.entity
			val = self.get_skill_value(key, "value", 100)
			dur = self.get_skill_value(key, "duration", 4.0)
			t_pc = target_ent.getPy("PlayerController")
			if t_pc:
				t_pc.applyEffect("SHIELD", dur, magnitude=val)
				target_ent.getProperties()["shieldHP"] = val
				pass
			sfx = stageData.get("sfx")
			if sfx: MobaCommon.play_sfx(self.entity, sfx)

		elif effect == "AOE_CC":
			# Apply CC to all enemies in radius
			cc_type = stageData.get("ccType", "STUN")
			radius = stageData.get("radius", 5.0)
			cc_dur = self.get_skill_value(key, "duration", 1.0)
			mag = stageData.get("magnitude", 0.0)
			enemy_tag = "teamB" if self.entity.hasTag("teamA") else "teamA"
			targets = MobaCommon.EntityRegistry.get_active(enemy_tag)
			for t in targets:
				if (t.getTransform().worldPosition - self.transf.worldPosition).length() <= radius:
					t_pc = t.getPy("PlayerController")
					if t_pc:
						MobaCommon.apply_cc(t_pc, cc_type, cc_dur, mag, source=self.entity)
			sfx = stageData.get("sfx")
			if sfx: MobaCommon.play_sfx(self.entity, sfx)
			pass

		elif effect == "SPIN_DAMAGE":
			# Sustained melee AoE (Garen E style) — uses channel state
			dps = self.get_skill_value(key, "dps", 50)
			duration = self.get_skill_value(key, "duration", 3.0)
			spin_range = stageData.get("range", 3.5)
			enemy_tag = "teamB" if self.entity.hasTag("teamA") else "teamA"
			# Apply immediate tick and set up as channel
			targets = MobaCommon.EntityRegistry.get_active(enemy_tag)
			for t in targets:
				if (t.getTransform().worldPosition - self.transf.worldPosition).length() <= spin_range:
					armor = t.getProperties().get("armor", 0)
					t_pc = t.getPy("PlayerController")
					MobaCommon.apply_damage(t, dps, MobaCommon.DamageType.MAGIC, attacker=self.entity)
			# Set up as a channel so it ticks over time
			self.fsm.setState(MobaStates.ChannelState(key, duration))
			sfx = stageData.get("sfx")
			if sfx: MobaCommon.play_sfx(self.entity, sfx)
			pass

		elif effect == "DAMAGE_REDUCTION":
			# Percentage damage reduction self-buff
			reduction = self.get_skill_value(key, "reduction", 0.3)
			duration = self.get_skill_value(key, "duration", 3.0)
			self.applyEffect("DAMAGE_REDUCTION", duration, magnitude=reduction)
			# Also apply bonus mods if specified

		elif effect == "MARK_DASH":
			# Dash to a marked target (reset mechanic)
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData.get("range", 8.0))
			if target:
				t_pc = target.getPy("PlayerController")
				if t_pc and t_pc.hasEffect("Marked"):
					self.fsm.setState(MobaStates.DashState(target.getTransform().worldPosition, speed=stageData.get("speed", 40.0), duration=0.25))
					self.cooldowns[key].set(999) # Cave API: SceneTimer.set()
				else:
					self.fsm.setState(MobaStates.DashState(target.getTransform().worldPosition, speed=stageData.get("speed", 40.0), duration=0.25))

		elif effect == "EXECUTE_CONSUME":
			# Darius R: Bonus damage per stack, consume stacks, reset CD on kill
			stack_name = stageData.get("stackName", "hemorrhage")
			base_dmg = self.get_skill_value(key, "baseDamage", 100)
			per_stack = self.get_skill_value(key, "perStack", 20)
			is_true = stageData.get("trueDamage", True)
			target_range = stageData.get("range", 3.0)
			
			target = MobaCommon.get_closest_target(self.transf.worldPosition, target_range)
			if target:
				stacks = self.getStacksOn(target, stack_name)
				final_dmg = base_dmg + (per_stack * stacks)
				
				dmg_type = MobaCommon.DamageType.TRUE if is_true else MobaCommon.DamageType.PHYSICAL
				MobaCommon.apply_damage(target, final_dmg, dmg_type, attacker=self.entity)
				
				# Consume stacks
				stack_key = f"{stack_name}_{self.entity.name}"
				target.getProperties()[stack_key] = 0
				
				# Reset on kill
				if target.getProperties().get("health", 0) <= 0:
					self.cooldowns[key].set(999)  # Cave API: SceneTimer.set()
			
			sfx = stageData.get("sfx")
			if sfx: MobaCommon.play_sfx(self.entity, sfx)

		elif effect == "EMPOWERED_AA":
			# Buff the next auto-attack (Garen Q, Nasus Q, Rengar Q)
			bonus = self.get_skill_value(key, "bonusDamage", 30)
			duration = self.get_skill_value(key, "duration", 6.0)
			
			# Build empowered AA data
			self.empoweredAA = {
				"bonusDamage": bonus,
				"trueDamage": stageData.get("trueDamage", False),
				"aaReset": stageData.get("aaReset", True),
				"cc": stageData.get("cc"),  # e.g. {"type": "SILENCE", "duration": 1.5}
			}
			
			# Schedule auto-expiry if not used in time
			self.empoweredAATimer = duration
			
			# Optional: grant speed boost while empowered (Garen Q)
			speed_boost = stageData.get("speedBoost")
			if speed_boost:
				self.applyEffect("MS_BOOST", duration, magnitude=speed_boost)
			
			# AA RESET: If player is currently in AttackState, reset the timers
			if self.fsm.state and isinstance(self.fsm.state, MobaStates.AttackState):
				self.fsm.state.startup = 0
				self.fsm.state.recovery = 0
			
			sfx = stageData.get("sfx")
			if sfx: MobaCommon.play_sfx(self.entity, sfx)
		
		elif effect == "BOOMERANG_PROJECTILE":
			# Projectile goes out, then returns (Ahri Q, Sivir Q, Gnar Q)
			out = scene.getDataOverMousePosition()
			if not out.hit: return
			
			target_pos = out.position
			speed = stageData.get("speed", 25.0)
			max_range = stageData.get("range", 12.0)
			
			# Calculate direction and clamped target
			direction = (target_pos - self.transf.worldPosition).normalized()
			width = stageData.get("width", 2.0)
			
			# Define missing damage variables from stageData
			out_dmg = self.get_skill_value(key, "outDamage", 50.0)
			ret_dmg = self.get_skill_value(key, "returnDamage", 50.0)
			out_type = stageData.get("outDamageType", MobaCommon.DamageType.MAGIC)
			ret_type = stageData.get("returnDamageType", MobaCommon.DamageType.TRUE)
			
			template = "BoomerangTemplate"
			# Logic Fix: Use the mouse-derived 'direction' for the boomerang path, not just entity forward
			clamped_pos = self.transf.worldPosition + direction * stageData.get("range", 12.0)
			
			proj = scene.addFromTemplate(template, self.transf.worldPosition)
			if proj:
				proj.getProperties()["owner"] = self.entity
				proj.getProperties()["targetPos"] = clamped_pos
				proj.getProperties()["speed"] = speed
				proj.getProperties()["outDamage"] = out_dmg
				proj.getProperties()["outDamageType"] = out_type
				proj.getProperties()["returnDamage"] = ret_dmg
				proj.getProperties()["returnDamageType"] = ret_type
				proj.getProperties()["width"] = width
				proj.getProperties()["team"] = "teamA" if self.entity.hasTag("teamA") else "teamB"
				proj.getProperties()["phase"] = "outgoing"  # "outgoing" or "returning"
				proj.scheduleKill(4.0)  # Safety cleanup
			
			if sfx := stageData.get("sfx"): MobaCommon.play_sfx(self.entity, sfx)

		elif effect == "HEAL":
			# Heal self (flat + scaled by level)
			val = self.get_skill_value(key, "value", 100)
			self.entity.getProperties()["health"] = min(self.entity.getProperties()["maxHealth"], self.entity.getProperties()["health"] + val)
			sfx = stageData.get("sfx")
			if fct := self.entity.getPy("FloatingCombatTextComponent"): # Show healing number
				fct.setup(val, MobaCommon.DamageType.HEAL)
			if sfx: MobaCommon.play_sfx(self.entity, sfx)

		elif effect == "SMITE":
			# Phase 125: Evolved Smite Logic
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData.get("range", 6.0))
			is_evolved = self.jungleStacks >= 40
			
			if target:
				is_monster = target.getProperties().get("isJungle") or target.hasTag("minion")
				if is_monster:
					damage = 1200 if is_evolved else (600 + (self.level - 1) * 35)
					MobaCommon.apply_damage(target, damage, MobaCommon.DamageType.TRUE, attacker=self.entity)
					# Update stacks
					if target.getProperties().get("isJungle"): self.jungleStacks += 1
				elif is_evolved and target.hasTag("player"):
					# Evolved Smite can target champions: 100 true dmg + 2s Slow
					MobaCommon.apply_damage(target, 100, MobaCommon.DamageType.TRUE, attacker=self.entity)
					MobaCommon.apply_cc(target.getPy("PlayerController"), "SLOW", 2.0, magnitude=0.20)
				
				heal_val = 90 + (self.entity.getProperties()["maxHealth"] * 0.1)
				MobaCommon.apply_heal(self.entity, heal_val, source=self.entity)
				if sfx := stageData.get("sfx"): MobaCommon.play_sfx(self.entity, sfx)

		elif effect == "RECALL":
			# 8-second channel, teleports to Fountain on finish
			# Usually called by stage finishing logic in AbilityState
			scene = self.entity.getScene()
			team = "teamA" if self.entity.hasTag("teamA") else "teamB"
			fountain = MobaCommon.EntityRegistry.get(team + "_fountain")
			if fountain:
				fnt_pos = fountain[0].getTransform().worldPosition
				self.transf.setPosition(fnt_pos.x, fnt_pos.y, fnt_pos.z)
			else:
				# Fallback to origin
				self.transf.setPosition(0, 0, 0)
		elif effect == "DASH_STRIKE":
			# Kage Q: Dash towards mouse and hit closest enemy
			out = scene.getDataOverMousePosition()
			if out.hit:
				self.fsm.setState(MobaStates.DashState(out.position, speed=stageData.get("speed", 35.0), duration=0.3))
				# Actual damage logic triggered at end of state or here (instant for proto)
				target = MobaCommon.get_closest_target(self.transf.worldPosition, 4.0, attacker=self.entity)
				if target:
					val = self.get_skill_value(key, "damage", 100)
					MobaCommon.apply_damage(target, val, MobaCommon.DamageType.PHYSICAL, attacker=self.entity)

		elif effect == "BLINK_EXECUTE":
			# Kage R: Blink and execute target
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData.get("range", 7.0), attacker=self.entity)
			if target:
				# Teleport behind target
				t_pos = target.getTransform().worldPosition
				fwd = target.getTransform().getForwardVector(True)
				self.transf.setPosition(t_pos.x - fwd.x * 1.5, t_pos.y, t_pos.z - fwd.z * 1.5)
				# Deal execute damage
				damage = self.get_skill_value(key, "damage", 300)
				MobaCommon.apply_damage(target, damage, MobaCommon.DamageType.TRUE, attacker=self.entity)
				MobaCommon.spawn_vfx(scene, "VFX_Shadow_Execute", t_pos)

		elif effect == "ACTIVE_STEALTH":
			# Kage W / Dredge E / Umbra Q / Zora E: Camouflage + MoveSpeed
			duration = self.get_skill_value(key, "duration", 2.5)
			ms_boost = self.get_skill_value(key, "msBoost", 0.3)
			# UNTARGETABLE prevents clicks, CAMOUFLAGE handles visuals/bars.
			self.applyEffect("CAMOUFLAGE", duration, flags=MobaCommon.EffectFlags.UNTARGETABLE | MobaCommon.EffectFlags.CAMOUFLAGE, magnitude=ms_boost)
			MobaCommon.spawn_vfx(scene, "VFX_Shadow_Camouflage", self.transf.worldPosition, duration=duration, parent=self.entity)

		elif effect == "SUMMON_OBJECT":
			# Aether Q: Conduit setup
			out = scene.getDataOverMousePosition()
			if out.hit:
				obj = scene.addFromTemplate(stageData["template"], out.position)
				if obj:
					self.conduits.append(obj)
					# Keep max 2
					if len(self.conduits) > stageData.get("maxCount", 2):
						old = self.conduits.pop(0)
						old.scheduleKill(0.1)
					MobaCommon.spawn_vfx(scene, "VFX_Arcane_Conduit_Spawn", out.position)

		elif effect == "PULL_TO_OBJECTS":
			# Aether E: Pull enemies toward all active conduits
			for obj in self.conduits:
				if not obj.isActive(): continue
				targets = MobaCommon.get_entities_in_radius(scene, obj.getTransform().worldPosition, stageData.get("range", 8.0))
				for t in targets:
					if MobaCommon.get_entity_team(t) != MobaCommon.get_entity_team(self.entity):
						MobaCommon.pull_target(t, obj.getTransform().worldPosition)

		elif effect == "OBJECT_EXPLOSION":
			# Aether R: All conduits explode
			val = self.get_skill_value(key, "damage", 250)
			for obj in self.conduits:
				if not obj.isActive(): continue
				MobaCommon.apply_circular_aoe(obj.getTransform().worldPosition, 6.5, val, MobaCommon.DamageType.MAGIC, attacker=self.entity)
				MobaCommon.spawn_vfx(scene, "VFX_Arcane_Detonation", obj.getTransform().worldPosition)
				obj.scheduleKill(0.1)
			self.conduits = []

		elif effect == "GLOBAL_DASH":
			# Icarus R: Low-collision terrain flight
			out = scene.getDataOverMousePosition()
			if out.hit:
				target_pos = out.position
				# Clamp to semi-global 65.0 range
				diff = target_pos - self.transf.worldPosition
				if diff.length() > stageData.get("range", 65.0):
					target_pos = self.transf.worldPosition + diff.normalized() * 65.0
				
				self.is_flying = True
				self.fsm.setState(MobaStates.DashState(target_pos, speed=stageData.get("speed", 55.0), duration=1.2))
				# On impact (approx 1.2s later) deal dmg
				MobaCommon.apply_circular_aoe(target_pos, 5.0, self.get_skill_value(key, "damage", 200), MobaCommon.DamageType.MAGIC, attacker=self.entity)

		elif effect == "LINEAR_BEAM":
			# Nova Q: Instant beam
			out = scene.getDataOverMousePosition()
			if out.hit:
				dir = (out.position - self.transf.worldPosition).normalized()
				end_pos = self.transf.worldPosition + dir * stageData["range"]
				# Beam scan logic: hits all enemies in line
				enemies = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, stageData["range"])
				for e in enemies:
					if MobaCommon.get_entity_team(e) != MobaCommon.get_entity_team(self.entity):
						# Distance to line segment check (simplified)
						dist = MobaCommon.dist_to_segment(e.getTransform().worldPosition, self.transf.worldPosition, end_pos)
						if dist < 2.0:
							MobaCommon.apply_damage(e, self.get_skill_value(key, "damage", 100), MobaCommon.DamageType.MAGIC, attacker=self.entity)
				MobaCommon.spawn_vfx(scene, "VFX_Nova_Beam", self.transf.worldPosition)

		elif effect == "ORBITAL_SHIELD":
			# Nova W: Defensive orbit
			val = self.get_skill_value(key, "damagePerSec", 40)
			dur = stageData["duration"]
			self.applyEffect("SHIELD", dur, magnitude=100) # Quick shield
			# Spawn personal zone
			zone = scene.addFromTemplate("GroundZoneTemplate", self.transf.worldPosition)
			if zone:
				comp = zone.getPy("ZoneComponent")
				comp.setup(self.entity, 4.5, dur, effect_type="DAMAGE", dps=val)
				zone.setParent(self.entity) # Keep orbiting

		elif effect == "GLOBAL_AOE":
			# Nova R: Semi-global bombardment
			out = scene.getDataOverMousePosition()
			if out.hit:
				target_pos = out.position
				# Delay logic (pseudo-projectile)
				MobaCommon.spawn_delayed_aoe(scene, target_pos, 7.5, self.get_skill_value(key, "damage", 300), delay=1.5, vfx="VFX_Nova_Supernova")

		elif effect == "TETHER_DRAIN":
			# Vex W: Life drain tether
			target = MobaCommon.get_closest_target(self.transf.worldPosition, stageData["range"], attacker=self.entity)
			if target:
				dps = self.get_skill_value(key, "dps", 50)
				dur = stageData["duration"]
				t_pc = target.getPy("PlayerController")
				if t_pc:
					t_pc.applyEffect("TETHERED", dur, magnitude=dps, source=self.entity)
					MobaCommon.spawn_vfx(scene, "VFX_Soul_Tether", self.transf.worldPosition, duration=dur)

		elif effect == "BLINK_DECOY":
			# Vex E: Blink and leave shadow
			out = scene.getDataOverMousePosition()
			if out.hit:
				old_pos = self.transf.worldPosition
				self.transf.setPosition(out.position.x, out.position.y, out.position.z)
				# Spawn decoy
				decoy = scene.addFromTemplate("VexDecoyTemplate", old_pos)
				if decoy: decoy.scheduleKill(stageData.get("duration", 1.5))

		elif effect == "AOE_DRAIN":
			# Vex R: Massive soul feast
			rad = stageData["radius"]
			dmg = self.get_skill_value(key, "damage", 200)
			targets = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, rad)
			total_healed = 0
			for t in targets:
				if MobaCommon.get_entity_team(t) != MobaCommon.get_entity_team(self.entity):
					dealt = MobaCommon.apply_damage(t, dmg, MobaCommon.DamageType.MAGIC, attacker=self.entity)
					total_healed += dealt * stageData.get("healPercent", 0.5)
			MobaCommon.apply_heal(self.entity, total_healed, source=self.entity)

		else:
			# Phase 42: Dispatcher Warning for unknown effects
			print(f"WARNING: Unknown effect tag '{effect}' in {key} execution.")
		
		# 4. Dispatch Command to State Machine if blocking
		if stageData.get("isChannel"):
			self.fsm.setState(MobaStates.ChannelState(key, stageData.get("channelTime", 1.0)))
		elif stageData.get("isBlocking"):
			self.inputBuffer = ("CAST", key)
			self.bufferTimer = self.INPUT_BUFFER_TIME

	def applyEffect(self, effect_id, duration, flags=0, magnitude=0, source=None, dmg_type=None):
		"""Apply a status effect to this hero, respecting tenacity."""
		tenacity = self.entity.getProperties().get("tenacity", 0)
		isAirborne = (flags & MobaCommon.EffectFlags.STUN) != 0
		final_duration = duration if isAirborne else duration * (1 - tenacity)
		
		# Phase 73: MISSION CRITICAL - Interface with Engine-level EffectComponent
		if self.eff_comp:
			# This handles the internal status list and combined_flags automatically
			# Phase 77 FIX: Pass dmg_type if provided, else MAGIC
			final_type = dmg_type if dmg_type is not None else MobaCommon.DamageType.MAGIC
			self.eff_comp.apply(effect_id, final_duration, magnitude=magnitude, flags=flags, source=source, dmg_type=final_type)
			# Sync back
			self.activeEffects = list(self.eff_comp.active_effects.values())
			self.flags = self.eff_comp.combined_flags
			MobaCommon.refresh_stats(self.entity)
			return
		
		# Fallback for systems that haven't fully transitioned to EffectComponent
		
		# --- Stacking Rules ---
		# Effects that always REFRESH (only one instance at a time):
		#   CC (STUN, ROOT, etc.), self-buffs (SHIELD, DAMAGE_REDUCTION, ARMOR_BOOST, MS_BOOST)
		# Effects that STACK PER SOURCE (multiple instances if different attackers):
		#   DoTs (BLEED), debuffs (SLOW, CRIPPLE, STEAL_PENALTY, SHRED)
		
		REFRESH_ONLY = {"STUN", "ROOT", "SILENCE", "KNOCKUP", "KNOCKBACK", "CHARM", "FEAR",
						"SHIELD", "DAMAGE_REDUCTION", "ARMOR_BOOST", "MS_BOOST", "STAT_MOD",
						"STEALTH", "UNTARGETABLE"}
		
		if effect_id in REFRESH_ONLY:
			# Refresh: only one instance, take longest duration / strongest magnitude
			for eff in self.activeEffects:
				if eff.id == effect_id:
					eff.duration = max(eff.duration, final_duration)
					if magnitude > eff.magnitude:
						eff.magnitude = magnitude
					return
		else:
			# Stack per source: same source refreshes, different sources stack
			for eff in self.activeEffects:
				if eff.id == effect_id and eff.source is source and source is not None:
					# Same source reapplied → refresh duration, update magnitude
					eff.duration = max(eff.duration, final_duration)
					eff.magnitude = magnitude
					return
			# Different source or first application → add new instance
		
		new_eff = MobaCommon.StatusEffect(effect_id, final_duration, flags, magnitude, source)
		self.activeEffects.append(new_eff)
		
		# Trigger forced movement states for Charm/Fear
		if flags & MobaCommon.EffectFlags.CHARM:
			self.fsm.setState(MobaStates.ForcedMovementState(source, toward=True))
		elif flags & MobaCommon.EffectFlags.FEAR:
			self.fsm.setState(MobaStates.ForcedMovementState(source, toward=False))
			
		# Stat-Mod Refresh
		if effect_id in ["ARMOR_BOOST", "MS_BOOST", "STAT_MOD", "SHRED", "STEAL_PENALTY", "BARON_BUFF"]:
			self.recalculate_stats()

	def hasEffect(self, effect_id: str) -> bool:
		for eff in self.activeEffects:
			if eff.id == effect_id: return True
		return False

	def removeEffect(self, effect_id: str):
		self.activeEffects = [eff for eff in self.activeEffects if eff.id != effect_id]


	def update(self):
		if not self.entity or not self.entity.isActive(): return
		dt = cave.getDeltaTime()
		scene = self.entity.getScene()

		# --- Phase 116: Camera Lock ---
		if getattr(self, "cameraLocked", False) and getattr(self, "camera_pivot", None):
			p_pos = self.transf.worldPosition
			self.camera_pivot.getTransform().setPosition(p_pos.x, 0, p_pos.z)
		
		from Core import MobaCommon
		
		# Phase 73: Sync Flags and ActiveEffects from Engine to Controller
		if self.eff_comp:
			self.flags = self.eff_comp.combined_flags
			self.activeEffects = list(self.eff_comp.active_effects.values())
		
		# --- Phase 117: Soft Collision ---
		MobaCommon.resolve_unit_overlap(self.entity, radius=1.0)

		# --- Phase 117: Death Screen & Respawn Logic ---
		if self.respawnTimer > 0:
			self.respawnTimer -= dt
			# Apply grayscale to camera if this is the local player
			if self.entity.hasTag("local_player"):
				cam = scene.getCamera()
				if cam:
					# Standard Cave post-process override
					cam.exposure.value = 0.5 # Dim the screen
					# Ideally we have a post-process shader with 'u_grayscale'
			
			if self.respawnTimer <= 0:
				self.respawn()
			return # Don't update while dead
		else:
			# Reset camera exposure when alive
			if self.entity.hasTag("local_player"):
				cam = scene.getCamera()
				if cam: cam.exposure.value = 1.0

		# Phase 38: Soft-Pause logic
		if MobaCommon.is_match_over:
			# Stop movement and abort logic
			if self.character: 
				# Optimization: Only set if moving
				if self.character.isMoving():
					self.character.setWalkDirection(0, 0, 0)
			return

		scene = self.entity.getScene()
		events = cave.getEvents()

		# --- Wave 76: Systemic Active Item Usage (Keys 1-6) ---
		# Mapping: 1, 2, 3 -> Slot 0, 1, 2 | 4 -> Trinket | 5, 6 -> Slot 3, 4
		key_map = {
			cave.event.KEY_1: 0, cave.event.KEY_2: 1, cave.event.KEY_3: 2,
			cave.event.KEY_4: 6, # Trinket Slot
			cave.event.KEY_5: 3, cave.event.KEY_6: 4
		}
		for key, slot_idx in key_map.items():
			if events.pressed(key):
				self.inventory_mgr.trigger_active(slot_idx)

		# Phase 131: Ctrl+QWER Skill Leveling (Feature 9)
		if self.leveling.skillPoints > 0:
			ctrl = events.active(cave.event.KEY_LCTRL) or events.active(cave.event.KEY_RCTRL)  # Cave API: active() not isDown()
			if ctrl:
				skill_keys = {"Q": cave.event.KEY_Q, "W": cave.event.KEY_W, "E": cave.event.KEY_E, "R": cave.event.KEY_R}
				for sk, kc in skill_keys.items():
					if events.pressed(kc):
						max_lvl = 3 if sk == "R" else 5
						if self.skillLevels.get(sk, 0) < max_lvl:
							# R requires hero level 6/11/16
							if sk == "R" and self.leveling.level < (6 + self.skillLevels.get("R", 0) * 5):
								continue
							self.skillLevels[sk] = self.skillLevels.get(sk, 0) + 1
							self.leveling.skillPoints -= 1
							MobaUI.spawn_fct(scene, self.transf.worldPosition, f"{sk} LEVELED!", cave.Vector4(1, 0.9, 0.2, 1))
							break
		
		# Phase 115: Summoner Spell Cooldown Tick
		if hasattr(self, 'summoner_spell_mgr') and self.summoner_spell_mgr:
			self.summoner_spell_mgr.update(dt)

		# ── Wave 76: Stasis Tint Cleanup ─────────────────────────────
		if self.flags & MobaCommon.EffectFlags.INVULNERABLE:
			# If we have stasis flag, we assume tint is applied. 
			# In a real game, we'd check for a specific 'stasis' effect ID.
			pass
		else:
			# Reset tint if not in stasis (simple approach for prototype)
			if self.mesh:
				mesh_comp = self.mesh.get("Mesh")
				if mesh_comp:
					mat = mesh_comp.getFinalMaterial()
					if mat and mat.uniforms.get("u_baseColor") != cave.Vector4(1,1,1,1):
						mat.uniforms.set("u_baseColor", cave.Vector4(1, 1, 1, 1))

		self.update_vision_tick(dt)
		
		# Phase 100: Support Quest Tick
		if MobaCommon.GameTick.is_tick_frame() and MobaCommon.GameTick._current_tick % 10 == 0:
			self.inventory_mgr.update_support_quest()
			
		# Phase 100: Ward Recharge
		if self.wardCharges < self.wardMaxCharges:
			if self.wardChargeTimer.get() >= 120.0: # 2 min recharge
				self.wardCharges += 1
				self.wardChargeTimer.reset()

		# Phase 125: Jungle Pet Passives
		if self.junglePetType:
			if self.junglePetType == "MOSSTOMPER":
				# Shield after 10s out of combat
				if (scene.getElapsedSceneTime() - self.lastCombatTime) >= 10.0 and not self.hasEffect("JUNGLE_SHIELD"):
					self.applyEffect("JUNGLE_SHIELD", 999, magnitude=150)
			elif self.junglePetType == "GUSTWALKER":
				# MS in brush or river
				is_in_brush = self.entity.getProperties().get("in_brush_id") is not None
				if is_in_brush or MobaCommon.VisionManager.is_in_river(scene, self.transf.worldPosition):
					self.applyEffect("GUSTWALKER_SPEED", 1.0, magnitude=1.15)
					
		# Phase 100: Vento Aura Pulse (Every 1s)
		if self.heroName == "Vento" and MobaCommon.GameTick.is_tick_frame() and MobaCommon.GameTick._current_tick % 20 == 0:
			# Apply Buff to nearby allies
			team = self.entity.getProperties().get("team")
			allies = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, 10.0)
			for a in allies:
				if a.hasTag("player") and a.hasTag(team):
					a_pc = a.getPy("PlayerController")
					if a_pc:
						if self.vento_aura == 0: # Speed
							a_pc.applyEffect("VENTO_SPEED", 1.5, magnitude=35.0)
							MobaCommon.spawn_vfx(scene, "VFX_Vento_SpeedTrail", a.getTransform().worldPosition, duration=0.8)
						else: # Vitality (Regen)
							MobaCommon.apply_heal(a, 10 + (self.leveling.level * 2), source=self.entity)
							MobaCommon.spawn_vfx(scene, "VFX_Vento_HealSpark", a.getTransform().worldPosition, duration=0.8)

		# Environmental Damage & Cheats (Legacy Logic Restoration)
		if cave.hasEditor():
			if events.active(cave.event.KEY_C):
				self.entity.getProperties()["health"] -= 1
			if events.active(cave.event.KEY_V):
				self.entity.getProperties()["health"] += 1

		# Losing Health (Environmental Damage)
		cooldownTime = self.damageCooldown.get()
		if cooldownTime > self.damageCooldownTime and self.character.collidedWith("damage"):
			self.trigger_damage_blink()
			MobaCommon.apply_damage(self.entity, 25, MobaCommon.DamageType.PHYSICAL, attacker=None)

		# Portal / Level Completion Check
		nextLevelColl = self.character.getCollisionsWith("portal")
		if len(nextLevelColl) > 0:
			nextLevelName = nextLevelColl[0].entity.getParent().getProperties().get("scene", "")
			if nextLevelName != "":
				levelComplete = self.entity.getChild("Level Complete")
				if levelComplete:
					scene.paused = True
					levelComplete.activate(scene)
				else:
					cave.setScene(nextLevelName)
			
		if self.isRecalling:
			self.recallTimer -= dt
			if self.recallTimer <= 0:
				self.finishRecall()
				
		# Phase 30: ARAM Aura & Logic
		if self.isARAM:
			# 1. Shop Locking (Permanent once you exit Fountain)
			if not self.shopLocked:
				dist_to_spawn = (self.transf.worldPosition - self.spawnPoint).length()
				if dist_to_spawn > 20.0: # Exited base
					self.shopLocked = True

			if self.snowballMarkTimer <= 0:
				self.snowballMarkedTarget = None

		# Phase 74: Universal Passive Income & Regeneration System
		if not MobaCommon.is_match_over:
			self.passiveGoldTimer -= dt
			if self.passiveGoldTimer <= 0:
				self.passiveGoldTimer = 1.0 # Every 1s
				self.leveling.gold += 1.8 # Standard income (ARAM adds more below)
				if self.isARAM: self.leveling.gold += 2.2 

			# Phase 100: Ticking Logic (Hero Passives)
			# Guard: Only update if hero is alive and match is active
			if hasattr(self, "passive_mgr"):
				self.passive_mgr.update(dt)
			self.add_exp(1.5)
			
			# Regen Tick (Scale with Regen stats)
			props = self.entity.getProperties()
			hp_r = props.get("hpRegen", 1.5) / 5.0 # per 1s
			mp_r = props.get("manaRegen", 1.0) / 5.0 # per 1s
			
			if props["health"] < props["maxHealth"]:
				props["health"] = min(props["maxHealth"], props["health"] + hp_r)
			if self.mana < self.maxMana:
				self.mana = min(self.maxMana, self.mana + mp_r)

		# Phase 100: Resurrection Timer
		if hasattr(self, "resurrection_timer") and self.resurrection_timer > 0:
			self.resurrection_timer -= dt
			if self.resurrection_timer <= 0:
				max_hp = self.entity.getProperties().get("maxHealth", 100)
				self.entity.getProperties()["health"] = max_hp * 0.5
				self.mana = self.maxMana * 0.5
				MobaCommon.spawn_vfx(scene, "VFX_GA_Rise", self.transf.worldPosition)
				MobaCommon.play_sfx(self.entity, "SFX_GA_Rise")
				del self.resurrection_timer

		# Phase 101: Item Passive Tick (Hullbreaker/Shojin/etc)
		if MobaCommon.GameTick.is_tick_frame() and MobaCommon.GameTick._current_tick % 20 == 0:
			MobaItems.ItemEffectManager.process_tick_passives(self, dt)

		# Phase 30: Spectator Camera while dead
		if self.respawnTimer > 0:
			self.spectateAllyUpdate(dt)

		self.processInput()
		
		# ============================
		# PHASE 101: CAMOUFLAGE VISUALS (GLASS SHADE + UI SUPPRESSION)
		# ============================
		if self.flags & MobaCommon.EffectFlags.CAMOUFLAGE:
			if self.mesh:
				mesh_instance = self.mesh.get("Mesh")
				if mesh_instance:
					mat = mesh_instance.getFinalMaterial()
					if mat:
						# Tint to ghostly glass (Alpha 0.25)
						mat.uniforms.set("u_baseColor", cave.Vector4(0.7, 0.8, 1.0, 0.25))
			
			# Suppress UI Bars
			if self.lifeBarUI: self.lifeBarUI.visible = False
			if self.shadowBarUI: self.shadowBarUI.visible = False
		else:
			# Restore UI if was hidden by camouflage
			if self.lifeBarUI and not self.lifeBarUI.visible:
				self.lifeBarUI.visible = True
				if self.shadowBarUI: self.shadowBarUI.visible = True
				# u_baseColor restore handled by the Stasis Tint Cleanup block above
				
		# ============================
		# 1. TICK STATUS EFFECTS (modifies stats + sets flags)
		# ============================
		# Baseline resets every frame to prevent flat stat leak (Phase 17 Fix)
		# Phase 69 OPTIMIZATION: recalculate_stats is now EVENT-DRIVEN.
		# Do NOT call it every frame.
		
		# Reset frame-based multipliers
		self.entity.getProperties()["msMultiplier"] = 1.0 
		self.entity.getProperties()["asMultiplier"] = 1.0
		self.entity.getProperties()["damageReduction"] = 0.0
		# Phase 74 FIX: REMOVED self.flags = 0 (This was wiping engine state every frame)
		expired = []
		
		# Apply non-stacking base reductions (e.g. general slows)
		# stacking logic is handled within the effect tick loop
		passive_slow = 0.0
		for eff in self.activeEffects:
			if eff.flags & MobaCommon.EffectFlags.SLOW:
				passive_slow = max(passive_slow, eff.magnitude)
		self.entity.getProperties()["msMultiplier"] *= (1.0 - passive_slow)

		for eff in self.activeEffects:
			if eff.tick(dt):
				expired.append(eff)
			else:
				self.flags |= eff.flags
				# Apply modifiers
				if eff.id == "MS_BOOST":
					self.entity.getProperties()["msMultiplier"] *= eff.magnitude
				elif eff.id == "ARMOR_BOOST":
					self.entity.getProperties()["armor"] += eff.magnitude
				elif eff.id == "DAMAGE_REDUCTION":
					self.entity.getProperties()["damageReduction"] = max(self.entity.getProperties()["damageReduction"], eff.magnitude)
				elif eff.id == "CRIPPLE":
					self.entity.getProperties()["asMultiplier"] *= (1.0 - eff.magnitude)
				elif eff.id == "STAT_MOD":
					if isinstance(eff.magnitude, dict):
						for prop, val in eff.magnitude.items():
							if prop in self.entity.getProperties():
								self.entity.getProperties()[prop] += val
				elif eff.flags & MobaCommon.EffectFlags.BLEED:
					# Systemic Bleed (Phase 20 Fix): Uses apply_damage with CONTINUOUS flag to trigger shields but suppress FX spam
					MobaCommon.apply_damage(self.entity, eff.magnitude * dt, MobaCommon.DamageType.TRUE, attacker=eff.source, flags=MobaCommon.EffectFlags.CONTINUOUS)

		for e in expired:
			self.activeEffects.remove(e)


		# ============================
		# 2. SYNC PROPERTIES (Instant result for UI/FSM)
		# ============================
		self.entity.getProperties()["moveSpeed"] = self.speed * self.entity.getProperties()["msMultiplier"]
		self.entity.getProperties()["attackSpeed"] = self.totalAS * self.entity.getProperties().get("asMultiplier", 1.0)

		# CC Hard-Stop (Align with Cave Physics)
		if self.flags & (MobaCommon.EffectFlags.STUN | MobaCommon.EffectFlags.ROOT):
			if hasattr(self.character, "setWalkDirection"):
				self.character.setWalkDirection(0, 0, 0)

		# 3. Cooldowns
		for k in list(self.item_cooldowns.keys()):
			if self.item_cooldowns[k] > 0:
				self.item_cooldowns[k] -= dt
			else:
				del self.item_cooldowns[k]

		# Death's Dance Bleed (Linear 3-second tick-down)
		if self.deferred_damage > 0:
			# Standard LoL: 1/3 of the amount per second.
			bleed_tick = (self.deferred_damage / 3.0) * dt
			if bleed_tick > self.deferred_damage: bleed_tick = self.deferred_damage
			
			MobaCommon.apply_damage(self.entity, bleed_tick, MobaCommon.DamageType.TRUE, attacker=None, flags=MobaCommon.EffectFlags.CONTINUOUS)
			self.deferred_damage -= bleed_tick

		for k in self.cooldowns:
			# skillStageTimers still using dt for simplicity as they are short-lived
			if self.skillStageTimers[k] > 0:
				self.skillStageTimers[k] -= dt
				if self.skillStageTimers[k] <= 0:
					self.skillStages[k] = 0 # Reset stage on timeout
					# Start full cooldown since player didn't finish the combo
					ability = self.abilities.get(k)
					if ability and ability.get("stages"):
						self.cooldownDurations[k] = self.get_skill_value(k, "cd", 10.0)
						self.cooldowns[k].reset()
						pass
			
		# Empowered AA expiry
		if self.empoweredAA and self.empoweredAATimer > 0:
			self.empoweredAATimer -= dt
			if self.empoweredAATimer <= 0:
				self.empoweredAA = None
				pass

		# Visuals: Handle Stealth Transparency
		if self.mesh:
			mesh_cmp = self.mesh.get("Mesh")
			if mesh_cmp:
				if self.flags & MobaCommon.EffectFlags.UNTARGETABLE:
					mesh_cmp.tint = cave.Vector4(1, 1, 1, 0.3) # Semi-transparent
				else:
					mesh_cmp.tint = cave.Vector4(1, 1, 1, 1.0) # Opaque
					
		# Visual Effects & Invisibility (True Sight bypass)
		if self.mesh:
			is_stealthed = self.hasEffect("STEALTH")
			is_revealed = self.flags & MobaCommon.EffectFlags.REVEALED
			# Mesh is hidden if stealthed AND NOT revealed
			if is_stealthed and not is_revealed:
				self.mesh.deactivate(scene)
			else:
				self.mesh.activate(scene)
		
		# Shield expiry check
		shieldHP = self.entity.getProperties().get("shieldHP", 0)
		if shieldHP > 0 and not self.hasEffect("SHIELD"):
			self.entity.getProperties()["shieldHP"] = 0
		
		# ============================
		# 3. HP & MANA REGENERATION
		# ============================
		maxHP = self.entity.getProperties().get("maxHealth", 1)
		currentHP = self.entity.getProperties().get("health", 0)
		
		# HP Regen (uses 'recovery' stat from MobaCommon.apply_heal)
		growth = self.heroData.get("growthStats", {})
		base_regen = self.baseStats.get("recovery", 0) + (growth.get("recovery", 0) * (self.level - 1))
		if currentHP < maxHP and currentHP > 0:
			MobaCommon.apply_heal(self.entity, base_regen * dt)
		
		# Mana Regen (Phase 23: Deterministic pulse via GameTick)
		# Phase 31: Mana Regen Pulse
		if MobaCommon.GameTick.is_tick_frame():
			# 1. Base Regen
			regen_per_tick = self.manaRegen * 0.1
			self.mana = min(self.maxMana, self.mana + regen_per_tick)
			
			# 2. Jungle/River Recovery (Monster Hunter bonus)
			if hasattr(self, "inventory_mgr") and self.inventory_mgr.has_item_effect("onTick", "JUNGLE_HUNTER"):
				# Check if in Jungle/River
				pos = self.transf.worldPosition
				# Simplified: Zone check (assuming map bounds or tags provide 'in_jungle')
				if self.entity.getProperties().get("in_jungle", False) or abs(pos.x) < 8: 
					# Scaled Regen: (4.0/6.0 base + level growth) divided by 10 for 0.1s tick
					lvl = self.level
					h_regen = (4.0 + (0.5 * lvl)) * 0.1
					m_regen = (6.0 + (0.4 * lvl)) * 0.1
					
					self.mana = min(self.maxMana, self.mana + m_regen)
					curr_hp = self.entity.getProperties().get("health", 0)
					self.entity.getProperties()["health"] = min(self.maxHP, curr_hp + h_regen)
					
			self.entity.getProperties()["mana"] = self.mana # Sync for HUD

		# --- ITEM TICK PASSIVES (Sunfire, Moonstone, etc) ---
		MobaItems.ItemEffectManager.process_on_tick(self, dt)
		# --- DEFERRED ITEM ACTIVES (Redemption drop, etc) ---
		MobaItems.ItemEffectManager.tick_pending_actives(self, dt)

		# --- UI/Indicator Cancellation Logic (Phase 43 Restored) ---
		is_cced = self.flags & (MobaCommon.EffectFlags.STUN | MobaCommon.EffectFlags.SILENCE)
		is_dead = self.entity.getProperties().get("health", 0) <= 0
		
		if is_cced or is_dead:
			# Cancel active indicators and range on death/CC
			if hasattr(self, "rangeActive") and (self.rangeActive or self.activeCastKey):
				self.rangeActive = False
				self.activeCastKey = None
				self.indicator.hide()

		if is_dead:
			# Cleanup persistent toggles on death (Phase 22 Fix)
			for key in list(self.activeToggles.keys()):
				data = self.activeToggles[key]
				if data.get("vfx"): data["vfx"].kill()
				if data.get("sfx"): data["sfx"].stop()
				del self.activeToggles[key]

		# ============================
		# 4. TOGGLE ABILITIES (mana drain + persistent effects)
		# ============================
		drain_total = 0
		to_remove = []
		for key, toggle_data in self.activeToggles.items():
			# Mana drain calculation
			mana_per_sec = toggle_data.get("manaPerSec", 15.0)
			drain_total += mana_per_sec
			
			# Pulse Logic (usually 0.5s or 1s intervals)
			toggle_data["timer"] += dt
			if toggle_data["timer"] >= 1.0:
				toggle_data["timer"] = 0
				
				radius = toggle_data.get("radius", 5.0)
				dps = toggle_data.get("dps", 50.0)
				
				# Determine center (stationary pivot or follow player)
				center = self.transf.worldPosition
				if "pivot" in toggle_data:
					center = toggle_data["pivot"]
					# Check leash
					if (self.transf.worldPosition - center).length() > toggle_data.get("leash", 20.0):
						to_remove.append(key)
						continue
				
				# Apply AoE
				MobaCommon.apply_circular_aoe(scene, center, radius, dps, MobaCommon.DamageType.MAGIC, attacker=self.entity)

		for r in to_remove:
			if r in self.activeToggles:
				data = self.activeToggles[r]
				if "vfx" in data and data["vfx"]: data["vfx"].kill()
				if "sfx" in data and data["sfx"]: data["sfx"].stop()
				del self.activeToggles[r]

		if drain_total > 0:
			if self.mana < drain_total * dt:
				# Force Deactivate All on mana empty
				for key in list(self.activeToggles.keys()):
					data = self.activeToggles[key]
					try:
						if "vfx" in data and data["vfx"]: data["vfx"].kill()
						if "sfx" in data and data["sfx"]: data["sfx"].stop()
					except: pass
				self.activeToggles.clear()
			else:
				self.mana -= drain_total * dt
				self.entity.getProperties()["mana"] = self.mana # Sync for HUD


		# Phase 101: Smite Execute Indicator
		if MobaCommon.GameTick.is_tick_frame() and MobaCommon.GameTick._current_tick % 10 == 0:
			smite_dmg = (900 if getattr(self, "large_monsters_killed", 0) >= 20 else 600) + (self.level * 40)
			monsters = MobaCommon.get_entities_in_radius(scene, self.transf.worldPosition, 12.0)
			for m in monsters:
				if m.hasTag("monster"):
					hp = m.getProperties().get("health", 0)
					m.getProperties()["isSmiteable"] = (hp > 0 and hp <= smite_dmg)
			
		# ============================
		# 7. RUN STATE MACHINE
		# ============================
		self.fsm.run()
		
		# Channeled Skill Ticking moved to MobaStates.ChannelState (Wave 62)

		# ============================
		# 8. DEFLECTOR TAG
		# ============================
		if self.flags & (MobaCommon.EffectFlags.DEFLECT_PHYS | MobaCommon.EffectFlags.DEFLECT_MAGICAL):
			if not self.entity.hasTag("deflector"):
				self.entity.addTag("deflector")
		else:
			if self.entity.hasTag("deflector"):
				self.entity.removeTag("deflector")
		
		# 9. Professional Passive Logic
		# Passive update moved to update() for unified state guard

		if self.entity.getProperties()["health"] <= 0:
			# TRIGGER DEATH / REWARDS
			contributors = self.entity.getProperties().get("contributions", {})
			killer = self.entity.getProperties().get("lastAttacker", None)  # FIX: was undefined
			MobaCommon.RewardManager.distribute(self.entity, killer)
			
			# Phase 122: Bounty Reset and HUD update
			if self.entity.hasTag("local_player"):
				MobaUI.broadcast_event(f"SHUT DOWN! {killer.name if killer else 'Execution'}")
			
			# Phase 100: Systematic state purge on death
			MobaCommon.cleanup_entity_state(self.entity)
			
			# Respawn Deadlock Fix: Do not deactivate entity (which stops updates). 
			# Instead, hide visuals and disable collision.
			self.respawnTimer = MobaCommon.get_respawn_timer(self.level, self.entity.getScene().getElapsedSceneTime())
			self.entity.getProperties()["contributions"] = {}
			
			if self.mesh: self.mesh.deactivate(self.entity.getScene())
			if self.character: self.character.disable()
			# Phase 57 Hardening: Move to fountain during death instead of a 'void'
			# This keeps the camera at base while waiting to respawn.
			self.transf.setPosition(self.spawnPoint.x, self.spawnPoint.y, self.spawnPoint.z) 
			
			pass

	def respawn(self):
		"""Restores the hero at the fountain."""
		if self.mesh: self.mesh.activate(self.entity.getScene())
		if self.character: self.character.enable()
		
		self.transf.setPosition(self.spawnPoint.x, self.spawnPoint.y, self.spawnPoint.z)
		self.mana = self.maxMana
		self.entity.getProperties()["health"] = self.maxHP
		self.entity.getProperties()["mana"] = self.maxMana
		# Reset FSM to idle
		self.fsm = SimpleFSM(MobaStates.IdleState())
		self.fsm.bind(self)
		
		# ARAM Rule: Reset shop lock on respawn
		if self.isARAM:
			self.shopLocked = False
			
		pass

	def spectateAllyUpdate(self, dt):
		"""Phase 30: Centers camera on a living teammate while dead."""
		scene = self.entity.getScene()
		teamTag = "teamA" if self.entity.hasTag("teamA") else "teamB"
		allies = [e for e in MobaCommon.EntityRegistry.get_team_entities(teamTag, "player") if e != self.entity and e.getProperties().get("health", 0) > 0]
		
		if allies:
			# Focus on the first living ally
			self.track_camera_to(allies[0])

	def executeSnowball(self, key):
		"""Phase 30: ARAM Summoner 'Snowball' (Mark & Dash)."""
		# If target is already marked, Dash to them
		if self.snowballMarkedTarget and self.snowballMarkedTarget.isActive():
			self.dashToMarked()
			return

		# Otherwise, Fire the Mark
		scene = self.entity.getScene()
		out = scene.getDataOverMousePosition()
		if not out.hit: return
		
		target_pos = out.position
		dir = (target_pos - self.transf.worldPosition).normalized()
		
		# Spawn Projectile
		spawn_pos = self.transf.worldPosition + cave.Vector3(0, 1.5, 0)
		proj = scene.addFromTemplate(MobaCommon.Templates.PROJ_BASIC, spawn_pos)
		if proj:
			comp = proj.add("HomingProjectileComponent") # We'll hijack homing or use linear
			# For ARAM Snowball we want Skillshot (Linear)
			# But for simplicity let's use the registry logic
			MobaCommon.spawn_homing_projectile(scene, self.entity, None, MobaCommon.Templates.PROJ_BASIC, 35.0, 50, hit_vfx=MobaCommon.Templates.SFX_SNOWBALL)
			# We'll need a custom projectile component for linear skillshots
			# For now, let's pretend it hits and marks the first enemy.
			pass

	def dashToMarked(self):
		"""Second cast of Snowball."""
		target = self.snowballMarkedTarget
		if not target or not target.isActive(): return
		
		pass
		# Use the Procedural Sliding pattern from earlier
		self.fsm.setState(MobaStates.DashState(target.getTransform().worldPosition, 0.4))
		
		# Cleanup mark
		self.snowballMarkedTarget = None
		self.snowballMarkTimer = 0

	def executeTrinket(self):
		"""Phase 123: Vision Control routing."""
		if not hasattr(self, "inventory") or len(self.inventory) <= 6: return
		
		trinket_item = self.inventory[6]
		data = ItemRegistry.ITEM_REGISTRY.get(trinket_item)
		if not data: return
		
		active_id = data.get("active_id")
		if active_id:
			# Check Cooldown in InventoryManager (Slot 6)
			if not self.inventory_mgr.has_cooldown(active_id):
				MobaItems.ItemEffectManager.process_active(self, active_id)
				self.inventory_mgr.set_cooldown(active_id, data.get("active_cd", 120.0))

	def executeRecall(self):
		"""Phase 28: Start 8-second channel to return to base."""
		if self.isRecalling: return
		
		# ARAM Constraint (Phase 30)
		if self.isARAM:
			pass
			MobaUI.broadcast_event("Battle has no return!")
			return

		# Interruption: Cannot recall if CC'd
		if self.flags & (MobaCommon.EffectFlags.STUN | MobaCommon.EffectFlags.SILENCE):
			pass
			return
			
		self.isRecalling = True
		# Phase 118: Empowered Recall (Baron Buff)
		self.recallTimer = 4.0 if self.hasEffect("BARON_BUFF") else 8.0
		self.flags |= MobaCommon.EffectFlags.RECALLING
		
		# Visuals & Sound
		MobaCommon.play_sfx(self.entity, MobaCommon.Templates.SFX_RECALL_START)
		self.recallVFX = MobaCommon.spawn_vfx(
			self.entity.getScene(), 
			MobaCommon.Templates.VFX_RECALL, 
			self.transf.worldPosition, 
			duration=-1, # Persistent until cancelled
			parent=self.entity
		)
		pass

	def cancelRecall(self, reason="Interrupted"):
		"""Cancels current recall channel."""
		if not self.isRecalling: return
		
		self.isRecalling = False
		self.recallTimer = 0
		self.flags &= ~MobaCommon.EffectFlags.RECALLING
		
		if self.recallVFX:
			self.recallVFX.kill()
			self.recallVFX = None
			
		pass

	def finishRecall(self):
		"""Completes recall and teleports to fountain."""
		self.isRecalling = False
		self.flags &= ~MobaCommon.EffectFlags.RECALLING
		
		if self.recallVFX:
			self.recallVFX.kill()
			self.recallVFX = None
			
		# Teleport to spawn
		self.transf.setPosition(self.spawnPoint.x, self.spawnPoint.y, self.spawnPoint.z)
		MobaCommon.play_sfx(self.entity, MobaCommon.Templates.SFX_RECALL_FINISH)
		
		# Full Heal on arrival
		self.entity.getProperties()["health"] = self.entity.getProperties()["maxHealth"]
		self.mana = self.maxMana
		
		pass

	def trigger_damage_blink(self):
		"""Systemic trigger for the red damage flash (Phase 20)."""
		self.damageCooldown.reset()
		if self.mesh:
			mesh_cmp = self.mesh.get("Mesh")
			if mesh_cmp:
				mesh_cmp.tint = cave.Vector4(1, 0, 0, 1) # Flash Red
				# Reset tint is handled by the stealth/untargetable logic later in update or via a timer
				# For immediate feedback, we just set it and let recalculate/re-render handle the fade back
	
	def update_shadow_bar(self, shadow_val):
		"""Phase 35: Smoothly updates the white delay-drop bar."""
		if not self.shadowBarUI: return
		max_hp = self.entity.getProperties().get("maxHealth", 100)
		self.shadowBarUI.scale.setRelativeX(shadow_val / max_hp)

	def trigger_resurrection(self):
		"""Phase 100: Standard Guardian Angel / Resurrection sequence."""
		# Set CD (5 minutes)
		self.set_cooldown("Guardian Angel", 300.0)
		
		# 1. Apply 3.0s Stasis (Invulnerable + Untargetable + Stunned)
		self.applyEffect("RESURRECTION_STASIS", 3.0, 
			flags=MobaCommon.EffectFlags.INVULNERABLE | MobaCommon.EffectFlags.UNTARGETABLE | MobaCommon.EffectFlags.STUN
		)
		
		# 2. Visuals & Sounds (Golden shell VFX)
		MobaCommon.spawn_vfx(self.entity.getScene(), "VFX_GA_Indicator", self.transf.worldPosition, duration=3.0, parent=self.entity)
		MobaCommon.play_sfx(self.entity, "SFX_GA_Activate")
		
		# 3. Schedule final heal after stasis ends
		if not hasattr(self, "_pending_actives"): self._pending_actives = []
		def _ga_restore():
			# Restore 50% Max HP
			max_hp = self.entity.getProperties().get("maxHealth", 1000)
			self.entity.getProperties()["health"] = max_hp * 0.5
			MobaCommon.spawn_vfx(self.entity.getScene(), "VFX_GA_Burst", self.transf.worldPosition, duration=1.0)
			MobaUI.broadcast_event(f"{self.entity.name} has returned to the fray!")
			
		self._pending_actives.append({"fn": _ga_restore, "timer": 3.0})

	def end(self, scene: cave.Scene):
		# Phase 70: Removed destructive GameTick.reset()
		# Individual units must NOT wipe global state on death/removal.
		pass
