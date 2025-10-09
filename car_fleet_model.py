import pandas as pd
import numpy as np
from typing import List
import warnings
warnings.filterwarnings('ignore')

def simulate_fleet_evolution(investment_schedule: List):
    # Initial fleet composition
    initial_gas = 4_115_000
    initial_hybrid = 525_000
    initial_ev = 360_000

    # Annual retirement rates (fraction of fleet retired each year) as constants
    retirement_rate_gas = 1/17.8
    retirement_rate_hybrid = 1/25
    retirement_rate_ev = 1/18.4

    # Annual growth rates as constants
    total_growth_rate = 0.06
    growth_rate_gas = lambda t: (0.95**t) * 0.378 + (1-0.95**t) * 0.05
    growth_rate_hybrid = lambda t: (0.95**t) * 0.432 + (1-0.95**t) * 0.10
    growth_rate_ev = lambda t: (0.95**t) * 0.156 + (1-0.95**t) * 0.85

    # Emissions per car per year (tons CO2e) as constants
    gas_car_emissions_per_car = 3
    hybrid_car_emissions_per_car = 2.1
    ev_electricity_demand_per_car = 3.0  # MWh per year
    
    # Emission per newly produced car (tons CO2e)
    new_gas_car_emissions = 7.5 # Between 5 to 10
    new_hybrid_car_emissions = 9 # Between 6 to 12
    new_ev_car_emissions = 11.5 # Between 8 to 15

    # Cost of gas to EV replacement
    cost_per_ev = 300_000 * 0.5  # Cost to purchase one EV in SEK

    # Initialize parameters
    results = []
    
    gas_fleet = initial_gas
    hybrid_fleet = initial_hybrid  
    ev_fleet = initial_ev
    gas_purchases = 0
    hybrid_purchases = 0
    ev_purchases = 0
    
    for i, investment in enumerate(investment_schedule):
        # Retirements
        gas_retired = int(gas_fleet * retirement_rate_gas)
        hybrid_retired = int(hybrid_fleet * retirement_rate_hybrid)
        ev_retired = int(ev_fleet * retirement_rate_ev)

        # Retire cars from fleet
        gas_fleet = int(max(gas_fleet - gas_retired, 0))
        hybrid_fleet = int(max(hybrid_fleet - hybrid_retired, 0))
        ev_fleet = int(max(ev_fleet - ev_retired, 0))

        # Determine how many EVs can be purchased with the investment
        possible_gas_to_ev_replacements = int(investment / cost_per_ev)
        actual_gas_to_ev_replacements = int(min(possible_gas_to_ev_replacements, gas_fleet))  # Can only replace as many gas cars as exist
        actual_hybrid_to_ev_replacements = int(min(max(possible_gas_to_ev_replacements - actual_gas_to_ev_replacements, 0), hybrid_fleet))
        ev_fleet += int(actual_gas_to_ev_replacements + actual_hybrid_to_ev_replacements)
        gas_fleet -= actual_gas_to_ev_replacements
        hybrid_fleet -= actual_hybrid_to_ev_replacements
        surplus_investment = investment - (actual_gas_to_ev_replacements + actual_hybrid_to_ev_replacements) * cost_per_ev

        # New purchases
        new_cars = int((gas_fleet + hybrid_fleet + ev_fleet) * total_growth_rate)
        gas_purchases = int(new_cars * growth_rate_gas(i))
        hybrid_purchases = int(new_cars * growth_rate_hybrid(i))
        ev_purchases = int(new_cars * growth_rate_ev(i))

        # Add new purchases to fleet
        gas_fleet += gas_purchases
        hybrid_fleet += hybrid_purchases
        ev_fleet += ev_purchases

        # Calculate total current fleet
        total_fleet = int(gas_fleet + hybrid_fleet + ev_fleet)

        # Calculate emissions and electricity demand
        total_gas_emissions = gas_fleet * gas_car_emissions_per_car + gas_purchases * new_gas_car_emissions
        total_hybrid_emissions = hybrid_fleet * hybrid_car_emissions_per_car + hybrid_purchases * new_hybrid_car_emissions
        total_ev_emissions = (ev_purchases + actual_gas_to_ev_replacements + actual_hybrid_to_ev_replacements) * new_ev_car_emissions
        total_emissions = total_gas_emissions + total_hybrid_emissions + total_ev_emissions
        total_electricity_demand = ev_fleet * ev_electricity_demand_per_car

        results.append({
            "gas_emissions": total_gas_emissions,
            "hybrid_emissions": total_hybrid_emissions,
            "total_emissions": total_emissions,
            "ev_electricity_demand": total_electricity_demand,
            "gas_fleet": gas_fleet, 
            "hybrid_fleet": hybrid_fleet,
            "ev_fleet": ev_fleet,
            "total_fleet": total_fleet,
            "surplus_investment": surplus_investment
        })

    return pd.DataFrame(results)

if __name__ == "__main__":
    # Example usage
    #investment_schedule = [200_000_000, 300_000_000, 400_000_000, 500_000_000, 600_000_000] * 6  # 30 years
    investment_schedule = [30_000_000_000] * 100  # 30 years
    df_results = simulate_fleet_evolution(investment_schedule)
    print(df_results)
    import matplotlib.pyplot as plt
    df_results[["gas_fleet", "hybrid_fleet", "ev_fleet"]].plot(kind='area', title="Annual Fleet Composition Over Time", stacked=True, ylim=(0, 10_000_000))
    plt.show()
