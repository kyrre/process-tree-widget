import importlib.metadata
import pathlib

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
