# /// script
# [tool.marimo.display]
# theme = "light"
# ///

import marimo

__generated_with = "0.15.0"
app = marimo.App(width="medium", app_title="Demo")

with app.setup:
    import sys
    import ibis
    import json
    import marimo as mo

    from ibis import _
    from datetime import datetime

    from process_tree_widget import ProcessTreeWidget, TimeFilterWidget
    from process_tree_widget.tree import Process, ProcessTree
    from utils import prepare_mde_data, prepare_volatility_data

    ibis.options.interactive = True


@app.cell
def _():
    pstree = ibis.read_parquet("pstree.parquet")
    return (pstree,)


@app.cell
def _(pstree):
    pstree.schema()
    return


@app.cell
def _():
    return


@app.cell
def _(pstree):
    pstree.schema()
    return


@app.cell
def _():
    events = ibis.read_parquet("./public/demo.parquet")
    return


@app.cell
def _():
    # process_creation_events = prepare_mde_data(events)
    # process_creation_events
    return


@app.cell
def _():
    import ibis.selectors as s
    return


@app.cell
def _(pstree):
    process_creation_events = (
        prepare_volatility_data(pstree)
            .mutate(Timestamp = _.CreateTime)
            .order_by(_.CreateTime)
            .filter(~_.ActingProcessFilename.isnull())
    )

    process_creation_events
    return (process_creation_events,)


@app.cell
def _():
    return


@app.cell
def _(process_creation_events):

    # convert the dataframe to a python list of dicts
    _events = process_creation_events.to_pyarrow().to_pylist()
    tree = ProcessTree(_events)
    return (tree,)


@app.cell
def _(tree):
    # now we need the format required by the dependentree library
    dependentree_format = tree.create_dependentree_format()
    return (dependentree_format,)


@app.cell
def _(process_creation_events):
    process_creation_events
    return


@app.cell
def _(dependentree_format):
    u = mo.ui.anywidget(TimeFilterWidget(events=dependentree_format))
    u
    return (u,)


@app.cell
def _(u):
    [u.start_date, u.end_date]
    return


@app.cell
def _(dependentree_format, u):
    widget = mo.ui.anywidget(
        ProcessTreeWidget(
            events=dependentree_format, 
            start_date=u.start_date,
            end_date=u.end_date
        )
    )
    widget
    return (widget,)


@app.cell(hide_code=True)
def _(process_creation_events, widget):
    # this query displays the child processes for the node that is selected in the widget above
    (
        process_creation_events.filter(
            _.ActingProcessId == widget.process_id
        )
    ).execute()
    return


@app.cell
def _():
    return


@app.cell
def _(process_creation_events):
    process_creation_events
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
