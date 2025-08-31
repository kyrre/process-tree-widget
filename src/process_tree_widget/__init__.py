import importlib.metadata
import pathlib

import anywidget
import traitlets
from process_tree_widget.tree import ProcessTree
from process_tree_widget.utils import prepare_events

try:
    __version__ = importlib.metadata.version("process_tree_widget")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


class ProcessTreeWidget(anywidget.AnyWidget):
    _esm = pathlib.Path(__file__).parent / "static" / "widget.js"

    process_id = traitlets.Int(-1).tag(sync=True)
    events: traitlets.List = traitlets.List([]).tag(sync=True)
    _start_date = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    _end_date = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    show_timefilter = traitlets.Bool(True).tag(sync=True)

    def __init__(
        self,
        events,
        start_date=None,
        end_date=None,
        source: str | None = None,
        show_timefilter: bool = True,
        **kwargs,
    ):
        """Initialize the widget.

        events can be either:
        - A pre-built dependentree list[dict]
        - An ibis table (detected via to_pyarrow()) with process creation events.

        If an ibis table is provided and `source` is supplied ("mde" or "volatility"),
        the table is first normalized via utils.prepare_events (if available) before
        constructing the dependentree format expected by the frontend.
        """
        super().__init__(**kwargs)

        raw_list = prepare_events(events, source).to_pyarrow().to_pylist()
        tree = ProcessTree(raw_list)
        processed_events = tree.create_dependentree_format()

        self.events = processed_events
        self._start_date = start_date.isoformat() if start_date else None
        self._end_date = end_date.isoformat() if end_date else None
        self.show_timefilter = show_timefilter