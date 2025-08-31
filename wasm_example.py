# /// script
# [tool.marimo.display]
# theme = "light"
# ///

import marimo

__generated_with = "0.11.2"
app = marimo.App(width="medium", app_title="Demo")


@app.cell(hide_code=True)
def _():
    import sys
    import json
    import marimo as mo

    from datetime import datetime
    return datetime, json, mo, sys


@app.cell(hide_code=True)
def _(sys):
    is_wasm = "pyodide" in sys.modules
    return (is_wasm,)


@app.cell(hide_code=True)
async def _(is_wasm):
    if is_wasm:
        import js
        import micropip

        from urllib.parse import urlparse

        current_url = js.location.href
        parsed_url = urlparse(current_url)

        url = f"{parsed_url.scheme}://{parsed_url.netloc}/public/process_tree_widget-0.0.1-py2.py3-none-any.whl"

        await micropip.install(url)
        await micropip.install("ibis-framework[duckdb]")

    import ibis
    from ibis import _

    from process_tree_widget.tree import Process, ProcessTree
    from process_tree_widget import ProcessTree
    return (
        Process,
        ProcessTree,
        ProcessTree,
        current_url,
        ibis,
        js,
        micropip,
        parsed_url,
        url,
        urlparse,
    )


@app.cell(hide_code=True)
def _(ibis, is_wasm, mo):
    def read_device_process_events():
        path_to_data = mo.notebook_location() / "public" / "demo.parquet"

        if is_wasm:
            import requests
            import pyarrow as pa
            import pyarrow.parquet as pq

            table = pq.read_table(pa.py_buffer(requests.get(path_to_data).content))
            events = ibis.memtable(table)
        else:
            events = ibis.read_parquet(path_to_data)

        return events
    return (read_device_process_events,)


@app.cell
def _(read_device_process_events):
    events = read_device_process_events()
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
        selected_process_creation_events
        .filter(
            _.ActingProcessId == widget.process_id
        )
        .select(
            _.Timestamp,
            _.ActionType,
            _.FileName, 
            _.AccountName
        )
    ).execute()
    return


if __name__ == "__main__":
    app.run()
