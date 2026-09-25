import cave
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Core import MobaCommon

class FloatingCombatTextComponent(cave.Component):
	"""Logic for spawning and animating floating damage/heal numbers."""
	
	def start(self, scene):
		self.transf = self.entity.getTransform()
		# Colors based on MobaCommon.DamageType
		self.colors = {
			MobaCommon.DamageType.PHYSICAL: cave.Vector4(1, 0, 0, 1),    # Red
			MobaCommon.DamageType.MAGIC:    cave.Vector4(0.6, 0.2, 1, 1), # Purple
			MobaCommon.DamageType.TRUE:     cave.Vector4(1, 1, 1, 1),    # White
			MobaCommon.DamageType.HEAL:     cave.Vector4(0, 1, 0, 1),    # Green
			MobaCommon.DamageType.PURE:     cave.Vector4(1, 0.5, 0, 1),  # Orange
			MobaCommon.DamageType.GOLD:     cave.Vector4(1, 0.9, 0, 1)   # Gold (Yellow)
		}
		self.active_fcts = {} # Phase 42: Grouped FCT tracking

	def setup(self, amount, dmg_type, continuous=False):
		"""Public entry point called by apply_damage."""
		if amount <= 0 and dmg_type != MobaCommon.DamageType.HEAL: return
		
		# Phase 42: Continuous (DoT) grouping logic
		if continuous and dmg_type in self.active_fcts:
			fct_ent = self.active_fcts[dmg_type]
			if fct_ent and fct_ent.isActive():
				text_cmp = fct_ent.get("UIElement")
				if text_cmp:
					curr_text = text_cmp.getText()
					try:
						curr_val = int(curr_text.replace("+", ""))
						new_val = curr_val + int(amount)
						prefix = "+" if dmg_type == MobaCommon.DamageType.HEAL else ""
						text_cmp.setText(f"{prefix}{new_val}")
						
						# Reset animation timer
						anim = fct_ent.getPy("FCTAnimationComponent")
						if anim: anim.timer = 1.0 
						return
					except: pass
			else:
				# Cleanup stale reference
				del self.active_fcts[dmg_type]

		scene = self.entity.getScene()
		# Spawn a floating text template at chest height
		spawn_pos = self.transf.worldPosition + cave.Vector3(0, 2.0, 0)
		# Add slight random jitter to prevent overlap
		spawn_pos += cave.Vector3(
			cave.random.uniform(-0.5, 0.5),
			cave.random.uniform(0, 0.5),
			cave.random.uniform(-0.5, 0.5)
		)
		
		fct_ent = scene.addFromTemplate(MobaCommon.Templates.FCT_TEMPLATE, spawn_pos)
		if fct_ent:
			if continuous: self.active_fcts[dmg_type] = fct_ent
			# Setup text content
			text_cmp = fct_ent.get("UIElement")
			if text_cmp:
				prefix = "+" if dmg_type == MobaCommon.DamageType.HEAL else ""
				text_cmp.setText(f"{prefix}{int(amount)}")
				
				# Set Color
				color = self.colors.get(dmg_type, cave.Vector4(1,1,1,1))
				# Try to set material uniform if text is mesh-based or UI-based
				if hasattr(text_cmp, "color"):
					text_cmp.color = color
				
			# Attach animation component
			anim = fct_ent.add("FCTAnimationComponent")
			anim.color = self.colors.get(dmg_type, cave.Vector4(1,1,1,1))

