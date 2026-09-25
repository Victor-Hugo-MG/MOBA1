import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core.MobaCommon import DamageType, EffectFlags, GameTick, get_entities_in_radius, GOLD_XP_SPLIT_PERCENT, BountyConfig
from UI import MobaUI
from Managers.MatchStatsManager import MatchStatsManager
from Managers.AnnouncerManager import AnnouncerManager


class RewardManager:
	"""Handles Gold and XP distribution upon death."""
	@staticmethod
	def distribute(victim, killer):
		if not victim: return
		
		# Base Rewards
		gold_val = 0
		xp_val = 0
		
		mins = GameTick.get_time_minutes()
		scaling = 1.0 + (mins * 0.02)
		
		if victim.hasTag("player"):
			gold_val = BountyConfig.BASE_KILL_GOLD
			xp_val = 500
			
			v_pc = victim.getPy("PlayerController")
			if v_pc:
				gold_val += v_pc.bounty
				v_pc.bounty = 0
				v_pc.killStreak = 0
				v_pc.multiKillCount = 0
		elif victim.hasTag("minion"):
			m_scaling = min(2.0, 1.0 + (mins * 0.03))
			gold_val = int(20 * m_scaling)
			xp_val = int(60 * m_scaling)
		elif victim.hasTag("monster"):
			gold_val = int(victim.getProperties().get("goldReward", 50) * scaling)
			xp_val = int(victim.getProperties().get("xpReward", 100) * scaling)
			
		# Give gold to killer
		if killer:
			k_pc = killer.getPy("PlayerController") if hasattr(killer, 'getPy') else None
			if k_pc:
				reward_mult = 1.0
				if victim.hasTag("minion") and mins < 14.0:
					if k_pc.inventory_mgr.has_item_effect("onTick", "JUNGLE_HUNTER"):
						reward_mult = 0.5
				
				final_gold = int(gold_val * reward_mult)
				final_xp = int(xp_val * reward_mult)
				
				k_pc.leveling.gold += final_gold
				k_pc.add_exp(final_xp)
				MatchStatsManager.track_gold(killer.name, final_gold)
				
				if victim.hasTag("player"):
					k_pc.handleKillStreak(victim)
				
				if gold_val > 0:
					fct = victim.getPy("FloatingCombatTextComponent")
					if fct and hasattr(fct, "setup"):
						fct.setup(gold_val, DamageType.GOLD)
						
				if victim.hasTag("player"):
					k_pc.leveling.kills += 1
				elif victim.hasTag("minion") or victim.hasTag("monster"):
					k_pc.leveling.cs += 1
					
				if victim.hasTag("monster") and victim.getProperties().get("isLarge", True):
					k_pc.large_monsters_killed = getattr(k_pc, "large_monsters_killed", 0) + 1
					if k_pc.large_monsters_killed == 20:
						import Core.MobaCommon as MobaCommon
						MobaCommon.broadcast_event(f"The Jungle has Evolved! {killer.name}'s Smite is now PRIMAL.", is_banner=True)
						MobaCommon.play_sfx(killer, "SFX_Evolution")
				
				if hasattr(k_pc, "passive_mgr"):
					k_pc.passive_mgr.on_kill(victim)

			# --- UNINDENTED GLOBAL SYSTEMS (Works for Turret/Minion killers too!) ---
			team = killer.getProperties().get("team")
			if team:
				scene = victim.getScene()
				v_pos = victim.getTransform().worldPosition
				
				# Support Economy (Gold Sharing)
				if victim.hasTag("minion") and mins < 20:
					allies = [e for e in get_entities_in_radius(scene, v_pos, 14.0) if e.hasTag("player") and e.hasTag(team) and e != killer]
					for ally in allies:
						a_pc = ally.getPy("PlayerController")
						if a_pc and a_pc.inventory_mgr.has_item_effect("onTick", "SUPPORT_GOLD"):
							share = int(gold_val * 0.5)
							a_pc.leveling.gold += share
							a_pc.quest_gold = getattr(a_pc, "quest_gold", 0) + share
							MobaUI.spawn_fct(scene, ally.getTransform().worldPosition, f"+{share}G", cave.Vector4(0.8, 0.8, 0.0, 1.0))
				
				# XP Sharing Logic
				allies = [e for e in get_entities_in_radius(scene, v_pos, 14.0) if e.hasTag("player") and e.hasTag(team) and e != killer]
				if allies:
					shared_xp = xp_val * GOLD_XP_SPLIT_PERCENT / len(allies)
					for ally in allies:
						a_pc = ally.getPy("PlayerController")
						if a_pc and not (a_pc.flags & EffectFlags.INVULNERABLE):
							if a_pc.respawnTimer <= 0:
								a_pc.add_exp(shared_xp)
								
		# Shutdown Bounty Logic & Stat Tracking
		if victim.hasTag("player"):
			v_pc = victim.getPy("PlayerController")
			if killer:
				MatchStatsManager.track_kill(killer.name)
			MatchStatsManager.track_death(victim.name)
			
			contribs = victim.getProperties().get("contributions", {})
			scene_time = victim.getScene().getElapsedSceneTime()
			for name, data in contribs.items():
				c_time, c_ent = data
				if (not killer or name != killer.name) and (scene_time - c_time) < 10.0:
					MatchStatsManager._get_stats(name)["assists"] += 1
			
			# Reset spree
			if v_pc:
				v_pc.killing_spree = 0 # Phase 115 variable name fix (was killStreak)
				v_pc.killStreak = 0 # Reset both to be safe
				
			if killer:
				AnnouncerManager.on_hero_kill(killer, victim)
				
				# Bounty Payout to Killer
				k_pc = killer.getPy("PlayerController") if hasattr(killer, 'getPy') else None
				if k_pc and v_pc and hasattr(v_pc, "killing_spree") and v_pc.killing_spree >= 3:
					bounty = 150 + ((v_pc.killing_spree - 3) * 50)
					k_pc.leveling.gold += bounty
					AnnouncerManager.announce_shutdown(killer, victim, bounty)

		# Victim Death Increment
		v_pc = victim.getPy("PlayerController") if hasattr(victim, 'getPy') else None
		if v_pc:
			v_pc.leveling.deaths += 1
		
		# Assist Logic (LoL Parity: 50% Gold/XP Pool split among contributors)
		contribs = victim.getProperties().get("contributions", {})
		now = victim.getScene().getElapsedSceneTime()
		
		valid_assistants = []
		for ent_name, data in contribs.items():
			last_hit_time = data[0]
			entity = data[1]
			if entity and entity.isActive() and entity != killer and (now - last_hit_time) <= 10.0:
				valid_assistants.append(entity)
				
		if valid_assistants:
			pool_gold = int(gold_val * GOLD_XP_SPLIT_PERCENT)
			pool_xp = int(xp_val * GOLD_XP_SPLIT_PERCENT)
			
			is_dredge_ulti = False
			if killer:
				k_pc = killer.getPy("PlayerController") if hasattr(killer, 'getPy') else None
				if k_pc and k_pc.heroName == "Dredge":
					if getattr(k_pc, "last_kill_is_execute", False):
						is_dredge_ulti = True
						k_pc.last_kill_is_execute = False 
			
			share_gold_normal = int(pool_gold / len(valid_assistants))
			share_xp = int(pool_xp / len(valid_assistants))
			
			for i, ass in enumerate(valid_assistants):
				a_pc = ass.getPy("PlayerController") if hasattr(ass, 'getPy') else None
				if a_pc:
					earned_gold = share_gold_normal
					if is_dredge_ulti and i == 0:
						earned_gold = gold_val 
					a_pc.leveling.gold += earned_gold
					a_pc.add_exp(share_xp)
					if victim.hasTag("player"): a_pc.leveling.assists += 1
