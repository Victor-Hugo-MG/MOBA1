import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon
from Data import HeroRegistry
import json
import random
import os

class MatchmakingManager(cave.Component):
	"""Simulates a matchmaking queue and 'Match Found' sequence."""
	def start(self, scene):
		self.timer = 0.0
		self.is_searching = False
		self.match_found = False
		self.search_ui = self.entity.getChild("Search_Panel")
		self.found_ui = self.entity.getChild("Found_Panel")
		
		if self.search_ui: self.search_ui.deactivate(scene)
		if self.found_ui: self.found_ui.deactivate(scene)

	def start_search(self):
		scene = self.entity.getScene()
		self.is_searching = True
		self.timer = 0.0
		if self.search_ui: self.search_ui.activate(scene)
		# MobaCommon.play_sfx(self.entity, "SFX_Menu_Click")

	def update(self):
		if not self.is_searching or self.match_found: return
		
		scene = self.entity.getScene()
		dt = cave.getDeltaTime()
		self.timer += dt
		
		# Fake 'Match Found' after 2-6 seconds
		if self.timer > random.uniform(2.0, 6.0):
			self.match_found = True
			if self.search_ui: self.search_ui.deactivate(scene)
			if self.found_ui: self.found_ui.activate(scene)
			MobaCommon.play_sfx(self.entity, "SFX_Match_Found")

	def on_accept(self):
		"""Transition to Lobby scene."""
		try:
			cave.setScene("Lobby_MatchConfig")
		except:
			pass

class LobbyController(cave.Component):
	"""Manages the UI for champion selection and ARAM game setup."""
	def start(self, scene):
		# Initial State
		cave.getGlobalDict()["IsARAM"] = True
		# Phase 42: Use validated HeroRegistry key
		cave.getGlobalDict()["SelectedHero"] = "Ironclad"
		
	def on_select_hero(self, hero_id):
		"""Called by UI buttons for hero selection."""
		if hero_id in HeroRegistry.HERO_REGISTRY:
			cave.getGlobalDict()["SelectedHero"] = hero_id
		
	def on_start_match(self):
		"""Called by the Start Button."""
		# Load the ARAM Bridge scene
		try:
			cave.setScene("ARAM_Bridge")
		except:
			pass

class RandomizeButton(cave.Component):
	"""The 'All Random' button for ARAM."""
	def on_click(self):
		# Phase 42: Dynamic Pool from Registry
		heroes = list(HeroRegistry.HERO_REGISTRY.keys())
		import random
		selection = random.choice(heroes)
		
		lobby = self.entity.getScene().get("LobbyController").getPy("LobbyController")
		if lobby:
			lobby.on_select_hero(selection)
			# SFX for rolling
			# MobaCommon.play_sfx(self.entity, "SFX_Reroll")

class MainMenuController(cave.Component):
	"""Handles transitions from the legal/splash screens to the initial profile check."""
	def on_click_start(self):
		try:
			cave.setScene("Initial")
		except:
			pass

class ProfileController(cave.Component):
	"""Handles first-launch profile creation and landing logic."""
	def start(self, scene):
		profile = MobaCommon.load_data("profile.json")
		if profile:
			# Successfully loaded profile, head home
			self.populate_ui(scene, profile)
			# If we are in the Initial scene, auto-redirect to Home
			if scene.name == "Initial":
				try:
					cave.setScene("Home_Page")
				except:
					pass
		else:
			# No profile found, show the creation panel in the Initial scene
			panel = scene.get("Profile_Setup_Panel")
			if panel: panel.activate(scene)

	def save_profile(self, name, icon_id):
		data = {"name": name, "icon": icon_id}
		MobaCommon.save_data("profile.json", data)
		try:
			cave.setScene("Home_Page")
		except:
			pass

	def populate_ui(self, scene, profile):
		"""Updates profile widgets on current scene."""
		name_lbl = scene.get("Label_PlayerName")
		if name_lbl: name_lbl.get("UIElement").setText(profile.get("name", "Player"))
		# Icon logic would go here if we had sprite mapping

