import marimo

__generated_with = "0.23.3"
app = marimo.App(
    width="medium",
    layout_file="layouts/demo_mde.grid.json",
    sql_output="polars",
)


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import ibis
    from process_tree_widget import ProcessTreeWidget
    from process_tree_widget.timefilter import TimeFilterWidget

    return ProcessTreeWidget, TimeFilterWidget, ibis, mo


@app.cell(hide_code=True)
def _(ibis, mo):
    mde = ibis.read_parquet("data.parquet")
    mo.ui.table(mde, selection=None)
    return (mde,)


@app.cell(hide_code=True)
def _(ProcessTreeWidget, mde, mo):
    widget = mo.ui.anywidget(
        ProcessTreeWidget(events=mde, source="mde", custom_actions=[{"id": "load_events", "label": "Load events"}])
    )
    widget
    return (widget,)


@app.cell
def _(TimeFilterWidget, mde, mo):
    tf = mo.ui.anywidget(TimeFilterWidget(mde, source="mde"))
    tf
    return


@app.cell
def _(widget):
    widget.value['selected_event']
    return


@app.cell
def _(mo, widget):
    triggered = widget.value.get("triggered_action", {})
    mo.stop(not triggered, mo.callout(mo.md("Right-click a node and choose **Load events**"), kind="neutral"))
    mo.md(
        f"**Action fired:** `{triggered.get('id')}` on **{triggered.get('ProcessName')}** (PID {triggered.get('ProcessId')})"
    )
    return


if __name__ == "__main__":
    app.run()
