import pathlib

import anywidget
import narwhals as nw
import traitlets
from process_tree_widget.utils import prepare_events


class TimeFilterWidget(anywidget.AnyWidget):
    _esm = pathlib.Path(__file__).parent / "static" / "timefilter" / "widget.js"
    _css = pathlib.Path(__file__).parent / "static" / "timefilter" / "widget.css"

    events = traitlets.List([]).tag(sync=True)
    start_date = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    end_date = traitlets.Unicode(None, allow_none=True).tag(sync=True)

    def __init__(self, events: object, source: str | None = None, **kwargs: object) -> None:
        """Create a time-filter bar chart widget.

        Args:
            events: Any narwhals-compatible dataframe (pandas, polars, ibis, …) that has
                a ``TargetProcessCreationTime`` column, or a raw table with ``source``
                set to "mde" or "volatility" to normalize via ``prepare_events`` first.
            source: If provided, ``events`` is passed through ``prepare_events(events, source)``
                before use.
        """
        super().__init__(**kwargs)
        df = prepare_events(events, source) if source is not None else events
        frame = nw.from_native(df)
        nw_frame = frame.collect() if isinstance(frame, nw.LazyFrame) else frame
        rows = nw_frame.select("TargetProcessCreationTime").rows(named=True)
        self.events = [
            {"TargetProcessCreationTime": _to_iso(row["TargetProcessCreationTime"])}
            for row in rows
        ]


def _to_iso(value: object) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
