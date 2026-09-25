# Build Order Registry for MOBA Heroes (Core Items Only)

BUILD_ORDERS = {
    # FIGHTERS / TANKS
    "Ironclad": ["Sunfire Aegis", "Thornmail", "Force of Nature"],
    "Pyre": ["Sterak's Gage", "Sunfire Aegis", "Death's Dance"],
    "Berserker": ["Black Cleaver", "Death's Dance", "Sterak's Gage"],
    "DarkinApostle": ["Black Cleaver", "Death's Dance", "Sterak's Gage"],
    
    # MAGES
    "Frost Nova": ["Luden's Tempest", "Zhonya's Hourglass", "Liandry's Anguish"],
    "StormWeaver": ["Luden's Tempest", "Liandry's Anguish", "Morellonomicon"],
    
    # ASSASSINS
    "Shadow": ["Youmuu's Ghostblade", "Umbral Glaive", "Edge of Night"],
    "ShadowStalker": ["Umbral Glaive", "Youmuu's Ghostblade", "Death's Dance"],
    "Slayer": ["Umbral Glaive", "Death's Dance", "Black Cleaver"],
    
    # ADC
    "ArcaneSlinger": ["Kraken Slayer", "Infinity Edge", "Mortal Reminder"],
    "WindWalker": ["Kraken Slayer", "Infinity Edge", "Death's Dance"],
    "FlashFencer": ["Kraken Slayer", "Youmuu's Ghostblade", "Death's Dance"],
    
    # SUPPORTS
    "Guardian": ["Locket of Solari", "Redemption", "Thornmail"],
    "NatureGuardian": ["Luden's Tempest", "Redemption", "Morellonomicon"],
    "SpiritForm": ["Luden's Tempest", "Redemption", "Morellonomicon"],
    
    # FALLBACK
    "Warrior": ["Black Cleaver", "Sunfire Aegis"]
}

def get_recommended_build(hero_name):
    return BUILD_ORDERS.get(hero_name, BUILD_ORDERS["Warrior"])
