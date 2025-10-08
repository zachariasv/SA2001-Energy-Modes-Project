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

    mo.vstack([end_time_choice])
    return (end_time_choice,)


@app.cell
def _(end_time_choice, np):
    T = end_time_choice.value
    P_tilde = lambda tt: 40.5e9*(1-tt/18)*(tt<18) + 48.6e9*(1-tt/15)*(tt<15) + 2.43e9*(1-tt/19)*(tt<19) + 64.8e9*(1-tt/60)*(tt<60)
    t = np.arange(T+1)
    return P_tilde, T, t


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Simulation with constant investment""")
    return


@app.cell
def _(P_tilde, plt, t):
    plt.plot(P_tilde(t))
    plt.title("Clean energy capacity w/o investement&maintenance")
    plt.ylabel("kWh/year")
    plt.xlabel("$t$ (years)")
    return


@app.cell
def _(mo):
    x_Wind_choice = mo.ui.number(start=0, value=0, step=.1, label="$x_{Wind}$ (B SEK/year)")
    x_Nuclear_choice = mo.ui.number(start=0, value=0, step=.1, label="$x_{Nuclear}$ (B SEK/year)")
    x_Hydro_choice = mo.ui.number(start=0, value=0, step=.1, label="$x_{Hydro}$ (B SEK/year)")
    x_Solar_choice = mo.ui.number(start=0, value=0, step=.1, label="$x_{Solar}$ (B SEK/year)")
    x_EV_choice = mo.ui.number(start=0, value=0, step=.1, label="$x_{EV}$ (B SEK/year)")

    mo.vstack([x_Wind_choice, x_Nuclear_choice, x_Hydro_choice, x_Solar_choice, x_EV_choice])
    return (
        x_EV_choice,
        x_Hydro_choice,
        x_Nuclear_choice,
        x_Solar_choice,
        x_Wind_choice,
    )


@app.cell
def _(
    np,
    t,
    x_EV_choice,
    x_Hydro_choice,
    x_Nuclear_choice,
    x_Solar_choice,
    x_Wind_choice,
):
    x_i_choice = {
        "Wind":x_Wind_choice.value*1e9,
        "Nuclear":x_Nuclear_choice.value*1e9,
        "Hydro":x_Hydro_choice.value*1e9,
        "Solar":x_Solar_choice.value*1e9
    }

    ev_investment = x_EV_choice.value*1e9*np.ones_like(t)

    x_i = {key:(lambda tt, val=value_choice: np.ones_like(tt)*val) for key,value_choice in x_i_choice.items()}
    int_of_x_i = {key:(lambda tt, val=value_choice: tt*val) for key,value_choice in x_i_choice.items()}
    return ev_investment, int_of_x_i, x_i


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


@app.cell
def _(df_fleet, plt):
    (1e3*df_fleet["ev_electricity_demand"]).plot()
    plt.xlabel("$t$ (years)")
    plt.ylabel("Fleet's electrical demand per year (kWh)")
    return


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
    np,
    plt,
    t,
    x_i,
):
    df_elec = get_elec_simulation(t, df_fleet["ev_electricity_demand"].to_numpy()*1e3, x_i, int_of_x_i, P_tilde, lambda tt: 162e9*np.ones_like(tt))
    df_elec[[f"elec_prod_cap_{i}" for i in ["previous_infras"]+list(PRODUCTION_TYPE_CONSTANTS.keys())]].plot.area(linewidth=0.)
    plt.plot(df_elec["elec_total_demand"],c="k",linestyle="dashed", label="Elec total demand")
    plt.legend()
    plt.ylabel("Elec clean production capacity per year (kWh)")
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

    df_emissions.plot.area(linewidth=0., colormap="magma")
    plt.xlabel("$t$")
    plt.ylabel("kg$CO_2$")
    plt.gca()
    return (df_emissions,)


@app.cell(hide_code=True)
def _(T, df_emissions, mo):
    mo.md(rf"""*Total emmisions over time is* **{df_emissions.sum().sum():e} $kgCO_2$** *over* **{T} years**""")
    return


if __name__ == "__main__":
    app.run()
