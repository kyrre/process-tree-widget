import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import ibis
    import pendulum
    from process_tree_widget import ProcessTreeWidget, TimeFilterWidget

    mo, ibis, pendulum, ProcessTreeWidget, TimeFilterWidget
    return ProcessTreeWidget, TimeFilterWidget, ibis, mo, pendulum


@app.cell(hide_code=True)
def _(mo, pendulum):
    query_params = mo.query_params()
    _edit = mo.app_meta().mode == "edit"

    process_id = query_params.get("process_id", "10556" if _edit else None)
    _ts_raw = query_params.get("timestamp", "2026-04-22T12:20:40.575534" if _edit else None)

    anchor_time = pendulum.parse(_ts_raw).naive() if _ts_raw else None

    query_params, process_id, anchor_time
    return anchor_time, process_id


@app.cell
def _(ProcessTreeWidget, TimeFilterWidget, ibis, mo):
    table = ibis.read_parquet("data.parquet")
    widget = mo.ui.anywidget(ProcessTreeWidget(table, source="mde"))
    tf = mo.ui.anywidget(TimeFilterWidget(table, source="mde"))
    table, tf, widget
    return table, tf, widget


@app.cell
def _(mo, tf, widget):
    widget._start_date = tf.value["start_date"]
    widget._end_date = tf.value["end_date"]
    mo.vstack([tf, widget])
    return


@app.cell(hide_code=True)
def _(ProcessTreeWidget, TimeFilterWidget, anchor_time, mo, process_id, table):
    _node = f"{process_id}|{anchor_time}" if process_id and anchor_time else None

    focused_widget = mo.ui.anywidget(ProcessTreeWidget(table, source="mde", initial_node=_node))
    tf2 = mo.ui.anywidget(TimeFilterWidget(table, source="mde"))
    focused_widget, tf2
    return focused_widget, tf2


@app.cell
def _(focused_widget, mo, tf2):
    focused_widget._start_date = tf2.value["start_date"]
    focused_widget._end_date = tf2.value["end_date"]
    mo.vstack([tf2, focused_widget])
    return


if __name__ == "__main__":
    app.run()
