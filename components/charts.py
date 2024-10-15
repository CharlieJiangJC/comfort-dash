import base64
import io
from copy import deepcopy

import dash_mantine_components as dmc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pythermalcomfort.models import pmv
from pythermalcomfort.utilities import v_relative, clo_dynamic
from scipy import optimize

from components.drop_down_inline import generate_dropdown_inline
from utils.my_config_file import (
    ElementsIDs,
    Models,
    Functionalities,
    UnitSystem,
    UnitConverter,
)
from utils.website_text import TextHome
import matplotlib
from pythermalcomfort.models import adaptive_en, cooling_effect
from pythermalcomfort.psychrometrics import t_o, psy_ta_rh

matplotlib.use("Agg")

import plotly.graph_objects as go
from dash import dcc


def chart_selector(selected_model: str, function_selection: str, chart_selected: str):

    list_charts = list(Models[selected_model].value.charts)
    if function_selection == Functionalities.Compare.value:
        if selected_model == Models.PMV_ashrae.name:
            list_charts = list(Models[selected_model].value.charts_compare)

    list_charts = [chart.name for chart in list_charts]

    if chart_selected is not None:
        chart_selected_output = chart_selected
    else:
        chart_selected_output = list_charts[0]

    drop_down_chart_dict = {
        "id": ElementsIDs.chart_selected.value,
        "question": TextHome.chart_selection.value,
        "options": list_charts,
        "multi": False,
        "default": chart_selected_output,
    }

    return generate_dropdown_inline(
        drop_down_chart_dict, value=drop_down_chart_dict["default"], clearable=False
    )


def get_inputs(inputs):
    tr = inputs[ElementsIDs.t_r_input.value]
    t_db = inputs[ElementsIDs.t_db_input.value]
    met = inputs[ElementsIDs.met_input.value]
    clo = inputs[ElementsIDs.clo_input.value]
    v = inputs[ElementsIDs.v_input.value]
    rh = inputs[ElementsIDs.rh_input.value]

    return met, clo, tr, t_db, v, rh


def compare_get_inputs(inputs):
    met_2 = inputs[ElementsIDs.met_input_input2.value]
    clo_2 = inputs[ElementsIDs.clo_input_input2.value]
    tr_2 = inputs[ElementsIDs.t_r_input_input2.value]
    t_db_2 = inputs[ElementsIDs.t_db_input_input2.value]
    v_2 = inputs[ElementsIDs.v_input_input2.value]
    rh_2 = inputs[ElementsIDs.rh_input_input2.value]

    return met_2, clo_2, tr_2, t_db_2, v_2, rh_2


