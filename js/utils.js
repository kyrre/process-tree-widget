export function getCurrentNodePid(data, currentNode) {
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

export function filterAndSortData(data, startDate, endDate) {
	// TODO: add helper findClosestAncestorInFiltered(allEvents, filteredEvents, startNode)
	// that walks parent chain (_deps[0]) until it finds an event inside filteredEvents.
	// Will be used when currently selected node was filtered out by time window.
	// Normalize inputs to Date objects (or null)
	const start = startDate ? new Date(startDate) : null;
	const end = endDate ? new Date(endDate) : null;

	return data
		.filter(d => {
			if (d.ProcessCreationTime === undefined) return true; // keep if no time metadata
			if (!start && !end) return true; // no filtering applied

			const date = new Date(d.ProcessCreationTime);
			const hasChildren = data.some(child => child._deps?.includes(d._name));
			const isBeforeStartDate = start ? date < start : false;
			return (hasChildren && isBeforeStartDate) || (date >= start && date <= end);
		})
		.sort((a, b) => {
			if (!a.ProcessCreationTime) return -1;
			if (!b.ProcessCreationTime) return 1;
			return new Date(a.ProcessCreationTime) - new Date(b.ProcessCreationTime);
		});
}
