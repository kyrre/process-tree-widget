import { getCurrentNodePid, filterAndSortData } from "../utils.js";
import { ProcessTree } from "./tree.js";
import { html } from "htl";

// Pick a color based on marimo's actual theme.
// Marimo sets .dark or .dark-theme somewhere in the ancestor chain.
function isDark() {
  const { documentElement: h, body: b } = document;
  return h.classList.contains('dark') || h.classList.contains('dark-theme')
      || b.classList.contains('dark') || b.classList.contains('dark-theme');
}
function c(light, dark) {
  return isDark() ? dark : light;
}

function fmtDate(isoStr) {
  if (!isoStr) return null;
  const d = new Date(isoStr);
  const pad = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function updateDateLabel(el, model) {
  const s = fmtDate(model.get("_start_date"));
  const e = fmtDate(model.get("_end_date"));
  el.textContent = s && e ? `${s} — ${e}` : "";
}

function initializeProcessTree(processTree, model) {
	let allEvents = filterAndSortData(
		model.get("events"),
		model.get("_start_date"),
		model.get("_end_date")
	);

	let process_id = model.get("selected_event")?.ProcessId;
	let nodeInEvents = process_id != null && allEvents.find(d => d.ProcessId === process_id);

	if (!nodeInEvents && allEvents.length > 0) {
		process_id = getCurrentNodePid(allEvents, processTree.currentNode);
		if (process_id == null) process_id = allEvents[1]?.ProcessId;
		const event = allEvents.find(d => d.ProcessId === process_id) ?? {};
		model.set("selected_event", event);
		model.save_changes();
	}

	processTree.initialize(allEvents, process_id);
}


function fmtTooltipDate(val) {
  if (!val) return null;
  const d = new Date(val);
  if (isNaN(d)) return String(val);
  const pad = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function buildTooltip(data) {
  const bg        = c('#ffffff', '#1f2937');
  const border    = c('#d1d5db', '#374151');
  const divider   = c('#e5e7eb', '#374151');
  const textMain  = c('#111827', '#f9fafb');
  const textMuted = c('#6b7280', '#9ca3af');
  const codeBg    = c('#f3f4f6', '#111827');

  const sectionStyle = `padding:8px 10px;border-top:1px solid ${divider};`;
  const labelStyle   = `font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:${textMuted};margin-bottom:3px;`;
  const valueStyle   = `font-size:13px;color:${textMain};word-break:break-all;`;

  let html = `<div style="font-family:sans-serif;background:${bg};border:1px solid ${border};border-radius:4px;min-width:220px;max-width:340px;box-shadow:0 4px 12px rgba(0,0,0,0.2);overflow:hidden;">`;

  // ── Section 1: process header ──────────────────────────────────────────────
  html += `<div style="padding:8px 10px;">`;
  html += `<div style="font-size:14px;font-weight:700;color:${textMain};margin-bottom:2px;">${data.ProcessName ?? ''}</div>`;

  const timeStr = fmtTooltipDate(data.TargetProcessCreationTime);
  const imputedBadge = data.ImputedCreationTime
    ? ` <span style="font-size:10px;background:#f59e0b;color:#fff;border-radius:3px;padding:1px 4px;vertical-align:middle;">imputed ts</span>`
    : '';
  const syntheticBadge = data.Synthetic
    ? ` <span style="font-size:10px;background:#64748b;color:#fff;border-radius:3px;padding:1px 4px;vertical-align:middle;">inferred</span>`
    : '';
  html += `<div style="font-size:12px;color:${textMuted};">PID ${data.ProcessId ?? ''}${timeStr ? ` &middot; ${timeStr}` : ''}${imputedBadge}${syntheticBadge}</div>`;

  if (data.FolderPath) {
    html += `<div style="font-size:11px;color:${textMuted};margin-top:2px;word-break:break-all;">${data.FolderPath}</div>`;
  }
  html += `</div>`;

  // ── Section 2: parent process (skip if MISSING or -1) ─────────────────────
  const parentName = data.ActingProcessName;
  const parentId   = data.ActingProcessId;
  if (parentName && parentName !== 'MISSING' && parentId != null && parentId !== -1) {
    html += `<div style="${sectionStyle}">`;
    html += `<div style="${labelStyle}">Parent</div>`;
    html += `<div style="${valueStyle}">${parentName} <span style="color:${textMuted};">(PID ${parentId})</span></div>`;
    html += `</div>`;
  }

  // ── Section 3: command line (skip if empty) ────────────────────────────────
  if (data.CommandLine) {
    const truncated = data.CommandLine.length > 120
      ? data.CommandLine.slice(0, 120) + '…'
      : data.CommandLine;
    html += `<div style="${sectionStyle}">`;
    html += `<div style="${labelStyle}">Command line</div>`;
    html += `<div style="font-family:monospace;font-size:11px;color:${textMain};background:${codeBg};padding:4px 6px;border-radius:3px;word-break:break-all;">${truncated}</div>`;
    html += `</div>`;
  }

  html += `</div>`;
  return html;
}

function themeColors() {
  return {
    textStyleColor:          c("#0f172a", "#cbd5e1"),
    circleStrokeColor:       c("#94a3b8", "#64748b"),
    linkStrokeColor:         c("#e2e8f0", "#334155"),
    openNodeCircleColor:     c("#f8fafc", "#0f172a"),
    closedNodeCircleColor:   c("#cbd5e1", "#475569"),
    selectedNodeStrokeColor: c("#2563eb", "#7dd3fc"),
    selectedNodeColor:       c("#bfdbfe", "#0369a1"),
    imputedNodeColor:        "#f59e0b",
    syntheticNodeColor:      c("#94a3b8", "#475569"),
    syntheticNodeStrokeDash: "5,3",
    missingNodeColor:        c("#fef9c3", "#713f12"),
    cyclicNodeColor:         c("#fecaca", "#7f1d1d"),
    maxDepthNodeColor:       c("#e9d5ff", "#4c1d95"),
    tooltipStyleObj: {
      'background-color': 'transparent',
      'border': 'none',
      'padding': '0',
    },
    tooltipFormatter: buildTooltip,
  };
}

export default () => {
  let processTree = null;
  let layout = null;
  let labelStyle = null;

  return {
    initialize({ model }) {
      const onDateChange  = () => {
        if (layout) updateDateLabel(layout.querySelector("#ptw-date-label"), model);
        if (processTree) initializeProcessTree(processTree, model);
      };
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
        labelStyle = null;
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
              <span id="ptw-date-label" style="margin-left:auto;font-size:11px;font-family:sans-serif;opacity:0.5;"></span>
            </div>
            <div id="tree" style="flex:1;min-height:400px;padding:10px;display:flex;align-items:center;justify-content:center;"></div>
          </div>`;

        labelStyle = document.createElement('style');
        el.appendChild(labelStyle);

        const treeContainer = layout.querySelector("#tree");
        processTree = new ProcessTree(treeContainer);
        processTree.setOptions({
          modifyEntityName: ({ ProcessName, ProcessId }) => (ProcessName && ProcessName !== 'MISSING') ? ProcessName : `pid:${ProcessId}`,
          textClick: () => null,
          animationDuration: 300,
          parentNodeTextOrientation: 'right',
          childNodeTextOrientation: 'right',
          nodeClick: (node) => {
            const { _deps, ...event } = node;
            model.set("selected_event", event);
            model.save_changes();
            processTree.tree.selectedNode = node;
          }
        });
      }

      // Re-apply colors fresh on every render (picks up theme changes on reload)
      processTree.setOptions(themeColors());
      labelStyle.textContent = `.ptw-node-label { fill: ${c("#0f172a", "#e2e8f0")} !important; }`;

      // Re-attach layout to el (moves DOM node if already attached elsewhere)
      el.replaceChildren(layout);
      updateDateLabel(layout.querySelector("#ptw-date-label"), model);
      requestAnimationFrame(() => initializeProcessTree(processTree, model));

      return () => { el.innerHTML = ""; };
    },
  };
};
