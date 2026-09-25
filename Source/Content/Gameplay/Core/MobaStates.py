import cave
import sys, os, random
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Core import MobaCommon
from Core import MobaItems
from Data import AnimationRegistry

class IdleState:
	def start(self, controller):
		self.controller = controller
		self.animator = self.controller.animator
		# Stop any residual movement
		if getattr(self.controller, "character", None):
			self.controller.character.setWalkDirection(0, 0, 0)
			
		if self.animator:
			anim_name = AnimationRegistry.get_anim(self.controller.heroName, "idle")
			self.animator.playByName(anim_name, 0.2, loop=True)

	def run(self):
		if self.controller.inputBuffer:
			cmd, data = self.controller.inputBuffer
			if cmd == "MOVE":
				self.controller.inputBuffer = None
				return MovementState(data)
			elif cmd == "ATTACK":
				self.controller.inputBuffer = None
				return AttackState(data)
			elif cmd == "CAST":
				self.controller.inputBuffer = None
				# data is the key (Q, W, E, R, etc)
				return AbilityState(data)
		
		# Phase 116: Auto-Attack logic
		if getattr(self.controller, "autoAttack", False):
			radius = self.controller.entity.getProperties().get("attackRange", 5.0)
			target = MobaCommon.get_closest_target(self.controller.transf.worldPosition, radius, attacker=self.controller.entity)
			if target:
				return AttackState(target)

		return self

class MovementState:
	def __init__(self, target_pos):
		self.target_pos = target_pos

	def start(self, controller):
		self.controller = controller
		self.animator = self.controller.animator
		if self.animator:
			anim_name = AnimationRegistry.get_anim(self.controller.heroName, "walk")
			self.animator.playByName(anim_name, 0.2, loop=True)
		self.transf = self.controller.transf

	def run(self):
		# CC Interrupt
		if self.controller.flags & (MobaCommon.EffectFlags.STUN | MobaCommon.EffectFlags.ROOT):
			return IdleState()

		dt = cave.getDeltaTime()
		diff = self.target_pos - self.transf.worldPosition
		dist = diff.length()
		
		if dist < 0.2:
			return IdleState()
			
		# Check for new input override
		if self.controller.inputBuffer:
			cmd, data = self.controller.inputBuffer
			if cmd == "MOVE":
				self.target_pos = data
				self.controller.inputBuffer = None
			elif cmd == "ATTACK":
				self.controller.inputBuffer = None
				return AttackState(data)
			elif cmd == "CAST":
				self.controller.inputBuffer = None
				return AbilityState(data)
				
		# Apply Movement
		dir = diff.normalized()
		ms = self.controller.entity.getProperties().get("moveSpeed", 300)
		tr = self.controller.entity.getProperties().get("turnRate", 540)
		speed = ms * MobaCommon.SPEED_RATIO
		MobaCommon.rotate_towards(self.transf, dir, dt, tr)
		# Bible Pattern: Rotate Entity -> Move Local Z
		# Displacement Correction: setWalkDirection expects (m/s * dt)
		self.controller.character.setWalkDirection(0, 0, speed * dt)
		
		return self

