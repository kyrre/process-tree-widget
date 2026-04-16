import * as d3 from "d3";
import * as Plot from "@observablehq/plot";

const fmt = d3.timeFormat("%Y-%m-%d %H:%M");

function updateLabel(labelEl, startDateStr, endDateStr) {
  if (startDateStr && endDateStr) {
    labelEl.textContent = `${fmt(new Date(startDateStr))} — ${fmt(new Date(endDateStr))}`;
    labelEl.dataset.active = "true";
  } else {
    labelEl.textContent = "No filter active";
    labelEl.dataset.active = "false";
  }
}

export default {
  render({ model, el }) {
    el.classList.add("ptw-timefilter");
    let debounceTimer = null;

    const labelEl = document.createElement("div");
    labelEl.className = "ptw-timefilter-label";
    updateLabel(labelEl, model.get("start_date"), model.get("end_date"));

    function buildChart() {
      const data = model.get("events");
      const startDateStr = model.get("start_date");
      const endDateStr = model.get("end_date");
      const startDate = startDateStr ? new Date(startDateStr) : null;
      const endDate = endDateStr ? new Date(endDateStr) : null;

      const chart = Plot.plot({
        width: 600,
        height: 170,
        marginLeft: 50,
        marginTop: 20,
        marginBottom: 60,
        style: { color: "inherit", background: "var(--ptw-bg, transparent)" },
        x: {
          label: "Time",
          grid: false,
          type: "utc",
          tickFormat: d => d3.timeFormat("%Y-%m-%d")(d),
          tickRotate: -45,
          tickSpacing: 80,
        },
        y: {
          label: "Processes",
        },
        marks: [
          Plot.ruleY([0]),
          Plot.rectY(
            data,
            Plot.binX(
              { y: "count" },
              {
                x: d => new Date(d.TargetProcessCreationTime),
                fill: "var(--ptw-bar-fill, #6b7280)",
                tip: true,
                thresholds: 20,
              }
            )
          ),
          (index, scales, channels, dimensions) => {
            const { marginLeft, marginRight, width, height } = dimensions;
            const { marginTop: mt = 0 } = dimensions;
            const brush = d3.brushX()
              .extent([[marginLeft, mt], [width - marginRight, height - dimensions.marginBottom]])
              .on("brush end", (event) => {
                if (!event.sourceEvent) return;
                clearTimeout(debounceTimer);
                if (event.type === "end") {
                  if (!event.selection) {
                    model.set("start_date", null);
                    model.set("end_date", null);
                    model.save_changes();
                    return;
                  }
                  debounceTimer = setTimeout(() => {
                    const [s, e] = event.selection.map(scales.x.invert);
                    model.set("start_date", s.toISOString());
                    model.set("end_date", e.toISOString());
                    model.save_changes();
                  }, 150);
                }
              });

            const g = d3.create("svg:g").call(brush);
            if (startDate && endDate) {
              g.call(brush.move, [startDate, endDate].map(scales.x));
            }
            return g.node();
          },
        ],
      });

      el.innerHTML = "";
      el.appendChild(chart);
      el.appendChild(labelEl);
      updateLabel(labelEl, startDateStr, endDateStr);
    }

    buildChart();

    const onEventsChange = () => buildChart();
    const onDateChange = () => updateLabel(labelEl, model.get("start_date"), model.get("end_date"));
    model.on("change:events", onEventsChange);
    model.on("change:start_date", onDateChange);
    model.on("change:end_date", onDateChange);

    return () => {
      clearTimeout(debounceTimer);
      model.off("change:events", onEventsChange);
      model.off("change:start_date", onDateChange);
      model.off("change:end_date", onDateChange);
      el.innerHTML = "";
    };
  },
};
