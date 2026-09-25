import cave
import random
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Data import HeroRegistry
from Core import MobaCommon

class MobaPassiveManager:
	"""
	Centralized system to handle professional MOBA passive logic.
	Standardizes how 1 Passive + 4 Skills are executed.
	"""
	def __init__(self, owner):
		self.owner = owner # Usually the PlayerController or HeroEntity
		self.hero_name = owner.heroName
		self.passive_data = HeroRegistry.HERO_REGISTRY.get(self.hero_name, {}).get("passive", {})
		self.passive_id = self.passive_data.get("id")
		
		# Internal states for various passive types
		self.stacks = 0
		self.cooldown_timer = 0.0
		self.flow = 0.0
		self.is_active = False

	def update(self, dt):
		"""Called every frame to update passive logic (regen, auras, etc)."""
		if not self.passive_id:
			return

		if self.cooldown_timer > 0:
			self.cooldown_timer -= dt

		# --- PASSIVE LOGIC BY ID ---
		
		if self.passive_id == "VETERANCY":
			# Kael (Warrior): Bonus recovery when low HP
			threshold = self.passive_data.get("threshold", 0.3)
			cur_hp = self.owner.entity.getProperties().get("health", 0.0)
			if cur_hp / self.owner.maxHP < threshold:
				self.owner.recoveryMod = self.passive_data.get("recoveryBonus", 3.0)
			else:
				self.owner.recoveryMod = 0.0

		elif self.passive_id == "CHILLING_AURA":
			# Eira (Frost Nova): Slow nearby enemies
			pass 

		elif self.passive_id == "STONE_SKIN":
			# Orix (Guardian): Armor per nearby ally
			radius = self.passive_data.get("radius", 8.0)
			allies = MobaCommon.EntityRegistry.get_team_entities(MobaCommon.get_entity_team(self.owner.entity), "player")
			nearby_count = 0
			for a in allies:
				if a != self.owner.entity and (a.getTransform().worldPosition - self.owner.transf.worldPosition).length() < radius:
					nearby_count += 1
			bonus = nearby_count * self.passive_data.get("armorPerAlly", 8)
			self.owner.bonusArmor = bonus

		elif self.passive_id == "FRENZY":
			# Ragnar (Berserker): AS based on missing HP
			cur_hp = self.owner.entity.getProperties().get("health", 0.0)
			missing_pct = 1.0 - (cur_hp / self.owner.maxHP)
			max_bonus = self.passive_data.get("asMaxBonus", 0.5)
			self.owner.bonusAS = missing_pct * max_bonus

		elif self.passive_id == "MELTDOWN":
			# Cinder (The Magma Warden): Periodic Armor/MR Shred Aura (Phase 101)
			from Core import MobaCommon
			if MobaCommon.GameTick.is_tick_frame() and MobaCommon.GameTick._current_tick % 20 == 0:
				enemies = MobaCommon.get_entities_in_radius(self.owner.entity.getScene(), self.owner.transf.worldPosition, 7.0)
				shred = self.passive_data.get("armorShred", 5)
				for e in enemies:
					if MobaCommon.get_entity_team(e) != MobaCommon.get_entity_team(self.owner.entity):
						# Simple shred via STAT_MOD or internal effect
						e_pc = e.getPy("PlayerController")
						if e_pc: e_pc.applyEffect("SHRED", 1.5, magnitude=shred)

		elif self.passive_id == "FLOW":
			# Sora (WindWalker): Build flow by moving
			is_moving = False
			if hasattr(self.owner, "character"):
				is_moving = self.owner.character.isMoving()
				
			if is_moving:
				self.flow = min(100.0, self.flow + dt * 20.0)
			
			if self.flow >= 100.0 and not self.is_active:
				val = self.passive_data.get("shieldAtMaxFlow", 100)
				self.owner.applyEffect("SHIELD", 3.0, magnitude=val)
				self.owner.entity.getProperties()["shieldHP"] = val
				self.flow = 0.0 # Consume flow

	def on_skill_cast(self, skill_key):
		"""Triggered when the hero uses Q, W, E, or R."""
		if not self.passive_id:
			return

		if self.passive_id == "ADAPTIVE_BARRIER":
			# Cyrus (Techno Knight): Shield on skill cast
			if self.cooldown_timer <= 0:
				val = self.passive_data.get("value", 80)
				self.owner.applyEffect("SHIELD", 3.0, magnitude=val)
				self.owner.entity.getProperties()["shieldHP"] = val
				self.cooldown_timer = self.passive_data.get("cooldown", 12.0)

		elif self.passive_id == "CD_REDUCE" and skill_key == "E":
			# Kenji (WindGuardian): Dash reduces Q cooldown
			timer = self.owner.cooldowns.get("Q")
			if timer:
				red = self.passive_data.get("flatReduction", 1.0)
				timer.set(max(0, timer.get() - red))

	def on_hit_target(self, target, damage, is_basic_attack):
		"""Triggered when the hero deals damage."""
		if not self.passive_id:
			return

		if self.passive_id == "HEAL_AA" and is_basic_attack:
			# Mara (Tidecaller): Heal allies (Manual healing handled in apply_damage for Lyra, but Mara is simple self-heal or logic)
			MobaCommon.apply_heal(self.owner.entity, self.passive_data.get("healFlat", 20))

		elif self.passive_id == "AS_FLOW" and is_basic_attack:
			# Ezra (ArcaneSlinger): AS stacks per hit
			self.stacks = min(self.passive_data.get("maxStacks", 5), self.stacks + 1)
			self.owner.bonusAS = self.stacks * self.passive_data.get("asPerStack", 0.05)

		elif self.passive_id == "BURN":
			# Sol (Embermage): DoT on hit
			MobaCommon.apply_dot(target, self.passive_data.get("burnDmg", 10), duration=self.passive_data.get("duration", 4.0), source=self.owner.entity)

		elif self.passive_id == "STARLIGHT":
			# Nova: Stack-based detonation
			stack_key = f"starlight_{self.owner.entity.name}"
			props = target.getProperties()
			stacks = props.get(stack_key, 0) + 1
			
			if stacks >= self.passive_data.get("stacksRequired", 3):
				# Detonate
				dmg = self.passive_data.get("explosiveDamage", 100) + (self.owner.level * 10)
				MobaCommon.apply_damage(target, dmg, MobaCommon.DamageType.MAGIC, attacker=self.owner.entity)
				MobaCommon.spawn_vfx(target.getScene(), "VFX_Nova_Burst", target.getTransform().worldPosition)
				props[stack_key] = 0 # Reset
			else:
				props[stack_key] = stacks
				# Spawn tiny charge VFX
				MobaCommon.spawn_vfx(target.getScene(), "VFX_Nova_Charge", target.getTransform().worldPosition, duration=0.5)

	def on_kill(self, victim):
		"""Triggered when the hero kills a unit."""
		if self.passive_id == "SOUL_HARVEST":
			# Vex: AP Stacking logic
			self.owner.soul_stacks = min(50, self.owner.soul_stacks + 1)
			self.owner.recalculate_stats() # Refresh AP
			# Heal on kill (sustain)
			heal_amt = self.owner.maxHP * 0.04 
			MobaCommon.apply_heal(self.owner.entity, heal_amt)
		
		elif self.passive_id == "VETERANCY" and victim.hasTag("monster"):
			# Ragnar/Kael bonus logic (stub)
			pass

	def on_hit_taken(self, attacker, damage):
		"""Triggered when the hero takes damage."""
		if not self.passive_id:
			return

		if self.passive_id == "SPITE" and self.cooldown_timer <= 0:
			# Umbra: Shield when taking spike damage
			if damage > self.owner.maxHP * 0.15:
				val = 100
				self.owner.applyEffect("SHIELD", 3.0, magnitude=val)
				self.owner.entity.getProperties()["shieldHP"] = val
				self.cooldown_timer = 20.0
				
		elif self.passive_id == "SHIELD_BLOCK":
			# Bastian: 20% chance to block 15% damage (Phase 101)
			if random.random() < self.passive_data.get("blockChance", 0.2):
				dr = self.passive_data.get("dr", 0.15)
				# Reverse-heal to simulate reduction (damage already applied to health in takeDamage)
				MobaCommon.apply_heal(self.owner.entity, damage * dr)
				MobaCommon.spawn_vfx(self.owner.entity.getScene(), "VFX_Bastian_Block", self.owner.transf.worldPosition)

		elif self.passive_id == "BRAMBLE_THORNS":
			# Thorne: Reflect damage to attacker (Phase 101)
			from Core import MobaCommon
			if attacker and attacker != self.owner.entity:
				reflect = damage * self.passive_data.get("reflectPercent", 0.15)
				MobaCommon.apply_damage(attacker, reflect, MobaCommon.DamageType.MAGIC, attacker=self.owner.entity)
				# Only spawn reflect VFX occasionally to prevent clutter
				if random.random() < 0.3:
					MobaCommon.spawn_vfx(self.owner.entity.getScene(), "VFX_Thorne_Reflect", attacker.getTransform().worldPosition)
