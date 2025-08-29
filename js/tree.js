import DependenTree from "https://esm.sh/gh/kyrre/dependentree@dev";
import * as d3 from "d3";

export class ProcessTree {
    setOptions(options) {
        this.options = {
            ...this.options,
            ...options
        };
        return this;
    }
    constructor(container, options = {}) {
        this.container = container;
        this.currentNode = null;
        this.tree = null;
        this.data = null;
        this.zoom = null;

        this.options = {
            containerWidthMultiplier: 0.75,
            verticalSpaceBetweenNodes: 50,
            horizontalSpaceBetweenNodes: 200,
            textStyleFont: '16px sans-serif',
            textStyleColor: "var(--marimo-text-color, #ededed)",
            modifyEntityName: ({ ProcessName }) => ProcessName,
            contextMenuClick: null,
            selectedNodeStrokeColor: "var(--marimo-selected-node-stroke-color, #37353f)",
            selectedNodeColor: "var(--marimo-selected-node-color, #37353f)",
            selectedNodeStrokeWidth: 1.5,
            wrapNodeName: false,
            textOffset: 30, // Adjusted text position for larger circles
            tooltipStyleObj: {
                'background-color': 'var(--marimo-tooltip-bg, #1c1c25)',
                'opacity': '0.95',
                'border-style': 'solid',
                'border-width': '1px',
                'border-color': 'var(--marimo-tooltip-border-color, #37353f)',
                'border-radius': '3px',
                'padding': '10px',
                'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.5)'
            },
            animationDuration: 600,
            parentNodeTextOrientation: "right",
            childNodeTextOrientation: "right",
            nodeColor: "var(--marimo-node-color, #1c1c25)",
            nodeStrokeColor: "var(--marimo-node-stroke-color, #37353f)",
            nodeStrokeWidth: 5, // Made the node borders thicker
            enableZoom: false,
            minZoom: 0.5,
            maxZoom: 2.5,
            circleSize: 15, // Increased the size of the circles
            linkStrokeWidth: 3, // Made the connecting lines thicker
            ...options
        };
    }

    initialize(data, process_id) {


        console.log("process_id", process_id);

        this.data = data;
        // Find node by process_id
        let selectedNode = data.find(d => d.ProcessId === process_id);
        this.currentNode = this.currentNode ? this.currentNode : data[0]?._name;

        const expandedNodes = new Set();
        if (this.tree) {
            const collectExpandedNodes = (node) => {
                if (node.children) {
                    expandedNodes.add(node.data._name);
                    node.children.forEach(collectExpandedNodes);
                }
            };
            collectExpandedNodes(this.tree.root);
            this.tree.removeTree();
            this.tree = null;
        }

        const container = this.container;
        if (container) {
            container.innerHTML = '';
        }

        this.options.contextMenuClick = (event, d) => this.handleContextMenu(event, d);
        this.tree = new DependenTree(this.container, this.options);
        this.tree.addEntities(structuredClone(this.data));

        console.log("setting selected node", selectedNode)
        this.tree.selectedNode = selectedNode;


        this.tree.setTree(this.currentNode, "downstream");

        if (this.options.enableZoom) {
            this.initializeZoom();
        }

        const originalDuration = this.tree.options.animationDuration;
        this.tree.options.animationDuration = -10;

        const findAndExpandNode = (node) => {
            if (expandedNodes.has(node.data._name)) {
                this.tree.expandNode(node, 0);
            }
        };
        this.tree.root.each(findAndExpandNode);
        this.tree.options.animationDuration = originalDuration;

        return this;
    }

    initializeZoom() {
        this.zoom = d3.zoom()
            .scaleExtent([this.options.minZoom, this.options.maxZoom])
            .on('zoom', (event) => {
                if (this.tree && this.tree.svg) {
                    this.tree.svg.attr('transform', event.transform);
                }
            });

        if (this.tree && this.tree.svg) {
            this.tree.svg.call(this.zoom);
        }
    }

    handleContextMenu(event, d) {
        this.tree.svg.selectAll('.context-menu').remove();

        const menu = this.tree.svg.append('foreignObject')
            .attr('class', 'context-menu')
            .attr('x', d.y)
            .attr('y', d.x)
            .attr('width', 160)
            .attr('height', 200)
            .append('xhtml:div')
            .style('background-color', '#ffffff') // Light mode background
            .style('border', '1px solid #cccccc') // Light mode border
            .style('border-radius', '5px')
            .style('padding', '5px')
            .style('box-shadow', '0 2px 8px rgba(138, 132, 132, 0.9)') // Light mode shadow
            .style('font', this.options.textStyleFont)
            .style('color', '#262323ff'); // Light mode text color

        menu.append('div')
            .text('Set as new root')
            .style('padding', '8px 12px')
            .style('cursor', 'pointer')
            .on('click', () => {
                this.currentNode = d.data._name;
                this.tree.setTree(d.data._name, 'downstream');
                this.tree.svg.selectAll('.context-menu').remove();
            });

        menu.append('div')
            .text('Expand children')
            .style('padding', '8px 12px')
            .style('cursor', 'pointer')
            .on('click', () => {
                this.tree.expandNode(d);
                this.tree.svg.selectAll('.context-menu').remove();
            });

        this.tree.svg.on('click.context-menu', () => {
            this.tree.svg.selectAll('.context-menu').remove();
            this.tree.svg.on('click.context-menu', null);
        });
    }

      // Navigation methods
    goToParent() {
        if (this.currentNode === this.data[0]._name) return;

        const currentEntity = Object.values(this.data).find(entity =>
            entity._name === this.currentNode
        );

        if (currentEntity && currentEntity._deps && currentEntity._deps.length > 0) {
            const parent = currentEntity._deps[0];
            this.currentNode = parent;
            this.tree.setTree(this.currentNode, 'downstream');
        } else {
            this.currentNode = this.data[0]._name;
            this.tree.setTree(this.currentNode, 'downstream');
        }

        return this.currentNode; // Return for Observable reactivity
    }

    goToRoot() {
        this.currentNode = this.data[0]._name;
        this.tree.setTree(this.currentNode, 'downstream');
        return this.currentNode;
    }

    goToSelected() {
        if (!this.tree.selectedNode) return this.currentNode;
        this.currentNode = this.tree.selectedNode._name;
        this.tree.setTree(this.currentNode, 'downstream');
        return this.currentNode;
    }

    // Clean up method
    destroy() {
        if (this.zoom && this.tree && this.tree.svg) {
            this.tree.svg.on('.zoom', null);
        }

        if (this.container) {
            document.querySelector(this.container).innerHTML = "";
        }
    }
    
}
