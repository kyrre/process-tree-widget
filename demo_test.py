import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium", sql_output="polars")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import ibis
    from process_tree_widget import ProcessTreeWidget

    return ProcessTreeWidget, ibis, mo


@app.cell(hide_code=True)
def _(ibis, mo):
    pstree = ibis.read_parquet("pstree.parquet")
    mo.ui.table(pstree.head(5), selection=None)
    return (pstree,)


@app.cell(hide_code=True)
def _(ProcessTreeWidget, mo, pstree, tf):
    widget = (
        mo.ui.anywidget(ProcessTreeWidget(
            events=pstree,
            source="volatility",
            start_date=tf.value["start_date"],
            end_date=tf.value["end_date"],
        ))
    )
    widget
    return


@app.cell(hide_code=True)
def _(mo, pstree):
    import importlib, process_tree_widget.timefilter as _tf_mod

    importlib.reload(_tf_mod)
    from process_tree_widget.timefilter import TimeFilterWidget
    from process_tree_widget.utils import prepare_events

    normalized_df = prepare_events(pstree, "volatility").to_pandas()
    tf = mo.ui.anywidget(TimeFilterWidget(normalized_df))
    tf
    return (tf,)


@app.cell
def _(tf):
    tf.value
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
