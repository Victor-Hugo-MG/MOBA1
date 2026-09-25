import cave
import cave.math
import sys, os
import math
import random
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core.MobaCommon import *


class WardComponent(cave.Component):
	"""Phase 31: Provides vision in a radius and reveals brushes."""
	duration = 90.0
	vision_radius = 12.0
	team = "teamA"
	
	def start(self, scene):
		# Optimized Pattern: scheduleKill is more efficient than manual update ticking
		self.entity.scheduleKill(self.duration)
		self.entity.getProperties()["visionRange"] = self.vision_radius
		self.entity.getProperties()["team"] = self.team
		self.entity.addTag(f"{self.team}_ward")
		self.entity.addTag("ward")
		self.actors = set()
		
	def update(self):
		pass # Vision logic handled via VisionManager; lifetime handled by scheduleKill
