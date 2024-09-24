import base64
import io
from copy import deepcopy

import dash_mantine_components as dmc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pythermalcomfort.models import pmv, adaptive_ashrae
from pythermalcomfort.utilities import v_relative, clo_dynamic
from pythermalcomfort.psychrometrics import psy_ta_rh
from scipy import optimize

from components.drop_down_inline import generate_dropdown_inline
from utils.my_config_file import ElementsIDs, Models, UnitSystem, UnitConverter
from utils.website_text import TextHome
import matplotlib

matplotlib.use("Agg")

import plotly.graph_objects as go
import dash_html_components as html
import dash_core_components as dcc
import dash_core_components as dcc


def chart_selector(selected_model: str):
    list_charts = deepcopy(Models[selected_model].value.charts)
    list_charts = [chart.name for chart in list_charts]
    drop_down_chart_dict = {
        "id": ElementsIDs.chart_selected.value,
        "question": TextHome.chart_selection.value,
        "options": list_charts,
        "multi": False,
        "default": list_charts[0],
    }

    return generate_dropdown_inline(
        drop_down_chart_dict, value=drop_down_chart_dict["default"], clearable=False
    )


# fig example
def t_rh_pmv(inputs: dict = None, model: str = "iso"):
    results = []
    pmv_limits = [-0.5, 0.5]
    clo_d = clo_dynamic(
        clo=inputs[ElementsIDs.clo_input.value], met=inputs[ElementsIDs.met_input.value]
    )
    vr = v_relative(
        v=inputs[ElementsIDs.v_input.value], met=inputs[ElementsIDs.met_input.value]
    )
    for pmv_limit in pmv_limits:
        for rh in np.arange(0, 110, 10):

            def function(x):
                return (
                    pmv(
                        x,
                        tr=inputs[ElementsIDs.t_r_input.value],
                        vr=vr,
                        rh=rh,
                        met=inputs[ElementsIDs.met_input.value],
                        clo=clo_d,
                        wme=0,
                        standard=model,
                        limit_inputs=False,
                    )
                    - pmv_limit
                )

            temp = optimize.brentq(function, 10, 40)
            results.append(
                {
                    "rh": rh,
                    "temp": temp,
                    "pmv_limit": pmv_limit,
                }
            )

    df = pd.DataFrame(results)

    f, axs = plt.subplots(1, 1, figsize=(6, 4), sharex=True)
    t1 = df[df["pmv_limit"] == pmv_limits[0]]
    t2 = df[df["pmv_limit"] == pmv_limits[1]]
    axs.fill_betweenx(
        t1["rh"], t1["temp"], t2["temp"], alpha=0.5, label=model, color="#7BD0F2"
    )
    axs.scatter(
        inputs[ElementsIDs.t_db_input.value],
        inputs[ElementsIDs.rh_input.value],
        color="red",
    )
    axs.set(
        ylabel="RH (%)",
        xlabel="Temperature (°C)",
        ylim=(0, 100),
        xlim=(10, 40),
    )
    axs.legend(frameon=False).remove()
    axs.grid(True, which="both", linestyle="--", linewidth=0.5)
    axs.spines["top"].set_visible(False)
    axs.spines["right"].set_visible(False)
    plt.tight_layout()

    my_stringIObytes = io.BytesIO()
    plt.savefig(
        my_stringIObytes,
        format="png",
        transparent=True,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0,
    )
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()
    plt.close("all")
    return dmc.Image(
        src=f"data:image/png;base64, {my_base64_jpgData}",
        alt="Heat stress chart",
        py=0,
    )


