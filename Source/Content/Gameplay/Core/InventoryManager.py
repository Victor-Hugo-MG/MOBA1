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

	def has_item_effect(self, event_type, effect_id):
		"""Phase 100: Forward check to ItemEffectManager."""
		from Core import MobaItems
		return MobaItems.ItemEffectManager.has_item_effect(self.pc, event_type, effect_id)

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
