import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    from elec_production_model import get_elec_simulation, PRODUCTION_TYPE_CONSTANTS
    from car_fleet_model import simulate_fleet_evolution

    plt.style.use("ggplot")
    return (
        PRODUCTION_TYPE_CONSTANTS,
        get_elec_simulation,
        np,
        pd,
        plt,
        simulate_fleet_evolution,
    )


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Constants""")
    return


@app.cell
def _(mo):
    end_time_choice = mo.ui.number(start=5, step=1, value=100, label=r"Time of interest $T$ (years)")
    investment_per_year_choice = mo.ui.number(start=0, step=0.1, value=10, label="Total investment per year (B SEK)")

    mo.vstack([end_time_choice,investment_per_year_choice])
    return end_time_choice, investment_per_year_choice


@app.cell
def _(end_time_choice, investment_per_year_choice, np):
    T = end_time_choice.value
    V_tot = investment_per_year_choice.value*1e9
    P_tilde = lambda tt: 40.5e9*(1-tt/18)*(tt<18) + 48.6e9*(1-tt/15)*(tt<15) + 2.43e9*(1-tt/19)*(tt<19) + 64.8e9*(1-tt/60)*(tt<60)
    t = np.arange(T+1)
    return P_tilde, V_tot, t


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Simulation with constant investment""")
    return


@app.cell
def _(V_tot, mo):
    x_Hydro_choice = mo.ui.slider(start=0, stop=V_tot/1e9, value=0, step=0.5, label="$x_{Hydro}$ (B SEK)",show_value=True)

    mo.vstack([x_Hydro_choice])
    return (x_Hydro_choice,)


@app.cell
def _(V_tot, mo, np, t, x_Hydro_choice):
    x_i_choice = {"Hydro":x_Hydro_choice.value*1e9}

    ev_investment = (V_tot - sum([x for x in x_i_choice.values()]))*np.ones_like(t)

    x_i = {key:(lambda tt: np.ones_like(tt)*value_choice) for key,value_choice in x_i_choice.items()}
    int_of_x_i = {key:(lambda tt: tt*value_choice) for key,value_choice in x_i_choice.items()}

    mo.md(f"Investment in vehicule transition {ev_investment[0]:.2e} SEK")
    return ev_investment, int_of_x_i, x_i


@app.cell(hide_code=True)
def _(ev_investment, mo, np):
    mo.md(rf"""{"!!! There is not enough money" if np.any(ev_investment[0]<0) else "The choice is valid (enough moeny at each time)"}""")
    return


@app.cell
def _(ev_investment, plt, t, x_i):
    plt.figure()
    plt.stackplot(t,ev_investment,*[x(t) for x in x_i.values()], labels=["Vehicule"]+list(x_i.keys()), linewidth=0.)
    plt.legend()
    plt.ylabel("Investment (SEK)")
    plt.xlabel("$t$")
    plt.gca()
    return


@app.cell
def _(mo):
    mo.md(r"""## Fleet simulation""")
    return


@app.cell
def _(ev_investment, plt, simulate_fleet_evolution):
    df_fleet = simulate_fleet_evolution(ev_investment)

    df_fleet[["gas_fleet", "hybrid_fleet", "ev_fleet"]].plot.area(title="Annual Fleet Composition Over Time", stacked=True, linewidth=0.)
    plt.xlabel("$t$")
    plt.ylabel("Fleet composition")
    plt.gca()
    return (df_fleet,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Production mode simulation""")
    return


@app.cell
def _(
    PRODUCTION_TYPE_CONSTANTS,
    P_tilde,
    df_fleet,
    get_elec_simulation,
    int_of_x_i,
    plt,
    t,
    x_i,
):
    df_elec = get_elec_simulation(t, df_fleet["ev_electricity_demand"].to_numpy()*1e3+P_tilde(0), x_i, int_of_x_i, P_tilde)
    df_elec[[f"elec_prod_cap_{i}" for i in ["previous_infras"]+list(PRODUCTION_TYPE_CONSTANTS.keys())]].plot.area(linewidth=0.)
    plt.plot(df_elec["elec_total_demand"],c="k",linestyle="dashed", label="Elec total demand")
    plt.legend()
    plt.ylabel("Elec clean production capacity (kWh)")
    plt.xlabel("$t$")
    plt.gca().axis('tight')
    plt.gca()
    return (df_elec,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Emmissions over time""")
    return


@app.cell
def _(PRODUCTION_TYPE_CONSTANTS, df_elec, df_fleet, pd, plt):
    df_emissions = pd.DataFrame()
    df_emissions["elec_FF"] = df_elec["emission_elec_prod_FF"]
    for key in PRODUCTION_TYPE_CONSTANTS.keys():
        df_emissions[f"elec_{key}"] = df_elec[f"emmission_elec_{key}_infra"]
    df_emissions[["fleet_gas","fleet_hybrid"]] = df_fleet[["gas_emissions","hybrid_emissions"]]*1e3
    df_emissions["fleet_ev"] = df_fleet["total_emissions"]*1e3 - df_emissions["fleet_gas"] - df_emissions["fleet_hybrid"]

    df_emissions.plot.area(linewidth=0.)
    plt.xlabel("$t$")
    plt.ylabel("kg$CO_2$")
    plt.gca()
    return


if __name__ == "__main__":
    app.run()
