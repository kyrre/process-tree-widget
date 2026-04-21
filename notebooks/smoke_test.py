import marimo

__generated_with = "0.23.1"
app = marimo.App(width="full", sql_output="polars")


@app.cell
def _():
    import marimo as mo
    import ibis
    import pathlib
    from process_tree_widget import ProcessTreeWidget, TimeFilterWidget

    data_dir = pathlib.Path(__file__).parent.parent / "public"
    return ProcessTreeWidget, TimeFilterWidget, data_dir, ibis, mo


@app.cell(hide_code=True)
def _(data_dir, ibis, mo):
    mde_df = ibis.read_parquet(str(data_dir / "demo.parquet"))
    mo.md(f"**MDE rows:** {mde_df.count().execute()}")
    return (mde_df,)


@app.cell(hide_code=True)
def _(ProcessTreeWidget, mde_df, mo):
    mde_widget = ProcessTreeWidget(mde_df, source="mde")
    mo.ui.anywidget(mde_widget)
    return (mde_widget,)


@app.cell(hide_code=True)
def _(data_dir, ibis, mo):
    vol_df = ibis.read_parquet(str(data_dir / "pstree.parquet"))
    mo.md(f"**Volatility rows:** {vol_df.count().execute()}")
    return (vol_df,)


@app.cell(hide_code=True)
def _(TimeFilterWidget, mo, vol_df):
    vol_tf = mo.ui.anywidget(TimeFilterWidget(vol_df, source="volatility"))
    vol_tf
    return (vol_tf,)


@app.cell(hide_code=True)
def _(ProcessTreeWidget, mo, vol_df, vol_tf):
    vol_widget = ProcessTreeWidget(
        vol_df,
        source="volatility",
        start_date=vol_tf.value.get("start_date"),
        end_date=vol_tf.value.get("end_date"),
    )
    mo.ui.anywidget(vol_widget)
    return (vol_widget,)


@app.cell(hide_code=True)
def _(mde_widget, mo, vol_widget):
    assert len(mde_widget.events) > 0, "MDE widget has no events"
    assert mde_widget._start_date is not None, "MDE widget missing start date"
    assert len(vol_widget.events) > 0, "Volatility widget has no events"
    assert vol_widget._start_date is not None, "Volatility widget missing start date"
    mo.callout(mo.md("All smoke checks passed ✓"), kind="success")
    return


if __name__ == "__main__":
    app.run()