def t_rh_pmv_category(inputs: dict = None, model: str = "iso"):
    results = []
    # Specifies the category of the PMV interval
    pmv_limits = [-0.7, -0.5, -0.2, 0.2, 0.5, 0.7]
    colors = [
        "rgba(168,204,162,0.9)",  # Light green
        "rgba(114,174,106,0.9)",  # Medium green
        "rgba(78,156,71,0.9)",  # Dark green
        "rgba(114,174,106,0.9)",  # Medium green
        "rgba(168,204,162,0.9)",  # Light green
    ]
    clo_d = clo_dynamic(
        clo=inputs[ElementsIDs.clo_input.value], met=inputs[ElementsIDs.met_input.value]
    )
    vr = v_relative(
        v=inputs[ElementsIDs.v_input.value], met=inputs[ElementsIDs.met_input.value]
    )
    for i in range(len(pmv_limits) - 1):
        lower_limit = pmv_limits[i]
        upper_limit = pmv_limits[i + 1]
        color = colors[i]  # Corresponding color

        for rh in np.arange(0, 110, 10):
            # Find the upper and lower limits of temperature
            def function(x):
                return (
                    pmv(
                        x,
                        tr=inputs[ElementsIDs.t_r_input.value],
                        vr=vr,
                        rh=rh,
                        met=inputs[ElementsIDs.met_input.value],
                        clo=clo_d,
                        wme=0,
                        standard=model,
                        limit_inputs=False,
                    )
                    - lower_limit
                )

            temp_lower = optimize.brentq(function, 10, 40)

            def function_upper(x):
                return (
                    pmv(
                        x,
                        tr=inputs[ElementsIDs.t_r_input.value],
                        vr=vr,
                        rh=rh,
                        met=inputs[ElementsIDs.met_input.value],
                        clo=clo_d,
                        wme=0,
                        standard=model,
                        limit_inputs=False,
                    )
                    - upper_limit
                )

            temp_upper = optimize.brentq(function_upper, 10, 40)
            # Record RH and temperature upper and lower limits for each interval
            results.append(
                {
                    "rh": rh,
                    "temp_lower": temp_lower,
                    "temp_upper": temp_upper,
                    "pmv_lower_limit": lower_limit,
                    "pmv_upper_limit": upper_limit,
                    "color": color,  # Use the specified color
                }
            )
    df = pd.DataFrame(results)
    # Visualization: Create a chart with multiple fill areas
    fig = go.Figure()
    for i in range(len(pmv_limits) - 1):
        region_data = df[
            (df["pmv_lower_limit"] == pmv_limits[i])
            & (df["pmv_upper_limit"] == pmv_limits[i + 1])
        ]
        # Draw the temperature line at the bottom
        fig.add_trace(
            go.Scatter(
                x=region_data["temp_lower"],
                y=region_data["rh"],
                fill=None,
                mode="lines",
                line=dict(color="rgba(255,255,255,0)"),
            )
        )
        # Draw the temperature line at the top and fill in the color
        if colors[i]:
            fig.add_trace(
                go.Scatter(
                    x=region_data["temp_upper"],
                    y=region_data["rh"],
                    fill="tonexty",
                    fillcolor=colors[i],  # Use defined colors
                    mode="lines",
                    line=dict(color="rgba(255,255,255,0)"),
                    showlegend=False,
                )
            )
    # Add red dots to indicate the current input temperature and humidity
    fig.add_trace(
        go.Scatter(
            x=[inputs[ElementsIDs.t_db_input.value]],
            y=[inputs[ElementsIDs.rh_input.value]],
            mode="markers",
            marker=dict(color="red", size=12),
            name="Current Condition",
        )
    )
    # Update layout
    fig.update_layout(
        xaxis_title="Temperature (°C)",
        yaxis_title="Relative Humidity (%)",
        showlegend=False,
        template="simple_white",
        xaxis=dict(
            range=[10, 40],
            showgrid=True,
            gridcolor="lightgray",
            gridwidth=1,
            dtick=2,  # Set the horizontal scale interval to 2
        ),
        yaxis=dict(
            range=[0, 100],
            showgrid=True,
            gridcolor="lightgray",
            gridwidth=1,
            dtick=10,  # Set the ordinate scale interval to 10
        ),
    )
    return dcc.Graph(figure=fig)


