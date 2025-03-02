# /// script
# [tool.marimo.display]
# theme = "light"
# ///

import marimo

__generated_with = "0.11.13"
app = marimo.App(width="medium", app_title="Demo")


@app.cell
def _():
    import sys
    import ibis
    import json
    import marimo as mo

    from ibis import _
    from datetime import datetime
    return datetime, ibis, json, mo, sys


@app.cell
def _():
    from process_tree_widget import ProcessTreeWidget
    from process_tree_widget.tree import Process, ProcessTree
    return Process, ProcessTree, ProcessTreeWidget


@app.cell
def _(ibis):
    events = ibis.read_parquet("./public/demo.parquet")
    return (events,)


@app.cell
def _(events):
    process_creation_events = (
        events.filter(_.ActionType == "ProcessCreated")
        .distinct(on=["ReportId", "Timestamp", "DeviceName"], keep="first")
        .order_by(_.Timestamp)
        .mutate(
            TargetProcessId=_.ProcessId,
            TargetProcessFilename=_.FileName,
            TargetProcessCreationTime=_.ProcessCreationTime,
            ActingProcessId=_.InitiatingProcessId,
            ActingProcessFilename=_.InitiatingProcessFileName,
            ActingProcessCreationTime=_.InitiatingProcessCreationTime,
            ParentProcessId=_.InitiatingProcessParentId,
            ParentProcessFilename=_.InitiatingProcessParentFileName,
            ParentProcessCreationTime=_.InitiatingProcessParentCreationTime,
        )
    )
    return (process_creation_events,)


@app.cell(hide_code=True)
def _(mo, process_creation_events):
    series = process_creation_events.select(_.Timestamp).execute()["Timestamp"]
    start_range = mo.ui.datetime.from_series(
        label="Start",
        series=series,
        start=min(series),
        stop=max(series),
        value=min(series),
    )

    end_range = mo.ui.datetime.from_series(
        label="End",
        series=series,
        start=min(series),
        stop=max(series),
        value=max(series),
    )

    mo.hstack([start_range, end_range], justify="start", align="start")
    return end_range, series, start_range


@app.cell
def _(ProcessTree, end_range, process_creation_events, start_range):
    selected_process_creation_events = process_creation_events.filter(
        _.Timestamp.between(start_range.value, end_range.value)
    )

    # convert the dataframe to a python list of dicts
    _events = selected_process_creation_events.to_pyarrow().to_pylist()
    tree = ProcessTree(_events)
    return selected_process_creation_events, tree


@app.cell
def _(tree):
    # now we need the format required by the dependentree library
    dependentree_format = tree.create_dependentree_format()
    return (dependentree_format,)


@app.cell
def _(ProcessTreeWidget, dependentree_format, mo):
    widget = mo.ui.anywidget(ProcessTreeWidget(events=dependentree_format))
    widget
    return (widget,)


@app.cell
def _(selected_process_creation_events, widget):
    # this query displays the child processes for the node that is selected in the widget above
    (
        selected_process_creation_events.filter(
            _.ActingProcessId == widget.process_id
        ).select(_.Timestamp, _.ActionType, _.FileName, _.AccountName)
    ).execute()
    return


if __name__ == "__main__":
    app.run()
