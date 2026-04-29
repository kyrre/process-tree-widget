import DependenTree from "./dependentree/index.js";
import * as d3 from "d3";

const c = (light, dark) => document.querySelector('.dark, .dark-theme') ? dark : light;

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
        this.anchorNode = null;
        this.tree = null;
        this.data = null;
        this.zoom = null;

        this.options = {
            containerWidthMultiplier: 0.75,
            verticalSpaceBetweenNodes: 50,
            horizontalSpaceBetweenNodes: 200,
            textStyleFont: '16px sans-serif',
            textStyleColor: "currentColor",
            modifyEntityName: ({ ProcessName, ProcessId, ChildCount }) => (ProcessName && ProcessName !== 'MISSING') ? ProcessName : `${ProcessId} (${ChildCount ?? 0} nodes)`,
            contextMenuClick: null,
            selectedNodeStrokeWidth: 1.5,
            wrapNodeName: false,
            textOffset: 30,
            animationDuration: 600,
            parentNodeTextOrientation: "right",
            childNodeTextOrientation: "right",
            nodeStrokeWidth: 5,
            enableZoom: false,
            minZoom: 0.5,
            maxZoom: 2.5,
            circleSize: 15, // Increased the size of the circles
            linkStrokeWidth: 3, // Made the connecting lines thicker
            ...options
        };
    }

    // Walk both visible (children) and collapsed (_children) nodes
    _traverseAll(node, callback) {
        callback(node);
        (node.children || []).forEach(c => this._traverseAll(c, callback));
        (node._children || []).forEach(c => this._traverseAll(c, callback));
    }

    initialize(data, process_id) {
        this.data = data;

        let selectedNode = data.find(d => d.ProcessId === process_id);

        // Collect expanded nodes from the live tree before teardown.
        // _traverseAll walks both node.children (visible) and node._children
        // (collapsed) so the full state is captured regardless of what's expanded.
        const expandedNodes = new Set();
        const isFirstRender = !this.tree?.root;
        if (!isFirstRender) {
            this._traverseAll(this.tree.root, node => {
                if (node.children) expandedNodes.add(node.data._name);
            });
            this.currentNode = this.currentNode || "<root>";
        } else {
            if (this.initialNode) this.currentNode = this.initialNode;
            this.currentNode = this.currentNode || "<root>";
            this.initialNode = null;
        }

        if (this.tree) {
            this.tree.removeTree();
            this.tree = null;
        }

        const container = this.container;
        if (container) {
            container.innerHTML = '';
        }

        // Fall back if currentNode no longer exists in filtered data
        if (!data.find(d => d._name === this.currentNode)) {
            this.currentNode = "<root>";
        }

        this.options.contextMenuClick = (event, d) => this.handleContextMenu(event, d);
        const originalDuration = this.options.animationDuration;
        this.options.animationDuration = -10;  // suppress flicker during full rebuild
        this.tree = new DependenTree(this.container, this.options);
        this.tree.addEntities(structuredClone(this.data));
        this.tree.selectedNode = selectedNode;
        this.tree.setTree(this.currentNode, "downstream");

        if (this.options.enableZoom) {
            this.initializeZoom();
        }

        // Restore expanded nodes. Must walk _children too because setTree calls
        // collapseAll — after that, root.children is null and root.each() sees
        // nothing. We expand a node first, then recurse into its newly-visible
        // children, while also recursing into still-collapsed _children.
        const restoreExpanded = (node) => {
            if (expandedNodes.has(node.data._name) && node._children) {
                this.tree.expandNode(node, 0);
            }
            [...(node.children || []), ...(node._children || [])].forEach(restoreExpanded);
        };
        restoreExpanded(this.tree.root);

        this.options.animationDuration = originalDuration;
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
            .style('background-color', c('#ffffff', '#1f2937'))
            .style('border', `1px solid ${c('#d1d5db', '#374151')}`)
            .style('border-radius', '5px')
            .style('padding', '5px')
            .style('box-shadow', '0 2px 8px rgba(0, 0, 0, 0.25)')
            .style('font', this.options.textStyleFont)
            .style('color', c('#111827', '#f9fafb'));

        menu.append('div')
            .text('Set as new root')
            .style('padding', '8px 12px')
            .style('cursor', 'pointer')
            .on('click', () => {
                this.currentNode = d.data._name;
                this.anchorNode = d.data._name;
                this.tree.setTree(d.data._name, 'downstream');
                this.tree.svg.selectAll('.context-menu').remove();
                this.options.onRootChanged?.();
            });

        menu.append('div')
            .text('Expand children')
            .style('padding', '8px 12px')
            .style('cursor', 'pointer')
            .on('click', () => {
                this.tree.expandNode(d);
                this.tree.svg.selectAll('.context-menu').remove();
            });

        (this.options.customActions ?? []).forEach(action => {
            menu.append('div')
                .text(action.label)
                .style('padding', '8px 12px')
                .style('cursor', 'pointer')
                .on('click', () => {
                    this.options.onActionTriggered?.(action.id, d.data);
                    this.tree.svg.selectAll('.context-menu').remove();
                });
        });

        this.tree.svg.on('click.context-menu', () => {
            this.tree.svg.selectAll('.context-menu').remove();
            this.tree.svg.on('click.context-menu', null);
        });
    }

    // Navigation methods
    goToParent() {
        if (this.currentNode === "<root>") return;

        const currentEntity = Object.values(this.data).find(entity =>
            entity._name === this.currentNode
        );

        if (currentEntity && currentEntity._deps && currentEntity._deps.length > 0) {
            const parent = currentEntity._deps[0];
            this.currentNode = parent;
            this.tree.setTree(this.currentNode, 'downstream');
        } else {
            const root = this.data.find(d => d._name === "<root>") ?? this.data[0];
            this.currentNode = root._name;
            this.tree.setTree(this.currentNode, 'downstream');
        }

        return this.currentNode;
    }

    goToRoot() {
        const root = this.data.find(d => d._name === "<root>") ?? this.data[0];
        this.currentNode = root._name;
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
            this.container.innerHTML = "";
        }
    }

}
