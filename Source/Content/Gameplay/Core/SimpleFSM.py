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



class SimpleFSM:
	"""Lightweight state machine that drives MobaStates."""
	def __init__(self, initial_state):
		self._state = initial_state
		self._controller = None

	def setState(self, new_state):
		self._state = new_state
		if self._controller and hasattr(self._state, 'start'):
			self._state.start(self._controller)

	def run(self):
		if self._state:
			next_state = self._state.run()
			if next_state is not None and next_state is not self._state:
				self._state = next_state
				if self._controller and hasattr(self._state, 'start'):
					self._state.start(self._controller)

	def bind(self, controller):
		"""Bind controller reference and start the initial state."""
		self._controller = controller
		if self._state and hasattr(self._state, 'start'):
			self._state.start(controller)
