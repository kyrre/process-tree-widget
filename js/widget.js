import { ProcessTree } from "./tree.js";
import { html } from "htl";

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
				<div id="tree" style="flex: 1; min-height: 400px; padding: 10px; display: flex; align-items: center; justify-content: center;"></div>
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

		const getFilteredData = () => {
			const data = model.get("events") || [];
			const startDateStr = model.get("_start_date");
			const endDateStr = model.get("_end_date");
			const startDate = startDateStr ? new Date(startDateStr) : null;
			const endDate = endDateStr ? new Date(endDateStr) : null;

			console.debug("getFilteredData: data", data);
			console.debug("getFilteredData: startDate", startDate);
			console.debug("getFilteredData: endDate", endDate);

			const filtered = data.filter(d => {
				if (!startDate && !endDate) {
					console.debug("No start/end date, keeping", d);
					return true;
				}
				if (!d.ProcessCreationTime) {
					console.debug("No ProcessCreationTime, keeping", d);
					return true;
				}
				const date = new Date(d.ProcessCreationTime);
				const hasChildren = data.some(child => child._deps?.includes(d._name));
				const isBeforeStartDate = startDate && date < startDate;
				const inRange = startDate && endDate && date >= startDate && date <= endDate;
				const keep = (hasChildren && isBeforeStartDate) || inRange;
				return keep;
			});

			const sorted = filtered.sort((a, b) => {
				if (!a.ProcessCreationTime) return -1;
				if (!b.ProcessCreationTime) return 1;
				return new Date(a.ProcessCreationTime) - new Date(b.ProcessCreationTime);
			});

			console.debug("getFilteredData: result", sorted);
			return sorted;
		};

		this.processTree = new ProcessTree(treeContainer, options);

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
			this.processTree.initialize(getFilteredData(), { identifier: '<root>' });
		});

		model.on("change:_start_date", () => {
			this.processTree.initialize(getFilteredData(), { identifier: '<root>' });
		});

		model.on("change:_end_date", () => {
			this.processTree.initialize(getFilteredData(), { identifier: '<root>' });
		});

		requestAnimationFrame(() => {
			this.processTree.initialize(getFilteredData(), { identifier: '<root>' });
		});
	},

	destroy() {
		if (this.processTree) {
			this.processTree.destroy();
		}
	}
};