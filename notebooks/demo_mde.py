import marimo

__generated_with = "0.23.3"
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
    return


@app.cell
def _(TimeFilterWidget, mde, mo):
    tf = mo.ui.anywidget(TimeFilterWidget(mde, source="mde"))
    tf
    return (tf,)


@app.cell
def _(tf):
    tf.start_date
    return


@app.cell
def _(tf):
    tf.start_date
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
