import * as d3 from "d3";
import * as Plot from "@observablehq/plot";


// Time-based bar chart showing process counts with proper date handling
export function timeProcessBarplot(data, { width = 400, height = 200, startDate, endDate, setDateRange, resetDateRange }) {
    const defaultDimensions = { width: 400, height: 200 };
    const chartWidth = width || defaultDimensions.width;
    const chartHeight = height || defaultDimensions.height;

    return Plot.plot({
        width: chartWidth,
        height: chartHeight,
        marginLeft: 50, // Add margin to prevent label clipping
        marginBottom: 60, // Add margin to prevent x-axis label clipping
        x: {
            label: "Time",
            grid: false,
            type: "utc",
            tickFormat: d => d3.timeFormat("%Y-%m-%d")(d),
            tickRotate: -45,
            tickSpacing: 80,
        },
        y: {
            label: "Process Count",
        },
        marks: [
            Plot.ruleY([0]),
            Plot.rectY(data,
                Plot.binX(
                    { y: "count" },
                    {
                        x: d => new Date(d.ProcessCreationTime),
                        fill: "#6b7280",
                        tip: true,
                        thresholds: 20
                    }
                )
            ),
            (index, scales, channels, dimensions, context) => {
                const x1 = dimensions.marginLeft;
                const y1 = 0;
                const x2 = dimensions.width - dimensions.marginRight;
                const y2 = dimensions.height;

                let debounceTimer;

                const brushed = (event) => {
                    if (!event.sourceEvent) return;
                    let { selection } = event;

                    // Clear any existing timer
                    clearTimeout(debounceTimer);

                    // Only update on end of brush or after debounce
                    if (event.type === "end") {
                        if (!selection) {
                            resetDateRange();
                            return;
                        }

                        // Debounce the update by 100ms
                        debounceTimer = setTimeout(() => {
                            setDateRange(...selection.map(scales.x.invert));
                        }, 100);
                    }
                };

                const brush = d3.brushX()
                    .extent([[x1, y1], [x2, y2]])
                    .on("brush end", brushed);

                const g = d3.create("svg:g").call(brush);

                if (startDate && endDate) {
                    g.call(brush.move, [startDate, endDate].map(scales.x));
                }

                return g.node();
            }
        ]
    });
}