def adaptive_en_chart(inputs, units):
    traces = []

    if units == UnitSystem.IP.value:
        x_values = np.array([50, 92.3])
    else:
        x_values = np.array([10, 30])

    results_min = adaptive_en(
        tdb=inputs[ElementsIDs.t_db_input.value],
        tr=inputs[ElementsIDs.t_r_input.value],
        t_running_mean=x_values[0],
        v=inputs[ElementsIDs.v_input.value],
        units=units,
    )
    results_max = adaptive_en(
        tdb=inputs[ElementsIDs.t_db_input.value],
        tr=inputs[ElementsIDs.t_r_input.value],
        t_running_mean=x_values[1],
        v=inputs[ElementsIDs.v_input.value],
        units=units,
    )

    y_values_cat_iii_up = [
        results_min["tmp_cmf_cat_iii_up"],
        results_max["tmp_cmf_cat_iii_up"],
    ]
    y_values_cat_iii_low = [
        results_min["tmp_cmf_cat_iii_low"],
        results_max["tmp_cmf_cat_iii_low"],
    ]

    y_values_cat_ii_up = [
        results_min["tmp_cmf_cat_ii_up"],
        results_max["tmp_cmf_cat_ii_up"],
    ]
    y_values_cat_ii_low = [
        results_min["tmp_cmf_cat_ii_low"],
        results_max["tmp_cmf_cat_ii_low"],
    ]

    y_values_cat_i_up = [
        results_min["tmp_cmf_cat_i_up"],
        results_max["tmp_cmf_cat_i_up"],
    ]
    y_values_cat_i_low = [
        results_min["tmp_cmf_cat_i_low"],
        results_max["tmp_cmf_cat_i_low"],
    ]

    # traces[0]
    traces.append(
        go.Scatter(
            x=np.concatenate([x_values, x_values[::-1]]),
            y=np.concatenate([y_values_cat_iii_up, y_values_cat_iii_low[::-1]]),
            fill="toself",
            fillcolor="rgba(144, 238, 144, 0.3)",
            line=dict(color="rgba(144, 238, 144, 0)", shape="linear"),
            name="Category III",
            mode="lines",
        )
    )
    # traces[1]
    traces.append(
        go.Scatter(
            x=np.concatenate([x_values, x_values[::-1]]),
            y=np.concatenate([y_values_cat_ii_up, y_values_cat_ii_low[::-1]]),
            fill="toself",
            fillcolor="rgba(34, 139, 34, 0.5)",
            line=dict(color="rgba(34, 139, 34, 0)", shape="linear"),
            name="Category II",
            mode="lines",
        )
    )
    # traces[2]
    traces.append(
        go.Scatter(
            x=np.concatenate([x_values, x_values[::-1]]),
            y=np.concatenate([y_values_cat_i_up, y_values_cat_i_low[::-1]]),
            fill="toself",
            fillcolor="rgba(0, 100, 0, 0.7)",
            line=dict(color="rgba(0, 100, 0, 0)", shape="linear"),
            name="Category I",
            mode="lines",
        )
    )
    x = inputs[ElementsIDs.t_rm_input.value]
    y = t_o(
        tdb=inputs[ElementsIDs.t_db_input.value],
        tr=inputs[ElementsIDs.t_r_input.value],
        v=inputs[ElementsIDs.v_input.value],
    )
    red_point = [x, y]
    # traces[3]
    traces.append(
        go.Scatter(
            x=[red_point[0]],
            y=[red_point[1]],
            mode="markers",
            marker=dict(
                color="red",
                size=6,
            ),
            name="current input",
            showlegend=False,
        )
    )
    # theta = np.linspace(0, 2 * np.pi, 100)
    # circle_x = red_point[0] + 0.5 * np.cos(theta)
    # circle_y = red_point[1] + 0.8 * np.sin(theta)
    # # traces[4]
    # traces.append(
    #     go.Scatter(
    #         x=circle_x,
    #         y=circle_y,
    #         mode="lines",
    #         line=dict(color="red", width=2.5),
    #         # name='circle',
    #         showlegend=False,
    #     )
    # )

    layout = go.Layout(
        xaxis=dict(
            title="Outdoor Running Mean Temperature [°C]",
            range=[10, 30],
            dtick=2,
            showgrid=True,
            gridcolor="lightgray",
            gridwidth=1.5,
            ticks="outside",
            ticklen=5,
            showline=True,
            linewidth=1.5,
            linecolor="black",
        ),
        yaxis=dict(
            title="Operative Temperature [°C]",
            range=[14, 36],
            dtick=2,
            showgrid=True,
            gridcolor="lightgray",
            gridwidth=1.5,
            ticks="outside",
            ticklen=5,
            showline=True,
            linewidth=1.5,
            linecolor="black",
        ),
        legend=dict(x=0.8, y=1),
        showlegend=False,
        plot_bgcolor="white",
        margin=dict(l=40, r=40, t=40, b=40),
    )

    fig = go.Figure(data=traces, layout=layout)

    if units == UnitSystem.IP.value:
        fig.update_layout(
            xaxis=dict(
                title="Outdoor Running Mean Temperature [°F]", range=[50, 92.3], dtick=5
            ),
        )
        fig.update_layout(
            yaxis=dict(title="Operative Temperature [°F]", range=[60, 104], dtick=5),
        )

    return fig


