export function getCurrentNodePid(data, currentNode) {
	if (!currentNode) return undefined;
	return data.find(d => d._name === currentNode)?.ProcessId;
}

export function filterByRootNames(events, currentRoot, hiddenRootNames) {
	if (!hiddenRootNames || hiddenRootNames.size === 0) return events;
	const root = currentRoot || "<root>";
	const childrenOf = new Map();
	for (const e of events) {
		const p = e._deps?.[0];
		if (p) { if (!childrenOf.has(p)) childrenOf.set(p, []); childrenOf.get(p).push(e._name); }
	}
	const excluded = new Set();
	for (const e of events) {
		if (e._deps?.[0] === root && hiddenRootNames.has(e._name)) {
			const queue = [e._name];
			while (queue.length) { const cur = queue.shift(); excluded.add(cur); for (const child of (childrenOf.get(cur) ?? [])) queue.push(child); }
		}
	}
	return events.filter(e => !excluded.has(e._name));
}

export function filterAndSortData(data, startDate, endDate) {
	// TODO: add helper findClosestAncestorInFiltered(allEvents, filteredEvents, startNode)
	// that walks parent chain (_deps[0]) until it finds an event inside filteredEvents.
	// Will be used when currently selected node was filtered out by time window.
	// Normalize inputs to Date objects (or null)
	const start = startDate ? new Date(startDate) : null;
	const end = endDate ? new Date(endDate) : null;

	return data
		.filter(d => {
			if (d.TargetProcessCreationTime === undefined) return true; // keep if no time metadata
			if (!start && !end) return true; // no filtering applied

			const date = new Date(d.TargetProcessCreationTime);
			const hasChildren = data.some(child => child._deps?.includes(d._name));
			const isBeforeStartDate = start ? date < start : false;
			return (hasChildren && isBeforeStartDate) || (date >= start && date <= end);
		})
		.sort((a, b) => {
			if (!a.TargetProcessCreationTime) return -1;
			if (!b.TargetProcessCreationTime) return 1;
			return new Date(a.TargetProcessCreationTime) - new Date(b.TargetProcessCreationTime);
		});
}
