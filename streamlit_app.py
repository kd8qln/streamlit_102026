from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st

from calculator import OPERATIONS
from workbench import (
    TABLE_DEFINITIONS,
    calculate_batch,
    calculate_experiment_summary,
    calculate_formula,
    records_to_csv,
)


SPLASH_IMAGE = Path(__file__).resolve().parent / "splash.png"


def _as_records(value: Any) -> list[dict[str, Any]]:
    if hasattr(value, "to_dict"):
        return value.to_dict(orient="records")
    return [dict(row) for row in value]


def _initialize_session() -> None:
    defaults = {
        "experiment_name": "",
        "experiment_operator": "",
        "experiment_date": date.today(),
        "experiment_notes": "",
        "experiment_rows": [{"Measurement": "", "Value": None, "Unit": ""}],
        "experiment_summary": None,
        "formula_name": "",
        "formula_batch_size": 100.0,
        "formula_rows": [{"Component": "", "Percent": None}],
        "formula_results": None,
        "calculator_rows": [
            {"Left": None, "Operation": "+", "Right": None}
            for _ in range(5)
        ],
        "calculator_results": [],
        "table_rows": {
            name: [{column["name"]: None for column in columns}]
            for name, columns in TABLE_DEFINITIONS.items()
        },
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _download_csv(
    label: str,
    filename: str,
    rows: list[dict[str, Any]],
    fields: list[str],
    key: str,
) -> None:
    st.download_button(
        label,
        data=records_to_csv(rows, fields),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def _render_splashscreen() -> None:
    st.title("Voyager Workbench")
    if SPLASH_IMAGE.is_file():
        st.image(str(SPLASH_IMAGE), width="stretch")
    st.write("Experiment and formula development workspace")
    st.caption("Choose a workspace from the navigation menu to begin.")


def _render_experiment_development() -> None:
    st.title("Experiment Development")
    st.text_input("Experiment", key="experiment_name")
    left, right = st.columns(2)
    with left:
        st.text_input("Operator", key="experiment_operator")
    with right:
        st.date_input("Date", key="experiment_date")
    st.text_area("Notes", key="experiment_notes", height=80)

    st.subheader("Measurements")
    edited = st.data_editor(
        st.session_state["experiment_rows"],
        key="experiment_editor",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "Measurement": st.column_config.TextColumn("Measurement"),
            "Value": st.column_config.NumberColumn("Value", format="%.8g"),
            "Unit": st.column_config.TextColumn("Unit"),
        },
    )
    st.session_state["experiment_rows"] = _as_records(edited)

    if st.button("Calculate summary", type="primary", key="experiment_calculate"):
        try:
            summary = calculate_experiment_summary(st.session_state["experiment_rows"])
            st.session_state["experiment_summary"] = summary
        except ValueError as error:
            st.error(str(error))

    summary = st.session_state["experiment_summary"]
    if summary:
        st.subheader("Results")
        metrics = st.columns(4)
        for column, (label, value) in zip(metrics, summary.items()):
            column.metric(label, f"{value:.6g}" if isinstance(value, float) else value)

    metadata = {
        "Experiment": st.session_state["experiment_name"],
        "Operator": st.session_state["experiment_operator"],
        "Date": st.session_state["experiment_date"].isoformat(),
        "Notes": st.session_state["experiment_notes"],
    }
    measurements = st.session_state["experiment_rows"] or [{}]
    summary = summary or {}
    export_rows = [
        {**metadata, **row, **summary} for row in measurements
    ]
    fields = [
        "Experiment", "Operator", "Date", "Notes", "Measurement", "Value", "Unit",
        "Count", "Mean", "Minimum", "Maximum",
    ]
    _download_csv(
        "Download experiment CSV",
        "experiment.csv",
        export_rows,
        fields,
        "experiment_csv",
    )


def _render_formula_development() -> None:
    st.title("Formula Development")
    st.text_input("Formula", key="formula_name")
    st.number_input(
        "Batch size",
        min_value=0.000001,
        format="%.8g",
        key="formula_batch_size",
    )
    st.subheader("Components")
    edited = st.data_editor(
        st.session_state["formula_rows"],
        key="formula_editor",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "Component": st.column_config.TextColumn("Component"),
            "Percent": st.column_config.NumberColumn(
                "Percent", min_value=0.0, format="%.8g"
            ),
        },
    )
    st.session_state["formula_rows"] = _as_records(edited)

    if st.button("Calculate formula", type="primary", key="formula_calculate"):
        try:
            total, results = calculate_formula(
                st.session_state["formula_batch_size"],
                st.session_state["formula_rows"],
            )
            st.session_state["formula_results"] = {
                "Total Percent": total,
                "Components": results,
            }
        except ValueError as error:
            st.error(str(error))

    formula_results = st.session_state["formula_results"]
    if formula_results:
        total = formula_results["Total Percent"]
        st.metric("Total percentage", f"{total:.6g}%")
        if abs(total - 100) > 1e-6:
            st.warning("The component percentages do not total 100%.")
        st.dataframe(
            formula_results["Components"], hide_index=True, width="stretch"
        )

    formula_name = st.session_state["formula_name"]
    formula_rows = formula_results["Components"] if formula_results else st.session_state["formula_rows"]
    export_rows = [
        {
            "Formula": formula_name,
            "Batch Size": st.session_state["formula_batch_size"],
            "Total Percent": formula_results["Total Percent"] if formula_results else None,
            **row,
        }
        for row in formula_rows
    ]
    _download_csv(
        "Download formula CSV",
        "formula.csv",
        export_rows,
        ["Formula", "Batch Size", "Total Percent", "Component", "Percent", "Batch Amount"],
        "formula_csv",
    )


