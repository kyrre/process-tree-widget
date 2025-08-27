import { ProcessTree } from "./tree.js";
import {timeProcessBarplot} from "./timefilter.js";
import { html } from "htl";
import { Library } from "@observablehq/stdlib";

const library = new Library();
const startDate = library.Mutable(null);
const endDate = library.Mutable(null);


const setDateRange = (start, end) => {
    startDate.value = start;
    endDate.value = end;
    console.log("Date range updated:", startDate.value, endDate.value);
};

const resetDateRange = () => {
    startDate.value = null;
    endDate.value = null;
    console.log("Date range reset");
};

export default {
	initialize({ model }) {
		console.info('initialize called');
		return () => {
			console.info("model cleanup :>");
		};
	},

	render({ model, el }) {
		// Create a flexbox layout with controls in one row and the tree below
		const layout = html`
			<div style="display: flex; flex-direction: column; gap: 5px;">
				<div class="controls-container" style="display: flex; justify-content: flex-start; gap: 5px;">
					<button id="left-button" title="Go to parent">&larr;</button>
					<button id="home-button" title="Go to root">⌂</button>
					<button id="right-button" title="Go to selected">&rarr;</button>
				</div>
				<div id="chart-container" style="margin-top: 20px; align-self: flex-end;">
				</div>
				<div id="tree" style="flex: 1; min-height: 400px; padding: 10px; display: flex; align-items: center; justify-content: center;">
				</div>
			</div>
		`;

		// Append the layout to the root element
		el.appendChild(layout);

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
			nodeClick: (node) => {
				model.set("process_id", node.ProcessId);
				model.save_changes();
			}
		};

		this.processTree = new ProcessTree(treeContainer, options);

		// Initialize the time chart
		const chartContainer = layout.querySelector("#chart-container");
		this.timeChart = timeProcessBarplot(model.get("events"), {
			width: 300,
			height: 150,
			startDate,
			endDate,
			setDateRange,
			resetDateRange,
		});
		chartContainer.appendChild(this.timeChart);

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
			this.processTree.destroy();
			this.processTree = new ProcessTree(treeContainer, options);
			this.processTree.initialize(model.get("events"), { identifier: '<root>' });
		});

		requestAnimationFrame(() => {
			this.processTree.initialize(model.get("events"), { identifier: '<root>' });
		});
	},

	destroy() {
		if (this.processTree) {
			this.processTree.destroy();
		}
		if (this.timeChart) {
			this.timeChart.remove();
		}
	}
};