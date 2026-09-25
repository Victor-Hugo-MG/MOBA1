import cave
from Core import MobaCommon
from UI import MobaUI

class MatchManager(cave.Component):
	"""
	Phase 119: Match Orchestration.
	Manages the high-level flow of the game: 
	Loading -> Gates Closed -> Active -> Victory/Defeat.
	"""
	def start(self, scene):
		self.state = MobaCommon.MatchState.GATES_CLOSED
		self.timer = 0.0
		self.gates_opened = False
		self.minions_spawned = False
		
		# 1. Spawn Barriers (Fountain Gates)
		self.gates = []
		for team in ["teamA", "teamB"]:
			gate_pts = scene.getEntitiesWithTag(f"Gate_{team}")
			for pt in gate_pts:
				# Spawn a physical barrier template
				gate = scene.addFromTemplate("VFX_SpawnGate", pt.getTransform().worldPosition)
				if gate:
					mat = gate.get("Mesh").getFinalMaterial()
					color = MobaCommon.Team.COLORS[team]
					mat.uniforms.set("u_baseColor", color)
					self.gates.append(gate)

		# 2. Match Start Sequence
		MobaCommon.play_announcer(scene, "WELCOME_TO_THE_FLUX")
		
	def update(self):
		dt = cave.getDeltaTime()
		scene = self.entity.getScene()
		
		if self.state == MobaCommon.MatchState.GATES_CLOSED:
			self.timer += dt
			
			# 15s Countdown for Gates
			if self.timer >= 15.0 and not self.gates_opened:
				self.open_gates(scene)
				
			# 30s for Minions
			if self.timer >= 30.0 and not self.minions_spawned:
				self.minions_spawned = True
				MobaCommon.play_announcer(scene, "MINIONS_SPAWNED")
				self.state = MobaCommon.MatchState.ACTIVE

	def open_gates(self, scene):
		self.gates_opened = True
		MobaCommon.play_announcer(scene, "THE_BATTLE_BEGINS")
		for gate in self.gates:
			# Animate gate opening (move underground or fade)
			gate.getTransform().move(0, -5.0, 0, False)  # Cave API: move() not translate()
			# VFX
			MobaCommon.spawn_vfx(scene, "VFX_Gate_Dissolve", gate.getTransform().worldPosition)
