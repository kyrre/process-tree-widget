import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium", sql_output="polars")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import ibis
    from process_tree_widget import ProcessTreeWidget
    from process_tree_widget.timefilter import TimeFilterWidget

    return ProcessTreeWidget, TimeFilterWidget, ibis, mo


@app.cell(hide_code=True)
def _(ibis, mo):
    vol = ibis.read_parquet("data/pstree.parquet")
    mo.ui.table(vol, selection=None)
    return (vol,)


@app.cell(hide_code=True)
def _(ProcessTreeWidget, mo, vol):
    widget = mo.ui.anywidget(ProcessTreeWidget(events=vol, source="volatility"))
    widget
    return (widget,)


@app.cell(hide_code=True)
def _(TimeFilterWidget, mo, vol):
    tf = mo.ui.anywidget(TimeFilterWidget(vol, source="volatility"))
    tf
    return (tf,)


@app.cell(hide_code=True)
def _(tf, widget):
    widget.widget.date_range = tf.value
    return


if __name__ == "__main__":
    app.run()