def _render_calculators() -> None:
    st.title("Calculators")
    st.subheader("Batch arithmetic")
    edited = st.data_editor(
        st.session_state["calculator_rows"],
        key="calculator_editor",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "Left": st.column_config.NumberColumn("Left", format="%.8g"),
            "Operation": st.column_config.SelectboxColumn(
                "Operation", options=list(OPERATIONS), required=True
            ),
            "Right": st.column_config.NumberColumn("Right", format="%.8g"),
        },
    )
    st.session_state["calculator_rows"] = _as_records(edited)

    if st.button("Calculate rows", type="primary", key="batch_calculate"):
        st.session_state["calculator_results"] = calculate_batch(
            st.session_state["calculator_rows"]
        )

    results = st.session_state["calculator_results"]
    if results:
        st.dataframe(results, hide_index=True, width="stretch")
    _download_csv(
        "Download calculations CSV",
        "calculations.csv",
        results,
        ["Row", "Left", "Operation", "Right", "Result", "Status"],
        "calculations_csv",
    )


def _render_table_maintenance() -> None:
    st.title("Table Maintenance")
    table_name = st.selectbox("In-session table", options=list(TABLE_DEFINITIONS))
    fields = TABLE_DEFINITIONS[table_name]
    column_config = {}
    for field in fields:
        name = field["name"]
        if field["type"] == "number":
            column_config[name] = st.column_config.NumberColumn(name, format="%.8g")
        elif field["type"] == "checkbox":
            column_config[name] = st.column_config.CheckboxColumn(name)
        else:
            column_config[name] = st.column_config.TextColumn(name)

    edited = st.data_editor(
        st.session_state["table_rows"][table_name],
        key=f"table_editor_{table_name}",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config=column_config,
    )
    st.session_state["table_rows"][table_name] = _as_records(edited)
    _download_csv(
        "Download table CSV",
        f"{table_name.lower().replace(' ', '_')}.csv",
        st.session_state["table_rows"][table_name],
        [field["name"] for field in fields],
        f"table_csv_{table_name}",
    )


st.set_page_config(page_title="Voyager Workbench", page_icon="V", layout="wide")
_initialize_session()

screens = [
    "Splashscreen",
    "Experiment Development",
    "Formula Development",
    "Calculators",
    "Table Maintenance",
]
selected_screen = st.sidebar.radio("Workspace", screens, key="active_screen")
st.sidebar.caption("Working data is held for this session.")

renderers = {
    "Splashscreen": _render_splashscreen,
    "Experiment Development": _render_experiment_development,
    "Formula Development": _render_formula_development,
    "Calculators": _render_calculators,
    "Table Maintenance": _render_table_maintenance,
}
renderers[selected_screen]()