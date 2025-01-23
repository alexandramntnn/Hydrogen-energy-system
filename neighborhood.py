import random
import math
from dataclasses import dataclass, field
from typing import List, Dict
from constants import (
    HOURS_IN_DAY,
    WEATHER_CONDITIONS,
    HYDROGEN_PRICE_MIN, HYDROGEN_PRICE_MAX,
    GRID_PRICE_MIN, GRID_PRICE_MAX,
    EXTREME_WEATHER_PROB
)
from models import House, Battery, Electrolyzer

@dataclass
class Neighborhood:
    houses: List[House]
    days: int
    battery: Battery
    electrolyzer: Electrolyzer

    grid_prices: List[List[float]] = field(default_factory=list)
    weather_forecast: List[str] = field(default_factory=list)
    hydrogen_price_forecast: List[float] = field(default_factory=list)

    total_revenue: float = 0.0
    total_cost: float = 0.0
    neighborhood_log: Dict[int, Dict[int, Dict]] = field(default_factory=dict)

    def generate_weather_forecast(self):
        for _ in range(self.days):
            # base weather for a day
            base = random.choices(['sunny','cloudy','rainy'], weights=[0.6,0.3,0.1], k=1)[0]
            # if extreme conditions
            if random.random() < EXTREME_WEATHER_PROB:
                base = random.choice(['heatwave','coldsnap'])
            self.weather_forecast.append(base)

    def generate_hydrogen_price_forecast(self):
        # random hydrogen selling price for each day
        for _ in range(self.days):
            price = round(random.uniform(HYDROGEN_PRICE_MIN, HYDROGEN_PRICE_MAX), 2)
            self.hydrogen_price_forecast.append(price)

    def generate_grid_prices(self):
        # grid prices for each hour of every day
        for _ in range(self.days):
            daily_prices = []
            for hour in range(HOURS_IN_DAY):
                if 6 <= hour < 9 or 17 <= hour < 20:  # peak hours are more expensive
                    price = random.uniform(GRID_PRICE_MIN + 0.02, GRID_PRICE_MAX)
                else:
                    price = random.uniform(GRID_PRICE_MIN, GRID_PRICE_MAX - 0.02)
                daily_prices.append(round(price, 3))
            self.grid_prices.append(daily_prices)


    def simulate(self):
        self.generate_weather_forecast()
        self.generate_hydrogen_price_forecast()
        self.generate_grid_prices()

        for day in range(self.days):
            day_log = {}

            weather = self.weather_forecast[day]
            hydro_price = self.hydrogen_price_forecast[day]
            daily_prices = self.grid_prices[day]

            print(f"Day {day+1}: Weather={weather}, H2Price=${hydro_price:.2f}")

            # daily occupant factor for each house
            occupant_factors = [h.get_daily_consumption_factor() for h in self.houses]

            for hour in range(HOURS_IN_DAY):
                if weather == 'heatwave':
                    weather_modifier = WEATHER_CONDITIONS['sunny']
                elif weather == 'coldsnap':
                    weather_modifier = WEATHER_CONDITIONS['cloudy']
                else:
                    weather_modifier = WEATHER_CONDITIONS.get(weather, 1.0)

                total_consumption = 0.0
                total_solar = 0.0

                # occupant usage and solar generation across all houses
                for idx, house in enumerate(self.houses):
                    usage = house.daily_energy_consumption[hour] * occupant_factors[idx]
                    total_consumption += usage
                    gen = house.solar_panel.generate_energy(hour, weather_modifier, house.house_efficiency)
                    total_solar += gen

                # tracking variables
                energy_solar_to_consumption = 0.0
                energy_to_electrolyzer = 0.0
                energy_charged_battery = 0.0
                energy_from_battery = 0.0
                energy_from_grid = 0.0
                cost_incurred = 0.0
                revenue_generated = 0.0

                # supplying to occupant vs. electrolyzer 
                occupant_value_per_kwh = daily_prices[hour]
                hydrogen_value_per_kwh = (1.0 / self.electrolyzer.efficiency) * hydro_price


                if total_solar>0 and total_consumption>0:
                    if occupant_value_per_kwh > hydrogen_value_per_kwh:
                        # occupant usage is more profitable then give occupant first
                        used_for_consumption= min(total_solar, total_consumption)
                        energy_solar_to_consumption += used_for_consumption
                        total_solar -= used_for_consumption
                        total_consumption -= used_for_consumption
                    else:
                        # hydrogen more profitable then occupant might buy from grid
                        pass

                if total_solar>0:
                    # leftover solar send produce hydrogen
                    produced = self.electrolyzer.produce_hydrogen(total_solar*0.9)
                    energy_to_electrolyzer+= (total_solar*0.9)
                    # 10% to battery
                    leftover = total_solar*0.1
                    charged= self.battery.charge(leftover)
                    energy_charged_battery+=charged
                    total_solar=0.0

                if total_consumption>0:
                    if occupant_value_per_kwh> hydrogen_value_per_kwh:
                        used_batt= self.battery.discharge(total_consumption)
                        energy_from_battery+= used_batt
                        total_consumption-= used_batt
                    else:
                        # occupant buys from grid
                        pass

                if total_consumption > 0:
                    # if occupant still needs energy buy from grid
                    cost = total_consumption * occupant_value_per_kwh
                    self.total_cost += cost
                    cost_incurred += cost
                    energy_from_grid += total_consumption
                    total_consumption = 0.0

                # at night run electrolyzer from battery 
                if not (6 <= hour <= 18):
                    # if generating hydrogen is more profitable than house usage
                    if occupant_value_per_kwh < hydrogen_value_per_kwh:
                        # check if battery is ok
                        if not self.battery.is_offline():
                            desired = 2.0
                            av_batt = self.battery.current_charge - (0.2 * self.battery.capacity)
                            potential = min(desired, av_batt, self.battery.max_discharge_rate)
                            if potential > 0:
                                discharged = self.battery.discharge(potential)
                                energy_to_electrolyzer += discharged
                                self.electrolyzer.produce_hydrogen(discharged)

                # sell hydrogen
                if hour == HOURS_IN_DAY - 1:
                    day_revenue = self.electrolyzer.sell_hydrogen(hydro_price)
                    self.total_revenue += day_revenue
                    revenue_generated += day_revenue


                day_log[hour]={
                    'occupant_value/kWh': round(occupant_value_per_kwh,3),
                    'hydrogen_value/kWh': round(hydrogen_value_per_kwh,3),
                    'energy_solar_to_consumption': round(energy_solar_to_consumption,2),
                    'energy_to_electrolyzer': round(energy_to_electrolyzer,2),
                    'energy_charged_to_battery': round(energy_charged_battery,2),
                    'energy_from_battery': round(energy_from_battery,2),
                    'energy_from_grid': round(energy_from_grid,2),
                    'cost_incurred': round(cost_incurred,2),
                    'revenue_generated': round(revenue_generated,2),
                    'battery_charge': round(self.battery.current_charge,2),
                    'battery_health': round(self.battery.health,2),
                }
            self.neighborhood_log[day]= day_log

    # print results
    def report(self):
        net_profit= self.total_revenue- self.total_cost
        print("\nResults:")
        print(f"Hydrogen revenue: ${self.total_revenue:.2f}")
        print(f"Grid cost:        ${self.total_cost:.2f}")
        print(f"Profit:             ${net_profit:.2f}")
        print(f"Final battery charge:   {self.battery.current_charge:.2f} kWh")
