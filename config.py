GUILD_ID = 1222288591707967568
TRADE_CHARTER_ROLE = "Charter"
TRADE_TEAM_ROLE = "Travel Team"
SAVE_EDIT_CHANNEL = "✍︱save-edit-list"
TRADE_LOG_CHANNEL = "trade-log"
GREAT_HOUSE_ROLE = "Great House"

RESOURCES = ["Food","Wood","Stone","Iron","Luxury"]

# -------------------
# BUFFS
# -------------------

BUFFS = {
        "construction": {
        "name": "Construction Cost & Speed",
        "tiers": {
            "1 Well supplied masons": {"cost": {"Stone": 5}},
            "2 Large stockpiles": {"cost": {"Stone": 5, "Wood": 5}},
            "3 Empowered Masons guilds": {"cost": {"Stone": 5, "Wood": 5, "Luxury": 5}},
        },
        "type": "character",
        "modifier_name": "citadel_construction_t"
    }, 

    "garrison": {
        "name": "Garrison & Fortification",
        "tiers": {
            "1 Improved Fortification": {"cost": {"Stone": 5}},
            "2 Reinforced garrisons": {"cost": {"Stone": 5, "Iron": 5}},
            "3 Mighty Strongholds": {"cost": {"Stone": 5, "Iron": 5, "Luxury": 5}},
        },
        "type": "county",
        "modifier_name": "citadel_fort_t"
    },

    "travel": {
        "name": "Travel Safety & Speed",
        "tiers": {
            "1 Improved roads": {"cost": {"Stone": 5}},
            "2 Road Patrols": {"cost": {"Stone": 5, "Food": 5}},
            "3 Manned Waystations": {"cost": {"Stone": 5, "Food": 5, "Luxury": 5}},
        },
        "type": "county",
        "modifier_name": "citadel_travel_t"
    },

    "ships": {
        "name": "Ship Cost Reduction",
        "tiers": {
            "1 Stockpiled Timber": {"cost": {"Wood": 5}},
            "2 Fleet investment": {"cost": {"Wood": 5, "Iron": 5}},
            "3 Subsidised shipwrights": {"cost": {"Wood": 5, "Iron": 5, "Luxury": 5}},
        },
        "type": "midweek",
        "modifier_name": "citadel_midweek_only_t"
    },

    "siege": {
        "name": "Siege Progress",
        "tiers": {
            "1 Reinforced Frames": {"cost": {"Wood": 5}},
            "2 Flaming projectiles": {"cost": {"Wood": 5, "Stone": 5}},
            "3 Armoured crew": {"cost": {"Wood": 5, "Stone": 5, "Iron": 5}},
        },
        "type": "county",
        "modifier_name": "citadel_siege_t"
    },

    "archers": {
        "name": "Archers & Skirmishers",
        "tiers": {
            "1 Yew Bows": {"cost": {"Wood": 5}},
            "2 Extra Rations": {"cost": {"Wood": 5, "Food": 5}},
            "3 Mail Armour": {"cost": {"Wood": 5, "Food": 5, "Iron": 5}},
        },
        "type": "county",
        "modifier_name": "citadel_maa_t"
    },

    "development": {
        "name": "Development Growth",
        "tiers": {
            "1 Alms!": {"cost": {"Food": 5}},
            "2 Public Housing": {"cost": {"Food": 5, "Luxury": 5}},
            "3 City Planning": {"cost": {"Food": 5, "Luxury": 5, "Stone": 5}},
        },
        "type": "county",
        "modifier_name": "citadel_development_t"
    },

    "fertility": {
        "name": "Fertility & Health",
        "tiers": {
            "1 Crop Rotations": {"cost": {"Food": 5}},
            "2 Public Fountains": {"cost": {"Food": 5, "Stone": 5}},
            "3 Welfare State": {"cost": {"Food": 5, "Stone": 5, "Luxury": 5}},
        },
        "type": "character",
        "modifier_name": "citadel_health_t"
    },

    "levy": {
        "name": "Levy Replenishment",
        "tiers": {
            "1 Conscription": {"cost": {"Food": 5}},
            "2 Press Gangs": {"cost": {"Food": 5, "Wood": 5}},
            "3 Mass Mobilisation": {"cost": {"Food": 5, "Wood": 5, "Iron": 5}},
        },
        "type": "county",
        "modifier_name": "citadel_levy_t"
    },

    "army_maintenance": {
        "name": "Army Maintenance Reduction",
        "tiers": {
            "1 Efficient Rationing": {"cost": {"Food": 5}},
            "2 Supply Trains": {"cost": {"Food": 5, "Wood": 5}},
            "3 Forward Supply Bases": {"cost": {"Food": 5, "Wood": 5, "Stone": 5}},
        },
        "type": "character",
        "modifier_name": "citadel_army_maintenance_t"
    },

    "heavy_units": {
        "name": "Heavy Infantry & Cavalry",
        "tiers": {
            "1 Reinforced Weapons": {"cost": {"Iron": 5}},
            "2 Bread & Wine": {"cost": {"Iron": 5, "Food": 5}},
            "3 Standing Army": {"cost": {"Iron": 5, "Food": 5, "Wood": 5}},
        },
        "type": "county",
        "modifier_name": "citadel_heavy_t"
    },

    "maa_upkeep": {
        "name": "MAA Upkeep Reduction",
        "tiers": {
            "1 Inspired Patriotism": {"cost": {"Iron": 5}},
            "2 House Guard": {"cost": {"Iron": 5, "Wood": 5}},
            "3 Personal Army": {"cost": {"Iron": 5, "Wood": 5, "Luxury": 5}},
        },
        "type": "character",
        "modifier_name": "citadel_maa_upkeep_t"
    },

    "artifacts": {
        "name": "Artifact Cost Reduction",
        "tiers": {
            "1 Fine Tools": {"cost": {"Iron": 5}},
            "2 Thriving Workshops": {"cost": {"Iron": 5, "Stone": 5}},
            "3 Exotic Materials": {"cost": {"Iron": 5, "Stone": 5, "Luxury": 5}},
        },
        "type": "midweek",
        "modifier_name": "citadel_midweek_only_t"
    },

    "popular_opinion": {
        "name": "Popular Opinion & Control",
        "tiers": {
            "1 Imported Luxuries": {"cost": {"Luxury": 5}},
            "2 Circuses": {"cost": {"Luxury": 5, "Food": 5}},
            "3 Bread And Games": {"cost": {"Luxury": 5, "Food": 5, "Stone": 5}},
        },
        "type": "county",
        "modifier_name": "citadel_popular_t"
    },

    "general_opinion": {
        "name": "General Opinion & Stewardship",
        "tiers": {
            "1 Hand Bills": {"cost": {"Luxury": 5}},
            "2 Propaganda": {"cost": {"Luxury": 5, "Iron": 5}},
            "3 Wandering Minstrels": {"cost": {"Luxury": 5, "Iron": 5, "Food": 5}},
        },
        "type": "character",
        "modifier_name": "citadel_public_image_t"
    },

    "vassal_opinion": {
        "name": "Vassal Opinion",
        "tiers": {
            "1 Courtly Investments": {"cost": {"Luxury": 5}},
            "2 Prosperous Courts": {"cost": {"Luxury": 5, "Stone": 5}},
            "3 Vibrant Courts": {"cost": {"Luxury": 5, "Stone": 5, "Wood": 5}},
        },
        "type": "character",
        "modifier_name": "citadel_vassal_t"
    },
}