class HomeNavigationController(cave.Component):
	"""Central hub for navigation from the Home Page."""
	def on_goto_play(self):
		try:
			cave.setScene("Lobby_MatchConfig")
		except:
			pass
		
	def on_goto_heroes(self):
		try:
			cave.setScene("Gallery_Heroes")
		except:
			pass
		
	def on_goto_runes(self):
		try:
			cave.setScene("Gallery_Runes")
		except:
			pass
		
	def on_goto_history(self):
		try:
			cave.setScene("Profile_History")
		except:
			pass

	def on_exit_game(self):
		# Standard Cave quit logic if available, otherwise just print
		print("Exiting Game...")

class AdvancedLobbyController(cave.Component):
	"""Phase 110: Full Draft Lobby — Hero, Spell, and Rune selection with countdown."""
	def start(self, scene):
		self.countdown = 60.0
		self.slots = {
			"player": {
				"hero": "Ironclad", "pos": "MID", "skin": "base",
				"rune": "LETHAL_TEMPO", "spellD": "Flash", "spellF": "Ignite"
			},
			"enemy1": {
				"hero": "Random", "pos": "MID", "skin": "base",
				"rune": "CONQUEROR", "spellD": "Flash", "spellF": "Smite"
			},
		}
		# Phase 55: Persistent Selection
		last_hero = cave.getGlobalDict().get("SelectedHero", "Ironclad")
		self.slots["player"]["hero"] = last_hero

		self.is_locked = False
		self.timer_text = self.entity.getChild("Timer_Text")
		
		# Phase 119: Draft States
		self.draft_state = "PICKING"
		self.banned_heroes = []

	def update(self):
		if self.is_locked:
			return
		dt = cave.getDeltaTime()
		self.countdown -= dt
		
		# Update Timer UI
		if self.timer_text:
			ui = self.timer_text.get("UIElement")
			if ui: ui.setText(f"{int(max(0, self.countdown))}s")
			
		# Auto-lock if time runs out
		if self.countdown <= 0:
			self.is_locked = True
			self.start_match()

	def calculate_resonance_synergy(self):
		"""Phase 119: Bonus for picking thematic team comps."""
		counts = {}
		for slot in self.slots.values():
			h_id = slot.get("hero")
			h_data = HeroRegistry.HERO_REGISTRY.get(h_id)
			if h_data:
				fac = h_data.get("faction")
				counts[fac] = counts.get(fac, 0) + 1
		
		for fac, count in counts.items():
			if count >= 3: return fac
		return None

	def lock_in(self):
		"""Called by 'Lock In' button."""
		self.is_locked = True
		synergy = self.calculate_resonance_synergy()
		if synergy:
			MobaCommon.play_sfx(self.entity, "SFX_Resonance_Sync")
			print(f"Team has {synergy} Resonance Synergy!")
		
		# Transition to Loading (Setting state for orchestrator)
		cave.getGlobalDict()["MatchSetup_State"] = "LOADING"
		self.start_match()

	# --- Player Selection API ---
	def set_hero(self, hero_id):
		if hero_id in HeroRegistry.HERO_REGISTRY:
			self.slots["player"]["hero"] = hero_id

	def set_spell(self, slot_key, spell_id):
		"""slot_key is 'D' or 'F'."""
		from Core import SummonerSpells
		if spell_id in SummonerSpells.SPELL_REGISTRY:
			self.slots["player"][f"spell{slot_key}"] = spell_id

	def set_rune(self, rune_id):
		from Data import RuneRegistry
		if RuneRegistry.get_rune_data(rune_id):
			self.slots["player"]["rune"] = rune_id

	# --- Bot Management ---
	def add_bot(self, team="B"):
		"""Adds a bot to team A (allies, max 4) or team B (enemies, max 5)."""
		hero_pool = list(HeroRegistry.HERO_REGISTRY.keys())
		h_id = random.choice(hero_pool)
		if team == "A":
			for i in range(1, 5):
				key = f"ally{i}"
				if key not in self.slots:
					self.slots[key] = {"hero": h_id, "pos": "MID", "spellD": "Flash", "spellF": "Ignite"}
					return key
		else:
			for i in range(1, 6):
				key = f"enemy{i}"
				if key not in self.slots:
					self.slots[key] = {"hero": h_id, "pos": "MID", "spellD": "Flash", "spellF": "Smite"}
					return key
		return None

	def remove_bot(self, slot_id):
		if slot_id in self.slots and slot_id != "player":
			del self.slots[slot_id]
			return True
		return False

	# --- Match Launch ---
	def start_match(self):
		cave.getGlobalDict()["MatchSetup"] = json.dumps(self.slots)
		try:
			cave.setScene("ARAM_Bridge")
		except:
			pass

