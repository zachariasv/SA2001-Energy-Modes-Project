# ELECTRIC PRODUCTION MODEL
from typing import Callable
import numpy as np
import pandas as pd

# Constants TO CHANGE
GAMMA_FF: float = 0.820  # ???? # kgCO2/kWh
PRODUCTION_TYPE_CONSTANTS: dict[str, dict[str, float]] = {
    "Wind": {
        "delta_i": 2.0,  # years
        "T_i": 25.0,  # years
        "p_i": (1000 / 2.5e6) * 0.25 * 24 * 365,  # ? kWh/year/SEK
        "e_i": 0.011 * (1000 / 2.5e6) * 0.25 * 24 * 365,  # ? kgCO2/SEK
    }
}


def get_productions_capacity(
    t: np.ndarray,
    int_of_x_i: dict[str, Callable[[np.ndarray], np.ndarray]],
    P_tilde: Callable[[np.ndarray], np.ndarray],
) -> pd.DataFrame:
    df = pd.DataFrame(index=t)
    df["elec_prod_cap_previous_infras"] = P_tilde(t)
    for key, constants in PRODUCTION_TYPE_CONSTANTS.items():
        xhigh = t - constants["delta_i"]
        xhigh *= xhigh > 0
        xlow = t - constants["delta_i"] - constants["T_i"]
        xlow *= xlow > 0
        df[f"elec_prod_cap_{key}"] = constants["p_i"] * (
            int_of_x_i[key](xhigh) - int_of_x_i[key](xlow)
        )

    df["elec_prod_cap"] = df.sum(axis=1)

    return df


def get_elec_simulation(
    t: np.ndarray,
    ev_electicity_demand: np.ndarray,
    x_i: dict[str, Callable[[np.ndarray], np.ndarray]],
    int_of_x_i: dict[str, Callable[[np.ndarray], np.ndarray]],
    P_tilde: Callable[[np.ndarray], np.ndarray] = (
        lambda t: 12 * 16e6 * (1 - t / 20) * (1 - t / 20 > 0)
    ),  # 20 years left assumption
    other_electric_demand: Callable[[np.ndarray], np.ndarray] = (
        lambda t: 12 * 16e6 * np.ones_like(t)
    ),  # Production in Dec 2024 -> extrapolation # kWh/year
) -> pd.DataFrame:
    df = get_productions_capacity(t, int_of_x_i, P_tilde)
    df["elec_total_demand"] = other_electric_demand(t) + ev_electicity_demand
    df["emission_elec"] = 0.0
    df["emission_elec_prod_FF"] = (
        GAMMA_FF
        * (df["elec_total_demand"] - df["elec_prod_cap"])
        * (df["elec_prod_cap"] < df["elec_total_demand"])
    )
    df["emission_elec"] += df["emission_elec_prod_FF"]
    for key, constants in PRODUCTION_TYPE_CONSTANTS.items():
        df[f"emmission_elec_{key}_infra"] = constants["e_i"] * x_i[key](t)
        df["emission_elec"] += df[f"emmission_elec_{key}_infra"]

    return df
