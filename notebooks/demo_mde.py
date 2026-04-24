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
    mde = ibis.read_parquet("public/demo.parquet")
    mo.ui.table(mde, selection=None)
    return (mde,)


@app.cell(hide_code=True)
def _(ProcessTreeWidget, mde, mo):
    widget = mo.ui.anywidget(ProcessTreeWidget(events=mde, source="mde"))
    widget
    return (widget,)


@app.cell(hide_code=True)
def _(TimeFilterWidget, mde, mo):
    tf = mo.ui.anywidget(TimeFilterWidget(mde, source="mde"))
    tf
    return (tf,)


@app.cell(hide_code=True)
def _(tf, widget):
    widget.widget.date_range = tf.value
    return


if __name__ == "__main__":
    app.run()
