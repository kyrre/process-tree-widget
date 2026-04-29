import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import ibis
    from process_tree_widget import ProcessTreeWidget, TimeFilterWidget

    table = ibis.read_parquet("data.parquet")
    from datetime import datetime
    widget = mo.ui.anywidget(ProcessTreeWidget(table, source="mde", initial_node=(20412, datetime(2026, 4, 24, 6, 54, 4, 103188))))
    tf = mo.ui.anywidget(TimeFilterWidget(table, source="mde"))
    return mo, tf, widget


@app.cell
def _(mo, tf, widget):
    widget._start_date = tf.value["start_date"]
    widget._end_date = tf.value["end_date"]
    mo.vstack([tf, widget])
    return


@app.cell
def _(widget):
    widget
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
