import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon

# ──────────────────────────────────────────────
# Death & Respawn System + Passive Gold Income
# ──────────────────────────────────────────────


class DeathManager(cave.Component):
	"""Handles hero death, gray screen overlay, respawn timer, and passive gold income.
	
	Attach to every hero entity alongside PlayerController.
	Cave Engine 1.4: Plain Python class with start(scene) and update() hooks.
	"""

	# LoL death timer formula: base + (level * per_level) after minute scaling
	BASE_TIMER = 6.0
	PER_LEVEL = 2.0
	MAX_TIMER = 52.5

	# Passive gold income (gold per second, starts after 2 min)
	GOLD_PER_SECOND = 2.04
	GOLD_START_TIME = 120.0  # 2 minutes before gold starts ticking

	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		self.transf = self.entity.getTransform()

		# Death state
		self.is_dead = False
		self.death_timer = 0.0
		self.max_death_timer = 0.0
		self.spawn_pos = self.transf.worldPosition.copy()

		# Store spawn position (fountain)
		team = MobaCommon.get_entity_team(self.entity)
		# FIX: EntityRegistry tracks "teamA_fountain"/"teamB_fountain", not "fountain"
		fountains = MobaCommon.EntityRegistry.get(team + "_fountain")
		for f in fountains:
			if f.isActive():
				self.spawn_pos = f.getTransform().worldPosition.copy()
				break

		# Gold income tracking
		self.gold_timer = 0.0

		# Gray screen overlay reference (child entity named "DeathOverlay")
		self.death_overlay = self.entity.getChild("DeathOverlay")
		if self.death_overlay:
			self.death_overlay.deactivate(scene)

	def update(self):
		if MobaCommon.is_match_over:
			return

		dt = cave.getDeltaTime()
		scene = self.entity.getScene()
		if not scene:
			return

		# ─── Passive Gold Income ─────────────────────
		if not self.is_dead and self.pc:
			match_time = scene.getElapsedSceneTime()
			if match_time >= self.GOLD_START_TIME:
				self.gold_timer += dt
				if self.gold_timer >= 1.0:
					self.gold_timer -= 1.0
					self.pc.gold = getattr(self.pc, 'gold', 0) + self.GOLD_PER_SECOND

		# ─── Death Timer ─────────────────────────────
		if self.is_dead:
			self.death_timer -= dt
			if self.death_timer <= 0:
				self._respawn(scene)

	def on_death(self, killer=None):
		"""Called when this hero's HP reaches 0.
		
		Should be called by the damage system in MobaCommon or Player Toolkit.
		"""
		if self.is_dead:
			return

		self.is_dead = True
		scene = self.entity.getScene()

		# Calculate death timer based on level
		level = getattr(self.pc, 'level', 1)
		match_time = scene.getElapsedSceneTime() if scene else 0

		# LoL formula: BRW (base respawn wait) increases with time
		brw = self.BASE_TIMER + (level * self.PER_LEVEL)
		# Time scaling: after 15 min, timer increases by 0.5% per min
		if match_time > 900:  # 15 minutes
			extra_minutes = (match_time - 900) / 60.0
			time_factor = 1.0 + (extra_minutes * 0.005)
			brw *= time_factor

		self.death_timer = min(brw, self.MAX_TIMER)
		self.max_death_timer = self.death_timer

		# Disable the entity visually
		# Use deactivate to hide the entity but keep this component running
		# Instead, we disable movement and make untargetable
		ec = self.entity.getPy("EffectComponent")
		if ec:
			ec.apply("dead", self.death_timer + 1.0,
					 flags=MobaCommon.EffectFlags.UNTARGETABLE | MobaCommon.EffectFlags.INVULNERABLE)

		# Stop movement
		character = self.entity.get("Character")
		if character:
			character.setWalkDirection(0, 0, 0)

		# Show gray screen overlay
		if self.death_overlay and scene:
			self.death_overlay.activate(scene)

		# Play death animation
		animator = self.entity.get("Animation")
		if animator:
			try:
				animator.playByName("p-death", 0.1)
			except Exception:
				pass

		# VFX/SFX
		if scene:
			MobaCommon.spawn_vfx(scene, "VFX_Death_Burst", self.transf.worldPosition)
			MobaCommon.play_sfx(self.entity, "SFX_Hero_Death")

		# Track stats
		stats_delta = {"multi": 1, "streak": 1}
		if killer:
			killer_uid = killer.name if hasattr(killer, 'name') else "unknown"
			stats_delta = MobaCommon.MatchStatsManager.track_kill(killer_uid)
		MobaCommon.MatchStatsManager.track_death(self.entity.name)

		# Kill feed & Announcer
		try:
			from UI import MobaUI
			MobaUI.add_kill_feed(killer, self.entity)
			# Phase 132: Global Announcer Trigger
			MobaUI.trigger_kill_announcement(killer, self.entity, stats_delta)
		except Exception as e:
			print(f"Announcer Error: {e}")

	def _respawn(self, scene):
		"""Teleport hero back to fountain and restore to full."""
		self.is_dead = False
		self.death_timer = 0.0

		# Teleport to spawn
		self.transf.setPosition(self.spawn_pos.x, self.spawn_pos.y, self.spawn_pos.z)

		# Restore HP/Mana
		props = self.entity.getProperties()
		max_hp = props.get("maxHealth", 1000)
		max_mana = props.get("maxMana", 500)
		props["health"] = max_hp
		props["mana"] = max_mana

		# Clear dead debuff
		ec = self.entity.getPy("EffectComponent")
		if ec:
			ec.apply("dead", 0.0)  # Clear by setting duration to 0

		# Hide death overlay
		if self.death_overlay and scene:
			self.death_overlay.deactivate(scene)

		# Play idle animation
		animator = self.entity.get("Animation")
		if animator:
			try:
				animator.playByName("p-idle", 0.2, loop=True)
			except Exception:
				pass

		# VFX
		if scene:
			MobaCommon.spawn_vfx(scene, "VFX_Respawn", self.spawn_pos)
			MobaCommon.play_sfx(self.entity, "SFX_Respawn")

	def get_respawn_progress(self):
		"""Returns 0.0 to 1.0 progress toward respawn (for UI bar)."""
		if not self.is_dead or self.max_death_timer <= 0:
			return 1.0
		return 1.0 - (self.death_timer / self.max_death_timer)

	def get_timer_text(self):
		"""Returns formatted death timer string for UI (e.g. '12.5')."""
		if not self.is_dead:
			return ""
		return f"{max(0, self.death_timer):.1f}"
