import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon
import math

# ──────────────────────────────────────────────
# Summoner Spell Registry — LoL-style D/F spells
# ──────────────────────────────────────────────

SPELL_REGISTRY = {
	"Flash": {
		"cd": 300.0,
		"range": 8.0,
		"description": "Instantly teleport a short distance toward your cursor.",
		"icon": "Icon_Spell_Flash"
	},
	"Ignite": {
		"cd": 180.0,
		"range": 6.0,
		"damage": 70,           # Base true damage (scales: 70 + 20*level over 5s)
		"duration": 5.0,
		"tick_rate": 0.5,
		"description": "Set a target on fire, dealing true damage over 5s and applying Grievous Wounds.",
		"icon": "Icon_Spell_Ignite"
	},
	"Smite": {
		"cd": 90.0,
		"range": 5.0,
		"damage": 900,          # True damage to monsters
		"heal_percent": 0.10,   # Heal 10% max HP on use
		"description": "Deal heavy true damage to a jungle monster or minion.",
		"icon": "Icon_Spell_Smite"
	},
	"Teleport": {
		"cd": 360.0,
		"channel_time": 4.0,
		"description": "Channel for 4 seconds, then teleport to a friendly turret or ward.",
		"icon": "Icon_Spell_Teleport"
	},
	"Ghost": {
		"cd": 210.0,
		"duration": 10.0,
		"speed_bonus": 0.28,    # 28% bonus movement speed
		"description": "Gain 28% movement speed for 10 seconds.",
		"icon": "Icon_Spell_Ghost"
	},
	"Heal": {
		"cd": 240.0,
		"heal_base": 90,        # Scales: 90 + 15*level
		"speed_duration": 1.0,
		"speed_bonus": 0.30,
		"description": "Heal yourself and a nearby ally. Briefly gain movement speed.",
		"icon": "Icon_Spell_Heal"
	},
	"Barrier": {
		"cd": 180.0,
		"shield_base": 115,     # Scales: 115 + 10*level
		"duration": 2.5,
		"description": "Shield yourself for 2.5 seconds.",
		"icon": "Icon_Spell_Barrier"
	},
	"Exhaust": {
		"cd": 210.0,
		"range": 6.5,
		"duration": 3.0,
		"slow_amount": 0.30,	# 30% slow
		"damage_reduction": 0.40,  # 40% damage reduction on target
		"description": "Slow a target enemy and reduce their damage output.",
		"icon": "Icon_Spell_Exhaust"
	},
	"Cleanse": {
		"cd": 210.0,
		"description": "Remove all crowd control effects from yourself.",
		"icon": "Icon_Spell_Cleanse"
	}
}


