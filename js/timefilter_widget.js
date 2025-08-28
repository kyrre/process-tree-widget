import { timeProcessBarplot } from "./timefilter.js";
import { html } from "htl";

export default {
    initialize({ model }) {
        console.info('TimeFilterWidget initialized');
        return () => {
            console.info("TimeFilterWidget cleanup");
        };
    },

    render({ model, el }) {
        // Create a layout for the time filter widget
        const layout = html`
            <div style="display: flex; flex-direction: column; gap: 5px;">
                <div id="timefilter-chart-container"></div>
            </div>
        `;

        // Append the layout to the root element
        el.appendChild(layout);

        // Initialize the time chart
        const chartContainer = layout.querySelector("#timefilter-chart-container");
        this.timeChart = timeProcessBarplot(model.get("events"), {
            width: 400,
            height: 250,
            startDate: model.get("_start_date") ? new Date(model.get("_start_date")) : null,
            endDate: model.get("_end_date") ? new Date(model.get("_end_date")) : null,
            setDateRange: (start, end) => {
                model.set("_start_date", start.toISOString());
                model.set("_end_date", end.toISOString());
                model.save_changes();
            },
            resetDateRange: () => {
                model.set("_start_date", null);
                model.set("_end_date", null);
                model.save_changes();
            }
        });
        chartContainer.appendChild(this.timeChart);
    },

    destroy() {
        if (this.timeChart) {
            this.timeChart.remove();
        }
    }
};
