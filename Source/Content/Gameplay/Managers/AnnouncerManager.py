import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core import MobaCommon
from Core.MobaCommon import MatchStatsManager, play_sfx, Templates

class AnnouncerManager:
	"""Phase 32: Tracks killing sprees, multi-kill windows, and global broadcasts."""
	_multi_kill_window = 10.0 # Standard MOBA 10s window
	_spree_thresholds = {
		3: "Killing Spree", 4: "Rampage", 5: "Unstoppable", 
		6: "Dominating", 7: "Godlike", 8: "LEGENDARY"
	}
	_multi_labels = {
		2: ("Double Kill", "DOUBLE"), 
		3: ("Triple Kill", "TRIPLE"), 
		4: ("Quadra Kill", "DEFAULT"), # No quadra-specific art yet
		5: ("PENTAKILL!", "PENTA")
	}
	
	@staticmethod
	def on_hero_kill(killer, victim):
		k_pc = killer.getPy("PlayerController")
		if not k_pc: return
		
		# Phase 38: Stats
		MatchStatsManager.track_kill(killer.name)
		MatchStatsManager.track_death(victim.name)
		
		dt = cave.getDeltaTime()
		now = killer.getScene().getElapsedSceneTime()
		
		# 1. Killing Spree Logic
		k_pc.killing_spree = getattr(k_pc, "killing_spree", 0) + 1
		msg = AnnouncerManager._spree_thresholds.get(k_pc.killing_spree)
		if msg:
			AnnouncerManager.broadcast_global(f"{killer.name} is {msg.upper()}!", is_banner=True)
			
		# 2. Multi-Kill Logic
		last_kill_time = getattr(k_pc, "last_kill_time", 0.0)
		if (now - last_kill_time) <= AnnouncerManager._multi_kill_window:
			k_pc.multi_kill_count = getattr(k_pc, "multi_kill_count", 0) + 1
		else:
			k_pc.multi_kill_count = 1
			
		k_pc.last_kill_time = now
		
		multi_data = AnnouncerManager._multi_labels.get(k_pc.multi_kill_count)
		if multi_data:
			label, b_type = multi_data
			AnnouncerManager.broadcast_global(label.upper(), is_banner=True, source=killer, banner_type=b_type)
			
		# 3. Static Kill Feed Entry
		from UI import MobaUI
		MobaUI.add_kill_feed(killer, victim)
		
		# 4. Gold Popup FCT
		f_color = cave.Vector4(1.0, 0.8, 0.0, 1.0) # Gold
		MobaUI.spawn_fct(killer.getScene(), victim.getTransform().worldPosition, "+300G", f_color)

	@staticmethod
	def announce_shutdown(killer, victim, bounty):
		AnnouncerManager.broadcast_global(f"SHUT DOWN! {killer.name} ended {victim.name}'s spree (+{bounty}G)", is_banner=True)

	@staticmethod
	def broadcast_global(text, is_banner=False, source=None, banner_type="DEFAULT"):
		from UI import MobaUI
		# Feedback (Visual & Audio)
		if is_banner:
			MobaUI.show_announcement(text, banner_type=banner_type)
			if source: 
				scene = source.getScene()
				play_sfx(scene, Templates.SFX_ANNOUNCEMENT) 
		else:
			MobaUI.broadcast_event(text)

# ──────────────────────────────────────────────
# ROTATION HELPERS (Phase 76: Constant Turn Rate)
# ──────────────────────────────────────────────
