# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`process-tree-widget` is an interactive process tree visualization widget for security/forensics analysis. It ingests OS process telemetry from two sources—**MDE (Microsoft Defender for Endpoint)** `ProcessCreated` events and **Volatility** `pstree` memory forensics data—normalizes them to a common ASIM schema, builds a tree structure, and renders it as an interactive D3-backed widget inside **marimo** notebooks via the **anywidget** framework.

## Development Setup

```bash
# Python
uv venv --python 3.12 && uv sync && source .venv/bin/activate

# JavaScript
npm install && npm run dev   # watches js/ and rebuilds on change

# Run the demo notebook
marimo edit example.py
```

## Build Commands

```bash
npm run build    # bundle js/ → src/process_tree_widget/static/ (esbuild, ESM, minified)
npm run dev      # same with inline sourcemaps + watch mode
uv build         # full Python package build (triggers npm run build via hatch-jupyter-builder)
```

## Linting and Type Checking

```bash
ruff check .     # Python linting (excludes example.py)
ruff format .    # Python formatting
mypy src/        # type checking (Python 3.12, strict; excludes example.py)
```

No JavaScript linter is configured.

## Architecture

### Data Flow

```
Raw ibis table (MDE or Volatility)
  → utils.py: prepare_mde_data() / prepare_volatility_data()
  → normalized list of dicts (ASIM triplet schema)
  → tree.py: ProcessTree.build_tree()
  → ProcessTree.create_dependentree_format()
  → __init__.py: ProcessTreeWidget (anywidget traitlets synced to JS)
  → js/widget.js → js/tree.js + js/timefilter.js
```

### Python Layer (`src/process_tree_widget/`)

- **`__init__.py`** — `ProcessTreeWidget(anywidget.AnyWidget)`. Traitlets synced to frontend: `process_id` (Int), `events` (List), `_start_date`/`_end_date` (Unicode), `show_timefilter` (Bool). Accepts raw ibis tables or pre-built event lists.
- **`tree.py`** — `Process` (Pydantic model with ASIM field aliases) and `ProcessTree` (wraps `treelib.Tree`). `ProcessTree.build_tree()` inserts placeholder nodes for missing parents/grandparents. `create_dependentree_format()` serializes to the `[{_name, _deps, ...}]` format consumed by the JS DependenTree library.
- **`utils.py`** — `prepare_mde_data()` filters `ActionType == "ProcessCreated"`, deduplicates, and renames MDE columns to ASIM. `prepare_volatility_data()` self-joins the pstree table twice via `_vol_id`/`_vol_parent_id` to reconstruct acting/parent context using `ibis.coalesce` for missing values.
- **`src/utils.py`** (root-level) — older standalone version used only by `example.py` (uses inner joins); prefer `src/process_tree_widget/utils.py` for new work.

### JavaScript Layer (`js/`)

- **`widget.js`** — anywidget `render({model, el})` entry point. Builds DOM layout, wires model change listeners, delegates to `ProcessTree.initialize()`.
- **`tree.js`** — `ProcessTree` class wrapping the DependenTree library (forked, loaded from `https://esm.sh/gh/kyrre/dependentree@dev`). Manages expanded-node state across re-renders, D3 zoom, right-click context menu ("Set as new root", "Expand children"), and navigation methods.
- **`timefilter.js`** — Observable Plot bar chart (process count over time) with a D3 `brushX` selector. Fires `setDateRange`/`resetDateRange` callbacks that update model state.
- **`utils.js`** — `filterAndSortData()` filters events by time window while retaining parent nodes that have in-range children; `getCurrentNodePid()` resolves the current node to a PID.

### ASIM Schema

The normalized event dicts use a three-process triplet (Target / Acting / Parent) with PascalCase naming, e.g. `TargetProcessId`, `ActingProcessName`, `ParentProcessCreationTime`. Sentinel constants in `tree.py`: `MISSING_PROCESS_ID = -1`, `MISSING_FILE_NAME = "MISSING"`, `MISSING_CREATION_TIME = datetime(1970,1,1)`.

## Testing

No tests currently exist. `AGENTS.md` describes Jest as the intended JS test framework with `.test.js` naming convention, but no test files have been written.
