import random
from constants import DAYS_TO_SIMULATE
from models import SolarPanel, Battery, Electrolyzer, House
from neighborhood import Neighborhood
from typing import List

# adjust energy baseline based on house size
def adjust_energy_consumption(size: str) -> List[float]:
    base_consumption = [
        0.8, 0.7, 0.7, 0.6, 0.6, 0.8, 1.5, 2.0, 3.0, 4.0, 4.5, 4.5,
        4.5, 4.5, 4.5, 5.0, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.8
    ]
    #schange consumtions based on house size
    if size == 'small':
        factor = 0.8
    elif size == 'medium':
        factor = 1.0
    elif size == 'large':
        factor = 1.3
    else:
        factor = 1.0
    
    # scale consumptions
    scaled = [round(cons * factor, 2) for cons in base_consumption]
    return scaled


def main():
    # seed for randomness
    random.seed(42)

    house_sizes = ['small', 'medium', 'large']
    occupant_type = ['1-2','3-4','5+']

    # hourses
    num_houses = 15
    houses = []

    for i in range(num_houses):
        # create hourse
        size = random.choice(house_sizes)
        occupant_type = random.choice(occupant_type)

        # set consumption
        daily_consumption = adjust_energy_consumption(size)

        # solar based on house size
        if size == 'small':
            eff = 1.05
            max_out = 10.0
        elif size == 'medium':
            eff = 1.0
            max_out = 15.0
        else:
            eff = 0.95
            max_out = 20.0

        #solar panel
        panel = SolarPanel(max_out)
        house_obj = House(
            id=i+1,
            size=size,
            occupant_type=occupant_type,
            solar_panel=panel,
            daily_energy_consumption=daily_consumption,
            house_efficiency=eff
        )
        houses.append(house_obj)

    # battery 800 kWh
    big_battery = Battery(
        capacity=80.0,
        current_charge=40.0,
        max_charge_rate=10.0,
        max_discharge_rate=10.0
    )

    # electrolyzer 12 kWh/kg
    big_elec = Electrolyzer(
        efficiency=12.0,
    )

    # neighborhood
    neighborhood = Neighborhood(
        houses=houses,
        days=DAYS_TO_SIMULATE,
        battery=big_battery,
        electrolyzer=big_elec
    )

    # simulate and show results
    neighborhood.simulate()
    neighborhood.report()
    # initial investment estimate
    estimate_investment()

def estimate_investment():
    print("\nInitial investment:")
    # battery
    battery_capacity_kwh = 80.0
    cost_low_batt = battery_capacity_kwh * 200
    cost_high_batt= battery_capacity_kwh * 400
    print(f"Battery: ${cost_low_batt:,.0f} - ${cost_high_batt:,.0f}")

    # electrolyzer
    electrolyzer_kw = 12
    cost_low_elec = electrolyzer_kw * 700
    cost_high_elec= electrolyzer_kw * 1200
    print(f"Electrolyzer: ${cost_low_elec:,.0f} - ${cost_high_elec:,.0f}")


if __name__ == "__main__":
    main()