class MatchOrchestrator(cave.Component):
	"""Handles the dynamic spawning of all heroes and bots at match start."""
	def start(self, scene):
		import json
		from Data import HeroRegistry
		import random
		
		# 1. Load Setup Data
		setup_str = cave.getGlobalDict().get("MatchSetup")
		setup_data = {"player": {"hero": "Ironclad", "pos": "MID"}}
		if setup_str:
			try: setup_data = json.loads(setup_str)
			except: pass
			
		# 2. Find Spawn Points
		all_spawn_points = {}
		# Fallback Defaults (ARAM-style Bridge setup)
		fallback_a = [cave.Vector3(-45, 0, 0), cave.Vector3(-45, 0, 2), cave.Vector3(-45, 0, -2), cave.Vector3(-47, 0, 1), cave.Vector3(-47, 0, -1)]
		fallback_b = [cave.Vector3(45, 0, 0), cave.Vector3(45, 0, 2), cave.Vector3(45, 0, -2), cave.Vector3(47, 0, 1), cave.Vector3(47, 0, -1)]
		
		for team in ["teamA", "teamB"]:
			for i in range(1, 6):
				tag = f"Spawn_{team}_{i}"
				pts = scene.getEntitiesWithTag(tag)
				if pts: 
					all_spawn_points[tag] = pts[0].getTransform().worldPosition
				else:
					# Assign fallback based on team and index
					f_list = fallback_a if team == "teamA" else fallback_b
					all_spawn_points[tag] = f_list[i-1]
		
		# 3. Spawn Entities
		spawn_index_a = 1
		spawn_index_b = 1
		ally_keys = sorted([k for k in setup_data.keys() if "player" in k or "ally" in k])
		enemy_keys = sorted([k for k in setup_data.keys() if "enemy" in k])
		
		for slot_id in ally_keys + enemy_keys:
			config = setup_data[slot_id]
			from Data import SkinRegistry
			from Data import RuneRegistry
			hero_id = config.get("hero", "Ironclad")
			if hero_id == "Random":
				hero_id = random.choice(list(HeroRegistry.HERO_REGISTRY.keys()))
				
			hero_data = HeroRegistry.HERO_REGISTRY.get(hero_id)
			if not hero_data: continue
			
			team = "teamA" if "player" in slot_id or "ally" in slot_id else "teamB"
			idx = spawn_index_a if team == "teamA" else spawn_index_b
			spawn_tag = f"Spawn_{team}_{idx}"
			pos = all_spawn_points.get(spawn_tag, cave.Vector3(0,0,0))
			
			if team == "teamA": spawn_index_a += 1
			else: spawn_index_b += 1
			
			# Spawn Using Template logic
			template = hero_data.get("template", "HeroTemplate")
			hero_ent = scene.addFromTemplate(template, pos)
			if hero_ent:
				hero_ent.addTag(team)
				hero_ent.addTag("player")
				hero_ent.addTag("enemy" if team == "teamB" else "ally")
				
				pc = hero_ent.add("PlayerController")
				pc.heroData = hero_data
				pc.rune_id = config.get("rune", "LETHAL_TEMPO") # Phase 102
				
				# Initialize Summoner Spells (Phase 105)
				from Core import SummonerSpells
				spellD = config.get("spellD", "Flash")
				spellF = config.get("spellF", "Ignite")
				pc.summoner_spell_mgr = SummonerSpells.SummonerSpellManager(pc, spellD, spellF)
				
				if slot_id == "player":
					cave.getGlobalDict()["CurrentPlayer"] = hero_ent.name
				else:
					ai = hero_ent.add("HeroAIComponent")
					ai.team = team
			
		# 4. Global Init (Phase 70: Centralized here to prevent actor-race)
		MobaCommon.is_match_over = False
		MobaCommon.VisionManager.reset()
		MobaCommon.GameTick.reset()
		MobaCommon.MatchStatsManager.init(scene)

