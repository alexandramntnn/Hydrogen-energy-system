#time
HOURS_IN_DAY = 24
DAYS_TO_SIMULATE = 365

# battery
BATTERY_MAX_CYCLES = 1000
BATTERY_INITIAL_HEALTH = 100.0

# base weather
WEATHER_CONDITIONS = {
    'sunny': 0.8,
    'cloudy': 0.8,
    'rainy': 0.3,
}

# hydrogen prices $/kg
HYDROGEN_PRICE_MIN = 4.0
HYDROGEN_PRICE_MAX = 8.0

# grid prices $/kWh
GRID_PRICE_MIN = 0.05
GRID_PRICE_MAX = 0.15

# grid price threshold for battery
GRID_PRICE_THRESHOLD = 0.12

# occupant types
OCCUPANTS= {
    '1-2': 0.8,
    '3-4': 1.0,
    '5+': 1.3
}

# variation
EXTREME_WEATHER_PROB = 0.1
OCCUPANT_VARIATION = 0.25
OCCUPANT_SPIKE_PROB = 0.1
OCCUPANT_DIP_PROB   = 0.1

# battery offline threshold
BATTERY_OFFLINE_HEALTH = 5.0