class AttackState:
	def __init__(self, target_ent):
		self.target_ent = target_ent

	def start(self, controller):
		self.controller = controller
		self.animator = self.controller.animator
		self.transf = self.controller.transf
		
		# --- Attack Speed Scaling ---
		# Use cached totalAS from PlayerController instead of per-frame property lookup
		as_mult = getattr(self.controller, "totalAS", 1.0)
		# Phase 70: Minimum duration guard — prevents zero-frame attacks at high AS
		self.startup = max(0.05, 0.35 / as_mult)  # Never less than 50ms
		self.recovery = max(0.05, 0.45 / as_mult)  # Never less than 50ms
		self.hit_executed = False
		
		# Stop movement while attacking
		if getattr(self.controller, "character", None):
			self.controller.character.setWalkDirection(0, 0, 0)
			
		if self.animator:
			anim_name = AnimationRegistry.get_anim(self.controller.heroName, "attack")
			self.animator.playByName(anim_name, 0.1)

	def run(self):
		# Wave 70: CC Interrupt (LoL Standard: Silence doesn't stop AA, Disarm does)
		if self.controller.flags & (MobaCommon.EffectFlags.STUN | MobaCommon.EffectFlags.DISARM):
			return IdleState()

		dt = cave.getDeltaTime()
		
		# Wave 70: Target Validity & Vision Check (Cancel wind-up if target dies or enters fog/brush)
		if not self.target_ent or not self.target_ent.isActive():
			return IdleState()
			
		# --- Phase 100: Range & RFC Check ---
		t_pos = self.target_ent.getTransform().worldPosition
		dist = (t_pos - self.transf.worldPosition).length()
		
		attack_range = self.controller.entity.getProperties().get("attackRange", 5.0)
		if getattr(self.controller, "energized_stacks", 0) >= 100:
			if MobaItems.ItemEffectManager.has_item_effect(self.controller, "onHit", "FIRE_RANGE"):
				attack_range *= 1.35 # +35% Range bonus
		
		if not self.hit_executed:
			# LoL Rule: Losing vision during startup cancels the attack
			if not MobaCommon.is_target_visible(self.controller.entity, self.target_ent):
				return IdleState()

			if dist > attack_range:
				# Target out of range! Chase.
				dir = (t_pos - self.transf.worldPosition).normalized()
				tr = self.controller.entity.getProperties().get("turnRate", 540)
				MobaCommon.rotate_towards(self.transf, dir, dt, tr)
				
				ms = self.controller.entity.getProperties().get("moveSpeed", 300)
				speed = ms * MobaCommon.SPEED_RATIO
				self.controller.character.setWalkDirection(0, 0, speed * dt)
				
				# Reset windup if we were previously in range
				# (Prevents partial attacks after target dashes away)
				return self 

			# In range! Stop moving and rotate to target
			self.controller.character.setWalkDirection(0, 0, 0)
			dir = (t_pos - self.transf.worldPosition).normalized()
			tr = self.controller.entity.getProperties().get("turnRate", 540)
			MobaCommon.rotate_towards(self.transf, dir, dt, tr)
			
		# Wind-up
		if not self.hit_executed:
			self.startup -= dt
			if self.startup <= 0:
				self.execute_hit()
				self.hit_executed = True
		else:
			# Recovery (Orbwalking slot)
			self.recovery -= dt
			if self.recovery <= 0:
				return IdleState()
				
			# Animation Break (Orbwalking / Clipping)
			if self.controller.inputBuffer:
				cmd, data = self.controller.inputBuffer
				if cmd in ["MOVE", "ATTACK", "CAST"]:
					# Clip backswing and transition immediately
					self.controller.inputBuffer = None
					if cmd == "MOVE": return MovementState(data)
					if cmd == "ATTACK": return AttackState(data)
					if cmd == "CAST": return AbilityState(data)
					
		return self

	def execute_hit(self):
		if not self.target_ent or not self.target_ent.isActive(): return
		
		# Asset Isolation: Pull audio-visuals from heroData
		sfx_atk = self.controller.heroData.get("sfx_attack")
		if sfx_atk: MobaCommon.play_sfx(self.controller.entity, sfx_atk)
		
		vfx_cast = self.controller.heroData.get("vfx_attack_cast")
		if vfx_cast: MobaCommon.spawn_vfx(self.controller.entity.getScene(), vfx_cast, self.transf.worldPosition)

		# Wave 25: Ranged Projectile Support
		is_ranged = self.controller.entity.getProperties().get("isRanged", False)
		
		# --- Wave 100: Crit RNG Check ---
		crit_chance = self.controller.entity.getProperties().get("critChance", 0.0)
		is_crit = random.random() < crit_chance
		dmg = self.controller.ad
		
		if is_crit:
			# Signal for passives & FCT
			self.controller.entity.getProperties()["isLastHitCrit"] = True
			# Infinity Edge modifier
			crit_mult = 2.0
			if MobaItems.ItemEffectManager.has_item_effect(self.controller, "critPower", "IE_PASSIVE"):
				crit_mult = 2.35 # +35% bonus
			dmg *= crit_mult
			
			# Flickerblade CD reduction
			if hasattr(self.controller, "on_crit_landed"):
				self.controller.on_crit_landed()
		else:
			self.controller.entity.getProperties()["isLastHitCrit"] = False

		if is_ranged:
			# Spawn Homing Projectile
			template = self.controller.heroData.get("attackProjectile", MobaCommon.Templates.PROJ_BASIC)
			speed = self.controller.heroData.get("attackProjSpeed", 35.0)
			MobaCommon.spawn_homing_projectile(
				self.controller.entity.getScene(),
				self.controller.entity,
				self.target_ent,
				template,
				speed,
				dmg,
				hit_vfx=self.controller.heroData.get("vfx_attack_hit"),
				is_basic=True
			)
		else:
			# Melee: Immediate Interaction
			# 1. On-Hit Effects (Items & Special Passive hooks)
			MobaItems.ItemEffectManager.process_on_hit(self.controller, self.target_ent, is_ability=False, flags=MobaCommon.EffectFlags.BASIC_ATTACK)
			
			# 2. Damage Application
			MobaCommon.apply_damage(self.target_ent, dmg, MobaCommon.DamageType.PHYSICAL, attacker=self.controller.entity, flags=MobaCommon.EffectFlags.BASIC_ATTACK)
			
			# 3. Visual Feedback
			vfx_hit = self.controller.heroData.get("vfx_attack_hit")
			if vfx_hit: MobaCommon.spawn_vfx(self.controller.entity.getScene(), vfx_hit, self.target_ent.getTransform().worldPosition)