def pmot_ot_adaptive_ashrae(inputs: dict = None, model: str = "ashrae"):
    # Input parameter
    air_temperature = inputs[ElementsIDs.t_db_input.value]  # Air Temperature
    mean_radiant_temp = inputs[ElementsIDs.t_r_input.value]  # Mean Radiant Temperature
    prevailing_mean_outdoor_temp = inputs[
        ElementsIDs.t_rm_input.value
    ]  # Prevailing Mean Outdoor Temperature
    air_speed = inputs[ElementsIDs.v_input.value]  # Air Speed
    operative_temperature = air_temperature  # 计算 Operative Temperature
    units = inputs[ElementsIDs.UNIT_TOGGLE.value]  # unit (IP or SI)
    # Calculate the values for the special points t_running_mean = 10 and t_running_mean = 33.5
    t_running_means = [10, 33.5]  # special points
    results = []
    for t_running_mean in t_running_means:
        adaptive = adaptive_ashrae(
            tdb=air_temperature,
            tr=mean_radiant_temp,
            t_running_mean=t_running_mean,
            v=air_speed,
        )
        if units == UnitSystem.IP.value:
            t_running_mean = UnitConverter.celsius_to_fahrenheit(t_running_mean)
            adaptive.tmp_cmf = UnitConverter.celsius_to_fahrenheit(adaptive.tmp_cmf)
            adaptive.tmp_cmf_80_low = UnitConverter.celsius_to_fahrenheit(
                adaptive.tmp_cmf_80_low
            )
            adaptive.tmp_cmf_80_up = UnitConverter.celsius_to_fahrenheit(
                adaptive.tmp_cmf_80_up
            )
            adaptive.tmp_cmf_90_low = UnitConverter.celsius_to_fahrenheit(
                adaptive.tmp_cmf_90_low
            )
            adaptive.tmp_cmf_90_up = UnitConverter.celsius_to_fahrenheit(
                adaptive.tmp_cmf_90_up
            )
        results.append(
            {
                "prevailing_mean_outdoor_temp": t_running_mean,
                "tmp_cmf_80_low": round(adaptive.tmp_cmf_80_low, 2),
                "tmp_cmf_80_up": round(adaptive.tmp_cmf_80_up, 2),
                "tmp_cmf_90_low": round(adaptive.tmp_cmf_90_low, 2),
                "tmp_cmf_90_up": round(adaptive.tmp_cmf_90_up, 2),
            }
        )

    # Convert the result to a DataFrame
    df = pd.DataFrame(results)

    # Create a Plotly graphics object
    fig = go.Figure()

    if units == UnitSystem.IP.value:
        air_temperature = UnitConverter.celsius_to_fahrenheit(air_temperature)
        mean_radiant_temp = UnitConverter.celsius_to_fahrenheit(mean_radiant_temp)
        prevailing_mean_outdoor_temp = UnitConverter.celsius_to_fahrenheit(
            prevailing_mean_outdoor_temp
        )
        operative_temperature = UnitConverter.celsius_to_fahrenheit(
            operative_temperature
        )

    # 80% acceptance zone
    fig.add_trace(
        go.Scatter(
            x=df["prevailing_mean_outdoor_temp"],
            y=df["tmp_cmf_80_up"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["prevailing_mean_outdoor_temp"],
            y=df["tmp_cmf_80_low"],
            fill="tonexty",  # Fill into the next trace
            fillcolor="rgba(0, 100, 200, 0.2)",
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            # name="80% Acceptability",
        )
    )

    # 90% acceptance zone
    fig.add_trace(
        go.Scatter(
            x=df["prevailing_mean_outdoor_temp"],
            y=df["tmp_cmf_90_up"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["prevailing_mean_outdoor_temp"],
            y=df["tmp_cmf_90_low"],
            fill="tonexty",  # Fill into the next trace
            fillcolor="rgba(0, 100, 200, 0.4)",
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            # name="90% Acceptability",
        )
    )

    # Red dot of the current condition
    fig.add_trace(
        go.Scatter(
            x=[prevailing_mean_outdoor_temp],
            y=[operative_temperature],
            mode="markers",
            marker=dict(color="red", size=10),
            name="Current Condition",
            showlegend=False,
        )
    )
    if units == UnitSystem.IP.value:
        xaxis_range = [
            UnitConverter.celsius_to_fahrenheit(10),
            UnitConverter.celsius_to_fahrenheit(33.5),
        ]
        xaxis_tick0 = UnitConverter.celsius_to_fahrenheit(10)
        # xaxis_tick0 = 50
        xaxis_dtick = UnitConverter.celsius_to_fahrenheit(
            2
        ) - UnitConverter.celsius_to_fahrenheit(
            0
        )  # calculate dtick
        # xaxis_dtick = 5
        xaxis_title = "Prevailing Mean Outdoor Temperature (°F)"
    else:
        xaxis_range = [10, 33.5]
        xaxis_tick0 = 10
        xaxis_dtick = 2
        xaxis_title = "Prevailing Mean Outdoor Temperature (°C)"
    # Set chart style
    fig.update_layout(
        xaxis_title=xaxis_title,
        yaxis_title=(
            "Operative Temperature (°C)"
            if units == UnitSystem.SI.value
            else "Operative Temperature (°F)"
        ),
        xaxis=dict(
            range=xaxis_range,
            linecolor="lightgray",
            tick0=xaxis_tick0,
            dtick=xaxis_dtick,
            showgrid=True,
            gridcolor="lightgray",
        ),  # Set the X-axis range and scale dynamically
        yaxis=dict(
            range=[df["tmp_cmf_80_low"].min(), df["tmp_cmf_80_up"].max()],
            linecolor="lightgray",
            showgrid=True,
            gridcolor="lightgray",
        ),
        showlegend=True,
        template="simple_white",
    )

    return dmc.Paper(children=[dcc.Graph(figure=fig)])


def t_hr_pmv(inputs: dict = None, model: str = "iso"):
    results = []
    pmv_limits = [-0.5, 0.5]
    clo_d = clo_dynamic(
        clo=inputs[ElementsIDs.clo_input.value], met=inputs[ElementsIDs.met_input.value]
    )
    vr = v_relative(
        v=inputs[ElementsIDs.v_input.value], met=inputs[ElementsIDs.met_input.value]
    )

    current_tdb = inputs[ElementsIDs.t_db_input.value]
    current_rh = inputs[ElementsIDs.rh_input.value]
    psy_data = psy_ta_rh(current_tdb, current_rh)

    for pmv_limit in pmv_limits:
        for rh in np.arange(10, 110, 10):
            psy_data_rh = psy_ta_rh(current_tdb, rh)

            def function(x):
                return (
                    pmv(
                        x,
                        tr=inputs[ElementsIDs.t_r_input.value],
                        vr=vr,
                        rh=rh,
                        met=inputs[ElementsIDs.met_input.value],
                        clo=clo_d,
                        wme=0,
                        standard=model,
                        limit_inputs=False,
                    )
                    - pmv_limit
                )

            temp = optimize.brentq(function, 10, 40)
            results.append(
                {
                    "rh": rh,
                    "hr": psy_data_rh["hr"] * 1000,
                    "temp": temp,
                    "pmv_limit": pmv_limit,
                }
            )

    df = pd.DataFrame(results)

    fig, ax = plt.subplots(figsize=(8, 6))

    for rh in np.arange(10, 110, 10):
        temp_range = np.arange(10, 40, 1)
        hr_values = [psy_ta_rh(t, rh)["hr"] * 1000 for t in temp_range]
        ax.plot(temp_range, hr_values, color="grey", linestyle="--")

    t1 = df[df["pmv_limit"] == pmv_limits[0]]
    t2 = df[df["pmv_limit"] == pmv_limits[1]]
    ax.fill_betweenx(t1["hr"], t1["temp"], t2["temp"], alpha=0.5, color="#7BD0F2")

    ax.scatter(
        current_tdb, psy_data["hr"] * 1000, color="red", edgecolor="black", s=100
    )

    ax.set_xlabel("Dry-bulb Temperature (°C)", fontsize=14)
    ax.set_ylabel("Humidity Ratio (g_water/kg_dry_air)", fontsize=14)
    ax.set_xlim(10, 40)
    ax.set_ylim(0, 30)

    label_text = (
        f"t_db: {current_tdb:.1f} °C\n"
        f"rh: {current_rh:.1f} %\n"
        f"Wa: {psy_data['hr'] * 1000:.1f} g_w/kg_da\n"
        f"twb: {psy_data['t_wb']:.1f} °C\n"
        f"tdp: {psy_data['t_dp']:.1f} °C\n"
        f"h: {psy_data['h'] / 1000:.1f} kJ/kg"
    )

    ax.text(
        0.05,
        0.95,
        label_text,
        transform=ax.transAxes,
        fontsize=12,
        verticalalignment="top",
        bbox=dict(facecolor="white", alpha=0.6),
    )
    plt.tight_layout()
    my_stringIObytes = io.BytesIO()
    plt.savefig(
        my_stringIObytes,
        format="png",
        transparent=True,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0,
    )
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()
    plt.close("all")

    return dmc.Image(
        src=f"data:image/png;base64, {my_base64_jpgData}",
        alt="Psychrometric chart",
        py=0,
    )


def speed_temp_pmv(inputs: dict = None, model: str = "iso"):
    results = []
    pmv_limits = [-0.5, 0.5]
    clo_d = clo_dynamic(
        clo=inputs[ElementsIDs.clo_input.value], met=inputs[ElementsIDs.met_input.value]
    )

    for pmv_limit in pmv_limits:
        for vr in np.arange(0.1, 1.3, 0.1):

            def function(x):
                return (
                    pmv(
                        x,
                        tr=inputs[ElementsIDs.t_r_input.value],
                        vr=vr,
                        rh=inputs[ElementsIDs.rh_input.value],
                        met=inputs[ElementsIDs.met_input.value],
                        clo=clo_d,
                        wme=0,
                        standard=model,
                        limit_inputs=False,
                    )
                    - pmv_limit
                )

            temp = optimize.brentq(function, 10, 40)
            results.append(
                {
                    "vr": vr,
                    "temp": temp,
                    "pmv_limit": pmv_limit,
                }
            )


def SET_outputs_chart(
    inputs: dict = None, calculate_ce: bool = False, p_atmospheric: int = 101325
):
    # Dry-bulb air temperature (x-axis)
    tdb_values = np.arange(10, 40, 0.5, dtype=float).tolist()

    # Prepare arrays for the outputs we want to plot
    set_temp = []  # set_tmp()
    skin_temp = []  # t_skin
    core_temp = []  # t_core
    clothing_temp = []  # t_cl
    mean_body_temp = []  # t_body
    total_skin_evaporative_heat_loss = []  # e_skin
    sweat_evaporation_skin_heat_loss = []  # e_rsw
    vapour_diffusion_skin_heat_loss = []  # e_diff
    total_skin_senesible_heat_loss = []  # q_sensible
    total_skin_heat_loss = []  # q_skin
    heat_loss_respiration = []  # q_res
    skin_wettedness = []  # w

    # Extract common input values
    tr = float(inputs[ElementsIDs.t_r_input.value])
    vr = float(
        v_relative(  # Ensure vr is scalar
            v=inputs[ElementsIDs.v_input.value], met=inputs[ElementsIDs.met_input.value]
        )
    )
    rh = float(inputs[ElementsIDs.rh_input.value])  # Ensure rh is scalar
    met = float(inputs[ElementsIDs.met_input.value])  # Ensure met is scalar
    clo = float(
        clo_dynamic(  # Ensure clo is scalar
            clo=inputs[ElementsIDs.clo_input.value], met=met
        )
    )

    # Iterate through each temperature value and call set_tmp
    for tdb in tdb_values:
        set = set_tmp(
            tdb=tdb,
            tr=tr,
            v=vr,
            rh=rh,
            met=met,
            clo=clo,
            wme=0,
            limit_inputs=False,
        )
        set_temp.append(float(set))  # Convert np.float64 to float

    # Iterate through each temperature value and call `two_nodes`
    for tdb in tdb_values:
        results = two_nodes(
            tdb=tdb,
            tr=tr,
            v=vr,
            rh=rh,
            met=met,
            clo=clo,
            wme=0,
        )
        # Collect relevant data for each variable, converting to float
        skin_temp.append(float(results["t_skin"]))  # Convert np.float64 to float
        core_temp.append(float(results["t_core"]))  # Convert np.float64 to float
        total_skin_evaporative_heat_loss.append(
            float(results["e_skin"])
        )  # Convert np.float64 to float
        sweat_evaporation_skin_heat_loss.append(
            float(results["e_rsw"])
        )  # Convert np.float64 to float
        vapour_diffusion_skin_heat_loss.append(
            float(results["e_skin"] - results["e_rsw"])
        )  # Convert np.float64 to float
        total_skin_senesible_heat_loss.append(
            float(results["q_sensible"])
        )  # Convert np.float64 to float
        total_skin_heat_loss.append(
            float(results["q_skin"])
        )  # Convert np.float64 to float
        heat_loss_respiration.append(
            float(results["q_res"])
        )  # Convert np.float64 to float
        skin_wettedness.append(
            float(results["w"]) * 100
        )  # Convert to percentage and float

        # calculate clothing temperature t_cl
        pressure_in_atmospheres = float(p_atmospheric / 101325)
        r_clo = 0.155 * clo
        f_a_cl = 1.0 + 0.15 * clo
        h_cc = 3.0 * pow(pressure_in_atmospheres, 0.53)
        h_fc = 8.600001 * pow((vr * pressure_in_atmospheres), 0.53)
        h_cc = max(h_cc, h_fc)
        if not calculate_ce and met > 0.85:
            h_c_met = 5.66 * (met - 0.85) ** 0.39
            h_cc = max(h_cc, h_c_met)
        h_r = 4.7
        h_t = h_r + h_cc
        r_a = 1.0 / (f_a_cl * h_t)
        t_op = (h_r * tr + h_cc * tdb) / h_t
        clothing_temp.append(
            float((r_a * results["t_skin"] + r_clo * t_op) / (r_a + r_clo))
        )
        # calculate mean body temperature t_body
        alfa = 0.1
        mean_body_temp.append(
            float(alfa * results["t_skin"] + (1 - alfa) * results["t_core"])
        )
    # df = pd.DataFrame(results)
    fig = go.Figure()
    # fig.add_trace(go.Scatter(
    #     x=tdb_values,
    #     y=set_temp,
    #     mode='lines',
    #     name='SET temperature',
    #     line=dict(color='blue')
    # ))

    # Added SET temperature curve
    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=set_temp,
            mode="lines",
            name="SET temperature",
            line=dict(color="blue"),
            yaxis="y1",  # Use a  y-axis
        )
    )

    # Adding skin temperature curve
    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=skin_temp,
            mode="lines",
            name="Skin temperature",
            line=dict(color="cyan"),
        )
    )

    # Added core temperature curve
    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=core_temp,
            mode="lines",
            name="core temperature",
            line=dict(color="limegreen"),
            yaxis="y1",  # Use a second y-axis
        )
    )

    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=clothing_temp,
            mode="lines",
            name="clothing temperature",
            line=dict(color="lightgreen"),
            yaxis="y1",  # Use a second y-axis
        )
    )

    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=mean_body_temp,
            mode="lines",
            name="mean body temperature",
            line=dict(color="green"),
            yaxis="y1",  # Use a second y-axis
        )
    )
    # total skin evaporative heat loss
    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=total_skin_evaporative_heat_loss,
            mode="lines",
            name="total skin evaporative heat loss",
            line=dict(color="lightgrey"),
            yaxis="y2",  # Use a second y-axis
        )
    )
    # sweat evaporation skin heat loss
    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=sweat_evaporation_skin_heat_loss,
            mode="lines",
            name="sweat evaporation skin heat loss ",
            line=dict(color="orange"),
            yaxis="y2",  # Use a second y-axis
        )
    )

    # vapour diffusion skin heat loss
    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=vapour_diffusion_skin_heat_loss,
            mode="lines",
            name="vapour diffusion skin heat loss ",
            line=dict(color="darkorange"),
            yaxis="y2",  # Use a second y-axis
        )
    )

    # total skin sensible heat loss
    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=total_skin_heat_loss,
            mode="lines",
            name="total skin sensible heat loss ",
            line=dict(color="darkgrey"),
            yaxis="y2",  # Use a second y-axis
        )
    )

    # Added  total skin heat loss curve
    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=total_skin_heat_loss,
            mode="lines",
            name="Total skin heat loss",
            line=dict(color="black"),
            yaxis="y2",  # Use a second y-axis
        )
    )

    #  heat loss respiration curve
    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=heat_loss_respiration,
            mode="lines",
            name="heat loss respiration",
            line=dict(color="black", dash="dash"),
            yaxis="y2",  # Use a second y-axis
        )
    )

    # Added skin moisture curve
    fig.add_trace(
        go.Scatter(
            x=tdb_values,
            y=skin_wettedness,
            mode="lines",
            name="Skin wettedness",
            line=dict(color="yellow", dash="dash"),
            yaxis="y1",  # Use a second y-axis
        )
    )

    # Set the layout of the chart and adjust the legend position
    fig.update_layout(
        title="Temperature and Heat Loss",
        xaxis=dict(
            title="Dry-bulb Air Temperature [°C]",
            showgrid=False,
            range=[10, 40],
            dtick=2,
        ),
        yaxis=dict(title="Temperature [°C]", showgrid=False, range=[18, 38], dtick=2),
        yaxis2=dict(
            title="Heat Loss [W] / Skin Wettedness [%]",
            showgrid=False,
            overlaying="y",
            side="right",
            range=[0, 70],
            # title_standoff=50  # Increase the distance between the Y axis title and the chart
        ),
        legend=dict(
            x=0.5,  # Adjust the horizontal position of the legend
            y=-0.2,  # Move the legend below the chart
            orientation="h",  # Display the legend horizontally
            traceorder="normal",  # 按顺序显示
            xanchor="center",
            yanchor="top",
        ),
        template="plotly_white",
        autosize=False,
        width=700,  # 3:4
        height=700,  # 3:4
    )

    # show
    return fig
