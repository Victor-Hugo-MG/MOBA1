import cave
from Core import MobaCommon

class FactionShaderComponent(cave.Component):
	"""
	Phase 117: Premium Visual Polish.
	Periodically updates material uniforms based on faction identity to create 
	dynamic effects like crystalline pulses, techno-glitches, and organic magic.
	"""
	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		self.mesh_comp = self.entity.get("Mesh")
		self.faction = self.entity.getProperties().get("faction", "Nomade")
		self.update_timer = 0.0
		self.death_anim_timer = 0.0
		
	def update(self):
		self.update_timer += cave.getDeltaTime()
		if self.update_timer < 0.05: return # Performance: 20 FPS update for shaders is plenty
		self.update_timer = 0.0
		
		if not self.mesh_comp: return
		mat = self.mesh_comp.getFinalMaterial()
		if not mat: return
		
		# 1. Update Faction Signatures
		params = MobaCommon.get_faction_shader_params(self.faction)
		for p, v in params.items():
			mat.uniforms.set(p, v)
			
		# 2. Death Dissolve logic
		if self.pc and self.pc.health <= 0:
			self.death_anim_timer += cave.getDeltaTime()
			dissolve = cave.math.clamp(self.death_anim_timer / 2.0, 0, 1) # 2s dissolve
			mat.uniforms.set("u_dissolve", dissolve)
			mat.uniforms.set("u_emissiveColor", cave.Vector3(1.0, 0.2, 0.1) * (1.0 - dissolve))
		else:
			self.death_anim_timer = 0.0
			mat.uniforms.set("u_dissolve", 0.0)
