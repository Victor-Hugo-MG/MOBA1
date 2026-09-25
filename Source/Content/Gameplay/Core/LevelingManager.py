import cave
import cave.event
import cave.math
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Data import HeroRegistry
from Data import ItemRegistry
from Data import RuneRegistry
from Data import SkinRegistry
from Data import AnimationRegistry
from UI import MobaUI
from UI import MobaUIFX
from Core import MobaStates
from Core import MobaItems
from Core import MobaCommon
from Core.MobaPassives import MobaPassiveManager
import math
import random
import json



class LevelingManager:
	"""Phase 18: Decoupled XP and Gold logic."""
	def __init__(self, pc):
		self.pc = pc
		self.level = 1
		self.exp = 0
		self.gold = 500
		self.kills = 0
		self.deaths = 0
		self.assists = 0
		self.cs = 0
		self.skillPoints = 1
		self.skillLevels = {"Q": 0, "W": 0, "E": 0, "R": 0}
		self.expToNext = 280

	def add_exp(self, amount):
		self.exp += amount
		while self.exp >= self.expToNext and self.level < 18:
			self.level_up()

	def level_up(self):
		self.exp -= self.expToNext
		self.level += 1
		self.skillPoints += 1
		self.expToNext = int(self.expToNext * 1.15) + 100
		self.pc.recalculate_stats() # Force update on level up
		
		# ── Wave 35/37: Level Up Feedback ───────────────────────────
		from Core import MobaCommon
		from UI import MobaUI
		MobaCommon.play_sfx(self.pc.entity, MobaCommon.Templates.SFX_ANNOUNCEMENT)
		MobaCommon.spawn_vfx(self.pc.entity.getScene(), MobaCommon.Templates.VFX_LEVEL_UP, self.pc.entity.getTransform().worldPosition)
		
		f_color = cave.Vector4(1.0, 0.9, 0.2, 1.0) # Golden-Yellow
		MobaUI.spawn_fct(self.pc.entity.getScene(), self.pc.entity.getTransform().worldPosition, "LEVEL UP!", f_color)
