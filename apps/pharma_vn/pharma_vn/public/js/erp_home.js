window.pharma_vn = window.pharma_vn || {};

(() => {
    const BODY_CLASS = "pharma-erp-home-enabled";
    const ROOT_CLASS = "pharma-erp-home";
    const ROOT_SELECTOR = `.${ROOT_CLASS}`;
    const MODULES_HEAD_CLASS = "pharma-erp-home__modules-head";
    const MODULES_HEAD_SELECTOR = `.${MODULES_HEAD_CLASS}`;
    const LAYOUT_EDIT_CLASS = "pharma-erp-home-layout-editing";
    const DASHBOARD_API_METHOD = "pharma_vn.api.desk_dashboard.get_desk_dashboard";
    const DASHBOARD_CACHE_TTL = 3 * 60 * 1000;
    const MAX_RETRY_ATTEMPTS = 18;
    const ICON_WORKSPACE_FALLBACKS = {
        Accounting: ["Invoicing", "Financial Reports"],
        Accounts: ["Invoicing", "Financial Reports"],
        "Kế toán": ["Invoicing", "Financial Reports"],
    };
    const REQUIRED_DESKTOP_ICONS = [
        {
            label: "HRM",
            name: "HRM",
            icon: "users",
            icon_type: "Link",
            link_type: "Workspace Sidebar",
            link_to: "HRM",
            hidden: 0,
            idx: 999,
            parent_icon: "",
        },
    ];

    let isBound = false;
    let applyTimeout = null;
    let retryHandle = null;
    let retryCount = 0;
    let bodyObserver = null;
    let lastLayoutEditState = false;
    let applySequence = 0;
    let desktopLayoutPromise = null;
    let hasFetchedServerDesktopLayout = false;

    const dashboardState = {
        data: null,
        loadedAt: 0,
        promise: null,
    };

    function t(value, replace) {
        const source = String(value ?? "");
        const translator =
            (typeof window !== "undefined" && typeof window.__ === "function" && window.__) ||
            (typeof frappe !== "undefined" && typeof frappe._ === "function" && frappe._);

        if (!translator) {
            return source;
        }

        try {
            return translator(source, replace);
        } catch (error) {
            return source;
        }
    }

    function getLocalizedLabel(value) {
        return t(value || "");
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function isDeskRoute() {
        const path = window.location.pathname || "";
        return path === "/" || path.startsWith("/app") || path.startsWith("/desk");
    }

    function isDesktopRoute() {
        if (!isDeskRoute()) {
            return false;
        }

        const route = frappe.get_route ? frappe.get_route() : [];
        return !route.length || !route[0] || route[0] === "desktop";
    }

    function getCurrentLanguage() {
        return String(
            frappe?.boot?.user?.language ||
                frappe?.boot?.lang ||
                frappe?.boot?.sysdefaults?.language ||
                document.documentElement.lang ||
                navigator.language ||
                "en"
        ).trim();
    }

    function getCurrentLocale() {
        const language = getCurrentLanguage();
        const normalized = language.replace(/_/g, "-");
        if (normalized.includes("-")) {
            return normalized;
        }

        return (
            {
                en: "en-US",
                vi: "vi-VN",
            }[normalized] || normalized || "en-US"
        );
    }

    function formatClock() {
        return new Intl.DateTimeFormat(getCurrentLocale(), {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        }).format(new Date());
    }

    function formatCompactDay(offset) {
        const day = new Date();
        day.setDate(day.getDate() - offset);
        return new Intl.DateTimeFormat(getCurrentLocale(), {
            day: "2-digit",
            month: "short",
        }).format(day);
    }

    function formatNumber(value) {
        return new Intl.NumberFormat(getCurrentLocale()).format(Number(value) || 0);
    }

    function isVisible(element) {
        if (!element) {
            return false;
        }

        const style = window.getComputedStyle(element);
        if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity) === 0) {
            return false;
        }

        return Boolean(element.offsetWidth || element.offsetHeight || element.getClientRects().length);
    }

    function isLayoutEditing() {
        if (!isDesktopRoute()) {
            return false;
        }

        // Frappe khong expose trang thai Desktop Edit ro rang, nen phai suy ra tu nut Save/Discard.
        const actionButtons = Array.from(document.querySelectorAll("button, .btn, a.btn"));
        const hasDiscard = actionButtons.some((button) => {
            const text = (button.innerText || "").trim();
            return (
                isVisible(button) &&
                (button.classList.contains("discard-button") || button.classList.contains("discard") || text === "Discard")
            );
        });
        const hasSave = actionButtons.some((button) => {
            const text = (button.innerText || "").trim();
            return (
                isVisible(button) &&
                (button.classList.contains("save-sidebar") || button.classList.contains("save") || text === "Save" || text === "Lưu")
            );
        });

        return hasDiscard && hasSave;
    }

    function setLayoutEditState(editing) {
        lastLayoutEditState = editing;
        document.body.classList.toggle(LAYOUT_EDIT_CLASS, editing);
    }

    function getServerDesktopLayoutCache() {
        return Array.isArray(window.pharma_vn.__desktopLayoutCache) ? window.pharma_vn.__desktopLayoutCache : null;
    }

    function setServerDesktopLayoutCache(layout) {
        window.pharma_vn.__desktopLayoutCache = Array.isArray(layout) ? layout : null;
        hasFetchedServerDesktopLayout = Array.isArray(layout);
        if (Array.isArray(layout)) {
            // Ghi lai localStorage ngay khi doc tu server de sidebar/home cung nhin cung mot layout.
            frappe.desktop_icons = JSON.parse(JSON.stringify(layout));
            const storageKey = frappe?.session?.user ? `${frappe.session.user}:desktop` : null;
            if (storageKey) {
                localStorage.setItem(storageKey, JSON.stringify(layout));
            }
        }
    }

    function fetchServerDesktopLayout(force = false) {
        if (!frappe?.session?.user || !frappe.db?.get_doc) {
            return Promise.resolve(null);
        }

        if (!force && getServerDesktopLayoutCache()) {
            return Promise.resolve(getServerDesktopLayoutCache());
        }

        if (!force && desktopLayoutPromise) {
            return desktopLayoutPromise;
        }

        desktopLayoutPromise = Promise.resolve(
            frappe.db.get_doc("Desktop Layout", frappe.session.user)
        )
            .then((doc) => {
                const layout = JSON.parse(doc?.layout || "[]");
                setServerDesktopLayoutCache(Array.isArray(layout) ? layout : null);
                return getServerDesktopLayoutCache();
            })
            .catch(() => null)
            .finally(() => {
                desktopLayoutPromise = null;
            });

        return desktopLayoutPromise;
    }

    function getDesktopLayoutSource() {
        const serverCache = getServerDesktopLayoutCache();
        if (hasFetchedServerDesktopLayout && Array.isArray(serverCache)) {
            return serverCache;
        }

        // Chi fallback local cache khi chua fetch duoc server, tranh de cache cu ghi de layout moi.
        if (Array.isArray(frappe?.desktop_icons) && frappe.desktop_icons.length) {
            return frappe.desktop_icons;
        }

        const storageKey = frappe?.session?.user ? `${frappe.session.user}:desktop` : null;
        if (storageKey) {
            const rawValue = localStorage.getItem(storageKey);
            if (rawValue && rawValue !== "null" && rawValue !== "undefined") {
                try {
                    const parsed = JSON.parse(rawValue);
                    if (Array.isArray(parsed) && parsed.length) {
                        return parsed;
                    }
                } catch (error) {
                    // Ignore invalid local layout cache and fall back to boot data.
                }
            }
        }

        return frappe?.boot?.desktop_icons || [];
    }

    function hasDesktopIcon(icons, target) {
        const keys = [target?.label, target?.name, target?.link_to]
            .map((value) => String(value || "").trim().toLowerCase())
            .filter(Boolean);

        if (!keys.length) {
            return false;
        }

        return icons.some((icon) => {
            const iconKeys = [icon?.label, icon?.name, icon?.link_to]
                .map((value) => String(value || "").trim().toLowerCase())
                .filter(Boolean);

            return iconKeys.some((key) => keys.includes(key));
        });
    }

    function withRequiredDesktopIcons(icons) {
        const source = Array.isArray(icons) ? icons.filter(Boolean).map((icon) => ({ ...icon })) : [];

        REQUIRED_DESKTOP_ICONS.forEach((icon) => {
            if (!hasDesktopIcon(source, icon)) {
                source.push({ ...icon });
            }
        });

        return source;
    }

    function getDesktopIcons() {
        const icons = withRequiredDesktopIcons(getDesktopLayoutSource());
        const hiddenParents = new Set(
            icons.filter((icon) => icon && icon.hidden == 1).map((icon) => icon.label)
        );

        return icons
            .filter((icon) => icon && icon.hidden != 1)
            .filter((icon) => !icon.parent_icon || hiddenParents.has(icon.parent_icon))
            .filter((icon) => !["My Workspaces", "AI Assistant"].includes(icon.label))
            .sort((left, right) => {
                if ((left.idx || 0) === (right.idx || 0)) {
                    return (left.label || "").localeCompare(right.label || "");
                }
                return (left.idx || 0) - (right.idx || 0);
            });
    }


    function getChildIconsForIcon(icon) {
        if (!icon) {
            return [];
        }

        if (Array.isArray(icon.child_icons) && icon.child_icons.length) {
            return icon.child_icons.filter((child) => child && child.hidden != 1);
        }

        const parentLabel = String(icon.label || icon.name || "").trim();
        if (!parentLabel) {
            return [];
        }

        return getDesktopLayoutSource()
            .filter((child) => child && child.hidden != 1)
            .filter((child) => String(child.parent_icon || "").trim() === parentLabel)
            .sort((left, right) => (left.idx || 0) - (right.idx || 0));
    }

    function iconOpensWorkspacePicker(icon) {
        const iconType = String(icon?.icon_type || "").trim();
        if (!["Folder", "App"].includes(iconType)) {
            return false;
        }

        return getChildIconsForIcon(icon).length > 0;
    }

    function slugifyWorkspace(workspaceName) {
        const source = String(workspaceName || "").trim();
        if (!source) {
            return "";
        }

        return (
            frappe.router?.slug?.(source) ||
            source
                .toLowerCase()
                .replace(/\s+/g, "-")
                .replace(/[^a-z0-9-]/g, "")
        );
    }

    function getWorkspaceRoute(workspaceName) {
        const source = String(workspaceName || "").trim();
        if (!source) {
            return "";
        }

        const slug = slugifyWorkspace(source);
        const workspace = frappe?.workspace_map?.[source] || frappe?.workspaces?.[slug];
        if (!workspace || !slug) {
            return "";
        }

        return workspace?.public === 0 || workspace?.public === "0" ? `/desk/private/${slug}` : `/desk/${slug}`;
    }

    function getFallbackRouteForIcon(icon) {
        if (!icon) {
            return "";
        }

        const directCandidates = [icon.link_to, icon.sidebar, icon.label, icon.name]
            .map((value) => String(value || "").trim())
            .filter(Boolean);

        for (const candidate of directCandidates) {
            const route = getWorkspaceRoute(candidate);
            if (route) {
                return route;
            }
        }

        const localizedKeys = [icon.label, icon.name]
            .map((value) => getLocalizedLabel(value))
            .filter(Boolean);
        const fallbackKeys = [...directCandidates, ...localizedKeys];

        for (const key of fallbackKeys) {
            const fallbackWorkspaces = ICON_WORKSPACE_FALLBACKS[key];
            if (!Array.isArray(fallbackWorkspaces)) {
                continue;
            }

            for (const workspaceName of fallbackWorkspaces) {
                const route = getWorkspaceRoute(workspaceName);
                if (route) {
                    return route;
                }
            }
        }

        return "";
    }

    function getRouteForIcon(icon) {
        if (!icon) {
            return "#";
        }

        if (iconOpensWorkspacePicker(icon)) {
            return "";
        }

        if (frappe.utils?.get_route_for_icon) {
            const resolvedRoute = frappe.utils.get_route_for_icon(icon);
            if (resolvedRoute) {
                return resolvedRoute;
            }
        }

        const fallbackRoute = getFallbackRouteForIcon(icon);
        if (fallbackRoute) {
            return fallbackRoute;
        }

        if (icon.link && icon.link_type === "External") {
            return icon.link.startsWith("http") ? icon.link : `${window.location.origin}${icon.link}`;
        }

        return "#";
    }

    function openDesktopIconPicker(iconLabel) {
        const icon = getDesktopIcons().find((item) => item && item.label === iconLabel);
        const childIcons = getChildIconsForIcon(icon);
        if (!icon || !childIcons.length || !frappe.desktop_utils?.create_desktop_modal) {
            return false;
        }

        const modalIcon = {
            icon_title: icon.label,
            child_icons: childIcons,
        };
        const modal = frappe.desktop_utils.create_desktop_modal(modalIcon);
        modal.setup(icon.label, childIcons, 4);
        modal.show();
        return true;
    }

    function getFormRoute(doctype, name) {
        if (!doctype || !name) {
            return "#";
        }

        const slug =
            frappe.router?.slug?.(doctype) ||
            frappe.router?.slug?.(doctype.toLowerCase()) ||
            String(doctype)
                .trim()
                .toLowerCase()
                .replace(/\s+/g, "-");

        return `/app/${slug}/${encodeURIComponent(name)}`;
    }

    function getModuleIconMarkup(icon) {
        const localizedLabel = getLocalizedLabel(icon?.label);
        const desktopIcon = frappe.utils?.get_desktop_icon?.(icon.label, frappe.boot?.desktop_icon_style);
        if (desktopIcon) {
            return `<img src="${escapeHtml(desktopIcon)}" alt="${escapeHtml(localizedLabel)}">`;
        }

        if (icon.logo_url || icon.icon_image) {
            return `<img src="${escapeHtml(icon.logo_url || icon.icon_image)}" alt="${escapeHtml(localizedLabel)}">`;
        }

        if (icon.icon && icon.icon.startsWith("fa ")) {
            return `<span class="pharma-erp-home__quick-icon-fa ${escapeHtml(icon.icon)}" aria-hidden="true"></span>`;
        }

        return `<span>${escapeHtml(localizedLabel.slice(0, 1))}</span>`;
    }

    function buildPolylinePoints(values, width, height, padding) {
        const safeValues = Array.isArray(values) && values.length ? values : [0];
        const maxValue = Math.max(...safeValues, 1);
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;
        const stepX = safeValues.length > 1 ? chartWidth / (safeValues.length - 1) : 0;

        return safeValues
            .map((value, index) => {
                const x = padding + stepX * index;
                const normalized = maxValue > 0 ? Number(value || 0) / maxValue : 0;
                const y = height - padding - normalized * chartHeight;
                return `${x.toFixed(2)},${y.toFixed(2)}`;
            })
            .join(" ");
    }

    function buildSparklineMarkup(values, color) {
        const points = buildPolylinePoints(values, 160, 52, 8);
        return `
            <svg viewBox="0 0 160 52" preserveAspectRatio="none" aria-hidden="true">
                <polyline
                    points="${points}"
                    fill="none"
                    stroke="${escapeHtml(color || "#5b8cff")}"
                    stroke-width="3"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                ></polyline>
            </svg>
        `;
    }

    function buildTimelineMarkup(timeline) {
        const labels = Array.isArray(timeline?.labels) && timeline.labels.length ? timeline.labels : [];
        const series = Array.isArray(timeline?.series) && timeline.series.length ? timeline.series : [];
        const width = 820;
        const height = 250;
        const padding = 28;
        const maxValue = Math.max(
            1,
            ...series.flatMap((item) => (Array.isArray(item.values) ? item.values : [0])).map((value) => Number(value) || 0)
        );
        const gridLines = [0.2, 0.4, 0.6, 0.8].map((ratio) => {
            const y = padding + (height - padding * 2) * ratio;
            return `<line x1="${padding}" y1="${y}" x2="${width - padding}" y2="${y}" />`;
        });

        const lines = series
            .map((item) => {
                const points = buildPolylinePoints(item.values, width, height, padding);
                return `
                    <polyline
                        class="pharma-erp-home__chart-line"
                        points="${points}"
                        fill="none"
                        stroke="${escapeHtml(item.color || "#5b8cff")}"
                        stroke-width="3"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    ></polyline>
                `;
            })
            .join("");

        const legend = series
            .map(
                (item) => `
                    <span class="pharma-erp-home__legend-item">
                        <span class="pharma-erp-home__legend-dot" style="background:${escapeHtml(item.color || "#5b8cff")}"></span>
                        ${escapeHtml(getLocalizedLabel(item.name || "Series"))}
                    </span>
                `
            )
            .join("");

        const axis = labels
            .map((label) => `<span class="pharma-erp-home__axis-label">${escapeHtml(label)}</span>`)
            .join("");

        return `
            <div class="pharma-erp-home__chart-shell">
                <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
                    <g class="pharma-erp-home__chart-grid">${gridLines.join("")}</g>
                    ${lines}
                </svg>
            </div>
            <div class="pharma-erp-home__axis" style="grid-template-columns: repeat(${Math.max(labels.length, 1)}, minmax(0, 1fr));">
                ${axis}
            </div>
            <div class="pharma-erp-home__legend">${legend}</div>
        `;
    }

    function buildWorkloadMarkup(items) {
        const list = Array.isArray(items) ? items : [];
        if (!list.length) {
            return `<div class="pharma-erp-home__empty">Chưa có hàng chờ xử lý để hiển thị.</div>`;
        }

        const maxValue = Math.max(...list.map((item) => Number(item.value) || 0), 1);
        return `
            <div class="pharma-erp-home__queue">
                ${list
                    .map((item) => {
                        const ratio = Math.max(8, Math.round(((Number(item.value) || 0) / maxValue) * 100));
                        return `
                            <article class="pharma-erp-home__queue-item">
                                <div class="pharma-erp-home__queue-top">
                                    <span>${escapeHtml(getLocalizedLabel(item.label))}</span>
                                    <strong>${formatNumber(item.value)}</strong>
                                </div>
                                <div class="pharma-erp-home__queue-meter">
                                    <span style="--pharma-meter:${ratio}%"></span>
                                </div>
                                <p>${escapeHtml(getLocalizedLabel(item.hint || ""))}</p>
                            </article>
                        `;
                    })
                    .join("")}
            </div>
        `;
    }

    function buildRecentMarkup(items) {
        const list = Array.isArray(items) ? items : [];
        if (!list.length) {
            return `<div class="pharma-erp-home__empty">Chưa có chứng từ mới. Sau khi import hoặc phát sinh giao dịch, mục này sẽ tự cập nhật.</div>`;
        }

        return `
            <div class="pharma-erp-home__recent-list">
                ${list
                    .map((item) => {
                        const route = getFormRoute(item.doctype, item.name);
                        return `
                            <a class="pharma-erp-home__recent-item" href="${escapeHtml(route)}">
                                <div class="pharma-erp-home__recent-type">${escapeHtml(
                                    getLocalizedLabel(item.doctype_label || item.doctype)
                                )}</div>
                                <div class="pharma-erp-home__recent-title">${escapeHtml(item.name)}</div>
                                <div class="pharma-erp-home__recent-meta">
                                    <span>${escapeHtml(item.counterparty || getLocalizedLabel("No counterparty"))}</span>
                                    <span>${escapeHtml(item.date_label || "")}</span>
                                </div>
                                <div class="pharma-erp-home__recent-status">${escapeHtml(
                                    getLocalizedLabel(item.status || "Draft")
                                )}</div>
                            </a>
                        `;
                    })
                    .join("")}
            </div>
        `;
    }

    function buildHighlightsMarkup(items) {
        const list = Array.isArray(items) ? items : [];
        if (!list.length) {
            return "";
        }

        return `
            <div class="pharma-erp-home__highlight-grid">
                ${list
                    .map(
                        (item) => `
                            <article class="pharma-erp-home__highlight">
                                <strong>${formatNumber(item.value)}</strong>
                                <span>${escapeHtml(getLocalizedLabel(item.label))}</span>
                                <p>${escapeHtml(getLocalizedLabel(item.hint || ""))}</p>
                            </article>
                        `
                    )
                    .join("")}
            </div>
        `;
    }

    function getPrimaryActions(icons) {
        const priorities = ["Bán hàng", "Mua hàng", "Kho", "Kế toán", "Selling", "Buying", "Stock", "Accounting"];
        const selected = [];

        priorities.forEach((label) => {
            const match = icons.find((icon) => icon.label === label);
            if (match && !selected.some((item) => item.label === match.label)) {
                selected.push(match);
            }
        });

        icons.forEach((icon) => {
            if (selected.length >= 4) {
                return;
            }
            if (!selected.some((item) => item.label === icon.label)) {
                selected.push(icon);
            }
        });

        return selected.slice(0, 4);
    }

    function buildModuleSidebarMarkup(icons) {
        if (!icons.length) {
            return `
                <aside class="pharma-erp-home__sidebar">
                    <div class="pharma-erp-home__sidebar-head">
                        <div>
                            <div class="pharma-erp-home__panel-eyebrow">${escapeHtml(
                                getLocalizedLabel("Workspace Navigation")
                            )}</div>
                            <h3>${escapeHtml(getLocalizedLabel("Modules"))}</h3>
                        </div>
                    </div>
                    <div class="pharma-erp-home__sidebar-empty">${escapeHtml(
                        getLocalizedLabel("No modules to display.")
                    )}</div>
                </aside>
            `;
        }

        return `
            <aside class="pharma-erp-home__sidebar">
                <div class="pharma-erp-home__sidebar-head">
                    <div>
                        <div class="pharma-erp-home__panel-eyebrow">${escapeHtml(
                            getLocalizedLabel("Workspace Navigation")
                        )}</div>
                        <h3>${escapeHtml(getLocalizedLabel("Modules"))}</h3>
                    </div>
                    <span class="pharma-erp-home__sidebar-count">${formatNumber(icons.length)}</span>
                </div>
                <p class="pharma-erp-home__sidebar-copy">${escapeHtml(
                    getLocalizedLabel("Open each business area directly from Desk without scanning the old icon grid.")
                )}</p>
                <nav class="pharma-erp-home__module-list" aria-label="${escapeHtml(getLocalizedLabel("ERP Modules"))}">
                    ${icons
                        .map((icon, index) => {
                            const actionLabel = getLocalizedLabel(
                                iconOpensWorkspacePicker(icon) ? "Choose workspace" : "Open workspace"
                            );
                            const content = `
                                <span class="pharma-erp-home__module-icon">${getModuleIconMarkup(icon)}</span>
                                <span class="pharma-erp-home__module-copy">
                                    <strong>${escapeHtml(getLocalizedLabel(icon.label))}</strong>
                                    <small>${escapeHtml(actionLabel)}</small>
                                </span>
                            `;

                            if (iconOpensWorkspacePicker(icon)) {
                                return `
                                    <button
                                        type="button"
                                        class="pharma-erp-home__module-link"
                                        data-pharma-workspace-picker="${escapeHtml(icon.label)}"
                                        style="--pharma-stagger:${index + 1}"
                                    >
                                        ${content}
                                    </button>
                                `;
                            }

                            return `
                                <a class="pharma-erp-home__module-link" href="${escapeHtml(
                                    getRouteForIcon(icon)
                                )}" style="--pharma-stagger:${index + 1}">
                                    ${content}
                                </a>
                            `;
                        })
                        .join("")}
                </nav>
            </aside>
        `;
    }

    function getDefaultDashboardData() {
        const icons = getDesktopIcons();
        return {
            ok: true,
            generated_at_label: formatClock(),
            hero_note: "Run sales, purchasing, stock, and finance from one focused dashboard.",
            summary_cards: [
                {
                    key: "items",
                    label: "Item Master",
                    value: 0,
                    hint: "Master data will appear here after import.",
                    sparkline: [0, 0, 0, 0, 0, 0, 0, 0],
                    color: "#5b8cff",
                },
                {
                    key: "customers",
                    label: "Customer Master",
                    value: 0,
                    hint: "Customer records are waiting for live data.",
                    sparkline: [0, 0, 0, 0, 0, 0, 0, 0],
                    color: "#18b7a0",
                },
                {
                    key: "sales_30d",
                    label: "Sales Orders (30 Days)",
                    value: 0,
                    hint: "Activity volume will appear here once transactions begin.",
                    sparkline: [0, 0, 0, 0, 0, 0, 0, 0],
                    color: "#f08b3e",
                },
                {
                    key: "modules",
                    label: "Available Modules",
                    value: icons.length,
                    hint: "All workspaces are ready to access from the left navigation.",
                    sparkline: Array.from({ length: 8 }, (_, index) => Math.min(icons.length, index + 1)),
                    color: "#7856ff",
                },
            ],
            timeline: {
                labels: Array.from({ length: 14 }, (_, index) => formatCompactDay(13 - index)),
                series: [
                    { name: "Sales Orders", color: "#18b7a0", values: Array(14).fill(0) },
                    { name: "Purchase Orders", color: "#5b8cff", values: Array(14).fill(0) },
                    { name: "Sales Invoices", color: "#f08b3e", values: Array(14).fill(0) },
                ],
            },
            workload: [
                {
                    label: "SO chờ duyệt",
                    value: 0,
                    hint: "Approval pipeline will appear here as sales data arrives.",
                },
                {
                    label: "DN chờ submit",
                    value: 0,
                    hint: "Delivery preparation and dispatch progress are collected here.",
                },
                {
                    label: "PO đang mở",
                    value: 0,
                    hint: "Open purchase orders will be highlighted here.",
                },
            ],
            recent_documents: [],
            highlights: [
                { label: "Warehouses", value: 0, hint: "Warehouses are ready for operations." },
                { label: "Accounts", value: 0, hint: "Financial foundation is ready for accounting." },
                { label: "Sales Taxes", value: 0, hint: "Tax templates are ready for the sales flow." },
                { label: "Purchase Taxes", value: 0, hint: "Tax templates are ready for the purchase flow." },
            ],
        };
    }

    function normalizeDashboardData(rawData) {
        const fallback = getDefaultDashboardData();
        const source = rawData && rawData.ok !== false ? rawData : fallback;
        const summaryCards = Array.isArray(source.summary_cards) && source.summary_cards.length ? source.summary_cards : fallback.summary_cards;

        return {
            ok: true,
            generated_at_label: source.generated_at_label || fallback.generated_at_label,
            hero_note: source.hero_note || fallback.hero_note,
            summary_cards: summaryCards.slice(0, 4),
            timeline: source.timeline || fallback.timeline,
            workload: Array.isArray(source.workload) ? source.workload : fallback.workload,
            recent_documents: Array.isArray(source.recent_documents) ? source.recent_documents : fallback.recent_documents,
            highlights: Array.isArray(source.highlights) ? source.highlights : fallback.highlights,
        };
    }

    function renderLoading(root) {
        root.classList.remove("is-ready");
        root.innerHTML = `
            <section class="pharma-erp-home__hero pharma-erp-home__hero--loading">
                <div class="pharma-erp-home__loading-title"></div>
                <div class="pharma-erp-home__loading-copy"></div>
                <div class="pharma-erp-home__loading-copy pharma-erp-home__loading-copy--short"></div>
            </section>
        `;
    }

    function renderDashboard(root, rawData) {
        const data = normalizeDashboardData(rawData);
        const icons = getDesktopIcons();
        const primaryActions = getPrimaryActions(icons);
        const moduleSidebar = buildModuleSidebarMarkup(icons);
        const summaryCards = data.summary_cards
            .map(
                (item, index) => `
                    <article class="pharma-erp-home__metric" style="--pharma-stagger:${index + 1}">
                        <div class="pharma-erp-home__metric-label">${escapeHtml(getLocalizedLabel(item.label))}</div>
                        <div class="pharma-erp-home__metric-value">${formatNumber(item.value)}</div>
                        <p>${escapeHtml(getLocalizedLabel(item.hint || ""))}</p>
                        <div class="pharma-erp-home__metric-spark">${buildSparklineMarkup(item.sparkline, item.color || "#5b8cff")}</div>
                    </article>
                `
            )
            .join("");

        const heroActions = primaryActions
            .map((icon) => {
                const content = `
                    <span class="pharma-erp-home__quick-icon">${getModuleIconMarkup(icon)}</span>
                    <span>${escapeHtml(getLocalizedLabel(icon.label))}</span>
                `;

                if (iconOpensWorkspacePicker(icon)) {
                    return `
                        <button
                            type="button"
                            class="pharma-erp-home__quick-link"
                            data-pharma-workspace-picker="${escapeHtml(icon.label)}"
                        >
                            ${content}
                        </button>
                    `;
                }

                return `
                    <a class="pharma-erp-home__quick-link" href="${escapeHtml(getRouteForIcon(icon))}">
                        ${content}
                    </a>
                `;
            })
            .join("");

        root.innerHTML = `
            <div class="pharma-erp-home__shell">
                ${moduleSidebar}
                <div class="pharma-erp-home__main">
                    <section class="pharma-erp-home__hero">
                        <div class="pharma-erp-home__hero-copy">
                            <div class="pharma-erp-home__eyebrow">${escapeHtml(
                                getLocalizedLabel("Enterprise ERP Overview")
                            )}</div>
                            <h1>${escapeHtml(getLocalizedLabel("Business Control Center"))}</h1>
                            <p>${escapeHtml(getLocalizedLabel(data.hero_note))}</p>
                            <div class="pharma-erp-home__hero-meta">
                                <span>${escapeHtml(getLocalizedLabel("Live"))} ${escapeHtml(data.generated_at_label)}</span>
                                <span>${formatNumber(icons.length)} ${escapeHtml(getLocalizedLabel("modules"))}</span>
                            </div>
                        </div>
                        <div class="pharma-erp-home__hero-side">
                            <div class="pharma-erp-home__hero-stat">
                                <strong>${formatNumber(data.summary_cards[0]?.value || 0)}</strong>
                                <span>${escapeHtml(getLocalizedLabel(data.summary_cards[0]?.label || "KPI"))}</span>
                            </div>
                            <div class="pharma-erp-home__quick-links">
                                ${heroActions}
                            </div>
                            <button type="button" class="pharma-erp-home__refresh" data-pharma-refresh>
                                ${escapeHtml(getLocalizedLabel("Refresh dashboard"))}
                            </button>
                        </div>
                    </section>

                    <section class="pharma-erp-home__metrics">
                        ${summaryCards}
                    </section>

                    <section class="pharma-erp-home__content-grid">
                        <article class="pharma-erp-home__panel pharma-erp-home__panel--wide">
                            <div class="pharma-erp-home__panel-head">
                                <div>
                                    <div class="pharma-erp-home__panel-eyebrow">${escapeHtml(
                                        getLocalizedLabel("Operations Pulse")
                                    )}</div>
                                    <h3>${escapeHtml(getLocalizedLabel("Document Flow Over 14 Days"))}</h3>
                                </div>
                            </div>
                            ${buildTimelineMarkup(data.timeline)}
                        </article>

                        <article class="pharma-erp-home__panel">
                            <div class="pharma-erp-home__panel-head">
                                <div>
                                    <div class="pharma-erp-home__panel-eyebrow">${escapeHtml(
                                        getLocalizedLabel("Work Queue")
                                    )}</div>
                                    <h3>${escapeHtml(getLocalizedLabel("Pending Actions"))}</h3>
                                </div>
                            </div>
                            ${buildWorkloadMarkup(data.workload)}
                        </article>
                    </section>

                    <section class="pharma-erp-home__content-grid pharma-erp-home__content-grid--secondary">
                        <article class="pharma-erp-home__panel">
                            <div class="pharma-erp-home__panel-head">
                                <div>
                                    <div class="pharma-erp-home__panel-eyebrow">${escapeHtml(
                                        getLocalizedLabel("Recent Activity")
                                    )}</div>
                                    <h3>${escapeHtml(getLocalizedLabel("Latest Documents"))}</h3>
                                </div>
                            </div>
                            ${buildRecentMarkup(data.recent_documents)}
                        </article>

                        <article class="pharma-erp-home__panel">
                            <div class="pharma-erp-home__panel-head">
                                <div>
                                    <div class="pharma-erp-home__panel-eyebrow">${escapeHtml(
                                        getLocalizedLabel("System Readiness")
                                    )}</div>
                                    <h3>${escapeHtml(getLocalizedLabel("Core Setup Status"))}</h3>
                                </div>
                            </div>
                            ${buildHighlightsMarkup(data.highlights)}
                        </article>
                    </section>
                </div>
            </div>
        `;

        root.querySelector("[data-pharma-refresh]")?.addEventListener("click", () => {
            applyDesktopHome(true);
        });
        root.querySelectorAll("[data-pharma-workspace-picker]").forEach((element) => {
            element.addEventListener("click", (event) => {
                event.preventDefault();
                const iconLabel = element.getAttribute("data-pharma-workspace-picker") || "";
                if (!openDesktopIconPicker(iconLabel)) {
                    const icon = getDesktopIcons().find((item) => item && item.label === iconLabel);
                    const route = getRouteForIcon(icon);
                    if (route && route !== "#") {
                        window.location.href = route;
                    }
                }
            });
        });

        window.requestAnimationFrame(() => {
            root.classList.add("is-ready");
        });
    }

    function fetchDashboardData(force = false) {
        if (!window.frappe?.call) {
            return Promise.resolve(getDefaultDashboardData());
        }

        if (force) {
            dashboardState.data = null;
            dashboardState.loadedAt = 0;
        }

        const now = Date.now();
        if (dashboardState.data && now - dashboardState.loadedAt < DASHBOARD_CACHE_TTL) {
            return Promise.resolve(dashboardState.data);
        }

        if (dashboardState.promise) {
            return dashboardState.promise;
        }

        dashboardState.promise = Promise.resolve(
            frappe.call({
                method: DASHBOARD_API_METHOD,
            })
        )
            .then((response) => {
                dashboardState.data = response?.message || getDefaultDashboardData();
                dashboardState.loadedAt = Date.now();
                return dashboardState.data;
            })
            .catch(() => {
                dashboardState.data = getDefaultDashboardData();
                dashboardState.loadedAt = Date.now();
                return dashboardState.data;
            })
            .then((data) => {
                dashboardState.promise = null;
                return data;
            });

        return dashboardState.promise;
    }

    function ensureDesktopSections() {
        const container = document.querySelector(".desktop-container");
        const iconsContainer = container?.querySelector(".icons-container");
        if (!container || !iconsContainer) {
            return null;
        }

        let root = container.querySelector(ROOT_SELECTOR);
        if (!root) {
            root = document.createElement("section");
            root.className = ROOT_CLASS;
            container.insertBefore(root, iconsContainer);
        }

        let modulesHead = container.querySelector(MODULES_HEAD_SELECTOR);
        if (!modulesHead) {
            modulesHead = document.createElement("div");
            modulesHead.className = MODULES_HEAD_CLASS;
            container.insertBefore(modulesHead, iconsContainer);
        }

        return { container, root, modulesHead };
    }

    function updateModulesHead(modulesHead) {
        if (!modulesHead) {
            return;
        }

        const icons = getDesktopIcons();
        modulesHead.innerHTML = `
            <div>
                <div class="pharma-erp-home__panel-eyebrow">${escapeHtml(getLocalizedLabel("Workspace Modules"))}</div>
                <h3>${escapeHtml(getLocalizedLabel("Functional Areas"))}</h3>
            </div>
            <div class="pharma-erp-home__modules-chip">${formatNumber(icons.length)} ${escapeHtml(
                getLocalizedLabel("modules ready")
            )}</div>
        `;
    }

    function cleanupDesktopHome() {
        document.body.classList.remove(BODY_CLASS);
        document.querySelectorAll(`${ROOT_SELECTOR}, ${MODULES_HEAD_SELECTOR}`).forEach((node) => node.remove());
    }

    function applyDesktopHome(force = false) {
        const runId = ++applySequence;

        if (!isDesktopRoute() || frappe.is_mobile?.()) {
            setLayoutEditState(false);
            cleanupDesktopHome();
            return;
        }

        if (isLayoutEditing()) {
            setLayoutEditState(true);
            cleanupDesktopHome();
            return;
        }

        setLayoutEditState(false);

        const sections = ensureDesktopSections();
        if (!sections) {
            return;
        }

        document.body.classList.add(BODY_CLASS);
        updateModulesHead(sections.modulesHead);

        if (!sections.root.dataset.loaded || force) {
            renderLoading(sections.root);
        }

        fetchDashboardData(force).then((data) => {
            if (runId !== applySequence) {
                return;
            }

            const editing = isLayoutEditing();
            if (!isDesktopRoute() || editing) {
                setLayoutEditState(editing);
                cleanupDesktopHome();
                return;
            }

            const freshSections = ensureDesktopSections();
            if (!freshSections) {
                return;
            }

            document.body.classList.add(BODY_CLASS);
            updateModulesHead(freshSections.modulesHead);
            freshSections.root.dataset.loaded = "1";
            renderDashboard(freshSections.root, data);
        });
    }

    function scheduleApplyDesktopHome(force = false) {
        if (applyTimeout) {
            window.clearTimeout(applyTimeout);
        }

        applyTimeout = window.setTimeout(() => {
            applyTimeout = null;
            applyDesktopHome(force);
        }, 90);
    }

    function stopRetries() {
        if (retryHandle) {
            window.clearInterval(retryHandle);
            retryHandle = null;
        }
        retryCount = 0;
    }

    function startRetries() {
        stopRetries();
        retryHandle = window.setInterval(() => {
            retryCount += 1;
            applyDesktopHome();

            const isReady = !isDesktopRoute() || document.querySelector(".desktop-container .icons-container");
            if (isReady || retryCount >= MAX_RETRY_ATTEMPTS) {
                stopRetries();
            }
        }, 250);
    }

    function bindDesktopHomeEvents() {
        if (isBound) {
            return;
        }

        isBound = true;
        frappe.router?.on?.("change", () => {
            scheduleApplyDesktopHome();
            startRetries();
        });
        $(document).on("app_ready desktop_screen page-change form-refresh", () => {
            scheduleApplyDesktopHome();
        });
        window.addEventListener("load", () => {
            scheduleApplyDesktopHome();
            startRetries();
        });
        if (!bodyObserver && document.body) {
            bodyObserver = new MutationObserver(() => {
                const editing = isLayoutEditing();
                if (editing !== lastLayoutEditState) {
                    scheduleApplyDesktopHome();
                }
            });
            bodyObserver.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ["class"],
            });
        }
    }

    function initializeDesktopHome() {
        bindDesktopHomeEvents();
        scheduleApplyDesktopHome();
        startRetries();
        fetchServerDesktopLayout().then((layout) => {
            if (layout?.length) {
                scheduleApplyDesktopHome(true);
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeDesktopHome, { once: true });
    } else {
        initializeDesktopHome();
    }

    $(document).on("app_ready", initializeDesktopHome);
})();
