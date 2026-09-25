import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core import MobaCommon

class PerformanceHUD(cave.Component):
	"""Phase 39: Monitors logic stability and entity overhead."""
	def start(self, scene):
		self.text_el = self.entity.getChild("Perf_Text")
		self.update_timer = 0.0
		
	def update(self):
		dt = cave.getDeltaTime()
		self.update_timer += dt
		
		# Update every 1s to avoid UI overhead
		if self.update_timer >= 1.0:
			self.update_timer = 0.0
			scene = self.entity.getScene()
			
			# Logic Pulse Check
			tps = MobaCommon.GameTick._tick_rate
			tick_num = MobaCommon.GameTick._current_tick
			
			# Entity Counts
			counts = {}
			for tag in ["player", "minion", "turret", "monster"]:
				counts[tag] = len(scene.getEntitiesWithTag(tag))
			
			total_units = sum(counts.values())
			
			# Status
			match_status = "OVER" if MobaCommon.is_match_over else "ACTIVE"
			
			if self.text_el:
				ui = self.text_el.get("UIElement")
				if ui:
					perf_str = f"TPS: {int(tps)} | Ticks: {tick_num} | Units: {total_units} [{match_status}]"
					ui.setText(perf_str)
					
			# Console Heartbeat (Professional)
			# print(f"[PERF] TPS: {tps} | Units: {total_units} | GC: 0")
