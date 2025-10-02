import pandas as pd
from typing import List
import warnings
warnings.filterwarnings('ignore')

def simulate_fleet_evolution(investment_schedule: List):
    # Initial fleet composition (millions of vehicles)
    initial_gas = 5_000_000      # 80% of 15M total fleet
    initial_hybrid = 1_250_000   # 15% of 15M total fleet  
    initial_ev = 750_000       # 5% of 15M total fleet

    # Annual retirement rates (fraction of fleet retired each year) as functions of year and fleet size (or constants)
    retirement_rate_gas = lambda year, gas_fleet: 1/15 
    retirement_rate_hybrid = lambda year, hybrid_fleet: 1/16
    retirement_rate_ev = lambda year, ev_fleet: 1/18

    # Annual growth rates as function of year and fleet size (or constants)
    growth_rate_gas = lambda year, gas_fleet: 0.05
    growth_rate_hybrid = lambda year, hybrid_fleet: 0.08
    growth_rate_ev = lambda year, ev_fleet: 0.08

    # Emissions per car per year (tons CO2e) as functions of year and fleet size (or constants)
    gas_car_emissions_per_car = lambda t, gas_fleet: 4.6 * (0.98 ** t)  # Decreasing by 2% per year
    hybrid_car_emissions_per_car = lambda t, hybrid_fleet: 2.3 * (0.97 ** t)  # Decreasing by 3% per year
    ev_electricity_demand_per_car = lambda t, ev_fleet: 3.0  # MWh per year, assumed constant
    
    # Emission per newly produced car (tons CO2e)
    new_gas_car_emissions = 10.0
    new_hybrid_car_emissions = 7.0
    new_ev_car_emissions = 5.0

    # Cost of gas to EV replacement
    cost_per_ev = 40_000  # Cost to purchase one EV

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
        gas_retired = int(gas_fleet * retirement_rate_gas(i, gas_fleet))
        hybrid_retired = int(hybrid_fleet * retirement_rate_hybrid(i, hybrid_fleet))
        ev_retired = int(ev_fleet * retirement_rate_ev(i, ev_fleet))

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
        gas_purchases = int(gas_fleet * growth_rate_gas(i, gas_fleet))
        hybrid_purchases = int(hybrid_fleet * growth_rate_hybrid(i, hybrid_fleet))
        ev_purchases = int(ev_fleet * growth_rate_ev(i, ev_fleet))

        # Add new purchases to fleet
        gas_fleet += gas_purchases
        hybrid_fleet += hybrid_purchases
        ev_fleet += ev_purchases

        # Calculate total current fleet
        total_fleet = int(gas_fleet + hybrid_fleet + ev_fleet)

        # Calculate emissions and electricity demand
        total_gas_emissions = gas_fleet * gas_car_emissions_per_car(i, gas_fleet) + gas_purchases * new_gas_car_emissions
        total_hybrid_emissions = hybrid_fleet * hybrid_car_emissions_per_car(i, hybrid_fleet) + hybrid_purchases * new_hybrid_car_emissions
        total_ev_emissions = (ev_purchases + actual_gas_to_ev_replacements + actual_hybrid_to_ev_replacements) * new_ev_car_emissions
        total_emissions = total_gas_emissions + total_hybrid_emissions + total_ev_emissions
        total_electricity_demand = ev_fleet * ev_electricity_demand_per_car(i, ev_fleet)

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
    investment_schedule = [200_000_000, 300_000_000, 400_000_000, 500_000_000, 600_000_000] * 6  # 30 years
    df_results = simulate_fleet_evolution(investment_schedule)
    print(df_results)
    import matplotlib.pyplot as plt
    df_results[["gas_fleet", "hybrid_fleet", "ev_fleet"]].plot(title="Annual Fleet Composition Over Time")
    plt.show()