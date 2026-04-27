import importlib.metadata
import pathlib
import anywidget
import narwhals as nw
import traitlets
from process_tree_widget.timefilter import TimeFilterWidget as TimeFilterWidget
from process_tree_widget.tree import ProcessTree as ProcessTree
from process_tree_widget.utils import prepare_events as prepare_events

__all__ = ["ProcessTreeWidget", "TimeFilterWidget", "ProcessTree", "prepare_events"]

try:
    __version__ = importlib.metadata.version("process_tree_widget")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


class ProcessTreeWidget(anywidget.AnyWidget):
    _esm = pathlib.Path(__file__).parent / "static" / "process-tree" / "widget.js"

    selected_event: traitlets.Dict = traitlets.Dict({}).tag(sync=True)
    events: traitlets.List = traitlets.List([]).tag(sync=True)
    _start_date = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    _end_date = traitlets.Unicode(None, allow_none=True).tag(sync=True)

    def __init__(
        self,
        events,
        start_date: str | None = None,
        end_date: str | None = None,
        source: str | None = None,
        impute_date_times: bool = True,
        **kwargs,
    ):
        """Initialize the widget.

        ``events`` can be one of:

        - An ibis table + ``source`` ("mde" or "volatility"): normalized via
          ``prepare_events`` before tree construction.
        - Any narwhals-compatible dataframe (pandas, polars, …) already in ASIM
          format (output of ``prepare_events``): converted directly.
        - A pre-built dependentree ``list[dict]``: used as-is.

        ``start_date`` / ``end_date`` are ISO-format strings.  Pass
        ``tf.value["start_date"]`` / ``tf.value["end_date"]`` directly from a
        :class:`~process_tree_widget.timefilter.TimeFilterWidget` to wire
        time-based filtering.

        ``impute_date_times`` controls whether null creation times are filled
        with the earliest non-null timestamp in the dataset (default: True).
        Imputed nodes carry ``ImputedCreationTime=True`` for downstream styling.
        """
        super().__init__(**kwargs)

        if source is not None:
            prepared = prepare_events(
                events, source, impute_date_times=impute_date_times
            )
            if isinstance(prepared, nw.LazyFrame):
                prepared = prepared.collect()
            raw_list = prepared.to_arrow().to_pylist()
        elif isinstance(events, list):
            raw_list = events
        else:
            prepared = nw.from_native(events)
            raw_list = prepared.to_arrow().to_pylist()

        tree = ProcessTree(raw_list)
        self.events = tree.create_dependentree_format()

        # Derive the default time window from real (non-synthetic) nodes so the
        # timefilter brush covers the actual data range on first render.
        # Synthetic nodes carry epoch timestamps and would skew the window to 1970.
        from datetime import datetime
        _epoch = datetime(1970, 1, 1)
        if start_date is None or end_date is None:
            times = sorted(
                e["TargetProcessCreationTime"]
                for e in self.events
                if e.get("TargetProcessCreationTime")
                and e["TargetProcessCreationTime"] != _epoch
                and not e.get("Synthetic")
            )
            if times:
                if start_date is None:
                    t = times[0]
                    start_date = t.isoformat() if hasattr(t, "isoformat") else str(t)
                if end_date is None:
                    t = times[-1]
                    end_date = t.isoformat() if hasattr(t, "isoformat") else str(t)

        self._start_date = start_date
        self._end_date = end_date

    @property
    def date_range(self) -> dict:
        return {"start_date": self._start_date, "end_date": self._end_date}

    @date_range.setter
    def date_range(self, value: dict) -> None:
        self._start_date = value.get("start_date")
        self._end_date = value.get("end_date")