class SummonerSpellManager:
	"""Manages two summoner spells (D and F slots) for a PlayerController."""

	def __init__(self, player_controller, spell_d_id="Flash", spell_f_id="Ignite"):
		self.pc = player_controller
		self.entity = player_controller.entity
		self.spells = {
			"D": {"id": spell_d_id, "cd_remaining": 0.0},
			"F": {"id": spell_f_id, "cd_remaining": 0.0}
		}

	def update(self, dt):
		"""Tick cooldowns down each frame."""
		for slot in self.spells.values():
			if slot["cd_remaining"] > 0:
				slot["cd_remaining"] -= dt

	def try_cast(self, slot_key):
		"""Attempt to cast the spell in slot D or F. Returns True on success."""
		if slot_key not in self.spells:
			return False

		slot = self.spells[slot_key]
		spell_id = slot["id"]
		data = SPELL_REGISTRY.get(spell_id)
		if not data:
			return False

		# Check cooldown
		if slot["cd_remaining"] > 0:
			return False

		# Check CC (can't cast while stunned, except Cleanse)
		ec = self.entity.getPy("EffectComponent")
		if ec and ec.is_cced() and spell_id != "Cleanse":
			return False

		# Execute spell logic
		success = self._execute_spell(spell_id, data)
		if success:
			slot["cd_remaining"] = data["cd"]
		return success

	def get_cooldown_remaining(self, slot_key):
		"""Returns remaining cooldown for a slot."""
		if slot_key in self.spells:
			return max(0, self.spells[slot_key]["cd_remaining"])
		return 0

	def get_cooldown_max(self, slot_key):
		"""Returns max cooldown for a slot."""
		if slot_key in self.spells:
			data = SPELL_REGISTRY.get(self.spells[slot_key]["id"])
			return data["cd"] if data else 0
		return 0

	def get_spell_id(self, slot_key):
		"""Returns the spell name for a slot."""
		if slot_key in self.spells:
			return self.spells[slot_key]["id"]
		return None

	# ─── Spell Implementations ───────────────────────

	def _execute_spell(self, spell_id, data):
		"""Route to specific spell logic."""
		scene = self.entity.getScene()
		if not scene:
			return False

		if spell_id == "Flash":
			return self._cast_flash(scene, data)
		elif spell_id == "Ignite":
			return self._cast_ignite(scene, data)
		elif spell_id == "Smite":
			return self._cast_smite(scene, data)
		elif spell_id == "Teleport":
			return self._cast_teleport(scene, data)
		elif spell_id == "Ghost":
			return self._cast_ghost(scene, data)
		elif spell_id == "Heal":
			return self._cast_heal(scene, data)
		elif spell_id == "Barrier":
			return self._cast_barrier(scene, data)
		elif spell_id == "Exhaust":
			return self._cast_exhaust(scene, data)
		elif spell_id == "Cleanse":
			return self._cast_cleanse(scene, data)
		return False

	def _cast_flash(self, scene, data):
		"""BLINK: Instant teleport toward cursor/movement target."""
		transf = self.entity.getTransform()
		pos = transf.worldPosition
		forward = transf.getForwardVector()
		flash_range = data["range"]

		# Teleport forward (toward facing direction)
		new_pos = cave.Vector3(
			pos.x + forward.x * flash_range,
			pos.y,
			pos.z + forward.z * flash_range
		)
		transf.setPosition(new_pos.x, new_pos.y, new_pos.z)

		# VFX at origin and destination
		MobaCommon.spawn_vfx(scene, "VFX_Flash_Origin", pos)
		MobaCommon.spawn_vfx(scene, "VFX_Flash_Dest", new_pos)
		MobaCommon.play_sfx(self.entity, "SFX_Flash")
		return True

	def _cast_ignite(self, scene, data):
		"""DOT: Apply true damage over time + Grievous Wounds to nearest enemy."""
		my_pos = self.entity.getTransform().worldPosition
		target = MobaCommon.get_closest_target(my_pos, data["range"], self.entity)
		if not target:
			return False

		# Calculate damage: 70 + 20 * level
		level = getattr(self.pc, 'level', 1)
		total_dmg = data["damage"] + (20 * level)
		dmg_per_tick = total_dmg / (data["duration"] / data["tick_rate"])

		# Apply DoT
		MobaCommon.apply_dot(
			target, dmg_per_tick, data["duration"],
			data["tick_rate"], self.entity, MobaCommon.DamageType.TRUE
		)

		# Apply Grievous Wounds (reduce healing by 40% for duration)
		ec = target.getPy("EffectComponent")
		if ec:
			ec.apply("ignite_grievous", data["duration"],
					 flags=MobaCommon.EffectFlags.BLEED, magnitude=0.4)

		MobaCommon.spawn_vfx(scene, "VFX_Ignite", target.getTransform().worldPosition)
		MobaCommon.play_sfx(target, "SFX_Ignite")
		return True

	def _cast_smite(self, scene, data):
		"""Instant true damage to a monster or minion. Evolved to hit heroes."""
		my_pos = self.entity.getTransform().worldPosition
		is_evolved = getattr(self.pc, 'large_monsters_killed', 0) >= 20
		
		# Find closest valid target (Monsters/Minions always, Heroes if evolved)
		target = None
		best_dist = float('inf')
		search_radius = data["range"]
		
		for e in MobaCommon.get_entities_in_radius(scene, my_pos, search_radius):
			if not e.isActive(): continue
			# Check if hero targeting is allowed
			is_valid_target = e.hasTag("monster") or e.hasTag("minion")
			if is_evolved and e.hasTag("player") and not e.hasTag(MobaCommon.get_entity_team(self.entity)):
				is_valid_target = True
				
			if is_valid_target:
				d = (e.getTransform().worldPosition - my_pos).length()
				if d < best_dist:
					best_dist = d
					target = e
					
		if not target:
			return False

		# 1. Monster/Minion Execution
		if target.hasTag("monster") or target.hasTag("minion"):
			dmg = (1200 if is_evolved else 900)
			MobaCommon.apply_damage(target, dmg, MobaCommon.DamageType.TRUE, self.entity)
			MobaCommon.spawn_vfx(scene, "VFX_Smite_Monster", target.getTransform().worldPosition)
			MobaCommon.apply_heal(self.entity, self.pc.maxHP * 0.1)
		
		# 2. Hero Ganking (Chilling vs Challenging)
		elif is_evolved and target.hasTag("player"):
			stype = "BLUE" if "Slayer's Resolve" in getattr(self.pc, 'inventory', []) else "RED"
			if stype == "BLUE":
				# Chilling: 20% MS Steal
				MobaCommon.apply_cc(target, "SLOW", 2.0, magnitude=0.2)
				self.pc.applyEffect("MS_BOOST", 2.0, magnitude=self.pc.speed * 0.2)
				MobaCommon.spawn_vfx(scene, "VFX_Smite_Blue", target.getTransform().worldPosition)
			else:
				# Challenging: Burn + Exhaust-lite
				MobaCommon.apply_dot_hero(target.getPy("PlayerController"), 25 + (self.pc.level * 5), 4.0, source=self.entity)
				MobaCommon.spawn_vfx(scene, "VFX_Smite_Red", target.getTransform().worldPosition)
				
		MobaCommon.play_sfx(self.entity, "SFX_Smite")
		return True

	def _cast_teleport(self, scene, data):
		"""Channel, then teleport to a friendly structure/ward."""
		# --- Phase 105: Unleashed Teleport (Evolution at 10:00) ---
		mins = MobaCommon.GameTick.get_time_minutes()
		is_unleashed = mins >= 10.0
		
		target_tags = ["turret"]
		if is_unleashed:
			target_tags = ["turret", "ward", "minion"]

		team = MobaCommon.get_entity_team(self.entity)
		targets = []
		for tag in target_tags:
			for ent in MobaCommon.EntityRegistry.get(tag):
				if ent.isActive() and MobaCommon.get_entity_team(ent) == team:
					if ent != self.entity:
						targets.append(ent)

		if not targets:
			return False

		# Pick closest target
		my_pos = self.entity.getTransform().worldPosition
		targets.sort(key=lambda e: (
			(e.getTransform().worldPosition.x - my_pos.x) ** 2 +
			(e.getTransform().worldPosition.z - my_pos.z) ** 2
		))
		tp_target = targets[0]

		# Store teleport target for channeling callback
		self.pc._tp_target = tp_target

		# Start channel (uses existing ChannelState)
		if hasattr(self.pc, 'beginChannel'):
			self.pc.beginChannel("TP", data["channel_time"], self._on_teleport_complete)
			# Unleashed TP has reduced cooldown
			if is_unleashed:
				slot = [s for s in self.spells.values() if s["id"] == "Teleport"]
				if slot:
					slot[0]["cd_remaining"] = 240.0  # Override CD for this cast only
					return True
			MobaCommon.spawn_vfx(scene, "VFX_Teleport_Channel", my_pos)
			MobaCommon.play_sfx(self.entity, "SFX_Teleport_Start")
			return True
		return False

	def _on_teleport_complete(self):
		"""Callback when TP channel finishes."""
		tp_target = getattr(self.pc, '_tp_target', None)
		if tp_target and tp_target.isActive():
			dest = tp_target.getTransform().worldPosition
			# Offset slightly so we don't land inside the turret
			self.entity.getTransform().setPosition(dest.x + 2, dest.y, dest.z)
			scene = self.entity.getScene()
			if scene:
				MobaCommon.spawn_vfx(scene, "VFX_Teleport_Arrive", dest)
				MobaCommon.play_sfx(self.entity, "SFX_Teleport_End")
				
				# Unleashed Bonus MS (Phase 105)
				mins = MobaCommon.GameTick.get_time_minutes()
				if mins >= 10.0:
					ec = self.entity.getPy("EffectComponent")
					if ec:
						# Use standard MS_BOOST logic
						ec.apply("MS_BOOST", 3.0, flags=MobaCommon.EffectFlags.NONE, magnitude=0.45)
					from UI import MobaUI
					MobaUI.spawn_fct(scene, dest, "UNLEASHED!", cave.Vector4(0.0, 1.0, 1.0, 1.0))

	def _cast_ghost(self, scene, data):
		"""Movement speed buff for duration."""
		ec = self.entity.getPy("EffectComponent")
		if ec:
			ec.apply("ghost_speed", data["duration"],
					 flags=MobaCommon.EffectFlags.NONE, magnitude=data["speed_bonus"])

		# Apply speed directly via properties
		props = self.entity.getProperties()
		base_speed = props.get("speed", 330)
		props["ghost_bonus_speed"] = base_speed * data["speed_bonus"]

		MobaCommon.spawn_vfx(scene, "VFX_Ghost", self.entity.getTransform().worldPosition)
		MobaCommon.play_sfx(self.entity, "SFX_Ghost")
		return True

	def _cast_heal(self, scene, data):
		"""Heal self + nearest ally. Brief speed boost."""
		level = getattr(self.pc, 'level', 1)
		heal_amount = data["heal_base"] + (15 * level)

		# Heal self
		MobaCommon.apply_heal(self.entity, heal_amount)

		# Find nearest ally
		team = MobaCommon.get_entity_team(self.entity)
		allies = MobaCommon.EntityRegistry.get_team_entities(team, "player")
		my_pos = self.entity.getTransform().worldPosition
		best_ally = None
		best_dist = float('inf')

		for a in allies:
			if a == self.entity or not a.isActive():
				continue
			a_pos = a.getTransform().worldPosition
			dist_sq = (a_pos.x - my_pos.x)**2 + (a_pos.z - my_pos.z)**2
			if dist_sq < best_dist:
				best_dist = dist_sq
				best_ally = a

		# Heal ally if within 35 units
		if best_ally and best_dist < 35**2:
			MobaCommon.apply_heal(best_ally, heal_amount)

		# Speed boost
		ec = self.entity.getPy("EffectComponent")
		if ec:
			ec.apply("heal_speed", data["speed_duration"],
					 flags=MobaCommon.EffectFlags.NONE, magnitude=data["speed_bonus"])

		MobaCommon.spawn_vfx(scene, "VFX_Heal_Burst", my_pos)
		MobaCommon.play_sfx(self.entity, "SFX_Heal")
		return True

	def _cast_barrier(self, scene, data):
		"""Shield self for a duration."""
		level = getattr(self.pc, 'level', 1)
		shield_amount = data["shield_base"] + (10 * level)

		# Apply shield via EffectComponent + PlayerController
		ec = self.entity.getPy("EffectComponent")
		if ec:
			ec.apply("barrier_shield", data["duration"],
					 flags=MobaCommon.EffectFlags.SHIELD, magnitude=shield_amount)
		# Also set shield on PlayerController if available
		if self.pc:
			self.pc.shield = getattr(self.pc, 'shield', 0) + shield_amount

		MobaCommon.spawn_vfx(scene, "VFX_Barrier", self.entity.getTransform().worldPosition)
		MobaCommon.play_sfx(self.entity, "SFX_Barrier")
		return True

	def _cast_exhaust(self, scene, data):
		"""Slow enemy + reduce their damage output."""
		my_pos = self.entity.getTransform().worldPosition
		target = MobaCommon.get_closest_target(my_pos, data["range"], self.entity)
		if not target:
			return False

		# Apply slow
		MobaCommon.apply_cc(target, "SLOW", data["duration"], magnitude=data["slow_amount"])

		# Apply damage reduction as a debuff
		ec = target.getPy("EffectComponent")
		if ec:
			ec.apply("exhausted", data["duration"],
					 flags=MobaCommon.EffectFlags.NONE, magnitude=data["damage_reduction"])

		MobaCommon.spawn_vfx(scene, "VFX_Exhaust", target.getTransform().worldPosition)
		MobaCommon.play_sfx(target, "SFX_Exhaust")
		return True

	def _cast_cleanse(self, scene, data):
		"""Remove all negative CC effects from self (preserves positive buffs)."""
		ec = self.entity.getPy("EffectComponent")
		if ec:
			ec.remove_negative_effects()

		MobaCommon.spawn_vfx(scene, "VFX_Cleanse", self.entity.getTransform().worldPosition)
		MobaCommon.play_sfx(self.entity, "SFX_Cleanse")
		return True
