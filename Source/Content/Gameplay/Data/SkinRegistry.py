SKIN_REGISTRY = {
	# Updated to match current HeroRegistry naming (Phase 115 audit)
	"Kael": [
		{"id": "base", "name": "Default", "template": "Hero_Kael", "icon": "Icon_Kael_Base"},
	],
	"Cyrus": [
		{"id": "base", "name": "Default", "template": "Hero_Cyrus", "icon": "Icon_Cyrus_Base"},
		{"id": "cyber", "name": "Cybernetic", "template": "Skin_Cyrus_Cyber", "icon": "Icon_Cyrus_Cyber"}
	],
	"Borum": [
		{"id": "base", "name": "Default", "template": "Hero_Borum", "icon": "Icon_Borum_Base"},
		{"id": "cyber", "name": "Cybernetic", "template": "Skin_Borum_Cyber", "icon": "Icon_Borum_Cyber"}
	],
	"Zora": [
		{"id": "base", "name": "Default", "template": "Hero_Zora", "icon": "Icon_Zora_Base"},
		{"id": "rogue", "name": "Deep Sea Rogue", "template": "Skin_Zora_Sea", "icon": "Icon_Zora_Sea"}
	],
	"Eira": [
		{"id": "base", "name": "Default", "template": "Hero_Eira", "icon": "Icon_Eira_Base"},
		{"id": "volcanic", "name": "Volcanic Frost", "template": "Skin_Eira_Fire", "icon": "Icon_Eira_Fire"}
	],
	"Ignis": [{"id": "base", "name": "Default", "template": "Hero_Ignis", "icon": "Icon_Ignis_Base"}],
	"Zarek": [{"id": "base", "name": "Default", "template": "Hero_Zarek", "icon": "Icon_Zarek_Base"}],
	"Mortis": [{"id": "base", "name": "Default", "template": "Hero_Mortis", "icon": "Icon_Mortis_Base"}],
	"Sora": [{"id": "base", "name": "Default", "template": "Hero_Sora", "icon": "Icon_Sora_Base"}],
	"Krix": [{"id": "base", "name": "Default", "template": "Hero_Krix", "icon": "Icon_Krix_Base"}],
	"Orix": [{"id": "base", "name": "Default", "template": "Hero_Orix", "icon": "Icon_Orix_Base"}],
	"Bastian": [{"id": "base", "name": "Default", "template": "Hero_Bastian", "icon": "Icon_Bastian_Base"}],
	"Ragnar": [{"id": "base", "name": "Default", "template": "Hero_Ragnar", "icon": "Icon_Ragnar_Base"}],
	"Umbra": [{"id": "base", "name": "Default", "template": "Hero_Umbra", "icon": "Icon_Umbra_Base"}],
	"Ezra": [{"id": "base", "name": "Default", "template": "Hero_Ezra", "icon": "Icon_Ezra_Base"}],
	"Kenji": [{"id": "base", "name": "Default", "template": "Hero_Kenji", "icon": "Icon_Kenji_Base"}],
	"Arath": [{"id": "base", "name": "Default", "template": "Hero_Arath", "icon": "Icon_Arath_Base"}],
	"Thorne": [{"id": "base", "name": "Default", "template": "Hero_Thorne", "icon": "Icon_Thorne_Base"}],
	"Silvan": [{"id": "base", "name": "Default", "template": "Hero_Silvan", "icon": "Icon_Silvan_Base"}],
	"Spirit": [{"id": "base", "name": "Default", "template": "Hero_Spirit", "icon": "Icon_Spirit_Base"}],
	"Fiore": [{"id": "base", "name": "Default", "template": "Hero_Fiore", "icon": "Icon_Fiore_Base"}],
	"Nyx": [{"id": "base", "name": "Default", "template": "Hero_Nyx", "icon": "Icon_Nyx_Base"}],
	"Sol": [{"id": "base", "name": "Default", "template": "Hero_Sol", "icon": "Icon_Sol_Base"}],
	"Vern": [{"id": "base", "name": "Default", "template": "Hero_Vern", "icon": "Icon_Vern_Base"}],
	"Mara": [{"id": "base", "name": "Default", "template": "Hero_Mara", "icon": "Icon_Mara_Base"}],
	"Dredge": [{"id": "base", "name": "Default", "template": "Hero_Dredge", "icon": "Icon_Dredge_Base"}],
	"Vento": [{"id": "base", "name": "Default", "template": "Hero_Vento", "icon": "Icon_Vento_Base"}],
	"Lyra": [{"id": "base", "name": "Default", "template": "Hero_Lyra", "icon": "Icon_Lyra_Base"}],
}

def get_skin_template(hero_id, skin_id="base"):
	"""Returns the template name for a hero+skin combo."""
	skins = SKIN_REGISTRY.get(hero_id, [])
	for skin in skins:
		if skin["id"] == skin_id:
			return skin["template"]
	# Fallback: default template from hero ID
	return f"Hero_{hero_id}"
