import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon

# ──────────────────────────────────────────────
# Extended HUD Components
# Summoner Spell Slots, Death Timer, CS, XP, Stats, Skill Levels
# ──────────────────────────────────────────────


class SummonerSpellHUD:
	"""Displays the D and F summoner spell slots with cooldown overlays.
	
	Expected entity hierarchy:
	  - Icon_Spell_D (child) — icon mesh
	  - Icon_Spell_F (child) — icon mesh
	  - CD_Spell_D (child) — cooldown overlay
	  - CD_Spell_F (child) — cooldown overlay
	"""

	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		self.icon_d = self.entity.getChild("Icon_Spell_D")
		self.icon_f = self.entity.getChild("Icon_Spell_F")
		self.cd_d = self.entity.getChild("CD_Spell_D")
		self.cd_f = self.entity.getChild("CD_Spell_F")
		self.update_timer = 0.0

	def update(self):
		dt = cave.getDeltaTime()
		self.update_timer += dt
		if self.update_timer < 0.1:  # Throttle: 10 Hz
			return
		self.update_timer = 0.0

		if not self.pc:
			return

		ssm = getattr(self.pc, 'summonerSpells', None)
		if not ssm:
			return

		scene = self.entity.getScene()

		for slot_key, icon_ent, cd_ent in [("D", self.icon_d, self.cd_d), ("F", self.icon_f, self.cd_f)]:
			cd_remaining = ssm.get_cooldown_remaining(slot_key)
			cd_max = ssm.get_cooldown_max(slot_key)

			if cd_ent and scene:
				if cd_remaining > 0:
					cd_ent.activate(scene)
					progress = max(0, min(1, cd_remaining / cd_max)) if cd_max > 0 else 0
					cd_ent.getTransform().setScale(1.0, progress, 1.0)

					# Show timer text
					ui = cd_ent.get("UIElement")
					if ui:
						ui.setText(f"{int(cd_remaining)}")
				else:
					cd_ent.deactivate(scene)


class DeathTimerHUD:
	"""Shows a death timer overlay and countdown when the player is dead.
	
	Expected entity hierarchy:
	  - Death_Overlay (child) — full-screen gray tint
	  - Death_Timer_Text (child) — countdown text
	  - Death_Progress_Bar (child) — respawn progress bar
	"""

	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		self.overlay = self.entity.getChild("Death_Overlay")
		self.timer_text = self.entity.getChild("Death_Timer_Text")
		self.progress_bar = self.entity.getChild("Death_Progress_Bar")

		if self.overlay:
			self.overlay.deactivate(scene)

	def update(self):
		scene = self.entity.getScene()
		if not scene or not self.pc:
			return

		dm = self.entity.getPy("DeathManager")
		if not dm:
			return

		if dm.is_dead:
			# Show overlay
			if self.overlay and not self.overlay.isActive():
				self.overlay.activate(scene)

			# Update timer text
			if self.timer_text:
				ui = self.timer_text.get("UIElement")
				if ui:
					ui.setText(dm.get_timer_text())

			# Update progress bar
			if self.progress_bar:
				progress = dm.get_respawn_progress()
				self.progress_bar.getTransform().setScale(progress, 1.0, 1.0)
		else:
			if self.overlay and self.overlay.isActive():
				self.overlay.deactivate(scene)


class CSCounterHUD:
	"""Displays the player's Creep Score (minion/monster kills).
	
	Expected entity child: CS_Text
	"""

	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		self.text_ent = self.entity.getChild("CS_Text")
		self.update_timer = 0.0

	def update(self):
		dt = cave.getDeltaTime()
		self.update_timer += dt
		if self.update_timer < 0.5:  # 2 Hz is enough
			return
		self.update_timer = 0.0

		if not self.pc or not self.text_ent:
			return

		cs = getattr(self.pc, 'cs_count', 0)
		ui = self.text_ent.get("UIElement")
		if ui:
			ui.setText(f"CS: {cs}")