class FCTAnimationComponent(cave.Component):
	"""Handles the upward drift and fade-out of an FCT instance."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.timer = 1.0 # 1 second lifetime
		self.fade_start = 0.5 # Start fading at 0.5s
		self.drift_speed = 2.0 # Units per second
		self.ui = self.entity.get("UIElement")

	def update(self):
		dt = cave.getDeltaTime()
		self.timer -= dt
		
		if self.timer <= 0:
			self.entity.kill()
			return
			
		# Drift Up
		self.transf.applyMovement(cave.Vector3(0, self.drift_speed * dt, 0))
		
		# Fade Out
		if self.timer < self.fade_start:
			alpha = self.timer / self.fade_start
			if self.ui and hasattr(self.ui, "color"):
				c = self.ui.color
				self.ui.color = cave.Vector4(c.x, c.y, c.z, alpha)

class HealthJuiceComponent(cave.Component):
	"""Phase 35: Handles smooth 'delayed drop' health bar bar animations."""
	def start(self, scene):
		self.props = self.entity.getProperties()
		self.current_hp = self.props.get("health", 100)
		self.shadow_hp = self.current_hp
		self.timer = 0.0
		self.delay = 0.5 # Wait 0.5s before shadow bar drops
		self.drop_speed = 5.0 # HP per second scale
		
	def update(self):
		actual_hp = self.props.get("health", 0)
		dt = cave.getDeltaTime()
		
		# 1. Detect Damage
		if actual_hp < self.current_hp:
			self.timer = self.delay
			self.current_hp = actual_hp
		elif actual_hp > self.current_hp:
			# Healing snaps shadow up immediately or stays? usually stays for cleaner effect
			self.current_hp = actual_hp
			if actual_hp > self.shadow_hp:
				self.shadow_hp = actual_hp
		
		# 2. Update Shadow HP
		if self.timer > 0:
			self.timer -= dt
		else:
			if self.shadow_hp > self.current_hp:
				# Drop shadow bar smoothly
				diff = self.shadow_hp - self.current_hp
				self.shadow_hp -= diff * 5.0 * dt
				if self.shadow_hp < self.current_hp:
					self.shadow_hp = self.current_hp
					
		# 3. Update UI Uniforms (Assuming standard Moba health material)
		mesh = self.entity.getChild("Mesh")
		if mesh:
			# If this unit has a floating health bar component
			ui = self.entity.getPy("PlayerController")
			if ui and hasattr(ui, "update_shadow_bar"):
				ui.update_shadow_bar(self.shadow_hp)

class LowHPFeedbackComponent(cave.Component):
	"""Phase 37: Pulsing red vignette when player is low on health."""
	def start(self, scene):
		self.pc = self.entity.getPy("PlayerController")
		# Vignette is expected to be a child of the HUD entity this is attached to
		self.vignette = self.entity.getChild("HUD_Vignette")
		self.ui = self.vignette.get("UIElement") if self.vignette else None
		if self.vignette:
			self.vignette.deactivate(scene)
		
	def update(self):
		if not self.pc or not self.ui: return
		scene = self.entity.getScene()
		
		# Threshold: 25% HP
		props = self.pc.entity.getProperties()
		max_hp = props.get("maxHealth", props.get("maxHP", 100))
		current_hp = props.get("health", 0)
		hp_pct = current_hp / max_hp if max_hp > 0 else 1.0
		
		if hp_pct < 0.25 and current_hp > 0:
			if not self.vignette.isActive():
				self.vignette.activate(scene)
			
			# Pulse Alpha: math.sin(time * speed) mapped to [0.2, 0.8]
			import math
			t = scene.getElapsedSceneTime()
			pulse = (math.sin(t * 5.0) + 1.0) * 0.5 # [0, 1]
			alpha = 0.2 + (pulse * 0.6)
			
			# Cave API check: color is Vector4(r, g, b, a)
			c = self.ui.color
			self.ui.color = cave.Vector4(c.x, c.y, c.z, alpha)
		else:
			if self.vignette and self.vignette.isActive():
				self.vignette.deactivate(scene)

class UIPopComponent(cave.Component):
	"""Phase 37: Generic helper for 'Juicy' UI scale animations."""
	def start(self, scene):
		self.transf = self.entity.getTransform()
		self.base_scale = self.transf.getScale().copy()
		self.target_scale = self.base_scale
		self.timer = 0.0
		self.duration = 0.2
		
	def pop(self, factor=1.2, duration=0.2):
		"""Triggers a scale pop effect."""
		self.target_scale = self.base_scale * factor
		self.timer = duration
		self.duration = duration
		
	def update(self):
		if self.timer > 0:
			dt = cave.getDeltaTime()
			self.timer -= dt
			
			# Lerp back to base scale
			progress = 1.0 - (self.timer / self.duration)
			# Smooth snap: pop high and return
			current = cave.math.lerp(self.target_scale, self.base_scale, progress)
			self.transf.setScale(current)
			
			if self.timer <= 0:
				self.transf.setScale(self.base_scale)
