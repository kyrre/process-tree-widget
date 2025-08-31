import { getCurrentNodePid, filterAndSortData } from "./utils.js";
import { ProcessTree } from "./tree.js";
import { html } from "htl";
import { timeProcessBarplot } from "./timefilter.js"

function createTimeProcessBarplot(model) {
	return timeProcessBarplot(model.get("events"), {
		width: 400,
		height: 150,
		startDate: model.get("_start_date") ? new Date(model.get("_start_date")) : null,
		endDate: model.get("_end_date") ? new Date(model.get("_end_date")) : null,
		setDateRange: (start, end) => {
			model.set("_start_date", start.toISOString());
			model.set("_end_date", end.toISOString());
			model.save_changes();
		},
		resetDateRange: () => {
			model.set("_start_date", null);
			model.set("_end_date", null);
			model.save_changes();
		}
	});
}

// filterAndSortData moved to utils.js

function initializeProcessTree(processTree, model) {
	let allEvents = filterAndSortData(
		model.get("events"),
		model.get("show_timefilter") ? model.get("_start_date") : null,
		model.get("show_timefilter") ? model.get("_end_date") : null
	);

	let process_id = model.get("process_id");
	let processEvent = allEvents.find(d => d.ProcessId == process_id);

	// Debug logs removed

	// If processEvent or process_id is undefined, set process_id using util function, else fallback to first event's ProcessId
	// TODO: when closest-ancestor helper is implemented, try it before falling back to first event.
	if ((typeof processEvent === "undefined" || typeof process_id === "undefined") && allEvents.length > 0) {
		process_id = getCurrentNodePid(allEvents, processTree.currentNode);
		if (typeof process_id !== "undefined") {
			// derived from current node
		}
		// If still undefined, use the first event's ProcessId
		if (typeof process_id === "undefined") {
			process_id = allEvents[1].ProcessId;
			// fallback to first event
		}
		model.set("process_id", process_id);
		model.save_changes();
	}

	processTree.initialize(allEvents, process_id);

	// After initialization, check currentNode
	// currentNode set after init
}


export default {
  render({ model, el }) {
    let layout, timeChart, processTree;

    layout = html`
      <div style="display:flex;flex-direction:column;gap:5px;">
        <div style="display:flex;justify-content:flex-start;align-items:center;gap:5px;">
          <button title="Go to parent"   onclick=${() => processTree?.goToParent()}>&larr;</button>
          <button title="Go to root"     onclick=${() => processTree?.goToRoot()}>⌂</button>
          <button title="Go to selected" onclick=${() => processTree?.goToSelected()}>&rarr;</button>
        </div>
        ${model.get("show_timefilter")
          ? html`<div style="display:flex;flex-direction:row;justify-content:flex-start;align-items:flex-start;gap:5px;margin-top:20px;">
              <div id="timefilter-chart-container"></div>
            </div>`
          : null}
        <div id="tree" style="flex:1;min-height:400px;padding:10px;display:flex;align-items:center;justify-content:center;"></div>
      </div>
    `;
    el.replaceChildren(layout);

    if (model.get("show_timefilter")) {
      const chartContainer = layout.querySelector("#timefilter-chart-container");
      timeChart = createTimeProcessBarplot(model);
      chartContainer.appendChild(timeChart);
    }

    const treeContainer = layout.querySelector("#tree");
    processTree = new ProcessTree(treeContainer);
    processTree.setOptions({
      textStyleColor: "#506e86",
      modifyEntityName: ({ ProcessName }) => ProcessName,
  textClick: () => null,
      selectedNodeStrokeColor: "#506e86",
      selectedNodeColor: "#7b9fce",
      tooltipStyleObj: {
        'background-color': '#ffffff',
        'opacity': '0.9',
        'border-style': 'solid',
        'border-width': '0.5px',
        'border-color': '#cccccc',
        'border-radius': '3px',
        'padding': '10px',
        'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
      },
      animationDuration: 300,
      parentNodeTextOrientation: 'right',
      childNodeTextOrientation: 'right',
      nodeClick: (node) => {
        model.set("process_id", node.ProcessId);
        model.save_changes();
        processTree.tree.selectedNode = node;
      }
    });

    // --- model listeners ---
    const onEventsChange = () => {
      if (model.get("show_timefilter")) {
        if (timeChart) timeChart.remove();
        const chartContainer = layout.querySelector("#timefilter-chart-container");
        if (chartContainer) {
          timeChart = createTimeProcessBarplot(model);
          chartContainer.appendChild(timeChart);
        }
      }
      initializeProcessTree(processTree, model);
    };
    model.on("change:events", onEventsChange);

    const onDateChange = () => initializeProcessTree(processTree, model);
    model.on("change:_start_date", onDateChange);
    model.on("change:_end_date", onDateChange);

    const onShowTimefilterChange = () => {
      if (!model.get("show_timefilter") && timeChart) {
        timeChart.remove();
        timeChart = null;
      }
      initializeProcessTree(processTree, model);
    };
    model.on("change:show_timefilter", onShowTimefilterChange);

    requestAnimationFrame(() => initializeProcessTree(processTree, model));

    // --- cleanup ---
    return () => {
      model.off("change:events", onEventsChange);
      model.off("change:_start_date", onDateChange);
      model.off("change:_end_date", onDateChange);
      model.off("change:show_timefilter", onShowTimefilterChange);
      try { timeChart?.remove(); } catch {}
      try { processTree?.destroy?.(); } catch {}
      el.innerHTML = "";
      layout = timeChart = processTree = null;
    };
  }
};
