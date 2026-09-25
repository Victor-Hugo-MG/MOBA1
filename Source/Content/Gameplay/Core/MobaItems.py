import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon
from Data import ItemRegistry

class ItemEffectManager:
	"""Static logic for execution of item passives and actives."""
	
	@staticmethod
	def has_item_effect(player, event_type, effect_id):
		"""Phase 75: Systemic check for item effects, respecting Unique Passives."""
		# Phase 100 OPTIMIZATION: Check pre-compiled cache first if available
		if hasattr(player, "cached_item_effects") and effect_id not in player.cached_item_effects:
			return False
			
		best_item = None
		best_price = -1
		
		# 1. Find all candidates currently in inventory for this effect
		for item_name in player.inventory:
			item_data = ItemRegistry.ITEM_REGISTRY.get(item_name)
			if not item_data or "effects" not in item_data: continue
			
			event_data = item_data["effects"].get(event_type)
			
			is_match = False
			if isinstance(event_data, list):
				is_match = effect_id in event_data
			else:
				is_match = (event_data == effect_id)
				
			if is_match:
				group = item_data.get("uniquePassive")
				
				# If not a unique passive, find any instance (already confirmed by cache, but group logic needed)
				if not group:
					return True
				
				# If it IS a unique passive, we need to see if THIS item is the one that SHOULD run
				current_best_in_group = ItemEffectManager.get_best_item_in_group(player, group)
				if current_best_in_group and current_best_in_group == item_data:
					return True
					
		return False

	@staticmethod
	def get_best_item_in_group(player, group_name):
		"""Returns the Data of the highest-priced item in a uniquePassive group."""
		best_data = None
		best_price = -1
		
		for name in player.inventory:
			data = ItemRegistry.ITEM_REGISTRY.get(name)
			if data and data.get("uniquePassive") == group_name:
				price = data.get("price", 0)
				if price > best_price:
					best_price = price
					best_data = data
		return best_data

	@staticmethod
	def get_situational_multiplier(player, target):
		"""Lord Dominik's Regards (GIANT_SLAYER) and other contextual boosts."""
		mult = 1.0
		
		if ItemEffectManager.has_item_effect(player, "situationalDamage", "GIANT_SLAYER"):
			p_hp = player.entity.getProperties().get("maxHealth", 1)
			t_hp = target.getProperties().get("maxHealth", 1)
			# Giant Slayer: Deal up to 15% more physical damage based on max HP difference
			hp_diff = t_hp - p_hp
			if hp_diff > 0:
				# 1.5% bonus damage per 100 max HP difference, cap 15% (1000 HP diff)
				bonus = min(0.15, (hp_diff / 1000.0) * 0.15)
				mult += bonus
				
		return mult

	@staticmethod
	def process_on_tick(player, dt):
		"""Continuous passives (e.g. Sunfire burn, Moonstone, Bloodthirster)."""
		from Core import MobaCommon
		scene = player.entity.getScene()

		# ── Stormrazor / RFC (ENERGIZED) ──────────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTick", "ENERGIZED"):
			# Charge based on movement
			if hasattr(player, "character") and player.character.isMoving():
				# Gains ~12 stacks per second of movement
				player.energized_stacks = min(100, getattr(player, "energized_stacks", 0) + (24 * dt)) # 4s to full charge

		# ── Sunfire Aegis (IMMOLATE) ──────────────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTick", "IMMOLATE"):
			if "Sunfire_Burn" not in getattr(player, "active_vfx", {}):
				burn_vfx = MobaCommon.spawn_vfx(scene, "VFX_Sunfire_Aura", player.transf.worldPosition, duration=-1, parent=player.entity)
				burn_sfx = MobaCommon.play_sfx(player.entity, "SFX_Sunfire_Hum", loop=True)
				if not hasattr(player, "active_vfx"): player.active_vfx = {}
				player.active_vfx["Sunfire_Burn"] = {"vfx": burn_vfx, "sfx": burn_sfx}
			player.sunfire_timer = getattr(player, "sunfire_timer", 0) - dt
			if player.sunfire_timer <= 0:
				level = getattr(player, "level", 1)
				dmg = 15.0 + (level * 2.0)
				enemies = MobaCommon.get_entities_in_radius(scene, player.transf.worldPosition, 3.5)
				enemy_team = MobaCommon.Team.get_enemy(player.entity.getProperties().get("team", MobaCommon.Team.TEAM_A))
				for e in enemies:
					if e.hasTag(enemy_team) and e.isActive() and e.getProperties().get("health", 0) > 0:
						MobaCommon.apply_damage(e, dmg, MobaCommon.DamageType.MAGIC, player.entity)
						MobaCommon.spawn_vfx(scene, "VFX_Sunfire_Hit", e.getTransform().worldPosition, duration=0.5)
				player.sunfire_timer = 0.5
		else:
			if hasattr(player, "active_vfx") and "Sunfire_Burn" in player.active_vfx:
				data = player.active_vfx["Sunfire_Burn"]
				if data["vfx"]: data["vfx"].kill()
				if data["sfx"]:
					try: data["sfx"].stop()
					except: pass
				del player.active_vfx["Sunfire_Burn"]
				if hasattr(player, "sunfire_timer"): del player.sunfire_timer

		# ── Sterak's Gage / Phantom Dancer (LIFELINE_CHECK) ──────────────
		if ItemEffectManager.has_item_effect(player, "onTick", "LIFELINE_CHECK"):
			max_hp = max(1, player.entity.getProperties().get("maxHealth", 1))
			hp_pct = player.entity.getProperties().get("health", 0) / max_hp
			if hp_pct < 0.3 and not player.has_cooldown("LIFELINE"):
				shield_amt = max_hp * 0.4
				player.entity.getProperties()["shieldHP"] = max(player.entity.getProperties().get("shieldHP", 0), shield_amt)
				player.applyEffect("SHIELD", 5.0, magnitude=shield_amt)
				player.set_cooldown("LIFELINE", 60.0)
				MobaCommon.spawn_vfx(scene, "VFX_Lifeline_Shield", player.transf.worldPosition, duration=1.0)

		# ── Bloodthirster (OVERHEAL_SHIELD) ──────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTick", "OVERHEAL_SHIELD"):
			# Standard MOBA: BT shield decays slowly after 10s out of combat
			if player.outOfCombatTimer.getTime() > 10.0:
				existing = player.entity.getProperties().get("shieldHP", 0)
				if existing > 0:
					max_shield = min(50 + (getattr(player, "level", 1) * 10), 500)
					decay_rate = max_shield * 0.1 * dt # 10% per second
					player.entity.getProperties()["shieldHP"] = max(0, existing - decay_rate)
					if player.entity.getProperties()["shieldHP"] <= 0:
						player.removeEffect("OVERHEAL_SHIELD")

		# ── Moonstone Renewer (STARLIT_GRACE) ────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTick", "STARLIT_GRACE"):
			player.starlit_timer = getattr(player, "starlit_timer", 0) - dt
			if player.starlit_timer <= 0:
				player.starlit_timer = 2.5  # Pulses every 2.5s in combat
				# Heal the lowest-HP ally in 1000 units
				team = player.entity.getProperties().get("team", "teamA")
				allies = MobaCommon.EntityRegistry.get_team_entities(team, "player")
				lowest = None
				lowest_pct = 1.0
				for a in allies:
					if a == player.entity: continue
					mhp = max(1, a.getProperties().get("maxHealth", 1))
					pct = a.getProperties().get("health", 0) / mhp
					if pct < lowest_pct:
						lowest_pct = pct
						lowest = a
				if lowest:
					heal_amt = lowest.getProperties().get("maxHealth", 1) * 0.06
					MobaCommon.apply_heal(lowest, heal_amt)
					MobaCommon.spawn_vfx(scene, "VFX_Moonstone_Heal", lowest.getTransform().worldPosition, duration=0.5)

		# ── Edge of Night (SPELL_SHIELD_REFRESH) ─────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTick", "SPELL_SHIELD_REFRESH"):
			# Re-grant spell shield every 40s if not already present
			if not player.has_cooldown("SPELL_SHIELD") and not player.hasEffect("SPELL_SHIELD"):
				player.applyEffect("SPELL_SHIELD", 9999)  # Permanent until consumed
				player.set_cooldown("SPELL_SHIELD", 40.0)

		# ── Umbral Glaive (BLACKOUT_DETECT) ──────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTick", "BLACKOUT_DETECT"):
			# Detect and suppress enemy wards within 8 units (deny vision refill)
			player.blackout_timer = getattr(player, "blackout_timer", 0) - dt
			if player.blackout_timer <= 0:
				player.blackout_timer = 1.0
				enemy_team = MobaCommon.Team.get_enemy(player.entity.getProperties().get("team", MobaCommon.Team.TEAM_A))
				wards = MobaCommon.EntityRegistry.get("ward")
				for w in wards:
					if w.hasTag(enemy_team) and (w.getTransform().worldPosition - player.transf.worldPosition).length() < 8.0:
						MobaCommon.reveal_unit(w, 2.0)  # True sight on nearby wards

		# ── Force of Nature (STEADFAST) ───────────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTick", "STEADFAST"):
			stacks = getattr(player, "steadfast_stacks", 0)
			if stacks > 0:
				bonus_mr = min(stacks * 6, 30)
				player.entity.getProperties()["magicResist"] = player.entity.getProperties().get("magicResist", 30) + bonus_mr

	@staticmethod
	def on_cc_landed(player, target_ent):
		"""Phase 100: Solstice Sleigh (Area Team MS on CC)."""
		from Core import MobaCommon
		if not ItemEffectManager.has_item_effect(player, "onCC", "SOLSTICE_SLEIGH"):
			return

		scene = player.entity.getScene()
		team = player.entity.getProperties().get("team", "teamA")
		t_pos = target_ent.getTransform().worldPosition
		
		# Boost ALL allies within range of the victim
		allies = MobaCommon.get_entities_in_radius(scene, t_pos, 10.0)
		for a in allies:
			if a.hasTag(team) and a.hasTag("player"):
				a_pc = a.getPy("PlayerController")
				if a_pc:
					# Calculate Dynamic MS: Chasing (+30) or Fleeing (+15)
					# Velocity vs Victim position
					to_victim = (t_pos - a.getTransform().worldPosition).normalized()
					vel = getattr(a_pc.character, "getLinearVelocity", lambda: cave.Vector3(0,0,0))()
					
					ms_bonus = 15.0 # Fleeing/Neutral
					if vel.dot(to_victim) > 0.5: # 0.5 threshold for 'chasing'
						ms_bonus = 30.0
					
					# Using unique id to prevent stacking with self
					a_pc.applyEffect("SOLSTICE_SLEIGH_MS", 3.0, magnitude=ms_bonus)
					MobaCommon.spawn_vfx(scene, "VFX_Solstice_Boost", a.getTransform().worldPosition, duration=1.0)

	@staticmethod
	def process_taking_damage(player, attacker, dmg_type, final_dmg):
		"""Phase 100: Celestial Opposition Protection."""
		from Core import MobaCommon
		if not ItemEffectManager.has_item_effect(player, "onTakeDamage", "CELESTIAL_SHIELD"):
			return
			
		# Resets 5s after out-of-combat (done in PlayerController.update)
		if not player.isCelestialActive:
			player.isCelestialActive = True
			# Apply Buff: 20% DR + 30 MS for 5s
			player.applyEffect("CELESTIAL_PROTECTION", 5.0, magnitude=0.20)
			# MS boost handled by calculating stats from magnitudes or direct bump
			player.applyEffect("MS_BOOST", 5.0, magnitude=30.0) # Flat bump
			
			MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Celestial_Shield", player.transf.worldPosition, duration=5.0)
			MobaCommon.play_sfx(player.entity, "SFX_Celestial_Proc")

	@staticmethod
	def process_on_hit(player, target, is_ability=False, flags=0):
		"""Combat passives (e.g. Kraken Slayer, Black Cleaver, Spellblade, Liandry's, Luden's)."""
		from Core import MobaCommon

		# --- Tiered AS / On-Hit: Limit Break (Guinsoo Evolution) ---
		is_limit_broken = getattr(player, "is_limit_broken", False)
		
		hit_count = 1
		if not is_ability and ItemEffectManager.has_item_effect(player, "onHit", "PHANTOM_HIT"):
			# Requires Guinsoo + 3 other spawners (handled in PlayerController.recalculate_stats)
			# Phase 100: Restrict Phantom Hit to Ranged only
			if is_limit_broken and getattr(player, "isRanged", False):
				player.rageblade_hit_count = getattr(player, "rageblade_hit_count", 0) + 1
				if player.rageblade_hit_count >= 3:
					hit_count = 2

		# ── Spectral Mandate (SPECTRAL_SHRED) ─────────────────────────
		if ItemEffectManager.has_item_effect(player, "onHit", "SPECTRAL_SHRED") and not is_ability:
			# 5 armor shred per stack, max 5 stacks
			stack_id = f"SPECTRAL_SHRED_{player.entity.name}"
			stacks = target.getProperties().get(stack_id, 0)
			
			# Phase 100: Slow Cooldown (Avoid broken infinite procs)
			last_slow = target.getProperties().get("SPECTRAL_SLOW_TIME", 0.0)
			now = player.entity.getScene().getElapsedSceneTime()
			
			if stacks < 5:
				target.getProperties()[stack_id] = stacks + 1
				target_pc = target.getPy("PlayerController")
				if target_pc:
					target_pc.applyEffect("ARMOR_SHRED", 4.0, magnitude=5)
					
			# Slow on hit (4s per-target CD)
			if (now - last_slow) >= 4.0:
				MobaCommon.apply_cc(target, "SLOW", 1.5, magnitude=0.20)
				target.getProperties()["SPECTRAL_SLOW_TIME"] = now

		# ── Bloodsong (BLOODSONG_EXPOSE) ─────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onHit", "BLOODSONG_EXPOSE") and not is_ability:
			# Spellblade check (prime flag usually set in process_ability_cast)
			if getattr(player, "spellblade_primed", False):
				player.spellblade_primed = False
				# 1. Bonus Damage
				MobaCommon.apply_damage(target, player.baseStats.get("ad", 50) * 1.5, MobaCommon.DamageType.PHYSICAL, player.entity)
				# 2. Expose (10% dmg amp for 6s)
				t_pc = target.getPy("PlayerController")
				if t_pc: t_pc.applyEffect("EXPOSED_WEAKNESS", 6.0, magnitude=0.1)
				MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Bloodsong_Strike", target.getTransform().worldPosition)

		for _ in range(hit_count):
			# ── Wit's End (WITS_END_STING) ──────────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "WITS_END_STING") and not is_ability:
				level = getattr(player, "level", 1)
				sting_dmg = 15 + (level * 3) # Scales with level (15-69)
				MobaCommon.apply_damage(target, sting_dmg, MobaCommon.DamageType.MAGIC, player.entity)
				# MS Boost on hit
				player.applyEffect("MS_BOOST", 2.0, magnitude=1.15) # 15% boost

			# ── Grievous Wounds ───────────────────────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "GRIEVOUS_WOUNDS"):
				eff = target.getPy("EffectComponent")
				if eff:
					eff.apply("GRIEVOUS_WOUNDS", 3.0, flags=MobaCommon.EffectFlags.BLEED)

			# ── Spellblade (Sheen) ────────────────────────────────────────────
			if getattr(player, "has_spellblade", False) and (flags & MobaCommon.EffectFlags.BASIC_ATTACK):
				spellblade_dmg = player.baseAD
				MobaCommon.apply_damage(target, spellblade_dmg, MobaCommon.DamageType.PHYSICAL, player.entity)
				
				# Phase 100: Essence Reaver Mana Restore
				if ItemEffectManager.has_item_effect(player, "onHit", "SPELLBLADE_MANA"):
					missing_mana = player.maxMana - player.mana
					restore = 40 + (missing_mana * 0.03)
					player.mana = min(player.maxMana, player.mana + restore)
					player.entity.getProperties()["mana"] = player.mana
					MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Mana_Restore", player.transf.worldPosition, duration=0.5, parent=player.entity)
				
				player.has_spellblade = False

			# ── Black Cleaver (CLEAVE_SHRED) ──────────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "CLEAVE_SHRED"):
				t_pc = target.getPy("PlayerController")
				if t_pc:
					t_pc.applyEffect("SHRED", 4.0, magnitude=0.05)
				else:
					t_eff = target.getPy("EffectComponent")
					if t_eff:
						t_eff.apply("SHRED_DEBUFF", 4.0, magnitude=0.05)

			# ── Guinsoo's Rageblade (OVERDRIVE_PROC) ─────────────────────────
			if is_limit_broken:
				overflow = getattr(player, "as_overflow", 0)
				if overflow > 0:
					# Phase 100 Balance: Melee heroes deal 50% less Overdrive damage
					is_ranged = getattr(player, "isRanged", False)
					ratio = 150 if is_ranged else 75
					overdrive_dmg = overflow * ratio # Conversion: 0.1 AS -> 15 (Ranged) or 7.5 (Melee)
					MobaCommon.apply_damage(target, overdrive_dmg, MobaCommon.DamageType.MAGIC, player.entity)
					MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Guinsoo_Overdrive", target.getTransform().worldPosition, duration=0.2)

			# ── Kraken Slayer (BRING_IT_DOWN) ─────────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "BRING_IT_DOWN") and not is_ability:
				player.kraken_stacks = getattr(player, "kraken_stacks", 0) + 1
				if player.kraken_stacks >= 3:
					true_dmg = 50 + (getattr(player, "level", 1) * 10)
					MobaCommon.apply_damage(target, true_dmg, MobaCommon.DamageType.TRUE, player.entity)
					MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Kraken_Proc", target.getTransform().worldPosition, duration=0.5)
					player.kraken_stacks = 0

			# ── Luden's Tempest (ECHO_PROC) ───────────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "ECHO_PROC") and is_ability:
				if not player.has_cooldown("ECHO"):
					ap = player.entity.getProperties().get("ap", 0)
					echo_dmg = 100 + (ap * 0.10)
					# Chain to 3 nearby enemies
					enemies = MobaCommon.get_entities_in_radius(player.entity.getScene(), target.getTransform().worldPosition, 6.0)
					count = 0
					for e in enemies:
						if count >= 3: break
						if e == target or e == player.entity: continue
						enemy_team = MobaCommon.Team.get_enemy(player.entity.getProperties().get("team", MobaCommon.Team.TEAM_A))
						if e.hasTag(enemy_team) and e.isActive():
							MobaCommon.apply_damage(e, echo_dmg, MobaCommon.DamageType.MAGIC, player.entity)
							count += 1
					MobaCommon.apply_damage(target, echo_dmg, MobaCommon.DamageType.MAGIC, player.entity)
					MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Ludens_Echo", target.getTransform().worldPosition, duration=0.5)
					player.set_cooldown("ECHO", 10.0)

			# ── Liandry's Anguish (TORMENT_BURN) ─────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "TORMENT_BURN") and is_ability:
				# Burn for 4% max HP as magic damage over 4 seconds (1%/s)
				t_max_hp = target.getProperties().get("maxHealth", 100)
				burn_dps = t_max_hp * 0.01  # 1% per second
				MobaCommon.apply_dot(target, burn_dps, 4.0, source=player.entity)

			# ── Arcane Resolve — Jungle AP (SOUL_BURN) ───────────────────────
			if ItemEffectManager.has_item_effect(player, "onAbilityHit", "SOUL_BURN") and is_ability:
				ap = player.entity.getProperties().get("ap", 0)
				soul_dmg = 20 + (ap * 0.05)
				MobaCommon.apply_damage(target, soul_dmg, MobaCommon.DamageType.MAGIC, player.entity)

			# ── Warden's Shroud (SPECTRAL_CHAIN) ───────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "SPECTRAL_CHAIN") and is_ability:
				if target.hasTag("player") and not player.has_cooldown(f"GROUND_{target.name}"):
					t_pc = target.getPy("PlayerController")
					if t_pc:
						t_pc.applyEffect("GROUNDED", 1.5, flags=MobaCommon.EffectFlags.GROUNDED)
						MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Spectral_Chains", target.getTransform().worldPosition, duration=1.5)
						MobaCommon.play_sfx(target, "SFX_Spectral_Chain_Proc")
						player.set_cooldown(f"GROUND_{target.name}", 12.0)

			# ── Serylda's Grudge (ICY_SLOW) ──────────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onAbilityHit", "ICY_SLOW") and is_ability:
				t_hp = target.getProperties().get("health", 1)
				t_max = target.getProperties().get("maxHealth", 1)
				# 30% Slow for 1s only if target is under 40% HP
				if (t_hp / t_max) < 0.40:
					eff = target.getPy("EffectComponent")
					if eff:
						eff.apply("SERYLDA_SLOW", 1.0, magnitude=0.30, flags=MobaCommon.EffectFlags.SLOW)
					MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Serylda_Slow", target.getTransform().worldPosition, duration=0.5)

			# ── Force of Nature — magic hit tracking (STEADFAST) ─────────────
			if ItemEffectManager.has_item_effect(player, "onTakeMagicDamage", "STEADFAST"):
				# Track stacks on the TARGET (force of nature holder)
				t_pc = target.getPy("PlayerController")
				if t_pc:
					t_pc.steadfast_stacks = min(getattr(t_pc, "steadfast_stacks", 0) + 1, 5)

			# ── Stormrazor (GALE_STRIKE) ──────────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "GALE_STRIKE") and not is_ability:
				player.energized_stacks = getattr(player, "energized_stacks", 0) + 15
				if player.energized_stacks >= 100:
					player.energized_stacks = 0
					player.applyEffect("MS_BOOST", 1.5, magnitude=1.4) # +40% MS boost
					MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Stormrazor_Proc", target.getTransform().worldPosition, duration=0.5)

			# ── Navori Flickerblade (FLICKER_CD) ──────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "FLICKER_CD") and not is_ability:
				is_crit = player.entity.getProperties().get("isLastHitCrit", False)
				if is_crit:
					# Reduce remaining non-ultimate cooldowns by 15%
					for key in ["Q", "W", "E"]:
						if key in player.cooldowns:
							timer = player.cooldowns[key]
							cur = timer.getSeconds()
							if cur < 90.0: # If it's on cooldown
								total_dur = player.cooldownDurations.get(key, 10.0)
								reduction = total_dur * 0.15
								timer.set(max(0, cur - reduction))
					MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Navori_Proc", player.transf.worldPosition, duration=0.5, parent=player.entity)

			# ── Mortal Reminder (TRUE_SIGHT_REVEAL) ───────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "TRUE_SIGHT_REVEAL"):
				# Reveal the target for 3s
				target.getProperties()["revealed_timer"] = 3.0
				target.addTag("revealed")
				eff = target.getPy("EffectComponent")
				if eff:
					eff.apply("TRUE_SIGHT", 3.0, flags=MobaCommon.EffectFlags.REVEALED)
				MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Mortal_Reveal", target.getTransform().worldPosition, duration=3.0)

			# ── Phantom Dancer (PD_GHOSTING) ─────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "PD_GHOSTING") and not is_ability:
				# Gain MS and Ghosting (ignore collision) for 3s
				player.applyEffect("PD_BUFF", 3.0, magnitude=1.1, flags=MobaCommon.EffectFlags.GHOST)
				MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_PD_Wings", player.transf.worldPosition, duration=0.5, parent=player.entity)

			# ── Runaan's Hurricane (RUNAANS_BOLTS) ────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "RUNAANS_BOLTS") and not is_ability:
				# Shoot 2 bolts at nearby enemies
				enemies = MobaCommon.get_entities_in_radius(player.entity.getScene(), target.getTransform().worldPosition, 6.0)
				enemy_team = MobaCommon.Team.get_enemy(player.entity.getProperties().get("team", MobaCommon.Team.TEAM_A))
				bolt_count = 0
				for e in enemies:
					if bolt_count >= 2: break
					if e == target or e == player.entity or not e.isActive(): continue
					if e.hasTag(enemy_team):
						bolt_dmg = player.ad * 0.4 # Bolts deal 40% AD
						MobaCommon.spawn_homing_projectile(
							player.entity.getScene(), player.entity, e, 
							MobaCommon.Templates.PROJ_RUNAANS, 45.0, bolt_dmg
						)
						bolt_count += 1

			# ── Rapid Firecannon (FIRE_RANGE) ─────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "FIRE_RANGE") and not is_ability:
				player.energized_stacks = getattr(player, "energized_stacks", 0) + 15
				if player.energized_stacks >= 100:
					# Range logic handled in AttackState, here we consume it
					player.energized_stacks = 0
					MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_RFC_Proc", target.getTransform().worldPosition, duration=0.5)

			# ── Blade of the Ruined King (BORK_SHRED) ───────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "BORK_SHRED") and not is_ability:
				t_hp = target.getProperties().get("health", 0)
				shred_dmg = max(15, t_hp * 0.08) # 8% Current HP, min 15
				MobaCommon.apply_damage(target, shred_dmg, MobaCommon.DamageType.MAGIC, player.entity)
				
			# ── Horizon Focus (REVEAL_SNIPE) ──────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onAbilityHit", "REVEAL_SNIPE") and is_ability:
				MobaCommon.reveal_unit(target, 4.0)
				MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Horizon_Reveal", target.getTransform().worldPosition, duration=1.0)
				
			# ── Zaz'Zak's Realmspike (REALMSPIKE_SHRED) ──────────────────
			if ItemEffectManager.has_item_effect(player, "onAbilityHit", "REALMSPIKE_SHRED") and is_ability:
				t_pc = target.getPy("PlayerController")
				if t_pc:
					# -5 MR per hit, stacks to -20
					t_pc.applyEffect("MR_SHRED", 5.0, magnitude=5.0)
					MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Realmspike_Corrode", target.getTransform().worldPosition)
				
			# ── Terminus (JUXTAPOSITION) ──────────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "JUXTAPOSITION") and not is_ability:
				# Stacks Armor/Magic Pen and Armor/MR (Standard LoL Terminus)
				player.terminus_stacks = getattr(player, "terminus_stacks", 0) + 1
				if player.terminus_stacks <= 10:
					# Apply tiny stat buffs (managed by recalculate_stats or persistent effects)
					player.applyEffect("TERMINUS_STACK", 5.0, magnitude=1)
				
			# ── Nashor's Tooth (NASHORS_STING) ─────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "NASHORS_STING") and not is_ability:
				ap = player.entity.getProperties().get("ap", 0)
				sting_dmg = 15 + (ap * 0.20)
				MobaCommon.apply_damage(target, sting_dmg, MobaCommon.DamageType.MAGIC, player.entity)
				
			# ── Ravenous Hydra (HYDRA_CLEAVE) ──────────────────────────────
			if ItemEffectManager.has_item_effect(player, "onHit", "HYDRA_CLEAVE") and not is_ability:
				# Splash damage based on AD
				ad = player.entity.getProperties().get("ad", 0)
				splash_dmg = ad * 0.60
				scene = player.entity.getScene()
				enemies = MobaCommon.get_entities_in_radius(scene, target.getTransform().worldPosition, 4.0)
				enemy_team = MobaCommon.Team.get_enemy(player.entity.getProperties().get("team", MobaCommon.Team.TEAM_A))
				for e in enemies:
					if e == target or e == player.entity: continue
					if e.hasTag(enemy_team) and e.isActive():
						MobaCommon.apply_damage(e, splash_dmg, MobaCommon.DamageType.PHYSICAL, player.entity, flags=MobaCommon.EffectFlags.CONTINUOUS)
				MobaCommon.spawn_vfx(scene, "VFX_Hydra_Cleave", target.getTransform().worldPosition, duration=0.5)

	@staticmethod
	def process_on_take_damage(player, attacker, raw_dmg, dmg_type, flags=0):
		# Force of Nature (STEADFAST)
		if ItemEffectManager.has_item_effect(player, "onTakeMagicDamage", "STEADFAST") and dmg_type == MobaCommon.DamageType.MAGIC:
			player.steadfast_stacks = min(getattr(player, "steadfast_stacks", 0) + 1, 5)
		"""Defensive passives (e.g. Thornmail, Death's Dance, Steelcaps, Goliath)."""
		from Core import MobaCommon

		# ── Thornmail (THORNS) ────────────────────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTakeDamage", "THORNS") and dmg_type == MobaCommon.DamageType.PHYSICAL:
			if attacker and attacker.isActive():
				armor = player.entity.getProperties().get("armor", 0)
				reflect_dmg = 10 + (armor * 0.1)
				MobaCommon.apply_damage(attacker, reflect_dmg, MobaCommon.DamageType.MAGIC, player.entity)
				# Apply Grievous Wounds to attacker (Thornmail unique mechanic)
				a_eff = attacker.getPy("EffectComponent")
				if a_eff:
					a_eff.apply("GRIEVOUS_WOUNDS", 3.0, flags=MobaCommon.EffectFlags.BLEED)

		# ── Death's Dance (IGNORE_PAIN) ───────────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTakeDamage", "IGNORE_PAIN") and dmg_type == MobaCommon.DamageType.PHYSICAL:
			deferred = raw_dmg * 0.3
			player.deferred_damage = getattr(player, "deferred_damage", 0) + deferred
			raw_dmg -= deferred

		# ── Plated Steelcaps (AA_REDUCTION) ──────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTakeDamage", "AA_REDUCTION") and dmg_type == MobaCommon.DamageType.PHYSICAL:
			raw_dmg *= 0.88

		# ── Goliath's Resolve (TENACITY_BLOOM) ───────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTakeDamage", "TENACITY_BLOOM"):
			# Gain 20 tenacity for 4 seconds when taking damage (stacks with Mercury's Treads)
			if not player.has_cooldown("TENACITY_BLOOM"):
				player.applyEffect("TENACITY_BOOST", 4.0, magnitude=0.20)
				player.set_cooldown("TENACITY_BLOOM", 8.0)

		# ── Immortal Shieldbow (LIFELINE_SHIELD) ─────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTakeDamage", "LIFELINE_SHIELD"):
			hp_pct = player.entity.getProperties().get("health", 0) / player.entity.getProperties().get("maxHealth", 1)
			if hp_pct < 0.3 and not player.has_cooldown("LIFELINE"):
				shield_val = 300 + (getattr(player, "level", 1) * 25)
				player.applyEffect("SHIELD", 3.0, magnitude=shield_val)
				player.entity.getProperties()["shieldHP"] = shield_val
				MobaCommon.spawn_vfx(player.entity.getScene(), "VFX_Shieldbow_Proc", player.transf.worldPosition, duration=3.0)
				player.set_cooldown("LIFELINE", 90.0)

		# ── Celestial Opposition (Damage Reduction Logic Integration) ──
		if ItemEffectManager.has_item_effect(player, "onTakeDamage", "CELESTIAL_SHIELD"):
			if getattr(player, "isCelestialActive", False):
				# User specifically asked for reduction against AUTO ATTACKS
				# Check if the incoming damage is flagged as a Basic Attack
				if flags & MobaCommon.EffectFlags.BASIC_ATTACK:
					raw_dmg *= 0.8 # 20% reduction
				
		return raw_dmg

	@staticmethod
	def process_active(player, item_id):
		"""Manual item usage (keys 1-6 mapped to inventory slots)."""
		from Core import MobaCommon
		scene = player.entity.getScene()

		if item_id == "Zhonya's Hourglass":
			if not player.has_cooldown("ZHONYA"):
				player.applyEffect("STASIS", 2.5, flags=MobaCommon.EffectFlags.INVULNERABLE | MobaCommon.EffectFlags.STUN)
				MobaCommon.spawn_vfx(scene, "VFX_Zhonyas_Active", player.transf.worldPosition, duration=2.5)
				MobaCommon.play_sfx(player.entity, "SFX_Zhonyas_Activate")
				player.set_cooldown("ZHONYA", 120.0)

		elif item_id == "Youmuu's Ghostblade":
			if not player.has_cooldown("GHOSTBLADE"):
				player.applyEffect("GHOST_STEP", 6.0, magnitude=1.20)  # +20% MS
				MobaCommon.spawn_vfx(scene, "VFX_Ghostblade_Active", player.transf.worldPosition, duration=6.0)
				MobaCommon.play_sfx(player.entity, "SFX_Ghostblade_Activate")
				player.set_cooldown("GHOSTBLADE", 45.0)

		elif item_id == "Redemption":
			if not player.has_cooldown("REDEMPTION"):
				# Drop a zone that heals allies after 2.5s
				out = scene.getDataOverMousePosition()
				target_pos = out.position if out.hit else player.transf.worldPosition
				# Spawn landing marker
				MobaCommon.spawn_vfx(scene, "VFX_Redemption_Landing", target_pos, duration=2.5)
				MobaCommon.play_sfx(player.entity, "SFX_Redemption_Cast")
				# Schedule detonation via a scene timer
				def _redemption_detonate():
					heal_amt = 250 + (getattr(player, "level", 1) * 25)
					team = player.entity.getProperties().get("team", "teamA")
					allies_near = MobaCommon.get_entities_in_radius(scene, target_pos, 5.5)
					for a in allies_near:
						if a.hasTag(team):
							MobaCommon.apply_heal(a, heal_amt)
					MobaCommon.spawn_vfx(scene, "VFX_Redemption_Heal", target_pos, duration=1.0)
					MobaCommon.play_sfx(player.entity, "SFX_Redemption_Land")
				# Cave Engine doesn't have native callbacks; we store a pending detonation
				player._pending_actives.append({"fn": _redemption_detonate, "timer": 2.5})
				player.set_cooldown("REDEMPTION", 90.0)

		elif item_id == "THIRST_SLASH":
			# Gore-Drinker Active (Phase 101)
			if not player.has_cooldown("GOREDRINKER"):
				ents = MobaCommon.get_entities_in_radius(scene, player.transf.worldPosition, 4.5)
				hit_count = 0
				hp = player.entity.getProperties().get("health", 1)
				missing_hp = player.maxHP - hp
				for e in ents:
					if e != player.entity and MobaCommon.get_entity_team(e) != MobaCommon.get_entity_team(player.entity):
						MobaCommon.apply_damage(e, player.ad * 0.8, MobaCommon.DamageType.PHYSICAL, player.entity)
						hit_count += 1
				if hit_count > 0:
					# 8% missing HP per enemy hit (capped at 5)
					mult = min(hit_count, 5)
					heal_amt = (missing_hp * 0.08) * mult
					MobaCommon.apply_heal(player.entity, heal_amt, source=player.entity)
				MobaCommon.spawn_vfx(scene, "VFX_Goredrinker_Slam", player.transf.worldPosition, duration=0.8)
				player.set_cooldown("GOREDRINKER", 15.0)

		elif item_id == "HALTING_SLASH":
			# Stridebreaker Active (Phase 101)
			if not player.has_cooldown("STRIDEBREAKER"):
				ents = MobaCommon.get_entities_in_radius(scene, player.transf.worldPosition, 4.5)
				for e in ents:
					if e != player.entity and MobaCommon.get_entity_team(e) != MobaCommon.get_entity_team(player.entity):
						MobaCommon.apply_damage(e, player.ad * 0.7, MobaCommon.DamageType.PHYSICAL, player.entity)
						e_eff = e.getPy("EffectComponent")
						if e_eff: e_eff.apply("STRIDE_SLOW", 2.0, magnitude=0.4, flags=MobaCommon.EffectFlags.SLOW | MobaCommon.EffectFlags.CC)
				MobaCommon.spawn_vfx(scene, "VFX_Stride_Active", player.transf.worldPosition, duration=0.8)
				player.set_cooldown("STRIDEBREAKER", 15.0)

		elif item_id == "GALEFORCE_DASH":
			# Active Dash (Repositioning)
			out = scene.getDataOverMousePosition()
			if out.hit:
				target_pos = out.position
				# Bound the dash distance
				dir = (target_pos - player.transf.worldPosition).normalized()
				final_pos = player.transf.worldPosition + dir * 6.0 # Max 6 units
				from Core import MobaStates
				player.fsm.setState(MobaStates.DashState(final_pos, speed=40.0, duration=0.2))
				MobaCommon.spawn_vfx(scene, "VFX_Galeforce_Dash", player.transf.worldPosition, duration=0.5)
				MobaCommon.play_sfx(player.entity, "SFX_Galeforce_Active")

		elif item_id == "PHASE_SHIFT":
			# Active Untargetable for 2s
			player.applyEffect("PHASE_SHIFT", 2.0, flags=MobaCommon.EffectFlags.UNTARGETABLE)
			MobaCommon.spawn_vfx(scene, "VFX_PhaseShift_Active", player.transf.worldPosition, duration=2.0)
			MobaCommon.play_sfx(player.entity, "SFX_PhaseShift_Active")

		elif item_id == "CLEANSE_CC":
			# Active Cleanse
			if hasattr(player, "eff_comp"):
				player.eff_comp.remove_negative_effects()
			player.applyEffect("CLEANSE_SPEED", 1.5, magnitude=1.5) # 50% MS boost
			MobaCommon.spawn_vfx(scene, "VFX_Cleanse_Active", player.transf.worldPosition, duration=1.0)
			MobaCommon.play_sfx(player.entity, "SFX_Cleanse_Active")

		elif item_id == "Locket of Iron Solari":
			if not player.has_cooldown("LOCKET"):
				shield_val = 200 + (getattr(player, "level", 1) * 15)
				team = player.entity.getProperties().get("team", "teamA")
				allies_near = MobaCommon.get_entities_in_radius(scene, player.transf.worldPosition, 8.0)
				for a in allies_near:
					if a.hasTag(team):
						a_pc = a.getPy("PlayerController")
						if a_pc:
							a_pc.applyEffect("SHIELD", 2.5, magnitude=shield_val)
							a.getProperties()["shieldHP"] = max(a.getProperties().get("shieldHP", 0), shield_val)
						else:
							a.getProperties()["shieldHP"] = max(a.getProperties().get("shieldHP", 0), shield_val)
				MobaCommon.spawn_vfx(scene, "VFX_Locket_Shield", player.transf.worldPosition, duration=1.0)
				MobaCommon.play_sfx(player.entity, "SFX_Locket_Activate")
				player.set_cooldown("LOCKET", 60.0)

		elif item_id == "TOTAL_CLEANSE":
			# Staff of Flowing Waters: Purge all negative effects for self and most injured nearby ally
			team = player.entity.getProperties().get("team", "teamA")
			allies_near = MobaCommon.get_entities_in_radius(scene, player.transf.worldPosition, 8.0)
			for a in allies_near:
				if a.hasTag(team):
					a_pc = a.getPy("PlayerController")
					if a_pc and hasattr(a_pc, "eff_comp"):
						a_pc.eff_comp.remove_negative_effects()
						# Visual for each cleanse
						MobaCommon.spawn_vfx(scene, "VFX_Cleanse_Ally", a.getTransform().worldPosition, duration=1.0)
			MobaCommon.play_sfx(player.entity, "SFX_Staff_Cleanse")

		elif item_id == "TACTICAL_BLINK":
			# Horizon Focus: Long range repositioning
			out = scene.getDataOverMousePosition()
			if out.hit:
				target_pos = out.position
				dir = (target_pos - player.transf.worldPosition).normalized()
				final_pos = player.transf.worldPosition + dir * 18.0 # Long range: 18 units
				final_pos.y = player.transf.worldPosition.y # Safety
				
				# Teleport
				player.transf.setPosition(final_pos.x, final_pos.y, final_pos.z)
				MobaCommon.spawn_vfx(scene, "VFX_Horizon_Blink", final_pos, duration=1.0)
				MobaCommon.play_sfx(player.entity, "SFX_Horizon_Blink")

		elif item_id == "BATTLE_CRY":
			# Shurelya's: Area Movement Speed boost
			team = player.entity.getProperties().get("team", "teamA")
			allies_near = MobaCommon.get_entities_in_radius(scene, player.transf.worldPosition, 10.0)
			for a in allies_near:
				if a.hasTag(team):
					a_pc = a.getPy("PlayerController")
					if a_pc:
						a_pc.applyEffect("MS_BOOST", 3.0, magnitude=1.40, flags=MobaCommon.EffectFlags.BUFF)
			MobaCommon.spawn_vfx(scene, "VFX_Shurelya_Aura", player.transf.worldPosition, duration=1.5)
			MobaCommon.play_sfx(player.entity, "SFX_Shurelya_Cast")
 
		elif item_id == "PLACE_WARD":
			# Phase 123: Vision Ward
			out = scene.getDataOverMousePosition()
			if out.hit:
				ward = scene.addFromTemplate("Template_VisionWard", out.position)
				if ward:
					ward.getProperties()["team"] = player.entity.getProperties().get("team")
					ward.add("WardComponent")
				MobaCommon.play_sfx(player.entity, "SFX_Ward_Place")
				
		elif item_id == "ORACLE_SWEEP":
			# Phase 123: Red Trinket
			sweeper = scene.addFromTemplate("Template_OracleSweeper", player.transf.worldPosition)
			if sweeper:
				sweeper.setParent(player.entity)
				sweeper.getProperties()["team"] = player.entity.getProperties().get("team")
				sweeper.add("OracleSweepComponent")
			MobaCommon.play_sfx(player.entity, "SFX_Oracle_Activate")

	@staticmethod
	def tick_pending_actives(player, dt):
		"""Call this from PlayerController.update() to process deferred item effects."""
		if not hasattr(player, "_pending_actives"): return
		done = []
		for entry in player._pending_actives:
			entry["timer"] -= dt
			if entry["timer"] <= 0:
				try: entry["fn"]()
				except: pass
				done.append(entry)
		for d in done:
			player._pending_actives.remove(d)

	@staticmethod
	def process_tick_passives(player, dt):
		"""Periodic checks for Fighter/Support unique passives."""
		from Core import MobaCommon
		
		# ── Hullbreaker (HULLBREAKER_CHECK) ────────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTick", "HULLBREAKER_CHECK"):
			team = player.entity.getProperties().get("team", "teamA")
			scene = player.entity.getScene()
			nearby_allies = MobaCommon.get_entities_in_radius(scene, player.transf.worldPosition, 20.0)
			is_solo = True
			for a in nearby_allies:
				if a != player.entity and a.hasTag("player") and a.hasTag(team):
					if not a.getProperties().get("isDead", False):
						is_solo = False
						break
			
			# Apply Armor/MR bonus only if alone (Hullbreaker core mechanic)
			bonus = (35 + (player.leveling.level * 1.5)) if is_solo else 0
			if is_solo and player.hullbreaker_bonus <= 0:
				MobaCommon.spawn_vfx(scene, "VFX_Hullbreaker_Solo", player.transf.worldPosition, duration=1.0)
			player.hullbreaker_bonus = bonus
			player.entity.getProperties()["hullbreakerArmor"] = bonus
			
		# ── Spear of Shojin (DRAGON_FORCE) ──────────────────────────────────
		if ItemEffectManager.has_item_effect(player, "onTick", "DRAGON_FORCE"):
			# Grant up to 15% CDR bonus based on missing HP
			hp_pct = player.entity.getProperties().get("health", 0) / player.entity.getProperties().get("maxHealth", 1)
			shojin_cdr = (1.0 - hp_pct) * 0.15
			player.bonusCDR = getattr(player, "bonusCDR", 0) + shojin_cdr
	# ── End of ItemEffectManager ─────────────────────────────────────────────
