import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import ibis
    from process_tree_widget import ProcessTreeWidget, TimeFilterWidget

    ibis.options.interactive = True
    return ProcessTreeWidget, TimeFilterWidget, ibis, mo


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
def _(ProcessTreeWidget, TimeFilterWidget, mo, table):
    import ibis as _ibis

    _t = _ibis.read_parquet("data.parquet")
    _row = _t.filter(_t.FileName.lower() == "code.exe").order_by("ProcessCreationTime").limit(1).execute().iloc[0]
    _node = f"{_row['ProcessId']}|{_row['ProcessCreationTime']}"

    focused_widget = mo.ui.anywidget(ProcessTreeWidget(table, source="mde", initial_node=_node))
    tf2 = mo.ui.anywidget(TimeFilterWidget(table, source="mde"))
    focused_widget._start_date = tf2.value["start_date"]
    focused_widget._end_date = tf2.value["end_date"]
    mo.vstack([tf2, focused_widget])
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
