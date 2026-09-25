import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon
import math

class FloatingCombatTextComponent(cave.Component):
	"""Phase 35: Floating numbers for damage, healing, and gold."""
	def start(self, scene):
		self.timer = 1.2
		self.velocity = cave.Vector3(0, 1.5, 0) # Float upwards
		self.text_el = self.entity.getChild("Text")
		
	def setup(self, text, color):
		if self.text_el:
			ui = self.text_el.get("UIElement")
			if ui:
				ui.setText(text)
				ui.color = color
				
	def update(self):
		scene = self.entity.getScene()
		dt = cave.getDeltaTime()
		self.timer -= dt
		if self.timer <= 0:
			self.entity.kill()
			return
			
		# Apply smooth movement
		self.entity.getTransform().applyMovement(self.velocity * dt)
		
		# Fade out logic (using u_alpha if Material setup, or UIElement alpha)
		if self.text_el:
			ui = self.text_el.get("UIElement")
			if ui:
				alpha = cave.math.clamp(self.timer / 0.5, 0, 1) # Fade in last 0.5s
				ui.color = cave.Vector4(ui.color.x, ui.color.y, ui.color.z, alpha)

class UIIndicatorComponent(cave.Component):
	"""Handles visual indicators like attack range circles and skillshot arrows."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.active_indicator = None
		self.type = None
		self.params = {}
		
	def show(self, itype, params):
		"""
		itype: MobaCommon.IndicatorType
		params: {"range": float, "width": float, "color": Vector4}
		"""
		scene = self.entity.getScene()
		self.hide() # Clear old
		
		self.type = itype
		self.params = params
		
		# Templates (Assumed to exist, fallback to 'IndicatorPlane')
		template = "IndicatorCircle"
		if itype == MobaCommon.IndicatorType.LINE: template = "IndicatorArrow"
		elif itype == MobaCommon.IndicatorType.RECTANGLE: template = "IndicatorRect"
		
		self.active_indicator = scene.addFromTemplate(template, self.transf.worldPosition)
		if not self.active_indicator:
			# Last resort fallback: a basic plane
			self.active_indicator = scene.addFromTemplate("IndicatorPlane", self.transf.worldPosition)
		
		if self.active_indicator:
			# Apply Scale
			r = params.get("range", 5.0)
			w = params.get("width", 2.0)
			
			if itype == MobaCommon.IndicatorType.CIRCLE:
				# Circle scale is diameter (range * 2)
				self.active_indicator.getTransform().setScale(r * 2.0, 1.0, r * 2.0)
			else:
				# Line/Rect scale: X=width, Z=length (range)
				# Pivot of these should be at the base (hero feet)
				self.active_indicator.getTransform().setScale(w, 1.0, r)
			
			# Apply Color/Tint if shader supports it
			tint = params.get("color", cave.Vector4(0.2, 0.6, 1.0, 0.5))
			mesh = self.active_indicator.get("Mesh")
			if mesh:
				try: mesh.getFinalMaterial().uniforms.set("u_baseColor", tint)
				except: pass

	def hide(self):
		if self.active_indicator:
			self.active_indicator.kill()
			self.active_indicator = None
		self.type = None

	def update(self):
		if not self.active_indicator: return
		
		scene = self.entity.getScene()
		# 1. Stay glued to feet
		self.active_indicator.getTransform().setPosition(
			self.transf.worldPosition.x, 
			self.transf.worldPosition.y + 0.05, # Slight offset to avoid Z-fighting
			self.transf.worldPosition.z
		)
		
		# 2. Rotate to face mouse for directional types
		if self.type in (MobaCommon.IndicatorType.LINE, MobaCommon.IndicatorType.RECTANGLE):
			out = scene.getDataOverMousePosition()
			if out.hit:
				target_pos = out.position
				diff = target_pos - self.transf.worldPosition
				if diff.length() > 0.01:
					# Standard atan2 for top-down (XZ plane)
					angle = math.atan2(diff.x, diff.z)
					self.active_indicator.getTransform().setRotation(0, angle, 0)

class OverheadHealthBarComponent(cave.Component):
	"""Manages a floating UI HP bar that tracks an entity and changes color by team."""
	def start(self, scene):
		self.target = self.entity
		self.bar_ent = None
		self.fill_ent = None
		self.pc_local = None
		
		# Find the local player to determine "Green" vs "Blue"
		players = MobaCommon.EntityRegistry.get("player")
		for p in players:
			# Check if this player is controlled by the local client (MatchOrchestrator property)
			if cave.getGlobalDict().get("CurrentPlayer") == p.name:
				self.pc_local = p
				break

		# Delay UI spawning to ensure Template is ready
		self.spawn_timer = 0.5 
		
	def update(self):
		scene = self.entity.getScene()
		dt = cave.getDeltaTime()
		
		# 1. Spawn Bar if missing
		if not self.bar_ent:
			self.spawn_timer -= dt
			if self.spawn_timer <= 0:
				self.spawn_bar(scene)
			return

		# 2. Vision Gating
		is_visible = True
		if self.pc_local:
			is_visible = MobaCommon.is_target_visible(self.pc_local, self.entity)
		
		# Phase 70: Fixed API misuse — setActive requires scene argument
		scene = self.entity.getScene()
		if is_visible:
			self.bar_ent.activate(scene)
		else:
			self.bar_ent.deactivate(scene)
		if not is_visible: return

		# 3. Position Bar above head
		t_pos = self.entity.getTransform().worldPosition
		# Offset HP bar vertically (assuming ~2 units height for heroes)
		offset = 2.2 if self.entity.hasTag("player") else 1.2
		self.bar_ent.getTransform().setPosition(t_pos.x, t_pos.y + offset, t_pos.z)
		
		# 4. Update Fills (Health + Shield)
		props = self.entity.getProperties()
		hp = props.get("health", 100)
		max_hp = props.get("maxHealth", 100)
		shield = props.get("shieldHP", 0)
		
		hp_pct = cave.math.clamp(hp / max_hp, 0, 1)
		shield_pct = cave.math.clamp(shield / max_hp, 0, 1.2) # Shield can exceed max HP visually
		
		if self.fill_ent:
			self.fill_ent.getTransform().setScale(hp_pct, 1.0, 1.0)
		
		shield_bar = self.bar_ent.getChild("ShieldFill")
		if shield_bar:
			if shield > 0:
				shield_bar.activate(scene)
				# Position shield bar starting at the end of current HP
				shield_bar.getTransform().setScale(shield_pct, 1.1, 1.0) # Slightly taller
				shield_bar.getTransform().setPosition(hp_pct * 0.5, 0, 0.01) # Cave API: setPosition() is local
			else:
				shield_bar.deactivate(scene)

		# 5. CC Status Text
		st_ent = self.bar_ent.getChild("Status_Text")
		if st_ent:
			eff = self.entity.getPy("EffectComponent")
			status = ""
			if eff:
				if eff.has_flag(MobaCommon.EffectFlags.STUN): status = "STUNNED"
				elif eff.has_flag(MobaCommon.EffectFlags.ROOT): status = "ROOTED"
				elif eff.has_flag(MobaCommon.EffectFlags.SILENCE): status = "SILENCED"
				elif eff.has_flag(MobaCommon.EffectFlags.FEAR): status = "FEARED"
				elif eff.has_flag(MobaCommon.EffectFlags.CHARM): status = "CHARMED"
			
			if status != "":
				st_ent.activate(scene)
				ui = st_ent.get("UIElement")
				if ui: ui.setText(status.upper())
			else:
				st_ent.deactivate(scene)
				
		# 6. Patience Bar (Jungle Monsters only)
		p_bar = self.bar_ent.getChild("PatienceFill")
		if p_bar:
			if self.entity.hasTag("monster"):
				j_comp = self.entity.getPy("JungleMonsterComponent")
				if j_comp and hasattr(j_comp, "patience"):
					p_bar.activate(scene)
					p_pct = cave.math.clamp(j_comp.patience / j_comp.patience_max, 0, 1)
					p_bar.getTransform().setScale(p_pct, 1.0, 1.0)
					
					# Color based on danger (Orange -> Red)
					mesh = p_bar.get("Mesh")
					if mesh:
						mat = mesh.getFinalMaterial()
						if mat: 
							p_color = cave.Vector4(1.0, 0.5 + (p_pct * 0.3), 0.1, 1.0)
							mat.uniforms.set("u_baseColor", p_color)
				else:
					p_bar.deactivate(scene)
			else:
				p_bar.deactivate(scene)

	def spawn_bar(self, scene):
		template = MobaCommon.Templates.FCT_TEMPLATE # Reusing UI template base
		self.bar_ent = scene.addFromTemplate("UI_HealthBar_Overhead", self.entity.getTransform().worldPosition)
		if not self.bar_ent: return
		
		self.fill_ent = self.bar_ent.getChild("Fill")
		
		# Set Color based on Team
		team = MobaCommon.get_entity_team(self.entity)
		color = MobaCommon.Team.COLORS.get(team, MobaCommon.Team.COLORS[MobaCommon.Team.NEUTRAL])
		
		# Special case: Me (Green)
		if self.entity == self.pc_local:
			color = cave.Vector4(0.1, 1.0, 0.1, 1.0) # Bright Green
		
		mesh = self.fill_ent.get("Mesh") if self.fill_ent else None
		if mesh:
			mat = mesh.getFinalMaterial()
			if mat: mat.uniforms.set("u_baseColor", color)

class HUDIconComponent(cave.Component):
	"""Phase 116: Mastery configuration for contextual HUD interactions."""
	def start(self, scene):
		self.pc = None
		self.key = None
		
	def setup(self, pc, key):
		self.pc = pc
		self.key = key
		
	def on_mouse_enter(self):
		if self.pc and self.key:
			self.pc.showAbilityIndicator(self.key)
			
	def on_mouse_exit(self):
		if self.pc and hasattr(self.pc, "indicator"):
			self.pc.indicator.hide()
			
	def on_click(self):
		if not self.pc: return
		events = cave.getEvents()
		# LoL Standard: Alt+Click pings status
		if events.active(cave.event.KEY_LALT) or events.active(cave.event.KEY_RALT):
			timer = self.pc.cooldowns.get(self.key)
			max_cd = self.pc.cooldownDurations.get(self.key, 0)
			curr_rem = max(0, max_cd - timer.get()) if timer and max_cd > 0 else 0
			
			status = "READY" if curr_rem <= 0 else f"{int(curr_rem)}s"
			mana = getattr(self.pc, "mana", 0)
			cost = self.pc.get_skill_value(self.key, "mana", 0)
			if mana < cost and curr_rem <= 0: status = "LOW MANA"
			
			msg = f"{self.pc.heroName}: {self.key} - {status}"
			MobaCommon.broadcast_event(msg)

class MouseHighlightComponent(cave.Component):
	"""Handles mouse hover outlines. Red for enemies, Blue/Green for allies."""
	def start(self, scene):
		self.is_hovered = False
		self.pc_local = None
		# Find the local player for vision/team checks
		for p in MobaCommon.EntityRegistry.get("player"):
			if cave.getGlobalDict().get("CurrentPlayer") == p.name:
				self.pc_local = p
				break

	def on_mouse_enter(self):
		if not self.pc_local: return
		
		# Only highlight if visible
		if not MobaCommon.is_target_visible(self.pc_local, self.entity):
			return
			
		self.is_hovered = True
		self.apply_highlight(True)

	def on_mouse_exit(self):
		self.is_hovered = False
		self.apply_highlight(False)

	def apply_highlight(self, active):
		mesh = self.entity.get("Mesh")
		if not mesh: return
		
		mat = mesh.getFinalMaterial()
		if not mat: return
		
		if active:
			# Determine Highlight Color
			team_me = MobaCommon.get_entity_team(self.pc_local)
			team_them = MobaCommon.get_entity_team(self.entity)
			
			h_color = cave.Vector4(1.0, 0.1, 0.1, 1.0) # Red enemy
			if team_me == team_them:
				h_color = cave.Vector4(0.1, 0.8, 1.0, 1.0) # Blue ally
				
			# Cave Engine common uniform for selection outlines
			mat.uniforms.set("u_highlight", 1.0)
			mat.uniforms.set("u_highlightColor", h_color)
		else:
			mat.uniforms.set("u_highlight", 0.0)

class ItemTooltipComponent(cave.Component):
	"""Phase 100: Displays dynamic item descriptions and Guinsoo status."""
	def start(self, scene):
		# Look for local player controller in the scene
		self.pc = None
		players = MobaCommon.EntityRegistry.get("player")
		for p in players:
			if cave.getGlobalDict().get("CurrentPlayer") == p.name:
				self.pc = p.getPy("PlayerController")
				break
				
		self.item_id = None
		self.tooltip_ent = self.entity.getScene().get("UI_Item_Tooltip")
		
	def setup(self, item_id):
		self.item_id = item_id

	def on_mouse_enter(self):
		if not self.item_id or not self.tooltip_ent: return
		scene = self.entity.getScene()
		self.tooltip_ent.activate(scene)
		
		from Data import ItemRegistry
		data = ItemRegistry.ITEM_REGISTRY.get(self.item_id, {})
		
		# Construct dynamic description
		description = f"{self.item_id}\n"
		for stat, val in data.get("stats", {}).items():
			description += f"+{val} {stat.upper()}\n"
			
		# Guinsoo Extension
		if self.item_id == "Rageblade":
			is_broken = getattr(self.pc, "is_limit_broken", False) if self.pc else False
			if is_broken:
				description += "\n[LIMIT BREAK ACTIVE]\n+120% AS Surge\n3.0 Speed Cap Unlocked"
			else:
				description += "\n[EVOLUTION INCOMPLETE]\nRequires: AS Boots + 3 On Hit Items"
		
		# Update Tooltip Text
		text_ent = self.tooltip_ent.getChild("Description_Text")
		if text_ent:
			ui = text_ent.get("UIElement")
			if ui: ui.setText(description)
			
	def on_mouse_exit(self):
		if self.tooltip_ent:
			self.tooltip_ent.deactivate(self.entity.getScene())

class HUDController(cave.Component):
	"""Main UI controller for health bars and ability icons."""
	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		# Note: Cave has no scene.getCanvas() API; reference UI children directly
		
		# Phase 37: Visual Polish Attachments
		from UI import MobaUIFX
		self.entity.add("LowHPFeedbackComponent")
		
		# Attach UIPop to Gold Text
		gold_ent = self.entity.getChild("Gold_Text")
		if gold_ent: self.pop_gold = gold_ent.add("UIPopComponent")
		else: self.pop_gold = None
		
		self._prev_gold = 0
		self._prev_cooldowns = {"Q":0, "W":0, "E":0, "R":0}
		self.pop_skills = {}
		
		# Optimization (Phase 69): UI Throttle (10Hz)
		self.update_timer = 0.0
		self.update_interval = 0.1
		
	@staticmethod
	def spawn_fct(scene, pos, text, color=cave.Vector4(1,1,1,1)):
		"""Phase 35: Standardized FCT spawner."""
		fct = scene.addFromTemplate("UI_FloatingText", pos)
		if fct:
			comp = fct.add("FloatingCombatTextComponent")
			comp.setup(text, color)
			# Add random offset to prevent bunching
			import random
			rx = (random.random() - 0.5) * 1.5
			rz = (random.random() - 0.5) * 1.5
			fct.getTransform().setPosition(pos.x + rx, pos.y + 2.5, pos.z + rz)
		
	def update(self):
		if not self.pc: return
		
		scene = self.entity.getScene()
		dt = cave.getDeltaTime()
		self.update_timer += dt
		if self.update_timer < self.update_interval: return
		self.update_timer = 0.0
		
		# 1. Update Ability Icons (Q, W, E, R)
		for key in ["Q", "W", "E", "R"]:
			ui_key = f"Icon_{key}"
			icon_ent = self.entity.getChild(ui_key)
			if icon_ent:
				# Set Icon from Hero Data
				skill_data = self.pc.heroData.get("skills", {}).get(key, {})
				icon_name = skill_data.get("icon", MobaCommon.Templates.ICON_EMPTY)
				
				# In Cave, UI materials often use u_texture or similar
				mesh = icon_ent.get("Mesh")
				if mesh:
					mat = mesh.getFinalMaterial()
					if mat:
						# Phase 70 Fix: In Cave, uniforms for textures usually expect a Texture object
						mat.uniforms.set("u_icon", cave.getTexture(icon_name))
				
				# 2. Update Cooldown Overlay
				cd_overlay = icon_ent.getChild("Cooldown")
				if cd_overlay:
					# Phase 70: Updated to use cave.Timer remaining math
					timer = self.pc.cooldowns.get(key)
					max_cd = self.pc.cooldownDurations.get(key, 0)
					curr_remaining = max(0, max_cd - timer.get()) if timer and max_cd > 0 else 0
					
					if curr_remaining > 0:
						cd_overlay.activate(scene)
					else:
						cd_overlay.deactivate(scene)
					if curr_remaining > 0:
						progress = cave.math.clamp(curr_remaining / max_cd, 0, 1)
						cd_overlay.getTransform().setScale(1.0, progress, 1.0)
					
					# Phase 131: Cooldown Timer Numbers
					cd_text = icon_ent.getChild("CD_Text")
					if cd_text:
						ui_t = cd_text.get("UIElement")
						if ui_t:
							if curr_remaining > 0:
								cd_text.activate(scene)
								ui_t.setText(f"{curr_remaining:.1f}" if curr_remaining < 10 else str(int(curr_remaining)))
							else:
								cd_text.deactivate(scene)
						
				# Phase 37: Ability Ready Pop
				if key not in self.pop_skills:
					self.pop_skills[key] = icon_ent.add("UIPopComponent")
				
				# Phase 116: Pro Interactions
				ic = icon_ent.getPy("HUDIconComponent")
				if not ic:
					ic = icon_ent.add("HUDIconComponent")
					ic.setup(self.pc, key)

				prev_cd = self._prev_cooldowns.get(key, 0)
				curr_cd = curr_remaining
				if prev_cd > 0 and curr_cd <= 0:
					self.pop_skills[key].pop(factor=1.3)
					flash = icon_ent.getChild("Flash")
					if flash: flash.activate(scene)
				self._prev_cooldowns[key] = curr_cd
		
		# Phase 131: Ally Ultimate Indicators (Feature 3)
		ally_panel = self.entity.getChild("Ally_Ult_Panel")
		if ally_panel:
			allies = MobaCommon.EntityRegistry.get_team_entities(
				self.pc.entity.getProperties().get("team", "teamA"), "player")
			for idx, ally in enumerate(allies):
				if ally == self.pc.entity: continue
				dot = ally_panel.getChild(f"Ult_Dot_{idx}")
				if not dot: continue
				a_pc = ally.getPy("PlayerController")
				if a_pc:
					r_timer = a_pc.cooldowns.get("R")
					r_max = a_pc.cooldownDurations.get("R", 0)
					r_rem = max(0, r_max - r_timer.get()) if r_timer and r_max > 0 else 0
					mesh = dot.get("Mesh")
					if mesh:
						mat = mesh.getFinalMaterial()
						if mat:
							if r_rem <= 0:
								mat.uniforms.set("u_baseColor", cave.Vector4(0.2, 1.0, 0.3, 1))
							else:
								mat.uniforms.set("u_baseColor", cave.Vector4(0.4, 0.4, 0.4, 1))
						
		# 3. Update Inventory Icons (1-6)
		from Data import ItemRegistry
		for i in range(6):
			ui_key = f"Icon_Item_{i+1}"
			slot_ent = self.entity.getChild(ui_key)
			if slot_ent:
				# Default to empty icon
				icon_name = MobaCommon.Templates.ICON_ITEM_DEFAULT
				
				if i < len(self.pc.inventory):
					item_name = self.pc.inventory[i]
					item_data = ItemRegistry.ITEM_REGISTRY.get(item_name)
					if item_data:
						icon_name = item_data.get("icon", icon_name)
				
				mesh = slot_ent.get("Mesh")
				if mesh:
					mat = mesh.getFinalMaterial()
					if mat:
						mat.uniforms.set("u_icon", icon_name)
				
				# ── Phase 100: Dynamic Tooltips ──────────────────────────────
				tt = icon_ent.getPy("ItemTooltipComponent")
				if not tt:
					tt = icon_ent.add("ItemTooltipComponent")
				
				if i < len(self.pc.inventory):
					tt.setup(self.pc.inventory[i])
				else:
					tt.setup(None)
				
				# ── Active Cooldown Visualization (Wave 76) ──────────────────
				cd_overlay = slot_ent.getChild("Cooldown")
				if cd_overlay:
					# Get cooldown data from InventoryManager
					mgr = self.pc.inventory_mgr
					now = scene.getElapsedSceneTime()
					
					cd_rem = 0.0
					max_cd = 1.0
					
					if i < len(mgr.items):
						item_name = mgr.items[i]
						data = ItemRegistry.ITEM_REGISTRY.get(item_name)
						if data:
							max_cd = data.get("active_cd", 60.0)
							cd_ready_at = mgr.active_cooldowns.get(item_name, 0)
							cd_rem = max(0, cd_ready_at - now)
					
					if cd_rem > 0:
						cd_overlay.activate(scene)
						progress = cave.math.clamp(cd_rem / max_cd, 0, 1)
						cd_overlay.getTransform().setScale(1.0, progress, 1.0)
					else:
						cd_overlay.deactivate(scene)
						
		# 4. Update Gold & Stats
		gold_text = self.entity.getChild("Gold_Text")
		if gold_text:
			ui_el = gold_text.get("UIElement")
			if ui_el:
				ui_el.setText(f"{int(self.pc.gold)}")
				
				# Phase 37: Gold Pop
				if self.pc.gold > self._prev_gold:
					if self.pop_gold: self.pop_gold.pop(factor=1.4)
				self._prev_gold = self.pc.gold
				
		# 5. Update Trinket Icon (Slot 7)
		trinket_ent = self.entity.getChild("Icon_Trinket")
		if trinket_ent:
			trinket_id = self.pc.inventory_mgr.trinket
			item_data = ItemRegistry.ITEM_REGISTRY.get(trinket_id)
			icon_name = item_data.get("icon", MobaCommon.Templates.ICON_ITEM_DEFAULT) if item_data else MobaCommon.Templates.ICON_ITEM_DEFAULT
			
			mesh = trinket_ent.get("Mesh")
			if mesh:
				mat = mesh.getFinalMaterial()
				if mat: mat.uniforms.set("u_icon", icon_name)
				
			# ── Trinket Cooldown (Slot 6/Key 4) ───────────────────────────
			cd_overlay = trinket_ent.getChild("Cooldown")
			if cd_overlay:
				mgr = self.pc.inventory_mgr
				now = scene.getElapsedSceneTime()
				
				trinket_id = mgr.trinket
				data = ItemRegistry.ITEM_REGISTRY.get(trinket_id)
				max_cd = data.get("active_cd", 120.0) if data else 120.0
				
				cd_ready_at = mgr.active_cooldowns.get(trinket_id, 0)
				cd_rem = max(0, cd_ready_at - now)
				
				if cd_rem > 0:
					cd_overlay.activate(scene)
					progress = cave.math.clamp(cd_rem / max_cd, 0, 1)
					cd_overlay.getTransform().setScale(1.0, progress, 1.0)
				else:
					cd_overlay.deactivate(scene)

		# 6. Update Summoner Spells (D, F Slots)
		ss_mgr = getattr(self.pc, "summoner_spell_mgr", None)
		if ss_mgr:
			mins = MobaCommon.GameTick.get_time_minutes()
			for slot in ["D", "F"]:
				ui_key = f"Icon_Summoner_{slot}"
				slot_ent = self.entity.getChild(ui_key)
				if slot_ent:
					spell_id = ss_mgr.get_spell_id(slot)
					icon_name = f"Icon_Spell_{spell_id}"
					
					# Phase 105: Unleashed Teleport Visuals
					if spell_id == "Teleport" and mins >= 10.0:
						icon_name = "Icon_Spell_Teleport_Unleashed"
						glow = slot_ent.getChild("Unleashed_Glow")
						if glow: glow.activate(scene)
					
					# Apply Texture
					mesh = slot_ent.get("Mesh")
					if mesh:
						mat = mesh.getFinalMaterial()
						if mat: mat.uniforms.set("u_icon", icon_name)
					
					# Cooldown Overlay
					cd_rem = ss_mgr.get_cooldown_remaining(slot)
					max_cd = ss_mgr.get_cooldown_max(slot)
					cd_overlay = slot_ent.getChild("Cooldown")
					if cd_overlay:
						if cd_rem > 0:
							cd_overlay.activate(scene)
							progress = cave.math.clamp(cd_rem / max_cd, 0, 1)
							cd_overlay.getTransform().setScale(1.0, progress, 1.0)
						else:
							cd_overlay.deactivate(scene)

		# 7. Update Targeting Status (Phase 116)
		status_ent = self.entity.getChild("Targeting_Status")
		if status_ent:
			if self.pc.targetHeroesOnly:
				status_ent.activate(scene)
				ui = status_ent.get("UIElement")
				if ui:
					ui.setText("HEROES ONLY")
					ui.color = cave.Vector4(1.0, 0.4, 0.1, 1.0) # Vibrant Orange
			else:
				status_ent.deactivate(scene)

class ObjectiveTimersComponent(cave.Component):
	"""Phase 118: Displays spawn timers for lore-accurate Resonance Spires and Colossus."""
	def start(self, scene):
		self.timer_spire = self.entity.getChild("Timer_Spire")
		self.timer_colossus = self.entity.getChild("Timer_Colossus")
		
		# Initial Spawns
		self.spire_spawn_time = 300.0 # 5:00
		self.colossus_spawn_time = 1200.0 # 20:00
		
	def update(self):
		dt = cave.getDeltaTime()
		scene = self.entity.getScene()
		
		# 1. Update Spire Timer
		if self.spire_spawn_time > 0:
			self.spire_spawn_time -= dt
			if self.timer_spire:
				ui = self.timer_spire.get("UIElement")
				if ui: ui.setText(f"SPIRE: {int(self.spire_spawn_time//60)}:{int(self.spire_spawn_time%60):02d}")
		else:
			if self.timer_spire:
				ui = self.timer_spire.get("UIElement")
				if ui: 
					ui.setText("SPIRE UP")
					ui.color = cave.Vector4(0.1, 1.0, 0.4, 1.0) # Green alert
		
		# 2. Update Colossus Timer
		if self.colossus_spawn_time > 0:
			self.colossus_spawn_time -= dt
			if self.timer_colossus:
				ui = self.timer_colossus.get("UIElement")
				if ui: ui.setText(f"COLOSSUS: {int(self.colossus_spawn_time//60)}:{int(self.colossus_spawn_time%60):02d}")
		else:
			if self.timer_colossus:
				ui = self.timer_colossus.get("UIElement")
				if ui: 
					ui.setText("COLOSSUS UP")
					ui.color = cave.Vector4(1.0, 0.1, 0.1, 1.0) # Red alert

class LoadingScreenComponent(cave.Component):
	"""Phase 119: Premium cinematic loading screen logic."""
	def start(self, scene):
		self.progress = 0.0
		self.bar = self.entity.getChild("ProgressBar")
		self.hero_art = self.entity.getChild("HeroArt")
		
	def update(self):
		self.progress = cave.math.lerp(self.progress, 1.0, cave.getDeltaTime() * 0.5)
		if self.bar:
			self.bar.getTransform().setScale(self.progress, 1.0, 1.0)
		
		if self.progress >= 0.99:
			# Auto-fade out loading screen when done
			self.entity.deactivate(self.entity.getScene())

class AnnouncerBannerComponent(cave.Component):
	"""Phase 119: Large, animated banners for major match events."""
	def start(self, scene):
		self.timer = 0.0
		self.duration = 3.0
		self.lbl = self.entity.get("UIElement")
		
	def trigger(self, text):
		self.entity.activate(self.entity.getScene())
		if self.lbl: self.lbl.setText(text.upper())
		self.timer = self.duration
		# Play a 'whoosh' or 'impact' animation
		self.entity.getTransform().setScale(0, 0, 0)
		
	def update(self):
		if self.timer > 0:
			self.timer -= cave.getDeltaTime()
			# Pop-in animation
			s = cave.math.lerpEase(0, 1.0, (self.duration - self.timer) * 2.0)
			self.entity.getTransform().setScale(s, s, s)
			
			if self.timer <= 0:
				self.entity.deactivate(self.entity.getScene())

class PingWheelComponent(cave.Component):
	"""Phase 120: Professional Radial Ping Menu."""
	def start(self, scene):
		self.is_open = False
		self.wheel_ui = self.entity.getChild("Wheel_Container")
		self.mouse_start = cave.Vector2(0,0)
		
	def open(self, mouse_pos):
		self.is_open = True
		self.mouse_start = mouse_pos
		self.entity.activate(self.entity.getScene())
		# Snap UI to mouse
		self.entity.getTransform().setPosition(mouse_pos.x, mouse_pos.y, 0)  # Cave API: setPosition() is local
		
	def close(self):
		if not self.is_open: return
		self.is_open = False
		# Determine selection based on final mouse offset
		offset = cave.getMousePositionUI() - self.mouse_start
		ping = MobaCommon.PingType.GENERIC
		if offset.length() > 20: # Deadzone
			angle = cave.math.atan2(offset.y, offset.x) * (180.0 / 3.1415)
			if -45 < angle <= 45: ping = MobaCommon.PingType.OMW
			elif 45 < angle <= 135: ping = MobaCommon.PingType.DANGER
			elif -135 < angle <= -45: ping = MobaCommon.PingType.ASSIST
			else: ping = MobaCommon.PingType.MIA
			
		self.entity.deactivate(self.entity.getScene())
		return ping

class MusicManager(cave.Component):
	"""Phase 120: Orchestrates dynamic music intensity."""
	def start(self, scene):
		self.intensity = MobaCommon.CombatIntensity.IDLE
		self.fade_timer = 0.0
		
	def update(self):
		# Logic to detect combat would happen globally or via player events
		# For prototype, we'll auto-detect nearby hero combat
		players = MobaCommon.EntityRegistry.get("player")
		new_intensity = MobaCommon.CombatIntensity.IDLE
		
		for p in players:
			pc = p.getPy("PlayerController")
			if pc and pc.inCombatTimer > 0:
				new_intensity = MobaCommon.CombatIntensity.COMBAT
				break
				
		if new_intensity != self.intensity:
			self.intensity = new_intensity
			# Trigger crossfade logic here

class MinimapComponent(cave.Component):
	"""Handles world-to-UI coordinate mapping and entity icon tracking."""
	map_width = 256.0
	map_height = 256.0
	world_min = cave.Vector3(-60, 0, -60)
	world_max = cave.Vector3(60, 0, 60)
	
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.icons = {} # {entityID: iconEntity}
		self.background = self.entity.getChild("Background")
		self.update_timer = 0.0
		self.update_interval = 0.05 # 20 FPS Map Update is enough
		
	def update(self):
		dt = cave.getDeltaTime()
		self.update_timer += dt
		if self.update_timer < self.update_interval:
			return
		self.update_timer = 0.0
		
		scene = self.entity.getScene()
		player_list = MobaCommon.EntityRegistry.get("player")
		player = player_list[0] if player_list else None
		if not player: return

		# Phase 33: Dynamic Bounds from Scene Properties
		props = scene.getProperties()
		self.world_min = props.get("map_bounds_min", cave.Vector3(-100, 0, -100))
		self.world_max = props.get("map_bounds_max", cave.Vector3(100, 0, 100))

		# Phase 70: Use EntityRegistry instead of per-tag getEntitiesWithTag
		all_tracked = []
		for tag in ["player", "minion", "turret", "monster", "ward"]:
			all_tracked.extend(MobaCommon.EntityRegistry.get(tag))
		
		found_uids = set()
		for ent in all_tracked:
			if not ent.isActive(): continue
			
			# Phase 33: Fog of War Visibility
			is_visible = True
			if MobaCommon.get_entity_team(ent) != MobaCommon.get_entity_team(player):
				is_visible = MobaCommon.is_target_visible(player, ent)
			
			if is_visible:
				uid = ent.getUID()
				found_uids.add(uid)
				self.update_icon(ent, uid)
			
		# Cleanup icons for dead/missing/hidden entities
		to_cleanup = [eid for eid in self.icons if eid not in found_uids]
		for eid in to_cleanup:
			if self.icons[eid]:
				self.icons[eid].kill()
			del self.icons[eid]

	def update_icon(self, target, uid):
		t_pos = target.getTransform().worldPosition

		# Map world pos to 0.0 - 1.0 range
		range_x = self.world_max.x - self.world_min.x
		range_z = self.world_max.z - self.world_min.z
		
		# Prevent division by zero
		if range_x == 0 or range_z == 0: return

		norm_x = (t_pos.x - self.world_min.x) / range_x
		norm_z = (t_pos.z - self.world_min.z) / range_z
		
		# Phase 33: Clamping to Minimap Bounds
		norm_x = cave.math.clamp(norm_x, 0, 1)
		norm_z = cave.math.clamp(norm_z, 0, 1)

		# Map to UI space (relative to minimap background)
		ui_x = (norm_x - 0.5) * self.map_width
		ui_z = (norm_z - 0.5) * self.map_height
		
		if uid not in self.icons:
			self.icons[uid] = self.create_icon(target)
			
		ui_pos = self.get_ui_pos(t_pos)
		icon_transf = self.icons[uid].getTransform()
		icon_transf.setPosition(ui_pos.x, ui_pos.y, 0.1)

	def get_ui_pos(self, world_pos):
		"""Helper to map world position to UI coordinates."""
		range_x = self.world_max.x - self.world_min.x
		range_z = self.world_max.z - self.world_min.z
		
		norm_x = cave.math.clamp((world_pos.x - self.world_min.x) / range_x, 0, 1)
		norm_z = cave.math.clamp((world_pos.z - self.world_min.z) / range_z, 0, 1)
		
		ui_x = (norm_x - 0.5) * self.map_width
		ui_z = (norm_z - 0.5) * self.map_height
		return cave.Vector3(ui_x, ui_z, 0)

	def create_icon(self, target):
		scene = self.entity.getScene()
		template = MobaCommon.Templates.MINIMAP_HERO if target.hasTag("player") else MobaCommon.Templates.MINIMAP_BASIC
		icon = scene.addFromTemplate(template, cave.Vector3(0,0,0))
		icon.setParent(self.entity)
		
		# Color based on team
		mesh = icon.getPy("MeshComponent") or icon.get("Mesh")
		if mesh:
			mat = mesh.getFinalMaterial() if hasattr(mesh, "getFinalMaterial") else None
			if mat:
				team = MobaCommon.get_entity_team(target)
				color = MobaCommon.Team.COLORS.get(team, MobaCommon.Team.COLORS[MobaCommon.Team.NEUTRAL])
				# Correct Cave API: Material.uniforms is a ShaderUniforms object
				mat.uniforms.set("u_baseColor", color)
			
		return icon

class ShopComponent(cave.Component):
	"""Handles the display and interaction for the in-game shop."""
	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		self.background = self.entity.getChild("Background")
		self.background.deactivate(scene)
		self.items = [] # UI elements for items
		
	def toggle(self):
		scene = self.entity.getScene()
		if self.background.isActive():
			self.background.deactivate(scene)
		else:
			self.background.activate(scene)
			self.refresh_list()
			
	def refresh_list(self):
		"""Populates the shop UI with items, prioritizing Jungle Evolutions if eligible."""
		from Data import ItemRegistry
		from Core import MobaCommon
		scene = self.entity.getScene()
		if not self.pc: return
		
		# Cleanup old list
		for e in self.items: e.kill()
		self.items.clear()
		
		inventory = self.pc.inventory_mgr.items
		# Check for jungle starter to enable evolutions
		has_starter = any("Resolve" in item_id for item_id in inventory)
		
		# 1. Specialized Evolution Entries (Priority)
		evolutions = []
		standard_items = []
		
		for name, data in ItemRegistry.ITEM_REGISTRY.items():
			if data.get("isEvolution"):
				if has_starter: evolutions.append(name)
			else:
				# Don't show basic starters if already evolved? (LoL style)
				standard_items.append(name)
		
		# Sort items by Price ascending
		display_list = evolutions + sorted(standard_items, key=lambda x: ItemRegistry.get_item_price(x, inventory))
		
		# Grid parameters
		spacing_x = 80
		spacing_y = 100
		cols = 4
		
		for i, item_id in enumerate(display_list):
			price = ItemRegistry.get_item_price(item_id, inventory)
			item_data = ItemRegistry.ITEM_REGISTRY.get(item_id)
			
			# Logic: Spawn a ShopEntry button from template
			entry = scene.addFromTemplate("UI_ShopEntry", cave.Vector3(0, 0, 0))
			if entry:
				entry.getTransform().setParent(self.background.getTransform())
				self.items.append(entry)
				
				# Position in grid
				row = i // cols
				col = i % cols
				entry.getTransform().setPosition((col - (cols/2.0)) * spacing_x, 150 - (row * spacing_y), 0.1)
				
				# Setup internal logic
				comp = entry.getPy("ShopEntry")
				if comp and hasattr(comp, "setup"):
					comp.setup(item_id, price)
				
				# Update Visuals (Icon & Price Text)
				icon_ent = entry.getChild("Icon")
				if icon_ent and icon_ent.get("Mesh"):
					mat = icon_ent.get("Mesh").getFinalMaterial()
					if mat: mat.uniforms.set("u_icon", item_data.get("icon", MobaCommon.Templates.ICON_ITEM_DEFAULT))
				
				price_ent = entry.getChild("Price_Text")
				if price_ent and price_ent.get("UIElement"):
					price_ent.get("UIElement").setText(str(price))
					# Change color if unaffordable
					if self.pc.gold < price:
						price_ent.get("UIElement").color = cave.Vector4(1, 0.2, 0.2, 1) # Red
					else:
						price_ent.get("UIElement").color = cave.Vector4(1, 1, 1, 1) # White
	def buy_item(self, item_name):
		"""Attempt to purchase an item via the player controller."""
		if not self.pc: return
		success = self.pc.buy_item(item_name)
		if success:
			MobaCommon.play_sfx(self.entity, MobaCommon.Templates.SFX_SHOP_PURCHASE)
			self.refresh_list() # Update prices of other items
		else:
			MobaCommon.play_sfx(self.entity, MobaCommon.Templates.SFX_UI_CLICK, pitch_var=0.2)
		return success

	def sell_item(self, slot_index):
		"""Phase 61: Proxy to sell item through PC."""
		if not self.pc: return
		success = self.pc.inventory_mgr.sell_item(slot_index)
		if success:
			MobaCommon.play_sfx(self.entity, MobaCommon.Templates.SFX_UI_CLICK)
			self.refresh_list() # Update prices of items we might now need to buy back
		return success

class AmbientAudioComponent(cave.Component):
	"""Phase 36: Automatically manages background ambience based on the scene."""
	def start(self, scene):
		from Core import MobaCommon
		is_aram = cave.getGlobalDict().get("IsARAM", False)
		bgm = MobaCommon.Templates.BGM_ARAM if is_aram else MobaCommon.Templates.BGM_SUMMONERS_RIFT
		
		# Managed start
		MobaCommon.play_managed_ambience(bgm, volume=0.4)

class LowHPFeedbackComponent(cave.Component):
	"""Phase 37: Heartbeat / Red pulse when player is dangerously low on HP."""
	def start(self, scene):
		self.vignette = self.entity.getChild("Vignette_Danger")
		self.pulse_timer = 0.0
		if self.vignette: self.vignette.deactivate(scene)
		
	def update(self):
		scene = self.entity.getScene()
		pc = self.entity.getPy("PlayerController")
		if not pc or not self.vignette: return
		
		hp_pct = self.entity.getProperties().get("health", 0) / max(1, self.entity.getProperties().get("maxHealth", 1))
		
		if hp_pct < 0.3 and self.entity.isActive():
			self.vignette.activate(scene)
			# Pulse intensity
			self.pulse_timer += cave.getDeltaTime()
			import math
			intensity = 0.5 + 0.5 * math.sin(self.pulse_timer * 8.0)
			
			mesh = self.vignette.get("Mesh")
			if mesh:
				mat = mesh.getFinalMaterial()
				if mat:
					# Standard Cave Engine vignette color/alpha uniform
					mat.uniforms.set("u_intensity", intensity * 0.8)
		else:
			if self.vignette.isActive():
				self.vignette.deactivate(scene)

class ScoreboardController(cave.Component):
	"""Phase 28: Tracks and displays K/D/A and CS for all players."""
	def start(self, scene):
		self.background = self.entity.getChild("Background")
		if self.background:
			self.background.deactivate(scene)
		self.entries = {} # {uid: ui_entry_ent}
		
	def update(self):
		scene = self.entity.getScene()
		events = cave.getEvents()
		
		# Toggle visibility on TAB key
		if events.pressed(cave.event.KEY_TAB):
			if self.background: self.background.activate(scene)
			self.refresh()
		elif events.released(cave.event.KEY_TAB):
			if self.background: self.background.deactivate(scene)
			
	def refresh(self):
		scene = self.entity.getScene()
		players = MobaCommon.EntityRegistry.get("player")
		
		# Identify local player for vision context
		local_name = cave.getGlobalDict().get("CurrentPlayer")
		player_ent = scene.get(local_name) if local_name else None
		p_team = MobaCommon.get_entity_team(player_ent)
		
		# Sort players by team then name for consistent layout
		sorted_players = sorted(players, key=lambda x: (MobaCommon.get_entity_team(x), x.name))
		
		y_offset = 0
		for p in sorted_players:
			uid = p.name
			is_enemy = (MobaCommon.get_entity_team(p) != p_team) and p_team != MobaCommon.Team.NEUTRAL
			
			# Logic: Allies get LIVE stats, Enemies get VISION stats
			if not is_enemy:
				data = MobaCommon.MatchStatsManager.stats.get(uid)
			else:
				data = MobaCommon.MatchStatsManager.vision_cache.get(uid)
				
			if not data: continue
			
			# UI Update Logic
			entry = self.entries.get(uid)
			if not entry:
				# Spawn new entry from template if missing
				template = "UI_Scoreboard_Entry"
				entry = scene.addFromTemplate(template, cave.Vector3(0, 0, 0))
				if entry:
					entry.getTransform().setParent(self.background.getTransform())
					self.entries[uid] = entry
			
			if entry:
				# Position entry
				entry.getTransform().setPosition(0, 140 - (y_offset * 32), 0.1)
				y_offset += 1
				
				# Update Level
				lvl_txt = entry.getChild("Level_Text")
				if lvl_txt and lvl_txt.get("UIElement"):
					lvl_txt.get("UIElement").setText(str(data.get("level", 1)))
				
				# Update KDA & CS
				kda_txt = entry.getChild("KDA_Text")
				if kda_txt and kda_txt.get("UIElement"):
					kda_str = f"{data.get('kills',0)}/{data.get('deaths',0)}/{data.get('assists',0)}"
					cs_str = f"({data.get('cs',0)} CS)"
					kda_txt.get("UIElement").setText(f"{kda_str} {cs_str}")
				
				# Update Gold
				gold_txt = entry.getChild("Gold_Text")
				if gold_txt and gold_txt.get("UIElement"):
					gold_txt.get("UIElement").setText(f"{int(data.get('gold',0))}G")
					
				# Phase 124: Death Timers
				timer_overlay = entry.getChild("Death_Timer_Overlay")
				timer_txt = entry.getChild("Timer_Text")
				respawn_t = p.getPy("PlayerController").respawnTimer if p.getPy("PlayerController") else 0
				
				if respawn_t > 0:
					if timer_overlay: timer_overlay.activate(scene)
					if timer_txt and timer_txt.get("UIElement"):
						timer_txt.get("UIElement").setText(str(int(respawn_t)))
				else:
					if timer_overlay: timer_overlay.deactivate(scene)
					
		# --- Phase 105: Global Objective Tracking (Scoreboard Footer) ---
		obj_mgr = MobaCommon.GlobalObjectiveManager
		for team_id in ["teamA", "teamB"]:
			counter_ent = self.background.getChild(f"{team_id.upper()}_Dragon_Icon")
			if counter_ent:
				stacks = obj_mgr.dragon_stacks.get(team_id, 0)
				text_ent = counter_ent.getChild("Count_Text")
				if text_ent:
					ui = text_ent.get("UIElement")
					if ui: ui.setText(str(stacks))
					
				# Team-wide Baron logic
				baron_glow = counter_ent.getChild("Baron_Aura")
				if baron_glow:
					is_active = any(p.getProperties().get("hasBaronBuff") for p in players if MobaCommon.get_entity_team(p) == team_id)
					if is_active: baron_glow.activate(scene)
					else: baron_glow.deactivate(scene)
				
				# Update Hero Icon
				icon_ent = entry.getChild("Hero_Icon")
				if icon_ent and icon_ent.get("Mesh"):
					mat = icon_ent.get("Mesh").getFinalMaterial()
					if mat:
						# Assuming heroName is stored in stats or can be derived
						match_hero = p.getProperties().get("heroName", "Unknown")
						mat.uniforms.set("u_icon", f"Icon_{match_hero}")

				# Update Items (Icons 1-6)
				items = data.get("items", [])
				for i in range(6):
					item_icon = entry.getChild(f"Item_{i+1}")
					if item_icon and item_icon.get("Mesh"):
						mat = item_icon.get("Mesh").getFinalMaterial()
						if mat:
							icon_name = MobaCommon.Templates.ICON_ITEM_DEFAULT
							if i < len(items):
								from Data import ItemRegistry
								item_data = ItemRegistry.ITEM_REGISTRY.get(items[i])
								if item_data: icon_name = item_data.get("icon", icon_name)
							mat.uniforms.set("u_icon", icon_name)

# Phase 115: Module-level alias so callers can use MobaUI.spawn_fct() directly
def spawn_fct(scene, pos, text, color=cave.Vector4(1,1,1,1)):
	"""Module-level FCT spawner (delegates to HUDController)."""
	HUDController.spawn_fct(scene, pos, text, color)

def broadcast_event(message):
	"""Phase 30: Systemic announcements in the middle of the screen."""
	# Logic to activate a banner and set text
	scene = cave.getScene()
	banner = scene.get("AnnouncementBanner")
	if banner:
		comp = banner.getPy("AnnouncementBanner")
		if comp: comp.display(message)

def trigger_kill_announcement(killer, victim, stats):
	"""Phase 132: Logic to determine if a kill should trigger a special announcement."""
	if not killer: return
	
	multi = stats.get("multi", 1)
	streak = stats.get("streak", 1)
	
	killer_name = killer.name.split("_")[-1] if hasattr(killer, 'name') else "Hero"
	victim_name = victim.name.split("_")[-1] if hasattr(victim, 'name') else "Hero"
	
	# Priority 1: Multi-Kills
	if multi >= 2:
		labels = {2: "DOUBLE KILL", 3: "TRIPLE KILL", 4: "QUADRA KILL", 5: "PENTA KILL"}
		sfx_map = {2: MobaCommon.Templates.SFX_DOUBLE_KILL, 3: MobaCommon.Templates.SFX_TRIPLE_KILL,
				   4: MobaCommon.Templates.SFX_QUADRA_KILL, 5: MobaCommon.Templates.SFX_PENTA_KILL}
		
		label = labels.get(multi, "PENTA KILL")
		sfx = sfx_map.get(multi, MobaCommon.Templates.SFX_PENTA_KILL)
		
		# Show with specialized backdrop
		show_announcement(f"{killer_name} - {label}", banner_type=label.split()[0])
		MobaCommon.play_sfx(cave.getScene(), sfx)
		return

	# Priority 2: High Streaks
	if streak >= 3:
		streak_labels = {
			3: "is on a KILLING SPREE!",
			4: "is RAMPAGING!",
			5: "is UNSTOPPABLE!",
			6: "is DOMINATING!",
			7: "is GODLIKE!",
			8: "is LEGENDARY!"
		}
		sfx_streak = {
			3: MobaCommon.Templates.SFX_STREAK_3, 4: MobaCommon.Templates.SFX_STREAK_4,
			5: MobaCommon.Templates.SFX_STREAK_5, 6: MobaCommon.Templates.SFX_STREAK_6,
			7: MobaCommon.Templates.SFX_STREAK_7, 8: MobaCommon.Templates.SFX_STREAK_8
		}
		
		msg = streak_labels.get(streak, streak_labels[8])
		sfx = sfx_streak.get(streak, sfx_streak[8])
		
		show_announcement(f"{killer_name} {msg}", banner_type="STREAK")
		MobaCommon.play_sfx(cave.getScene(), sfx)
		return

	# Priority 3: Shut Down
	victim_streak = MobaCommon.MatchStatsManager._get_stats(victim.name).get("current_streak", 0)
	if victim_streak >= 3:
		show_announcement(f"{killer_name} SHUT DOWN {victim_name}!", banner_type="SHUTDOWN")
		MobaCommon.play_sfx(cave.getScene(), MobaCommon.Templates.SFX_KILL)
		return

	# Default: Just a normal kill
	# In high-end MOBAs, we don't always announce every single normal kill with a big banner
	# but for this prototype, we will broadcast it.
	broadcast_event(f"{killer_name} has slain {victim_name}!")

def show_announcement(text, banner_type="DEFAULT"):
	"""Phase 32/37: High-priority global alerts with stylized backdrops."""
	scene = cave.getScene()
	banner = scene.get("GlobalAnnouncer")
	if banner:
		comp = banner.getPy("AnnouncementBanner")
		if comp: comp.display(text, priority=True, banner_type=banner_type)

def broadcast_ping(world_pos, team):
	# ... (preserved)
	pass

def trigger_screen_shake(pos, intensity=0.15):
	"""Phase 127: Triggers a camera shake if near the impact."""
	scene = cave.getScene()
	cam = scene.getCamera()  # Cave API: getCamera() not getMainCamera()
	if cam:
		comp = cam.getPy("CameraShakeComponent")
		if not comp: comp = cam.add("CameraShakeComponent")
		comp.shake(intensity)

def trigger_mesh_flash(entity):
	"""Phase 127: Makes the entity mesh flash white for impact feedback."""
	mesh_child = entity.getChild("Mesh")
	if not mesh_child: return
	
	comp = mesh_child.getPy("MeshFlashComponent")
	if not comp: comp = mesh_child.add("MeshFlashComponent")
	comp.flash()

def add_kill_feed(killer, victim):
	"""Phase 32: Combat log entry (Hero A killed Hero B)."""
	scene = cave.getScene()
	feed = scene.get("KillFeed")
	if feed:
		comp = feed.getPy("KillFeedManager")
		if comp: comp.add_entry(killer, victim)

class CameraShakeComponent(cave.Component):
	"""Phase 127: Strategic camera trauma on heavy impacts."""
	def start(self, scene):
		self.intensity = 0.0
		self.orig_pos = self.entity.getTransform().position.copy()  # Cave API: 'position' not 'localPosition'
		
	def shake(self, intensity):
		self.intensity = max(self.intensity, intensity)
		
	def update(self):
		if self.intensity > 0:
			dt = cave.getDeltaTime()
			import random as _rand
			off = cave.Vector3(_rand.uniform(-1,1), _rand.uniform(-1,1), 0) * self.intensity
			self.entity.getTransform().setPosition(self.orig_pos + off)  # Cave API: setPosition() for local
			self.intensity -= dt * 1.5
			if self.intensity <= 0:
				self.entity.getTransform().setPosition(self.orig_pos)  # Cave API: setPosition() for local

class MeshFlashComponent(cave.Component):
	"""Phase 127: High-fidelity white flash for impact feedback."""
	def start(self, scene):
		self.timer = 0.0
		
	def flash(self):
		self.timer = 0.08
		
	def update(self):
		if self.timer > 0:
			self.timer -= cave.getDeltaTime()
			mesh = self.entity.get("Mesh")
			if mesh:
				mat = mesh.getFinalMaterial()
				if mat: mat.uniforms.set("u_baseColor", cave.Vector4(4, 4, 4, 1)) # Overbright white
			if self.timer <= 0:
				if mesh:
					mat = mesh.getFinalMaterial()
					if mat: mat.uniforms.set("u_baseColor", cave.Vector4(1, 1, 1, 1))

class KillFeedManager(cave.Component):
	"""Handles a sliding list of recent combat events."""
	def start(self, scene):
		self.entries = [] # List of UI elements
		self.max_entries = 5
		
	def add_entry(self, killer, victim):
		scene = self.entity.getScene()
		# Template: UI_KillFeedItem (Requires Image for both heroes)
		# For now, we simulate with a print and a temporary UI object
		entry = scene.addFromTemplate("UI_KillFeedItem", cave.Vector3(0,0,0))
		if entry:
			entry.getTransform().setParent(self.entity.getTransform())
			# Logic to shift existing entries UP
			self.entries.append(entry)
			if len(self.entries) > self.max_entries:
				oldest = self.entries.pop(0)
				oldest.kill()
			
			self.reposition_entries()

	def reposition_entries(self):
		for i, entry in enumerate(self.entries):
			# Stack from bottom up or top down
			entry.getTransform().setPosition(0, i * -30, 0)

class ObjectiveTrackerComponent(cave.Component):
	"""Phase 124: Displays respawn timers for Epic Objectives (Spires/Colossus)."""
	def start(self, scene):
		self.timer_labels = {} # {id: text_el}
		# Find child labels for each objective
		for obj_id in ["COLOSSUS", "SPIRE_AMPLIFIED", "SPIRE_RESONANT", "SPIRE_VITAL", "SPIRE_FLUX"]:
			label = self.entity.getChild(f"Timer_{obj_id}")
			if label: self.timer_labels[obj_id] = label
			
	def update(self):
		scene = self.entity.getScene()
		mgr = MobaCommon.GlobalObjectiveManager
		
		for obj_id, label in self.timer_labels.items():
			timer = mgr.get_timer(obj_id)
			ui = label.get("UIElement")
			if not ui: continue
			
			if timer > 0:
				# Show time remaining (M:SS)
				mins = int(timer // 60)
				secs = int(timer % 60)
				ui.setText(f"{mins}:{secs:02d}")
				ui.color = cave.Vector4(1, 1, 0, 1) # Yellow for counting down
			else:
				# Objective is up!
				ui.setText("READY")
				ui.color = cave.Vector4(0, 1, 0, 1) # Green for ready

class AnnouncementBanner(cave.Component):
	"""Handles center-screen big text popups.
	Phase 132: Enhanced with priority queueing to prevent overlap.
	"""
	def start(self, scene):
		self.text_el = self.entity.getChild("Text")
		self.timer = 0.0
		self.queue = [] # Queue of (text, banner_type, duration)
		self.entity.deactivate(scene)
		
	def display(self, text, duration=3.0, priority=False, banner_type="DEFAULT"):
		# If something is already playing, queue it (unless it's a high priority interruption)
		if self.timer > 0 and not priority:
			self.queue.append((text, banner_type, duration))
			return

		scene = self.entity.getScene()
		self.entity.activate(scene)
		self.timer = duration
		
		# Phase 37: Specialized Backdrops
		for child in ["Backdrop_Default", "Backdrop_Double", "Backdrop_Triple", "Backdrop_Penta"]:
			c_ent = self.entity.getChild(child)
			if c_ent: c_ent.deactivate(scene)
			
		backdrop = self.entity.getChild(f"Backdrop_{banner_type}")
		if backdrop: backdrop.activate(scene)
		
		# Set text
		if self.text_el:
			ui = self.text_el.get("UIElement")
			if ui: ui.setText(text)
			
		# Play Announcer SFX
		sfx = MobaCommon.Templates.SFX_ANNOUNCER if priority else MobaCommon.Templates.SFX_EVENT
		MobaCommon.play_sfx(self.entity, sfx)
		
	def update(self):
		if self.timer > 0:
			self.timer -= cave.getDeltaTime()
			if self.timer <= 0:
				if self.queue:
					# Play next in queue
					next_text, next_type, next_dur = self.queue.pop(0)
					self.display(next_text, duration=next_dur, banner_type=next_type)
				else:
					self.entity.deactivate(self.entity.getScene())

def broadcast_victory(team):
	"""Phase 30: Final game results sequence."""
	scene = cave.getScene()
	victory_ent = scene.get("VictoryScreen")
	if victory_ent:
		comp = victory_ent.getPy("VictoryScreenController")
		if comp:
			comp.show(team)

class VictoryScreenController(cave.Component):
	"""Handles the full-screen victory/defeat banner."""
	def start(self, scene):
		self.banner = self.entity.getChild("Banner")
		if self.banner: self.banner.deactivate(scene)
		
	def show(self, winning_team):
		scene = self.entity.getScene()
		if self.banner: self.banner.activate(scene)
		
		# 1. Determine local player victory status
		player_list = MobaCommon.EntityRegistry.get("player")
		player = player_list[0] if player_list else None
		p_team = player.getProperties().get("team") if player else "teamA"
		is_victory = (p_team == winning_team)
		
		# 2. Visuals & SFX
		sfx = MobaCommon.Templates.SFX_VICTORY if is_victory else MobaCommon.Templates.SFX_DEFEAT
		MobaCommon.play_sfx(self.entity, sfx)
		
		MobaCommon.is_match_over = True
		
		status_ent = self.banner.getChild("Status_Text")
		if status_ent:
			ui = status_ent.get("UIElement")
			if ui: ui.setText("VICTORY" if is_victory else "DEFEAT")

		# 3. Build Stats Summary Table
		all_stats = MobaCommon.MatchStatsManager.get_all_stats()
		
		# Filter for Heroes only (Player or Bot)
		# We assume heroes have names like "Player_..." or "Bot_..."
		hero_stats = {}
		for uid, s in all_stats.items():
			if "Player" in uid or "Bot" in uid or "Hero" in uid:
				hero_stats[uid] = s
		
		if not hero_stats: hero_stats = all_stats # Fallback if naming convention differs
		
		# Find highest stats for scaling
		max_dmg = 1.0
		max_vision = 1.0
		max_obj = 1.0
		mvp_uid = None
		mvp_score = -1
		
		for uid, s in hero_stats.items():
			max_dmg = max(max_dmg, s.get("damage", 0))
			max_vision = max(max_vision, s.get("visionScore", 0))
			max_obj = max(max_obj, s.get("objectiveDamage", 0))
			
			# MVP Score Calculation: K*3 + A*2 - D + (Dmg/1000) + (Vision*2)
			score = (s.get("kills",0)*3 + s.get("assists",0)*2 - s.get("deaths",0) + 
					 (s.get("damage",0)/1000.0) + (s.get("visionScore",0)*2))
			if score > mvp_score:
				mvp_score = score
				mvp_uid = uid
		
		# 4. Save to Match History (Phase 115)
		MobaCommon.save_match_result(winning_team, hero_stats)
		
		# 5. Populate Analytics Table
		container = self.banner.getChild("Stats_Container")
		if container:
			# Sort by MVP score
			sorted_uids = sorted(hero_stats.keys(), key=lambda x: (
				(hero_stats[x].get("kills",0)*3 + hero_stats[x].get("assists",0)*2 - hero_stats[x].get("deaths",0) + 
				 (hero_stats[x].get("damage",0)/1000.0) + (hero_stats[x].get("visionScore",0)*2))
			), reverse=True)
			
			for i, uid in enumerate(sorted_uids):
				s = hero_stats[uid]
				hero_name = uid.split("_")[-1]
				row = container.getChild(f"Row_{i}")
				if not row: continue
				
				row.activate(scene)
				# Basic Info
				if row.getChild("Name"): 
					prefix = "[MVP] " if uid == mvp_uid else ""
					row.getChild("Name").get("UIElement").setText(f"{prefix}{hero_name}")
				
				# KDA & CS
				if row.getChild("KDA"): 
					row.getChild("KDA").get("UIElement").setText(f"{s['kills']}/{s['deaths']}/{s['assists']} ({s['cs']} CS)")
				
				# Graphs
				dmg_bar = row.getChild("Damage_Bar")
				if dmg_bar:
					pct = s.get("damage", 0) / max_dmg
					dmg_bar.getTransform().setScale(pct, 1.0, 1.0)
					if dmg_bar.getChild("Val"): dmg_bar.getChild("Val").get("UIElement").setText(f"DMG: {int(s['damage'])}")
				
				vis_bar = row.getChild("Vision_Bar")
				if vis_bar:
					pct = s.get("visionScore", 0) / max_vision
					vis_bar.getTransform().setScale(pct, 1.0, 1.0)
					if vis_bar.getChild("Val"): vis_bar.getChild("Val").get("UIElement").setText(f"VIS: {s['visionScore']}")
					
				obj_bar = row.getChild("Objective_Bar")
				if obj_bar:
					pct = s.get("objectiveDamage", 0) / max_obj
					obj_bar.getTransform().setScale(pct, 1.0, 1.0)
					if obj_bar.getChild("Val"): obj_bar.getChild("Val").get("UIElement").setText(f"OBJ: {int(s['objectiveDamage'])}")
		else:
			# Fallback Multi-Stat View
			stats_text = self.banner.getChild("Stats_Text")
			if stats_text:
				ui = stats_text.get("UIElement")
				if ui:
					summary = "MATCH SUMMARY (TOP DAMAGE):\n"
					sorted_all = sorted(hero_stats.keys(), key=lambda x: hero_stats[x].get("damage", 0), reverse=True)
					for uid in sorted_all[:5]:
						s = hero_stats[uid]
						name = uid.split("_")[-1]
						kda = f"{s['kills']}/{s['deaths']}/{s['assists']}"
						summary += f"{name:12} | KDA: {kda:8} | DMG: {int(s['damage']):6} | HEAL: {int(s['healing']):5}\n"
					ui.setText(summary)

	def update(self):
		if self.banner and self.banner.isActive():
			if cave.getEvents().pressed(cave.event.KEY_RETURN):
				try:
					# Phase 70: Reset safety flag BEFORE scene transition
					MobaCommon.is_match_over = False
					cave.restartCurrentScene()
				except:
					pass

class DraftingController(cave.Component):
	"""Phase 130: Advanced Hero Drafting Interface."""
	def start(self, scene):
		self.timer = 60.0
		self.selected_hero = "Kael" # Default selection
		self.is_locked = False
		self.last_pop_time = 0.0
		
		# UI Elements
		self.root = self.entity.getChild("Draft_Root")
		self.grid = self.entity.getChild("Hero_Grid")
		self.preview = self.entity.getChild("Preview_Panel")
		
		if self.root: self.root.activate(scene)
		MobaCommon.is_match_over = False # Ensure logic runs
		
	def update(self):
		if self.is_locked: return
		
		dt = cave.getDeltaTime()
		scene = self.entity.getScene()
		self.timer -= dt
		
		# Pulse animation on timer for hype
		if self.timer < 10.0 and (scene.getElapsedSceneTime() - self.last_pop_time) > 1.0:
			self.last_pop_time = scene.getElapsedSceneTime()
			MobaCommon.play_sfx(self.entity, MobaCommon.Templates.SFX_ANNOUNCEMENT)
			
		if self.timer <= 0:
			self.lock_in()
			
		# Update Timer UI
		timer_ent = self.entity.getChild("Timer_Text")
		if timer_ent:
			ui = timer_ent.get("UIElement")
			if ui: ui.setText(str(int(self.timer)))

	def select_hero(self, hero_name):
		"""Called via UI Event from Hero Grid buttons."""
		if self.is_locked: return
		self.selected_hero = hero_name
		self.update_preview(hero_name)
		MobaCommon.play_sfx(self.entity, MobaCommon.Templates.SFX_UI_CLICK)

	def update_preview(self, hero_name):
		from Data import HeroRegistry
		data = HeroRegistry.HERO_REGISTRY.get(hero_name, {})
		
		# Update Splash
		splash_ent = self.entity.getChild("Preview_Splash")
		if splash_ent:
			mesh = splash_ent.get("Mesh")
			if mesh:
				mat = mesh.getFinalMaterial()
				if mat: mat.uniforms.set("u_icon", data.get("splash", ""))
				
		# Update Name & Stats
		name_ent = self.entity.getChild("Preview_Name")
		if name_ent: name_ent.get("UIElement").setText(hero_name.upper())
		
	def lock_in(self):
		if self.is_locked: return
		self.is_locked = True
		MobaCommon.play_sfx(self.entity, MobaCommon.Templates.SFX_UI_CONFIRM)
		
		# Transition to match start
		self.entity.deactivate(self.entity.getScene())
		# MobaCommon.MatchState.current = MobaCommon.MatchState.LOADING

# ── Phase 131: CC Duration Bar (Feature 2) ──────────────────────────
class CCStatusBarController(cave.Component):
	"""Shows a bar above the player indicating remaining CC duration."""
	def start(self, scene):
		self.bar = self.entity.getChild("CC_Fill")
		self.label = self.entity.getChild("CC_Label")
		self.entity.deactivate(scene)
		
	def show(self, cc_name, duration):
		scene = self.entity.getScene()
		self.entity.activate(scene)
		self.total = duration
		self.remaining = duration
		if self.label:
			ui = self.label.get("UIElement")
			if ui: ui.setText(cc_name.upper())
		
	def update(self):
		if self.remaining <= 0:
			self.entity.deactivate(self.entity.getScene())
			return
		self.remaining -= cave.getDeltaTime()
		if self.bar:
			pct = max(0, self.remaining / self.total)
			self.bar.getTransform().setScale(pct, 1.0, 1.0)

# ── Phase 131: Damage Recap Panel (Feature 4) ───────────────────────
class DamageRecapController(cave.Component):
	"""Shows last 3 damage sources when you die."""
	def start(self, scene):
		self.entries = [] # list of {source, amount, type, time}
		self.max_entries = 3
		self.panel = self.entity.getChild("Recap_Panel")
		if self.panel: self.panel.deactivate(scene)
		
	def record_damage(self, source_name, amount, dmg_type):
		entry = {"source": source_name, "amount": int(amount), "type": dmg_type}
		self.entries.append(entry)
		if len(self.entries) > 10:
			self.entries = self.entries[-10:]
		
	def show_on_death(self):
		scene = self.entity.getScene()
		if self.panel: self.panel.activate(scene)
		top3 = sorted(self.entries, key=lambda x: x["amount"], reverse=True)[:3]
		for i, entry in enumerate(top3):
			row = self.panel.getChild(f"Recap_Row_{i}") if self.panel else None
			if not row: continue
			row.activate(scene)
			src = row.getChild("Source")
			if src:
				ui = src.get("UIElement")
				if ui: ui.setText(entry["source"])
			val = row.getChild("Value")
			if val:
				ui = val.get("UIElement")
				if ui: ui.setText(str(entry["amount"]))
		self.entries = []
		
	def hide(self):
		if self.panel: self.panel.deactivate(self.entity.getScene())

# ── Phase 131: Settings Menu (Feature 5) ─────────────────────────────
class SettingsMenuController(cave.Component):
	"""In-game settings: keybinds, audio, video."""
	def start(self, scene):
		self.is_open = False
		self.panel = self.entity.getChild("Settings_Panel")
		if self.panel: self.panel.deactivate(scene)
		
		# Default settings
		self.settings = {
			"master_volume": 1.0,
			"sfx_volume": 0.8,
			"music_volume": 0.5,
			"quick_cast_all": False,
			"quick_cast": {"Q": False, "W": False, "E": False, "R": False},
			"show_range": True,
		}
		
	def update(self):
		events = cave.getEvents()
		if events.pressed(cave.event.KEY_ESCAPE):
			self.toggle()
			
	def toggle(self):
		self.is_open = not self.is_open
		scene = self.entity.getScene()
		if self.panel:
			if self.is_open:
				self.panel.activate(scene)
			else:
				self.panel.deactivate(scene)
				self.apply_settings()
		
	def apply_settings(self):
		"""Push settings to the relevant systems."""
		# NOTE: cave.getAudioDevice() does NOT exist in Cave Engine API.
		# Volume control must be managed per-AudioTrackInstance.
		# TODO: Implement volume control via stored AudioTrackInstance references.
		# audio = cave.getAudioDevice()  # REMOVED — non-existent API
		# Push quick cast to player
		players = MobaCommon.EntityRegistry.get("player")
		if players:
			pc = players[0].getPy("PlayerController")
			if pc:
				pc.quickCastSettings = self.settings["quick_cast"]

# ── Phase 131: Recall Channel Bar (Feature 8) ───────────────────────
class RecallBarController(cave.Component):
	"""Shows a progress bar during recall channeling."""
	def start(self, scene):
		self.bar = self.entity.getChild("Recall_Fill")
		self.text = self.entity.getChild("Recall_Text")
		self.entity.deactivate(scene)
		self.duration = 8.0
		self.elapsed = 0.0
		self.active = False
		
	def begin_recall(self, duration=8.0):
		self.duration = duration
		self.elapsed = 0.0
		self.active = True
		self.entity.activate(self.entity.getScene())
		if self.text:
			ui = self.text.get("UIElement")
			if ui: ui.setText("RECALLING...")
		
	def cancel(self):
		self.active = False
		self.entity.deactivate(self.entity.getScene())
		
	def update(self):
		if not self.active: return
		self.elapsed += cave.getDeltaTime()
		pct = cave.math.clamp(self.elapsed / self.duration, 0, 1)
		if self.bar:
			self.bar.getTransform().setScale(pct, 1.0, 1.0)
		if self.elapsed >= self.duration:
			self.active = False
			self.entity.deactivate(self.entity.getScene())
