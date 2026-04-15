import { getCurrentNodePid, filterAndSortData } from "./utils.js";
import { ProcessTree } from "./tree.js";
import { html } from "htl";

function initializeProcessTree(processTree, model) {
	let allEvents = filterAndSortData(
		model.get("events"),
		model.get("_start_date"),
		model.get("_end_date")
	);

	let process_id = model.get("process_id");
	let processEvent = allEvents.find(d => d.ProcessId == process_id);

	// TODO: when closest-ancestor helper is implemented, try it before falling back.
	if ((typeof processEvent === "undefined" || typeof process_id === "undefined") && allEvents.length > 0) {
		process_id = getCurrentNodePid(allEvents, processTree.currentNode);
		if (typeof process_id === "undefined") {
			process_id = allEvents[1].ProcessId;
		}
		model.set("process_id", process_id);
		model.save_changes();
	}

	processTree.initialize(allEvents, process_id);
}


export default () => {
  let processTree = null;
  let layout = null;

  return {
    initialize({ model }) {
      const onDateChange  = () => { if (processTree) initializeProcessTree(processTree, model); };
      const onEventsChange = () => { if (processTree) initializeProcessTree(processTree, model); };
      model.on("change:_start_date", onDateChange);
      model.on("change:_end_date",   onDateChange);
      model.on("change:events",      onEventsChange);
      return () => {
        model.off("change:_start_date", onDateChange);
        model.off("change:_end_date",   onDateChange);
        model.off("change:events",      onEventsChange);
        try { processTree?.destroy?.(); } catch {}
        processTree = null;
        layout = null;
      };
    },

    render({ model, el }) {
      if (!processTree) {
        layout = html`
          <div style="display:flex;flex-direction:column;gap:5px;">
            <div style="display:flex;justify-content:flex-start;align-items:center;gap:5px;">
              <button title="Go to parent"   onclick=${() => processTree?.goToParent()}>&larr;</button>
              <button title="Go to root"     onclick=${() => processTree?.goToRoot()}>⌂</button>
              <button title="Go to selected" onclick=${() => processTree?.goToSelected()}>&rarr;</button>
            </div>
            <div id="tree" style="flex:1;min-height:400px;padding:10px;display:flex;align-items:center;justify-content:center;"></div>
          </div>`;
        const treeContainer = layout.querySelector("#tree");
        processTree = new ProcessTree(treeContainer);
        processTree.storageKey = `ptw-${model.model_id ?? model.cid ?? "default"}`;
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
      }

      // Re-attach layout to el (moves DOM node if already attached elsewhere)
      el.replaceChildren(layout);
      requestAnimationFrame(() => initializeProcessTree(processTree, model));

      return () => { el.innerHTML = ""; };
    },
  };
};
