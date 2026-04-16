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
    pstree = ibis.read_parquet("public/demo.parquet")
    mo.ui.table(pstree, selection=None)
    return (pstree,)


@app.cell(hide_code=True)
def _(ProcessTreeWidget, mo, pstree):
    widget = mo.ui.anywidget(ProcessTreeWidget(events=pstree, source="mde"))
    widget
    return (widget,)


@app.cell
def _(TimeFilterWidget, mo, pstree):
    tf = mo.ui.anywidget(TimeFilterWidget(pstree, source="mde"))
    tf
    return (tf,)


@app.cell
def _(tf, widget):
    widget.widget.date_range = tf.value
    return


if __name__ == "__main__":
    app.run()