class AbilityState:
	def __init__(self, skill_key, ability_data=None, stage_data=None):
		self.skill_key = skill_key
		self.ability_data = ability_data
		self.stage_data = stage_data if stage_data else ability_data

	def start(self, controller):
		self.controller = controller
		# If data wasn't passed, try to fetch from controller
		if not self.ability_data:
			self.ability_data = self.controller.get_skill_data(self.skill_key)
			self.stage_data = self.ability_data
			
		self.startup = self.stage_data.get("startup", 0.2)
		self.recovery = self.stage_data.get("recovery", 0.3)
		self.executed = False
		
		# Stop movement for most abilities (unless dash/unstoppable)
		if getattr(self.controller, "character", None):
			if not self.stage_data.get("isDash"):
				self.controller.character.setWalkDirection(0, 0, 0)
			
		anim = self.stage_data.get("animStartup", AnimationRegistry.get_anim(self.controller.heroName, "ability"))
		if self.controller.animator:
			self.controller.animator.playByName(anim, 0.1)
			
		# Phase 116: Rotate toward target
		target_pos = getattr(self.controller, "clampedTargetPos", None)
		if not target_pos:
			# Phase 128: AI Virtual Cursor
			if getattr(self.controller, "virtualCursorPos", None):
				target_pos = self.controller.virtualCursorPos
			else:
				out = self.controller.entity.getScene().getDataOverMousePosition()
				if out.hit: target_pos = out.position
			
		if target_pos:
			diff = target_pos - self.controller.transf.worldPosition
			if diff.length() > 0.1:
				self.controller.transf.lookAt(diff.normalized())

	def run(self):
		# CC Interrupt
		if self.controller.flags & (MobaCommon.EffectFlags.STUN | MobaCommon.EffectFlags.SILENCE):
			return IdleState()

		dt = cave.getDeltaTime()
		
		# Lock rotation at startup unless explicitly allowed (LoL Standard)
		# (Removal of per-frame mouse-look-at to prevent 'steering' bugs)
		
		if not self.executed:
			self.startup -= dt
			if self.startup <= 0:
				self.controller.executeAbilityEffect(self.skill_key, self.stage_data)
				self.executed = True
		else:
			self.recovery -= dt
			if self.recovery <= 0:
				return IdleState()
				
		return self
