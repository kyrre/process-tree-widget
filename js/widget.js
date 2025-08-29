// Utility function to get ProcessId for a given currentNode and data
function getCurrentNodePid(data, currentNode) {
	if (!currentNode) return undefined;
	// If currentNode is a string (_name), find the event
	if (typeof currentNode === "string") {
		const nodeEvent = data.find(d => d._name === currentNode);
		return nodeEvent ? nodeEvent.ProcessId : undefined;
	}
	// If currentNode is an object with ProcessId
	if (typeof currentNode === "object" && currentNode.ProcessId !== undefined) {
		return currentNode.ProcessId;
	}
	return undefined;
}
import { ProcessTree } from "./tree.js";
import { html } from "htl";
import { timeProcessBarplot } from "./timefilter.js"

function createTimeProcessBarplot(model) {
	return timeProcessBarplot(model.get("events"), {
		width: 400,
		height: 250,
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

// Filter and sort data based on selected date range
function filterAndSortData(data, startDate, endDate) {
	// Ensure startDate and endDate are Date objects
	const start = startDate ? new Date(startDate) : null;
	const end = endDate ? new Date(endDate) : null;



	let filtered = data
		.filter(d => {

			if (d.ProcessCreationTime === undefined) return true;

			// If no time filter is set, keep everything
			if (!start && !end) return true;

			const date = new Date(d.ProcessCreationTime);

			// Keep the node if:
			// 1. It has children AND was created before start date (it's a parent that existed before our window)
			// 2. OR it's within our time window
			const hasChildren = data.some(child => child._deps?.includes(d._name));
			const isBeforeStartDate = start ? date < start : false;

			let keep = (hasChildren && isBeforeStartDate) || (date >= start && date <= end);
			return keep;
		})
		.sort((a, b) => {
			if (!a.ProcessCreationTime) return -1;
			if (!b.ProcessCreationTime) return 1;
			return new Date(a.ProcessCreationTime) - new Date(b.ProcessCreationTime);
		});


	return filtered;
}

function initializeProcessTree(processTree, model) {
    let allEvents = filterAndSortData(
        model.get("events"), 
        model.get("_start_date"), 
        model.get("_end_date")
    );

    let process_id = model.get("process_id");
    let processEvent = allEvents.find(d => d.ProcessId == process_id);

    console.log("[DEBUG] Initial process_id from model:", process_id);
    console.log("[DEBUG] Found processEvent:", processEvent);
    console.log("[DEBUG] allEvents count:", allEvents.length);

		// If processEvent or process_id is undefined, set process_id using util function, else fallback to first event's ProcessId
		if ((typeof processEvent === "undefined" || typeof process_id === "undefined") && allEvents.length > 0) {
			process_id = getCurrentNodePid(allEvents, processTree.currentNode);
			if (typeof process_id !== "undefined") {
				console.log("[DEBUG] Fallback: using getCurrentNodePid:", process_id);
			}
			// If still undefined, use the first event's ProcessId
			if (typeof process_id === "undefined") {
				process_id = allEvents[0].ProcessId;
				console.log("[DEBUG] Fallback: using first event's ProcessId:", process_id);
			}
			model.set("process_id", process_id);
			model.save_changes();
		}

    processTree.initialize(allEvents, process_id);

    // After initialization, check currentNode
    console.log("[DEBUG] processTree.currentNode after init:", processTree.currentNode);
}



export default {
	initialize({ model }) {
		console.info('initialize called');
		return () => {
			console.info("model cleanup :>");
		};
	},


	render({ model, el }) {
		// Create a flexbox layout with timeProcessBarplot above the tree, right-aligned
		const layout = html`
			<div style="display: flex; flex-direction: column; gap: 5px;">
				<div class="controls-container" style="display: flex; justify-content: flex-start; gap: 5px;">
					<button id="left-button" title="Go to parent">&larr;</button>
					<button id="home-button" title="Go to root">⌂</button>
					<button id="right-button" title="Go to selected">&rarr;</button>
				</div>
				<div style="display: flex; flex-direction: row; justify-content: flex-start; align-items: flex-start; gap: 5px;">
					<div id="timefilter-chart-container"></div>
				</div>
				<div id="tree" style="flex: 1; min-height: 400px; padding: 10px; display: flex; align-items: center; justify-content: center;"></div>
			</div>
		`;

		// Append the layout to the root element
		el.appendChild(layout);

		// Add timeProcessBarplot to the chart container
		const chartContainer = layout.querySelector("#timefilter-chart-container");
		this.timeChart = createTimeProcessBarplot(model);
		chartContainer.appendChild(this.timeChart);

		// Initialize the process tree
		const treeContainer = layout.querySelector("#tree");
		const options = {
			textStyleColor: "#506e86",
			modifyEntityName: ({ ProcessName }) => ProcessName,
			textClick: () => null,
			selectedNodeStrokeColor: "#506e86", // Light mode color
			selectedNodeColor: "#7b9fce", // Light mode color
			tooltipStyleObj: {
				'background-color': '#ffffff', // Light mode background
				'opacity': '0.9',
				'border-style': 'solid',
				'border-width': '0.5px',
				'border-color': '#cccccc', // Light mode border
				'border-radius': '3px',
				'padding': '10px',
				'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.1)' // Light mode shadow
			},
			animationDuration: 300,
			parentNodeTextOrientation: "right",
			childNodeTextOrientation: "right",
		};


		this.processTree = new ProcessTree(treeContainer);
		this.processTree.setOptions({
			...options,
			nodeClick: (node) => {
				model.set("process_id", node.ProcessId);
				model.save_changes();
				this.processTree.tree.selectedNode = node;
			}
		});

		// Add event listeners for navigation buttons
		layout.querySelector("#left-button").addEventListener("click", () => {
			this.processTree.goToParent();
		});

		layout.querySelector("#home-button").addEventListener("click", () => {
			this.processTree.goToRoot();
		});

		layout.querySelector("#right-button").addEventListener("click", () => {
			this.processTree.goToSelected();
		});

		model.on("change:events", () => {
			console.debug("model.on: change:events");

			if (this.timeChart) {
				this.timeChart.remove();
			}
			const chartContainer = layout.querySelector("#timefilter-chart-container");
			this.timeChart = createTimeProcessBarplot(model);
			chartContainer.appendChild(this.timeChart);

			initializeProcessTree(this.processTree, model);
		});

		model.on("change:_start_date", () => {
			console.debug("model.on: change:_start_date triggered", model.get("_start_date"));
			initializeProcessTree(this.processTree, model);
		});

		model.on("change:_end_date", () => {
			console.debug("model.on: change:_end_date triggered", model.get("_end_date"));
			initializeProcessTree(this.processTree, model);
		});

		requestAnimationFrame(() => {
			initializeProcessTree(this.processTree, model);
		});
	},

	destroy() {
		if (this.timeChart) {
			this.timeChart.remove();
		}
		if (this.processTree) {
			this.processTree.destroy();
		}
	}
};