# -------------------
# DEBUFFS
# -------------------

DEBUFFS = {
    "Food": {
        "name": "Food Deficit",
        "tiers": {
            1: {"name": "Minor Food Shortage"},
            2: {"name": "Widespread Hunger"},
            3: {"name": "Great Famine"},
        },
        "type": "county",
        "modifier_name": "citadel_food_deficit_t"
    },

    "Wood": {
        "name": "Wood Deficit",
        "tiers": {
            1: {"name": "Timber Scarcity"},
            2: {"name": "Wood Shortage"},
            3: {"name": "Severe Timber Crisis"},
        },
        "type": "county",
        "modifier_name": "citadel_wood_deficit_t"
    },

    "Stone": {
        "name": "Stone Deficit",
        "tiers": {
            1: {"name": "Cracked Walls"},
            2: {"name": "Crumbling Defenses"},
            3: {"name": "Ruined Fortifications"},
        },
        "type": "county",
        "modifier_name": "citadel_stone_deficit_t"
    },

    "Luxury": {
        "name": "Luxury Deficit",
        "tiers": {
            1: {"name": "Fading Splendor"},
            2: {"name": "Tarnished Name"},
            3: {"name": "House in Disgrace"},
        },
        "type": "character",
        "modifier_name": "citadel_luxury_deficit_t"
    },

    "Iron": {
        "name": "Iron Deficit",
        "tiers": {
            1: {"name": "Scarcity of Steel"},
            2: {"name": "Rusty Mail"},
            3: {"name": "Disarmed"},
        },
        "type": "character",
        "modifier_name": "citadel_iron_deficit_t"
    },
}