def t_rh_pmv(
    inputs: dict = None,
    model: str = "iso",
    function_selection: str = Functionalities.Default,
    units: str = "SI",
):
    results = []
    if model == "iso":
        pmv_limits = [-0.7, -0.5, -0.2, 0.2, 0.5, 0.7]
        colors = [
            "rgba(168,204,162,0.9)",
            "rgba(114,174,106,0.9)",
            "rgba(78,156,71,0.9)",
            "rgba(114,174,106,0.9)",
            "rgba(168,204,162,0.9)",
        ]
    else:  # ASHRAE
        pmv_limits = [-0.5, 0.5]
        colors = ["rgba(59, 189, 237, 0.7)"]

    met, clo, tr, t_db, v, rh = get_inputs(inputs)
    clo_d = clo_dynamic(clo, met)
    vr = v_relative(v, met)

    def calculate_pmv_results(tr, vr, met, clo):
        results = []
        for pmv_limit in pmv_limits:
            for rh in np.arange(0, 110, 10):

                def function(x):
                    return (
                        pmv(
                            x,
                            tr=tr,
                            vr=vr,
                            rh=rh,
                            met=met,
                            clo=clo,
                            wme=0,
                            standard=model,
                            units=units,
                            limit_inputs=False,
                        )
                        - pmv_limit
                    )

                try:
                    temp = optimize.brentq(function, 10, 120)
                    results.append(
                        {
                            "rh": rh,
                            "temp": temp,
                            "pmv_limit": pmv_limit,
                        }
                    )
                except ValueError:
                    continue
        return pd.DataFrame(results)

    df = calculate_pmv_results(
        tr=tr,
        vr=vr,
        met=met,
        clo=clo_d,
    )

    fig = go.Figure()

    for i in range(len(pmv_limits) - 1):
        t1 = df[df["pmv_limit"] == pmv_limits[i]]
        t2 = df[df["pmv_limit"] == pmv_limits[i + 1]]
        fig.add_trace(
            go.Scatter(
                x=t1["temp"],
                y=t1["rh"],
                fill=None,
                mode="lines",
                line=dict(color=colors[i]),
                name=f"{model} Lower Limit",
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=t2["temp"],
                y=t2["rh"],
                fill="tonexty",
                mode="lines",
                fillcolor=colors[i],
                line=dict(color=colors[i]),
                name=f"{model} Upper Limit",
                hoverinfo="skip",
            )
        )

    # Add scatter point for the current input
    fig.add_trace(
        go.Scatter(
            x=[t_db],
            y=[rh],
            mode="markers",
            marker=dict(color="red", size=8),
            name="Current Input",
            # hoverinfo="skip",
        )
    )
    # Add hover area to allow hover interaction

    # x_range_blue = np.linspace(t2["temp"].min(), t2["temp"].max(), 100)
    # y_range_blue = np.linspace(t2["rh"].min(), t2["rh"].max(), 100)
    # xx_blue, yy_blue = np.meshgrid(x_range_blue, y_range_blue)
    # fig.add_trace(
    #     go.Scatter(
    #         x=xx_blue.flatten(),
    #         y=yy_blue.flatten(),
    #         mode="markers",
    #         marker=dict(color="rgba(0,0,0,0)"),
    #         # hoverinfo="x+y",
    #         hoverinfo="none",
    #         name="Interactive Hover Area",
    #     )
    # )

    x_range = np.linspace(10, 40, 100)
    if units == UnitSystem.IP.value:  # The X-axis range of gridlines in the IP state
        x_range = np.linspace(50, 100, 100)
    y_range = np.linspace(0, 100, 100)
    xx, yy = np.meshgrid(x_range, y_range)
    fig.add_trace(
        go.Scatter(
            x=xx.flatten(),
            y=yy.flatten(),
            mode="markers",
            marker=dict(color="rgba(0,0,0,0)"),
            hoverinfo="none",
            name="Interactive Hover Area",
        )
    )

    if model == "ashrae" and function_selection == Functionalities.Compare.value:
        met_2, clo_2, tr_2, t_db_2, v_2, rh_2 = compare_get_inputs(inputs)
        clo_d_compare = clo_dynamic(clo_2, met_2)
        vr_compare = v_relative(v_2, met_2)

        df_compare = calculate_pmv_results(
            tr_2,
            vr_compare,
            met_2,
            clo_d_compare,
        )
        t1_compare = df_compare[df_compare["pmv_limit"] == pmv_limits[0]]
        t2_compare = df_compare[df_compare["pmv_limit"] == pmv_limits[1]]
        fig.add_trace(
            go.Scatter(
                x=t1_compare["temp"],
                y=t1_compare["rh"],
                fill=None,
                mode="lines",
                line=dict(color="rgba(30,70,100,0.5)"),
                name=f"{model} Compare Lower Limit",
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=t2_compare["temp"],
                y=t2_compare["rh"],
                fill="tonexty",
                mode="lines",
                fillcolor="rgba(30,70,100,0.5)",
                line=dict(color="rgba(30,70,100,0.5)"),
                name=f"{model} Compare Upper Limit",
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[t_db_2],
                y=[rh_2],
                mode="markers",
                marker=dict(color="blue", size=8),
                name="Compare Input",
                hoverinfo="skip",
            )
        )

    tdb = inputs[ElementsIDs.t_db_input.value]
    rh = inputs[ElementsIDs.rh_input.value]
    tr = inputs[ElementsIDs.t_r_input.value]
    psy_results = psy_ta_rh(tdb, rh)

    if units == UnitSystem.SI.value:
        annotation_text = (
            f"t<sub>db</sub>: {tdb:.1f} °C<br>"
            f"rh: {rh:.1f} %<br>"
            f"W<sub>a</sub>: {psy_results.hr*1000:.1f} g<sub>w</sub>/kg<sub>da</sub><br>"
            f"t<sub>wb</sub>: {psy_results.t_wb:.1f} °C<br>"
            f"t<sub>dp</sub>: {psy_results.t_dp:.1f} °C<br>"
            f"h: {psy_results.h / 1000:.1f} kJ/kg"
        )
        annotation_x = 32  # x coordinates in SI units
        annotation_y = 86  # Y-coordinate of relative humidity
    elif units == UnitSystem.IP.value:
        t_db = (t_db - 32) / 1.8
        psy_results = psy_ta_rh(t_db, rh)
        hr = psy_results.hr * 1000  # convert to g/kgda
        t_wb_value = psy_results.t_wb * 1.8 + 32
        t_dp_value = psy_results.t_dp * 1.8 + 32
        h = (psy_results.h / 1000) / 2.326  # convert to kj/kg
        annotation_text = (
            f"t<sub>db</sub>: {t_db * 1.8 + 32:.1f} °F<br>"
            f"RH: {rh:.1f} %<br>"
            f"W<sub>a</sub>: {hr:.1f} lb<sub>w</sub>/klb<sub>da</sub><br>"
            f"t<sub>wb</sub>: {t_wb_value:.1f} °F<br>"
            f"t<sub>dp</sub>: {t_dp_value:.1f} °F<br>"
            f"h: {h:.1f} btu/lb<br>"  # kJ/kg to btu/lb
        )
        annotation_x = 90  # x coordinates in IP units
        annotation_y = 86  # Y-coordinate of relative humidity (unchanged)

    fig.add_annotation(
        x=annotation_x,  # Dynamically adjust the x position of a comment
        y=annotation_y,  # The y coordinates remain the same
        xref="x",
        yref="y",
        text=annotation_text,
        showarrow=False,
        align="left",
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(0,0,0,0)",
        font=dict(size=14),
    )

    fig.update_layout(
        yaxis=dict(title="Relative Humidity [%]", range=[0, 100], dtick=10),
        xaxis=dict(
            title=(
                "Dry-bulb Temperature (°C)"
                if units == UnitSystem.SI.value
                else "Dry-bulb Temperature [°F]"
            ),
            range=[10, 36] if units == UnitSystem.SI.value else [50, 100],
            dtick=2 if units == UnitSystem.SI.value else 5,
        ),
        showlegend=False,
        plot_bgcolor="white",
        margin=dict(l=10, t=0),
        height=500,
        width=680,
        hovermode="closest",
        hoverdistance=5,
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0, 0, 0, 0.2)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0, 0, 0, 0.2)")

    return fig


