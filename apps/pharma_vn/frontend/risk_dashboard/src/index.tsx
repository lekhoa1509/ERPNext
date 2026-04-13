import React from "react";
import { createRoot, type Root } from "react-dom/client";

import { RiskDashboard } from "./RiskDashboard";
import type { RiskDashboardData } from "./types";

declare global {
    interface Window {
        renderRiskWidget?: (data: RiskDashboardData, target?: string | Element | null) => void;
        destroyRiskWidget?: (target?: string | Element | null) => void;
    }
}

const roots = new WeakMap<Element, Root>();

function resolveContainer(target?: string | Element | null): Element | null {
    if (typeof target === "string") {
        return document.getElementById(target);
    }
    if (target instanceof Element) {
        return target;
    }
    return document.getElementById("risk-root");
}

function renderRiskWidget(data: RiskDashboardData, target?: string | Element | null) {
    const container = resolveContainer(target);
    if (!container) {
        return;
    }

    let root = roots.get(container);
    if (!root) {
        root = createRoot(container);
        roots.set(container, root);
    }

    root.render(
        <React.StrictMode>
            <RiskDashboard data={data} />
        </React.StrictMode>
    );
}

function destroyRiskWidget(target?: string | Element | null) {
    const container = resolveContainer(target);
    if (!container) {
        return;
    }

    const root = roots.get(container);
    if (!root) {
        container.innerHTML = "";
        return;
    }

    root.unmount();
    roots.delete(container);
}

window.renderRiskWidget = renderRiskWidget;
window.destroyRiskWidget = destroyRiskWidget;