class MatchOverController(cave.Component):
	"""Handles transition from match end to results and back to Home."""
	def on_continue(self):
		"""Saves results and returns to Main Menu."""
		scene = self.entity.getScene()
		
		# 1. Final Sync of Items (Phase 55 Expansion)
		heroes = scene.getEntitiesWithTag("player")
		for h in heroes:
			pc = h.getPy("PlayerController")
			if pc and hasattr(pc, "inventory_mgr"):
				MobaCommon.MatchStatsManager.track_items(h.name, pc.inventory_mgr.items)
		
		# 2. Build Summary
		winner = cave.getGlobalDict().get("WinnerTeam", "UNKNOWN")
		stats_summary = []
		for uid, s in MobaCommon.MatchStatsManager.stats.items():
			stats_summary.append({
				"hero": uid, 
				"k": s["kills"], "d": s["deaths"], "a": s["assists"],
				"gold": s["gold"], "damage": s["damage"],
				"items": s["items"]
			})
		
		MobaCommon.save_match_result(winner, stats_summary)
		try:
			cave.setScene("Home_Page")
		except:
			pass

class HeroGalleryController(cave.Component):
	"""Interactive Gallery for inspecting heroes."""
	def view_hero(self, hero_id):
		data = HeroRegistry.HERO_REGISTRY.get(hero_id)
		if not data: return
		
		ui_name = self.entity.getChild("Hero_Name")
		if ui_name: ui_name.get("UIElement").setText(data.get("displayName", hero_id))
		
		stats = data.get("stats", {})
		for s in ["health", "mana", "ad"]:
			lbl = self.entity.getChild(f"Stat_{s}")
			if lbl: lbl.get("UIElement").setText(str(stats.get(s, 0)))

		# Display Faction Info
		faction_name = data.get("faction", "Unknown")
		from .FactionIdentity import FactionIdentity
		faction_data = FactionIdentity.get_faction(faction_name)
		
		faction_lbl = self.entity.getChild("Faction_Name")
		if faction_lbl: faction_lbl.get("UIElement").setText(faction_data["name"])
		
		faction_desc = self.entity.getChild("Faction_Description")
		if faction_desc: faction_desc.get("UIElement").setText(faction_data["description"])

class RuneGalleryController(cave.Component):
	"""Inspect Rune stats from the main menu."""
	def view_rune(self, rune_id):
		from Data import RuneRegistry
		data = RuneRegistry.get_rune_data(rune_id)
		if not data: return
		
		name_lbl = self.entity.getChild("Rune_Name")
		if name_lbl:
			ui = name_lbl.get("UIElement")
			if ui: ui.setText(data.get("name", rune_id))
		
		desc_lbl = self.entity.getChild("Rune_Description")
		if desc_lbl:
			ui = desc_lbl.get("UIElement")
			if ui: ui.setText(data.get("description", ""))


class HistoryController(cave.Component):
	"""Loads and renders the match_history.json as a UI list."""
	def start(self, scene):
		history = MobaCommon.load_data("match_history.json")
		if not history: return
		
		# Logic to populate a list template would go here
		# For local test, we just log to console to verify load
		print(f"Match History Loaded: {len(history)} entries.")