def speed_temp_pmv(
    inputs: dict = None,
    model: str = "iso",
    units: str = "SI",
):
    results = []
    met, clo, tr, t_db, v, rh = get_inputs(inputs)
    clo_d = clo_dynamic(clo, met)
    vr = v_relative(v, met)
    pmv_limits = [-0.5, 0.5]
    clo_d = clo_dynamic(
        clo=inputs[ElementsIDs.clo_input.value], met=inputs[ElementsIDs.met_input.value]
    )
    if units == UnitSystem.SI.value:
        for pmv_limit in pmv_limits:
            for vr in np.arange(0.1, 0.9, 0.1):

                def function(x):
                    ce = cooling_effect(t_db, tr, vr, rh, met, clo_d, 0, units)

                    if vr <= 0.1 or ce == 0:
                        pmv_value = (
                            pmv(
                                x,
                                tr=inputs[ElementsIDs.t_r_input.value],
                                vr=vr,
                                rh=inputs[ElementsIDs.rh_input.value],
                                met=inputs[ElementsIDs.met_input.value],
                                clo=clo_d,
                                wme=0,
                                standard=model,
                                units=units,
                                limit_inputs=False,
                            )
                            - pmv_limit
                        )
                    else:
                        pmv_value = (
                            pmv(
                                x - ce,
                                tr=inputs[ElementsIDs.t_r_input.value] - ce,
                                vr=0.1,
                                rh=inputs[ElementsIDs.rh_input.value],
                                met=inputs[ElementsIDs.met_input.value],
                                clo=clo_d,
                                wme=0,
                                standard=model,
                                units=units,
                                limit_inputs=False,
                            )
                            - pmv_limit
                        )
                    return pmv_value

                try:
                    temp = optimize.brentq(function, 10, 40)
                    results.append(
                        {
                            "vr": vr,
                            "temp": temp,
                            "pmv_limit": pmv_limit,
                        }
                    )

                except ValueError:
                    continue
    else:
        for pmv_limit in pmv_limits:
            for vr in np.arange(0.5, 3, 0.1):

                def function(x):
                    ce = cooling_effect(t_db, tr, vr, rh, met, clo_d, 0, units)
                    if vr <= 0.33 or ce == 0:
                        pmv_value = pmv(
                            x,
                            tr=inputs[ElementsIDs.t_r_input.value],
                            vr=vr,
                            rh=inputs[ElementsIDs.rh_input.value],
                            met=inputs[ElementsIDs.met_input.value],
                            clo=clo_d,
                            wme=0,
                            standard=model,
                            units=units,
                            limit_inputs=False,
                        )
                        -pmv_limit
                    else:
                        pmv_value = (
                            pmv(
                                x - ce,
                                tr=inputs[ElementsIDs.t_r_input.value] - ce,
                                vr=0.1,
                                rh=inputs[ElementsIDs.rh_input.value],
                                met=inputs[ElementsIDs.met_input.value],
                                clo=clo_d,
                                wme=0,
                                standard=model,
                                units=units,
                                limit_inputs=False,
                            )
                            - pmv_limit
                        )
                    return pmv_value

                try:
                    temp = optimize.brentq(function, 10, 100)
                    results.append(
                        {
                            "vr": vr,
                            "temp": temp,
                            "pmv_limit": pmv_limit,
                        }
                    )

                except ValueError:
                    continue

    df = pd.DataFrame(results)
    fig = go.Figure()
    # Define trace1
    fig.add_trace(
        go.Scatter(
            x=df[df["pmv_limit"] == pmv_limits[0]]["temp"],
            y=df[df["pmv_limit"] == pmv_limits[0]]["vr"],
            mode="lines",
            name=f"PMV {pmv_limits[0]}",
            showlegend=False,
            line=dict(color="rgba(0,0,0,0)"),
        )
    )
    # Define trace2
    fig.add_trace(
        go.Scatter(
            x=df[df["pmv_limit"] == pmv_limits[1]]["temp"],
            y=df[df["pmv_limit"] == pmv_limits[1]]["vr"],
            mode="lines",
            fill="tonextx",
            fillcolor="rgba(59, 189, 237, 0.7)",
            name=f"PMV {pmv_limits[1]}",
            showlegend=False,
            line=dict(color="rgba(0,0,0,0)"),
        )
    )

    # Define input point
    fig.add_trace(
        go.Scatter(
            x=[inputs[ElementsIDs.t_db_input.value]],
            y=[inputs[ElementsIDs.v_input.value]],
            mode="markers",
            marker=dict(color="red"),
            name="Input",
            showlegend=False,
        )
    )

    fig.update_layout(
        xaxis_title=(
            "Operative Temperature [°C]"
            if units == UnitSystem.SI.value
            else "Operative Temperature [°F]"
        ),
        # x title
        yaxis_title=(
            "Relative Air Speed [m/s]"
            if units == UnitSystem.SI.value
            else "Relative Air Speed [fp/s]"
        ),
        # y title
        template="plotly_white",
        margin=dict(l=10, t=0),
        height=500,
        width=680,
        xaxis=dict(
            range=[20, 40] if units == UnitSystem.SI.value else [65, 100],  # x range
            tickmode="linear",
            tick0=20 if units == UnitSystem.SI.value else 65,
            dtick=2 if units == UnitSystem.SI.value else 5,
            linecolor="lightgrey",
            gridcolor="lightgray",
            showgrid=True,
            mirror=True,
        ),
        yaxis=dict(
            range=[0.0, 1.2] if units == UnitSystem.SI.value else [0, 4],  # y range
            tickmode="linear",
            tick0=0.0,
            dtick=0.1 if units == UnitSystem.SI.value else 0.5,
            linecolor="lightgrey",
            gridcolor="lightgray",
            showgrid=True,
            mirror=True,
        ),
    )

    return fig
