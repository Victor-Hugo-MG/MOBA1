import cave

class FactionIdentity:
	"""
	Central database for Faction identities, aesthetics, and lore.
	Used by the UI to display banners, colors, and descriptions.
	"""
	
	DATA = {
		"Imperium": {
			"name": "The Imperium",
			"description": "A global military force seeking to unify the world through absolute power and 'Amplified' Resonance technology.",
			"color": cave.Vector4(1.0, 0.1, 0.1, 1.0),
			"accent": cave.Vector4(0.2, 0.2, 0.2, 1.0),
			"resonance_type": "Amplified",
			"vfx_tag": "resonance_amplified",
			"motto": "Order through Power.",
			"goals": "Global conquest; Eradicate resistance in the wildlands.",
			"allies": ["Armhold", "Gratewalls", "Jun Hu"],
			"enemies": ["The Front", "Monsters"]
		},
		"Armhold": {
			"name": "Armhold Family",
			"description": "Industrial magnates who specialize in heavy steam and hydraulic 'Brute' technology. They thrive on the logistics of war.",
			"color": cave.Vector4(0.8, 0.5, 0.2, 1.0), # Bronze
			"accent": cave.Vector4(0.3, 0.2, 0.1, 1.0),
			"resonance_type": "Industrial",
			"vfx_tag": "fire", # Fallback to fire for now
			"motto": "Build to Last, Fight to Win.",
			"goals": "Sell weapons to the highest bidder; Maintain industrial dominance.",
			"allies": ["Imperium", "Gratewalls"],
			"enemies": ["The Front"]
		},
		"Gratewalls": {
			"name": "Gratewalls Family",
			"description": "Architects of the world's most impenetrable fortresses. Their 'Fortress' technology provides absolute defense.",
			"color": cave.Vector4(0.9, 0.9, 1.0, 1.0), # White/Silver
			"accent": cave.Vector4(0.1, 0.4, 0.8, 1.0), # Blue
			"resonance_type": "Fortress",
			"vfx_tag": "shield",
			"motto": "None Shall Pass.",
			"goals": "Protect the Gilded District; Contract defense services to the Imperium.",
			"allies": ["Imperium", "Armhold"],
			"enemies": ["The Front", "Monsters"]
		},
		"Jun Hu": {
			"name": "Jun Hu Family",
			"description": "A secretive elite specializing in high-tech 'Harmonized' Resonance for assassination and precision strikes.",
			"color": cave.Vector4(0.1, 0.6, 1.0, 1.0), # Neon Blue
			"accent": cave.Vector4(0.05, 0.1, 0.2, 1.0),
			"resonance_type": "Harmonized",
			"vfx_tag": "resonance_harmonized",
			"motto": "Silence is the Sharpest Blade.",
			"goals": "High-profile assassinations; Master 'Perfect' Resonance.",
			"allies": ["Imperium"],
			"enemies": ["The Front"]
		},
		"The Front": {
			"name": "The Front",
			"description": "A loose alliance of the displaced and poor, using scavenged 'Glitch' technology to sabotage the Imperium.",
			"color": cave.Vector4(0.4, 1.0, 0.2, 1.0), # Neon Green
			"accent": cave.Vector4(1.0, 0.5, 0.0, 1.0), # Orange
			"resonance_type": "Glitch",
			"vfx_tag": "resonance_glitch",
			"motto": "Sync or Die.",
			"goals": "Sabotage the Imperium; Protect small cities from expansion.",
			"allies": ["Nomade's"],
			"enemies": ["Imperium", "The 3 Families"]
		},
		"Nomade's": {
			"name": "The Nomades",
			"description": "Mobile merchants and survivalists who bridge the gap between cities and the wilds. They are the blood of the world's trade.",
			"color": cave.Vector4(0.2, 0.8, 0.4, 1.0), # Nature Green
			"accent": cave.Vector4(0.4, 0.3, 0.1, 1.0),
			"resonance_type": "Organic",
			"vfx_tag": "nature",
			"motto": "The Earth Remembers.",
			"goals": "Control trade routes; Navigate safely between all zones.",
			"allies": ["The Front"],
			"enemies": ["Monsters"]
		},
		"Monsters": {
			"name": "Monsters & Mutants",
			"description": "Creatures warped by 'Chaotic' Resonance. They represent the raw, untamed power of the world's magical leak.",
			"color": cave.Vector4(0.6, 0.1, 0.9, 1.0), # Eldritch Purple
			"accent": cave.Vector4(0.1, 0.05, 0.2, 1.0),
			"resonance_type": "Chaotic",
			"vfx_tag": "resonance_chaotic",
			"motto": "We are the Aftermath.",
			"goals": "Survive; Spread the chaotic resonance.",
			"allies": [],
			"enemies": ["Everyone"]
		}
	}

	@staticmethod
	def get_faction(faction_name):
		return FactionIdentity.DATA.get(faction_name, FactionIdentity.DATA["Imperium"])