class XPBarHUD:
	"""Displays the player's XP progress bar toward next level.
	
	Expected children:
	  - XP_Bar_Fill (child) — scaled by progress
	  - Level_Text (child) — shows current level
	"""

	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		self.fill = self.entity.getChild("XP_Bar_Fill")
		self.level_text = self.entity.getChild("Level_Text")
		self.update_timer = 0.0

	def update(self):
		dt = cave.getDeltaTime()
		self.update_timer += dt
		if self.update_timer < 0.2:  # 5 Hz
			return
		self.update_timer = 0.0

		if not self.pc:
			return

		# XP thresholds per level (LoL standard, cumulative)
		xp_thresholds = [0, 280, 660, 1140, 1720, 2400, 3180, 4060, 5040,
						 6120, 7300, 8580, 9960, 11440, 13020, 14700, 16480, 18360]

		level = getattr(self.pc, 'level', 1)
		current_xp = getattr(self.pc, 'xp', 0)

		if self.level_text:
			ui = self.level_text.get("UIElement")
			if ui:
				ui.setText(str(level))

		if self.fill:
			if level >= 18:
				self.fill.getTransform().setScale(1.0, 1.0, 1.0)
			else:
				xp_for_current = xp_thresholds[level - 1] if level <= len(xp_thresholds) else 0
				xp_for_next = xp_thresholds[level] if level < len(xp_thresholds) else xp_for_current + 1000
				xp_in_level = current_xp - xp_for_current
				xp_needed = xp_for_next - xp_for_current
				progress = max(0, min(1, xp_in_level / max(xp_needed, 1)))
				self.fill.getTransform().setScale(progress, 1.0, 1.0)


class StatPanelHUD:
	"""Displays AD, AP, Armor, MR, AS, MS stats.
	
	Expected children: Stat_AD, Stat_AP, Stat_Armor, Stat_MR, Stat_AS, Stat_MS
	"""

	STAT_KEYS = ["AD", "AP", "Armor", "MR", "AS", "MS"]

	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		self.labels = {}
		for key in self.STAT_KEYS:
			child = self.entity.getChild(f"Stat_{key}")
			if child:
				self.labels[key] = child
		self.update_timer = 0.0

	def update(self):
		dt = cave.getDeltaTime()
		self.update_timer += dt
		if self.update_timer < 0.5:  # 2 Hz
			return
		self.update_timer = 0.0

		if not self.pc:
			return

		# Map stat names to PlayerController attributes
		stat_map = {
			"AD": ("attackDamage", 0),
			"AP": ("abilityPower", 0),
			"Armor": ("armor", 0),
			"MR": ("magicResist", 0),
			"AS": ("attackSpeed", 0),
			"MS": ("moveSpeed", 0)
		}

		for key, (attr, default) in stat_map.items():
			if key in self.labels:
				val = getattr(self.pc, attr, default)
				ui = self.labels[key].get("UIElement")
				if ui:
					if key == "AS":
						ui.setText(f"{val:.2f}")
					else:
						ui.setText(str(int(val)))


class SkillLevelDotsHUD:
	"""Shows level indicators (1-5 dots) for each ability Q/W/E/R.
	
	Expected children per skill: Dot_Q_1 through Dot_Q_5, Dot_W_1 through Dot_W_5, etc.
	Active dots are lit up, inactive are dimmed.
	"""

	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		self.dots = {}  # {"Q": [ent1, ent2, ..., ent5], ...}

		for key in ["Q", "W", "E", "R"]:
			self.dots[key] = []
			for i in range(1, 6):
				dot = self.entity.getChild(f"Dot_{key}_{i}")
				self.dots[key].append(dot)

		self.update_timer = 0.0

	def update(self):
		dt = cave.getDeltaTime()
		self.update_timer += dt
		if self.update_timer < 0.5:  # 2 Hz
			return
		self.update_timer = 0.0

		if not self.pc:
			return

		scene = self.entity.getScene()
		if not scene:
			return

		skill_levels = getattr(self.pc, 'skillLevels', {"Q": 0, "W": 0, "E": 0, "R": 0})

		for key in ["Q", "W", "E", "R"]:
			level = skill_levels.get(key, 0)
			for i, dot in enumerate(self.dots[key]):
				if dot:
					if i < level:
						dot.activate(scene)
					else:
						dot.deactivate(scene)