class ForcedMovementState:
	"""Handles Charm (toward) and Fear (away) forced movement."""
	def __init__(self, source, toward=True):
		self.source = source
		self.toward = toward

	def start(self, controller):
		self.controller = controller
		self.animator = self.controller.animator
		if self.animator:
			anim_name = AnimationRegistry.get_anim(self.controller.heroName, "walk")
			self.animator.playByName(anim_name, 0.2, loop=True)
		self.transf = self.controller.transf

	def run(self):
		if not self.source or not self.source.isActive(): return IdleState()
		
		# Check if effect still active (flags check)
		is_forced = self.controller.flags & (MobaCommon.EffectFlags.CHARM | MobaCommon.EffectFlags.FEAR | MobaCommon.EffectFlags.TAUNT)
		if not is_forced:
			return IdleState()

		dt = cave.getDeltaTime()
		diff = self.source.getTransform().worldPosition - self.transf.worldPosition
		
		# If Fear, move AWAY
		dir = diff.normalized()
		if not self.toward:
			dir = -dir
			
		speed = self.controller.entity.getProperties().get("moveSpeed", 300) * MobaCommon.SPEED_RATIO
		tr = self.controller.entity.getProperties().get("turnRate", 540)
		MobaCommon.rotate_towards(self.transf, dir, dt, tr)
		# Bible Pattern: Rotate Entity -> Move Local Z
		self.controller.character.setWalkDirection(0, 0, speed * dt)
		
		return self

class DashState:
	def __init__(self, target_pos, speed=30.0, duration=0.4, isUnstoppable=False):
		self.target_pos = target_pos
		self.speed = speed
		self.duration = duration
		self.isUnstoppable = isUnstoppable

	def start(self, controller):
		self.controller = controller
		self.transf = controller.transf
		dir = (self.target_pos - self.transf.worldPosition).normalized()
		self.transf.lookAt(dir)
		if self.controller.animator:
			self.controller.animator.playByName("p-ability", 0.1)

	def run(self):
		# CC Interrupt (unless unstoppable)
		if not self.isUnstoppable:
			if self.controller.flags & (MobaCommon.EffectFlags.STUN | MobaCommon.EffectFlags.SILENCE | MobaCommon.EffectFlags.ROOT):
				return IdleState()

		dt = cave.getDeltaTime()
		self.duration -= dt
		if self.duration <= 0:
			if getattr(self.controller, "character", None):
				self.controller.character.setWalkDirection(0, 0, 0)
			return IdleState()
		
		# Move Local Z
		self.controller.character.setWalkDirection(0, 0, self.speed * dt)
		return self

class ChannelState:
	def __init__(self, skill_key, duration):
		self.skill_key = skill_key
		self.duration = duration

	def start(self, controller):
		self.controller = controller
		if self.controller.animator:
			anim_name = AnimationRegistry.get_anim(self.controller.heroName, "ability")
			self.controller.animator.playByName(anim_name, 0.2, loop=True)

	def run(self):
		# CC Interrupt
		if self.controller.flags & (MobaCommon.EffectFlags.STUN | MobaCommon.EffectFlags.SILENCE):
			return IdleState()

		dt = cave.getDeltaTime()
		self.duration -= dt
		
		# --- Encapsulated Tick Logic (Wave 62 Refactor) ---
		# Handle persistent effects while channeling
		skill_data = self.controller.abilities.get(self.skill_key)
		if skill_data and skill_data.get("effect") == "SPIN_DAMAGE":
			radius = skill_data.get("range", 3.5)
			dps = self.controller.get_skill_value(self.skill_key, "dps", 50)
			MobaCommon.apply_circular_aoe(
				self.controller.entity.getScene(), 
				self.controller.transf.worldPosition, 
				radius, dps * dt, 
				MobaCommon.DamageType.MAGIC, 
				attacker=self.controller.entity
			)
		
		if self.duration <= 0:
			return IdleState()
		return self
