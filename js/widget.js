import DependenTree from "https://esm.sh/gh/kyrre/dependentree@dev"
export default {
	initialize({ model }) {
		console.info('initialize called');
		return () => {
			console.info("model cleanup :>");
		}
	},

	render({ model, el }) {

		this.treeDiv = document.createElement("div");
		this.treeDiv.id = "tree";
		this.activePid = null;

		// this callback function is called when
		model.on("change:events", () => {

			this.tree.removeTree();

			this.tree = new DependenTree(this.treeDiv, options);
			this.tree.addEntities(structuredClone(model.get("events")));
			this.tree.setTree('<root>', 'downstream');


		});


		el.classList.add("process_tree_widget");
		el.appendChild(this.treeDiv);

		const options = {
			horizontalSpaceBetweenNodes: 150,
			textStyleFont: "14px sans-serif",
			modifyEntityName: ({ ProcessName }) => ProcessName,
			textClick: () => null, // do nothing
			selectedNodeStrokeColor: "rgb(80, 110, 134)",
			selectedNodeColor: "#7b9fce",
			tooltipStyleObj: {
				'background-color': 'light-dark(#fff,#181c1a)',
				'opacity': '0.9',
				'border-style': 'solid',
				'border-width': '0.5px',
				'border-radius': '3px',
				'padding': '10px',
				'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.2)'

			},
			animationDuration: 300,
			parentNodeTextOrientation: "right",
			childNodeTextOrientation: "right",

			// whenever we click a node in tree we update the process_id value 
			// which is then synced back to Python :x
			nodeClick: (node) => {
				model.set("process_id", node.ProcessId);
				model.save_changes();
			}
		};

		// the rendering needs to complete before we create the tree
		// via discord :blessed:
		requestAnimationFrame(() => {
			this.tree = new DependenTree(this.treeDiv, options);
			this.tree.addEntities(structuredClone(model.get("events")));
			this.tree.setTree('<root>', 'downstream');
		});
	}
}