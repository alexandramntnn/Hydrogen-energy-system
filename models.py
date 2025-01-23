import math
import random
from dataclasses import dataclass, field
from typing import Dict, List
from constants import (
    BATTERY_INITIAL_HEALTH, BATTERY_OFFLINE_HEALTH,
    OCCUPANT_VARIATION, OCCUPANT_SPIKE_PROB, OCCUPANT_DIP_PROB,
    OCCUPANTS)

@dataclass
class SolarPanel:
    max_output: float

    def generate_energy(self, hour: int, weather_modifier: float, efficiency: float) -> float:
        # generate energy data hourly for times when daytime
        if 6 <= hour <= 18:
            angle = math.pi * (hour - 6) / 12.0
            base_energy = self.max_output * math.sin(angle)
            energy = base_energy * weather_modifier * efficiency
            energy *= random.uniform(0.95, 1.05)
            return max(energy, 0.0)
        else:
            # night
            return 0.0

@dataclass
class Battery:
    capacity: float
    current_charge: float = 0.0
    max_charge_rate: float = 10.0
    max_discharge_rate: float = 10.0
    health: float = BATTERY_INITIAL_HEALTH
    cycles: float = 0.0

    # turn off battery if health is not good
    def is_offline(self) -> bool:
        return self.health < BATTERY_OFFLINE_HEALTH
    
    # charge battery 
    def charge(self, amount: float) -> float:
        if self.is_offline():
            return 0.0
        # keep health in mind so only 80% charge target
        target_charge = 0.8 * self.capacity
        available_capacity = target_charge - self.current_charge
        chargeable = min(amount, self.max_charge_rate, available_capacity)
        # if it cant be charged
        if chargeable <= 0:
            return 0.0
        # update battery charge
        self.current_charge += chargeable
        self.update_health(chargeable, charging=True)
        return chargeable

    # discharge battery
    def discharge(self, amount: float) -> float:
        if self.is_offline():
            return 0.0
        # keep health in mind so only discharge to 20%
        min_charge = 0.2 * self.capacity
        available = self.current_charge - min_charge
        dischargeable = min(amount, self.max_discharge_rate, available)
        # if it cant be discharged
        if dischargeable <= 0:
            return 0.0
        # discharged battery and update value
        self.current_charge -= dischargeable
        self.update_health(dischargeable, charging=False)
        return dischargeable

    # battery health
    def update_health(self, energy: float, charging: bool):
        cycle_fraction = energy / self.capacity
        self.cycles += cycle_fraction
        if self.cycles >= 1.0:
            full_cycles = int(self.cycles)
            self.health -= 0.05 * full_cycles
            self.cycles -= full_cycles
            self.health = max(self.health, 0.0)

@dataclass
class Electrolyzer:
    efficiency: float
    hydrogen_storage: float = 0.0

    # produce hydrogen
    def produce_hydrogen(self, energy: float) -> float:
        h2 = energy / self.efficiency
        self.hydrogen_storage += h2
        return h2
    # sell the currently stored hydrogen
    def sell_hydrogen(self, current_price: float) -> float:
        revenue = self.hydrogen_storage * current_price
        self.hydrogen_storage = 0.0
        return revenue

@dataclass
class House:
    id: int
    size: str
    occupant_type: str
    solar_panel: SolarPanel
    daily_energy_consumption: List[float]
    house_efficiency: float
    daily_log: Dict[int, Dict] = field(default_factory=dict)

    def get_daily_consumption_factor(self) -> float:

        # get consuntion based on random +/- variations proportional to occupants
        day_factor = random.uniform(1 - OCCUPANT_VARIATION, 1 + OCCUPANT_VARIATION)
        occupant_factor = OCCUPANTS.get(self.occupant_type, 1.0)
        base = day_factor * occupant_factor

        # potential spike or dip
        roll = random.random()
        if roll < OCCUPANT_SPIKE_PROB:
            base *= 2.0
        elif roll < (OCCUPANT_SPIKE_PROB + OCCUPANT_DIP_PROB):
            base *= 0.5

        return base
