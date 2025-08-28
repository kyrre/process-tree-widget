import importlib.metadata
import pathlib
from datetime import datetime, timezone

import anywidget
import traitlets

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

    def __init__(self, events, start_date=None, end_date=None, **kwargs):
        super().__init__(**kwargs)
        self.events = events
        self._start_date = start_date.isoformat() if start_date else None
        self._end_date = end_date.isoformat() if end_date else None


class TimeFilterWidget(anywidget.AnyWidget):
    _esm = pathlib.Path(__file__).parent / "static" / "timefilter_widget.js"

    events: traitlets.List = traitlets.List([]).tag(sync=True)
    _start_date = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    _end_date = traitlets.Unicode(None, allow_none=True).tag(sync=True)

    def __init__(self, events, **kwargs):
        super().__init__(**kwargs)

        self.events = events
        creation_times = [event["ProcessCreationTime"] for event in self.events if 'ProcessCreationTime' in event]
        self._start_date = min(creation_times).isoformat()
        self._end_date = max(creation_times).isoformat()

    @property
    def start_date(self):
        return datetime.fromisoformat(self._start_date) if self._start_date else None

    @property
    def end_date(self):
        return datetime.fromisoformat(self._end_date) if self._end_date else None