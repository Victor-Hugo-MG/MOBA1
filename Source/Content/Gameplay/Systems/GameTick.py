import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))



class GameTick:
	"""Static framework for deterministic logic synchronization (Phase 18)."""
	_tick_rate = 30.0 # 30Hz Logic
	_tick_timer = 0.0
	_current_tick = 0
	_callbacks = []
	_hit_stop_timer = 0.0
	_time_scale = 1.0  # Custom time multiplier (Cave Engine has no setTimeScale)

	@staticmethod
	def update(dt, scene=None):
		GameTick._tick_timer += dt
		while GameTick._tick_timer >= (1.0 / GameTick._tick_rate):
			GameTick._tick_timer -= (1.0 / GameTick._tick_rate)
			GameTick._current_tick += 1
			# Phase 70: Update EntityRegistry at tick boundary
			if scene:
				EntityRegistry.tick(scene)
			for cb in GameTick._callbacks:
				cb()
		
		# Phase 127: Hit-Stop Reset logic
		# NOTE: cave.setTimeScale() does not exist in Cave Engine API.
		# Hit-stop is implemented via a custom time multiplier instead.
		if GameTick._hit_stop_timer > 0:
			GameTick._hit_stop_timer -= dt
			if GameTick._hit_stop_timer <= 0:
				GameTick._time_scale = 1.0

	@staticmethod
	def is_tick_frame():
		"""Returns True if the current frame falls within a logic tick boundary."""
		return GameTick._tick_timer < (1.0 / GameTick._tick_rate)

	@staticmethod
	def get_scaled_dt():
		"""Returns delta time adjusted by the custom hit-stop time scale."""
		return cave.getDeltaTime() * GameTick._time_scale

	@staticmethod
	def trigger_hit_stop(duration):
		"""Phase 127: Brief time freeze for impact feel.
		Uses custom time multiplier since Cave Engine has no setTimeScale()."""
		GameTick._time_scale = 0.01  # Near freeze
		GameTick._hit_stop_timer = duration

	@staticmethod
	def get_time_minutes():
		"""Returns the current elapsed game time in minutes."""
		return GameTick._current_tick / (GameTick._tick_rate * 60.0)

	@staticmethod
	def get_game_phase():
		"""Phase 77: Returns EARLY (0-14), MID (14-25), or LATE (25+)."""
		mins = GameTick.get_time_minutes()
		if mins < 14.0: return "EARLY"
		if mins < 25.0: return "MID"
		return "LATE"

	@staticmethod
	def get_temporal_scaling():
		"""Phase 31/77: Returns a multiplier for NPC growth. 
		Early: 1.0 + 5%/min. Late (25+): 1.0 + 8%/min (Accelerated)."""
		mins = GameTick.get_time_minutes()
		if mins < 25.0:
			return 1.0 + (mins * 0.05)
		else:
			# Accelerated curve for Late Game push
			return 1.0 + (25.0 * 0.05) + ((mins - 25.0) * 0.10)

	@staticmethod
	def subscribe(callback):
		if callback not in GameTick._callbacks:
			GameTick._callbacks.append(callback)
			
	@staticmethod
	def unsubscribe(callback):
		if callback in GameTick._callbacks:
			GameTick._callbacks.remove(callback)

	@staticmethod
	def reset():
		"""Phase 23: Complete reset for scene transitions to prevent callback leaks.
		NOTE: This only resets GameTick's own state. The full match reset
		(is_match_over, VisionManager, EntityRegistry, etc.) is handled by
		MobaCommon.py's GameTick.reset() which is the version that actually runs."""
		GameTick._callbacks = []
		GameTick._tick_timer = 0.0
		GameTick._current_tick = 0
		GameTick._hit_stop_timer = 0.0
		GameTick._time_scale = 1.0

# ──────────────────────────────────────────────
# Phase 70: Centralized Entity Registry & Spatial Grid
# Replaces scattered getEntitiesWithTag() calls
# ──────────────────────────────────────────────
