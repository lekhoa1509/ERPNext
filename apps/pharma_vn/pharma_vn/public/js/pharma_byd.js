window.pharma_vn = window.pharma_vn || {};
window.pharma_vn.__removedDesktopIconLabels = window.pharma_vn.__removedDesktopIconLabels || ["AI Assistant"];

(() => {
    const REQUIRED_DESKTOP_ICON_LABELS = ["Warehouse Layout 2D"];
    const REMOVED_DESKTOP_ICON_LABELS = window.pharma_vn.__removedDesktopIconLabels || [];
    const SAVE_LAYOUT_METHOD = "frappe.desk.doctype.desktop_layout.desktop_layout.save_layout";
    let desktopLayoutPromise = null;
    let hasFetchedServerDesktopLayout = false;

    function getDesktopStorageKey() {
        if (!window.frappe || !frappe.session || !frappe.session.user) {
            return null;
        }

        return `${frappe.session.user}:desktop`;
    }

    function getRequiredDesktopIcons() {
        const icons = frappe?.boot?.desktop_icons || [];
        return icons.filter((icon) => REQUIRED_DESKTOP_ICON_LABELS.includes(icon.label));
    }

    function getServerDesktopLayoutCache() {
        return Array.isArray(window.pharma_vn.__desktopLayoutCache) ? window.pharma_vn.__desktopLayoutCache : null;
    }

    function setServerDesktopLayoutCache(layout) {
        window.pharma_vn.__desktopLayoutCache = Array.isArray(layout) ? layout : null;
        hasFetchedServerDesktopLayout = Array.isArray(layout);
        if (Array.isArray(layout)) {
            // Dong bo ca RAM cache va localStorage de tranh UI "nhay" giua layout local va server.
            frappe.desktop_icons = cloneLayout(layout);
            const storageKey = getDesktopStorageKey();
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

    function loadSavedLayout() {
        const storageKey = getDesktopStorageKey();
        if (!storageKey) {
            return null;
        }

        const rawValue = localStorage.getItem(storageKey);
        if (!rawValue || rawValue === "null" || rawValue === "undefined") {
            return null;
        }

        try {
            const parsed = JSON.parse(rawValue);
            return Array.isArray(parsed) ? parsed : null;
        } catch (error) {
            return null;
        }
    }

    function hasIcon(layout, label) {
        return Array.isArray(layout) && layout.some((icon) => icon && icon.label === label);
    }

    function cloneLayout(layout) {
        return JSON.parse(JSON.stringify(layout || []));
    }

    function persistLayout(layout) {
        const storageKey = getDesktopStorageKey();
        if (!storageKey || !Array.isArray(layout)) {
            return;
        }

        localStorage.setItem(storageKey, JSON.stringify(layout));
        // Sau khi user sua layout, coi layout moi la source of truth ngay tren client.
        hasFetchedServerDesktopLayout = true;
        window.pharma_vn.__desktopLayoutCache = cloneLayout(layout);

        if (!window.frappe || !frappe.call || !frappe.session?.user) {
            return;
        }

        frappe.call({
            method: SAVE_LAYOUT_METHOD,
            args: {
                user: frappe.session.user,
                layout: JSON.stringify(layout),
                new_icons: JSON.stringify([]),
            },
        });
    }

    function normalizeDesktopLayout(layout) {
        if (!Array.isArray(layout)) {
            return null;
        }

        // Ham nay vua bo icon khong mong muon, vua ep icon bat buoc luon ton tai.
        const requiredIcons = getRequiredDesktopIcons();
        const mergedLayout = cloneLayout(layout);
        let changed = false;

        for (let index = mergedLayout.length - 1; index >= 0; index -= 1) {
            const icon = mergedLayout[index];
            if (REMOVED_DESKTOP_ICON_LABELS.includes(icon?.label)) {
                mergedLayout.splice(index, 1);
                changed = true;
            }
        }

        requiredIcons.forEach((icon) => {
            if (!hasIcon(mergedLayout, icon.label)) {
                mergedLayout.push(cloneLayout([icon])[0]);
                changed = true;
            }
        });

        return changed ? mergedLayout : null;
    }

    function ensureSavedLayoutContainsRequiredIcons() {
        const savedLayout = loadSavedLayout();
        if (!savedLayout) {
            return;
        }

        const mergedLayout = normalizeDesktopLayout(savedLayout);
        if (mergedLayout) {
            persistLayout(mergedLayout);
        }
    }

    function ensureCurrentDesktopContainsRequiredIcons() {
        if (!Array.isArray(frappe.desktop_icons)) {
            return;
        }

        const mergedLayout = normalizeDesktopLayout(frappe.desktop_icons);
        if (!mergedLayout) {
            return;
        }

        frappe.desktop_icons = mergedLayout;
        persistLayout(mergedLayout);

        if (frappe.pages?.desktop?.desktop_page) {
            frappe.pages.desktop.desktop_page.data = mergedLayout;
            frappe.pages.desktop.desktop_page.update();
        }
    }

    $(document).on("app_ready", () => {
        ensureSavedLayoutContainsRequiredIcons();
        fetchServerDesktopLayout().then(() => {
            ensureCurrentDesktopContainsRequiredIcons();
        });
    });

    $(document).on("desktop_screen", () => {
        ensureSavedLayoutContainsRequiredIcons();
        fetchServerDesktopLayout().then(() => {
            ensureCurrentDesktopContainsRequiredIcons();
        });
    });
})();

(() => {
    const REMOVED_DESKTOP_ICON_LABELS = window.pharma_vn.__removedDesktopIconLabels || [];
    const SHELL_BODY_CLASS = "pharma-shell-enabled";
    const DESKTOP_MODE_CLASS = "pharma-desktop-dashboard-mode";
    const WORKSPACE_MODE_CLASS = "pharma-workspace-mode";
    const MODULE_RAIL_SELECTOR = ".pharma-sidebar-modules";
    const DESKTOP_HERO_SELECTOR = ".pharma-desktop-stage";
    const DESKTOP_META_SELECTOR = ".pharma-desktop-navbar__meta";
    const DESKTOP_DASHBOARD_SELECTOR = ".pharma-desktop-dashboard";
    const DESKTOP_ICONS_HIDDEN_CLASS = "pharma-desktop-icons--hidden";
    const DASHBOARD_API_METHOD = "pharma_vn.api.desk_dashboard.get_desk_dashboard";
    const DASHBOARD_CACHE_TTL = 3 * 60 * 1000;
    const MAX_RETRY_ATTEMPTS = 24;

    let isBound = false;
    let clockIntervalId = null;
    let retryHandle = null;
    let retryCount = 0;
    let shellApplyTimeout = null;
    let lastModuleRailMarkup = "";
    const dashboardState = {
        data: null,
        loadedAt: 0,
        promise: null,
    };

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
        return path.startsWith("/app") || path.startsWith("/desk");
    }

    function isDesktopRoute() {
        const route = frappe.get_route ? frappe.get_route() : [];
        return !route.length || !route[0] || route[0] === "desktop";
    }

    function formatClock() {
        return new Intl.DateTimeFormat("vi-VN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        }).format(new Date());
    }

    function formatNumber(value) {
        return new Intl.NumberFormat("vi-VN").format(Number(value) || 0);
    }

    function formatCompactDay(offset) {
        const day = new Date();
        day.setDate(day.getDate() - offset);
        return new Intl.DateTimeFormat("vi-VN", {
            day: "2-digit",
            month: "short",
        }).format(day);
    }

    function getDesktopLayoutSource() {
        const serverCache = getServerDesktopLayoutCache();
        if (Array.isArray(serverCache) && serverCache.length) {
            return serverCache;
        }

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

    function getDesktopIcons() {
        const icons = getDesktopLayoutSource();
        const hiddenParents = new Set(
            icons.filter((icon) => icon && icon.hidden == 1).map((icon) => icon.label)
        );

        return icons
            .filter((icon) => icon && icon.hidden != 1)
            .filter((icon) => !icon.parent_icon || hiddenParents.has(icon.parent_icon))
            .filter((icon) => !["My Workspaces", ...REMOVED_DESKTOP_ICON_LABELS].includes(icon.label))
            .sort((left, right) => {
                if ((left.idx || 0) === (right.idx || 0)) {
                    return (left.label || "").localeCompare(right.label || "");
                }
                return (left.idx || 0) - (right.idx || 0);
            });
    }

    function getDefaultWorkspace() {
        const preferredLabel = "Pharma Operations";
        const icons = getDesktopIcons();
        return icons.find((icon) => icon.label === preferredLabel)?.label || icons[0]?.label || null;
    }

    function getRouteForIcon(icon) {
        if (!icon) {
            return null;
        }

        if (frappe.utils?.get_route_for_icon) {
            return frappe.utils.get_route_for_icon(icon);
        }

        if (icon.link && icon.link_type === "External") {
            return icon.link.startsWith("http") ? icon.link : `${window.location.origin}${icon.link}`;
        }

        return null;
    }

    function getCurrentSidebarTitles() {
        const sidebar = frappe?.app?.sidebar;
        return {
            current: sidebar?.sidebar_title || null,
            preferred: sidebar?.preferred_sidebars || [],
        };
    }

    function isModuleActive(icon, href) {
        if (isDesktopRoute()) {
            return false;
        }

        const { current, preferred } = getCurrentSidebarTitles();
        if (current === icon.label || preferred.includes(icon.label)) {
            return true;
        }

        if (!href) {
            return false;
        }

        const currentPath = decodeURIComponent(window.location.pathname).replace(/\/$/, "");
        const itemPath = decodeURIComponent(new URL(href, window.location.origin).pathname).replace(/\/$/, "");
        return currentPath === itemPath || currentPath.startsWith(`${itemPath}/`);
    }

    function getModuleIconMarkup(icon) {
        const desktopIcon = frappe.utils?.get_desktop_icon?.(icon.label, frappe.boot?.desktop_icon_style);
        if (desktopIcon) {
            return `<img src="${escapeHtml(desktopIcon)}" alt="${escapeHtml(icon.label)}">`;
        }

        if (icon.logo_url || icon.icon_image) {
            return `<img src="${escapeHtml(icon.logo_url || icon.icon_image)}" alt="${escapeHtml(icon.label)}">`;
        }

        if (icon.icon && icon.icon.startsWith("fa ")) {
            return `<span class="pharma-sidebar-module__fa ${escapeHtml(icon.icon)}" aria-hidden="true"></span>`;
        }

        return frappe.utils?.desktop_icon
            ? frappe.utils.desktop_icon(icon.label, icon.bg_color || "gray", "sm")
            : `<span>${escapeHtml((icon.label || "").slice(0, 1))}</span>`;
    }

    function getRouteKey() {
        const route = frappe.get_route ? frappe.get_route() : [];
        return Array.isArray(route) ? route.join("/") : String(route || "");
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

    function cleanupDesktopCustomSections() {
        document.querySelectorAll(`${DESKTOP_HERO_SELECTOR}, ${DESKTOP_DASHBOARD_SELECTOR}, ${DESKTOP_META_SELECTOR}`).forEach((element) => {
            element.remove();
        });
        toggleDesktopIcons(true);
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
        const points = buildPolylinePoints(values, 160, 60, 8);
        return `
            <svg viewBox="0 0 160 60" preserveAspectRatio="none" aria-hidden="true">
                <polyline points="${points}" fill="none" stroke="${escapeHtml(color || "#67e1c7")}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline>
            </svg>
        `;
    }

    function buildTimelineMarkup(timeline) {
        const labels = Array.isArray(timeline?.labels) && timeline.labels.length ? timeline.labels : [];
        const series = Array.isArray(timeline?.series) && timeline.series.length ? timeline.series : [];
        const width = 780;
        const height = 260;
        const padding = 28;
        const maxValue = Math.max(
            1,
            ...series.flatMap((item) => (Array.isArray(item.values) ? item.values : [0])).map((value) => Number(value) || 0)
        );
        const gridLines = [0.25, 0.5, 0.75].map((ratio) => {
            const y = (height - padding * 2) * ratio + padding;
            return `<line x1="${padding}" y1="${y}" x2="${width - padding}" y2="${y}" />`;
        });

        const paths = series
            .map((item) => {
                const points = buildPolylinePoints(item.values, width, height, padding);
                return `
                    <polyline
                        class="pharma-dashboard-chart__line"
                        points="${points}"
                        fill="none"
                        stroke="${escapeHtml(item.color || "#67e1c7")}"
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
                    <span class="pharma-dashboard-legend__item">
                        <span class="pharma-dashboard-legend__dot" style="background:${escapeHtml(item.color || "#67e1c7")}"></span>
                        <span>${escapeHtml(item.name)}</span>
                    </span>
                `
            )
            .join("");

        const axis = labels
            .map(
                (label) => `
                    <span class="pharma-dashboard-axis__label">${escapeHtml(label)}</span>
                `
            )
            .join("");

        return `
            <div class="pharma-dashboard-panel__header">
                <div>
                    <div class="pharma-dashboard-panel__eyebrow">Nhịp độ chứng từ</div>
                    <h3>Document Velocity</h3>
                    <p>Theo dõi khối lượng đơn bán, đơn mua và hóa đơn theo ngày.</p>
                </div>
                <div class="pharma-dashboard-panel__meta">
                    <span>Đỉnh tải: ${formatNumber(maxValue)}</span>
                </div>
            </div>
            <div class="pharma-dashboard-chart">
                <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
                    <g class="pharma-dashboard-chart__grid">${gridLines.join("")}</g>
                    ${paths}
                </svg>
            </div>
            <div class="pharma-dashboard-axis" style="grid-template-columns: repeat(${Math.max(labels.length, 1)}, minmax(0, 1fr));">${axis}</div>
            <div class="pharma-dashboard-legend">${legend}</div>
        `;
    }

    function buildWorkloadMarkup(workload) {
        if (!Array.isArray(workload) || !workload.length) {
            return `
                <div class="pharma-dashboard-panel__header">
                    <div>
                        <div class="pharma-dashboard-panel__eyebrow">Hàng chờ xử lý</div>
                        <h3>Action Queue</h3>
                    </div>
                </div>
                <div class="pharma-dashboard-empty">Chưa có dữ liệu hàng chờ để hiển thị.</div>
            `;
        }

        const maxValue = Math.max(1, ...workload.map((item) => Number(item.value) || 0));
        return `
            <div class="pharma-dashboard-panel__header">
                <div>
                    <div class="pharma-dashboard-panel__eyebrow">Hàng chờ xử lý</div>
                    <h3>Action Queue</h3>
                    <p>Những nhóm chứng từ cần tiếp tục thao tác trong ngày.</p>
                </div>
            </div>
            <div class="pharma-dashboard-queue">
                ${workload
                    .map((item) => {
                        const width =
                            Number(item.value || 0) > 0
                                ? `${Math.max(10, (Number(item.value || 0) / maxValue) * 100)}%`
                                : "0%";
                        return `
                            <div class="pharma-dashboard-queue__item">
                                <div class="pharma-dashboard-queue__meta">
                                    <span class="pharma-dashboard-queue__label">${escapeHtml(item.label)}</span>
                                    <span class="pharma-dashboard-queue__value">${formatNumber(item.value)}</span>
                                </div>
                                <div class="pharma-dashboard-queue__meter">
                                    <span style="width:${width}"></span>
                                </div>
                                <p>${escapeHtml(item.hint || "")}</p>
                            </div>
                        `;
                    })
                    .join("")}
            </div>
        `;
    }

    function buildRecentMarkup(recentDocuments) {
        if (!Array.isArray(recentDocuments) || !recentDocuments.length) {
            return `
                <div class="pharma-dashboard-panel__header">
                    <div>
                        <div class="pharma-dashboard-panel__eyebrow">Gần đây</div>
                        <h3>Recent Documents</h3>
                    </div>
                </div>
                <div class="pharma-dashboard-empty">
                    Chưa có chứng từ mới. Import dữ liệu hoặc bắt đầu tạo giao dịch để luồng vận hành xuất hiện tại đây.
                </div>
            `;
        }

        return `
            <div class="pharma-dashboard-panel__header">
                <div>
                    <div class="pharma-dashboard-panel__eyebrow">Gần đây</div>
                    <h3>Recent Documents</h3>
                    <p>Các chứng từ mới nhất được cập nhật trên site.</p>
                </div>
            </div>
            <div class="pharma-dashboard-list">
                ${recentDocuments
                    .map((item) => {
                        const route = getFormRoute(item.doctype, item.name);
                        return `
                            <a class="pharma-dashboard-list__item" href="${escapeHtml(route)}">
                                <div class="pharma-dashboard-list__type">${escapeHtml(item.doctype_label || item.doctype)}</div>
                                <div class="pharma-dashboard-list__title">${escapeHtml(item.name)}</div>
                                <div class="pharma-dashboard-list__meta">
                                    <span>${escapeHtml(item.counterparty || "N/A")}</span>
                                    <span>${escapeHtml(item.date_label || "")}</span>
                                </div>
                                <div class="pharma-dashboard-list__status">${escapeHtml(item.status || "Draft")}</div>
                            </a>
                        `;
                    })
                    .join("")}
            </div>
        `;
    }

    function buildHighlightsMarkup(highlights) {
        if (!Array.isArray(highlights) || !highlights.length) {
            return `
                <div class="pharma-dashboard-panel__header">
                    <div>
                        <div class="pharma-dashboard-panel__eyebrow">Nền tảng vận hành</div>
                        <h3>System Readiness</h3>
                    </div>
                </div>
                <div class="pharma-dashboard-empty">Không có chỉ số nền tảng để hiển thị.</div>
            `;
        }

        return `
            <div class="pharma-dashboard-panel__header">
                <div>
                    <div class="pharma-dashboard-panel__eyebrow">Nền tảng vận hành</div>
                    <h3>System Readiness</h3>
                    <p>Các cấu phần nền đã sẵn sàng để bạn import dữ liệu và chạy vận hành.</p>
                </div>
            </div>
            <div class="pharma-dashboard-highlights">
                ${highlights
                    .map(
                        (item) => `
                            <div class="pharma-dashboard-highlight">
                                <div class="pharma-dashboard-highlight__value">${formatNumber(item.value)}</div>
                                <div class="pharma-dashboard-highlight__label">${escapeHtml(item.label)}</div>
                                <p>${escapeHtml(item.hint || "")}</p>
                            </div>
                        `
                    )
                    .join("")}
            </div>
        `;
    }

    function getDefaultDashboardData() {
        const icons = getDesktopIcons();
        return {
            ok: true,
            generated_at_label: formatClock(),
            hero_note: "Điều hành bán hàng, mua hàng, kho và tài chính trong một dashboard thống nhất, gọn và chuyên nghiệp hơn Desk mặc định.",
            summary_cards: [
                {
                    key: "customers",
                    label: "Khách hàng",
                    value: 0,
                    hint: "Hồ sơ khách hàng sẽ hiển thị tại đây sau import.",
                    sparkline: [0, 0, 0, 0, 0, 0, 0, 0],
                },
                {
                    key: "suppliers",
                    label: "Nhà cung cấp",
                    value: 0,
                    hint: "Danh sách supplier sẵn sàng cho luồng mua hàng.",
                    sparkline: [0, 0, 0, 0, 0, 0, 0, 0],
                },
                {
                    key: "sales_30d",
                    label: "Đơn bán 30 ngày",
                    value: 0,
                    hint: "Biểu đồ sẽ nhảy khi có dữ liệu bán hàng.",
                    sparkline: [0, 0, 0, 0, 0, 0, 0, 0],
                },
            ],
            timeline: {
                labels: Array.from({ length: 14 }, (_, index) => formatCompactDay(13 - index)),
                series: [
                    { name: "Đơn bán", color: "#67e1c7", values: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] },
                    { name: "Đơn mua", color: "#5aa8ff", values: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] },
                ],
            },
            workload: icons.slice(0, 4).map((icon) => ({
                label: icon.label,
                value: 0,
                hint: "Module đã được chuyển sang sidebar trái để thao tác nhanh hơn.",
            })),
            recent_documents: [],
            highlights: [
                {
                    label: "Modules",
                    value: icons.length,
                    hint: "Toàn bộ module hiện đã được gom vào thanh trái.",
                },
            ],
        };
    }

    function getModuleSummaryCard() {
        const icons = getDesktopIcons();
        const sparkline = Array.from({ length: 8 }, (_, index) => Math.min(icons.length, index + 1));
        return {
            key: "modules",
            label: "Module sidebar",
            value: icons.length,
            hint: "Tất cả module điều hướng đã nằm bên trái để thao tác nhanh hơn.",
            sparkline,
            color: "#67e1c7",
        };
    }

    function normalizeDashboardData(rawData) {
        const fallback = getDefaultDashboardData();
        const source = rawData && rawData.ok !== false ? rawData : fallback;
        const summaryCards = [getModuleSummaryCard(), ...(Array.isArray(source.summary_cards) ? source.summary_cards : [])];
        const uniqueSummaryCards = [];

        summaryCards.forEach((card) => {
            if (!card?.key || uniqueSummaryCards.some((item) => item.key === card.key)) {
                return;
            }
            uniqueSummaryCards.push(card);
        });

        fallback.summary_cards.forEach((card) => {
            if (uniqueSummaryCards.length >= 4) {
                return;
            }
            if (!uniqueSummaryCards.some((item) => item.key === card.key)) {
                uniqueSummaryCards.push(card);
            }
        });

        return {
            ok: true,
            generated_at_label: source.generated_at_label || fallback.generated_at_label,
            hero_note: source.hero_note || fallback.hero_note,
            summary_cards: uniqueSummaryCards.slice(0, 4),
            timeline: source.timeline || fallback.timeline,
            workload: Array.isArray(source.workload) ? source.workload : fallback.workload,
            recent_documents: Array.isArray(source.recent_documents) ? source.recent_documents : fallback.recent_documents,
            highlights: Array.isArray(source.highlights) && source.highlights.length ? source.highlights : fallback.highlights,
        };
    }

    function renderDashboardLoading(dashboard) {
        dashboard.innerHTML = `
            <div class="pharma-dashboard-loading">
                <div class="pharma-dashboard-loading__title">Đang tải dashboard...</div>
                <p>Đang gom số liệu vận hành và dựng layout dashboard mới.</p>
            </div>
        `;
    }

    function renderDashboard(dashboard, rawData) {
        const data = normalizeDashboardData(rawData);
        const summaryCards = data.summary_cards
            .map(
                (item) => `
                    <article class="pharma-dashboard-card">
                        <div class="pharma-dashboard-card__label">${escapeHtml(item.label)}</div>
                        <div class="pharma-dashboard-card__value">${formatNumber(item.value)}</div>
                        <div class="pharma-dashboard-card__hint">${escapeHtml(item.hint || "")}</div>
                        <div class="pharma-dashboard-card__spark">${buildSparklineMarkup(
                            item.sparkline,
                            item.color || "#67e1c7"
                        )}</div>
                    </article>
                `
            )
            .join("");

        dashboard.innerHTML = `
            <div class="pharma-dashboard-shell">
                <div class="pharma-dashboard-heading">
                    <div>
                        <div class="pharma-dashboard-heading__eyebrow">Dashboard Center</div>
                        <h2>Executive Command Deck</h2>
                        <p>${escapeHtml(data.hero_note)}</p>
                    </div>
                    <div class="pharma-dashboard-heading__actions">
                        <span class="pharma-dashboard-chip">Live ${escapeHtml(data.generated_at_label)}</span>
                        <button type="button" class="pharma-dashboard-refresh" data-pharma-dashboard-refresh>Làm mới</button>
                    </div>
                </div>
                <div class="pharma-dashboard-summary">${summaryCards}</div>
                <div class="pharma-dashboard-grid">
                    <section class="pharma-dashboard-panel pharma-dashboard-panel--wide">
                        ${buildTimelineMarkup(data.timeline)}
                    </section>
                    <section class="pharma-dashboard-panel">
                        ${buildWorkloadMarkup(data.workload)}
                    </section>
                </div>
                <div class="pharma-dashboard-grid pharma-dashboard-grid--secondary">
                    <section class="pharma-dashboard-panel">
                        ${buildRecentMarkup(data.recent_documents)}
                    </section>
                    <section class="pharma-dashboard-panel">
                        ${buildHighlightsMarkup(data.highlights)}
                    </section>
                </div>
            </div>
        `;

        dashboard.querySelector("[data-pharma-dashboard-refresh]")?.addEventListener("click", () => {
            dashboardState.loadedAt = 0;
            dashboardState.data = null;
            dashboard.dataset.rendered = "";
            ensureDesktopDashboard(true);
        });
    }

    function fetchDashboardData(force = false) {
        if (!window.frappe?.call) {
            return Promise.resolve(getDefaultDashboardData());
        }

        if (force) {
            dashboardState.loadedAt = 0;
            dashboardState.data = null;
        }

        const now = Date.now();
        if (dashboardState.data && now - dashboardState.loadedAt < DASHBOARD_CACHE_TTL) {
            return Promise.resolve(dashboardState.data);
        }

        if (dashboardState.promise) {
            return dashboardState.promise;
        }

        dashboardState.promise = frappe
            .call({
                method: DASHBOARD_API_METHOD,
                freeze: false,
            })
            .then((response) => {
                dashboardState.data = response?.message || getDefaultDashboardData();
                dashboardState.loadedAt = Date.now();
                return dashboardState.data;
            })
            .catch((error) => {
                console.warn("Unable to load pharma desk dashboard", error);
                dashboardState.data = getDefaultDashboardData();
                dashboardState.loadedAt = Date.now();
                return dashboardState.data;
            })
            .finally(() => {
                dashboardState.promise = null;
            });

        return dashboardState.promise;
    }

    function toggleDesktopIcons(visible) {
        document.querySelectorAll(".desktop-container .icons-container").forEach((element) => {
            element.classList.toggle(DESKTOP_ICONS_HIDDEN_CLASS, !visible);
        });
    }

    function ensureDesktopDashboard(force = false) {
        if (!isDesktopRoute()) {
            toggleDesktopIcons(true);
            return;
        }

        const container = document.querySelector(".desktop-container");
        if (!container) {
            return;
        }

        toggleDesktopIcons(false);

        let dashboard = container.querySelector(DESKTOP_DASHBOARD_SELECTOR);
        if (!dashboard) {
            dashboard = document.createElement("section");
            dashboard.className = "pharma-desktop-dashboard";
            container.appendChild(dashboard);
        }

        if (!force && dashboard.dataset.rendered === "ready") {
            return;
        }

        if (dashboard.dataset.rendered !== "loading") {
            renderDashboardLoading(dashboard);
            dashboard.dataset.rendered = "loading";
        }

        const requestToken = `${Date.now()}`;
        dashboard.dataset.requestToken = requestToken;

        fetchDashboardData(force).then((data) => {
            if (!dashboard.isConnected || dashboard.dataset.requestToken !== requestToken || !isDesktopRoute()) {
                return;
            }
            renderDashboard(dashboard, data);
            dashboard.dataset.rendered = "ready";
        });
    }

    function ensureSidebarVisible() {
        const sidebar = frappe?.app?.sidebar;
        if (!sidebar || frappe.is_mobile?.()) {
            return;
        }

        if (frappe.container?.page?.page && isDesktopRoute()) {
            frappe.container.page.page.hide_sidebar = false;
        }

        sidebar.wrapper?.show();

        if (isDesktopRoute() && !sidebar.sidebar_title) {
            const defaultWorkspace = getDefaultWorkspace();
            if (defaultWorkspace) {
                sidebar.setup(defaultWorkspace);
            }
        }

        localStorage.setItem("sidebar-expanded", "true");
        if (!sidebar.sidebar_expanded) {
            sidebar.open();
        } else {
            sidebar.expand_sidebar();
        }
    }

    function decorateSidebarHeader() {
        const sidebarHeader = document.querySelector(".body-sidebar .sidebar-header");
        if (!sidebarHeader) {
            return;
        }

        const title = sidebarHeader.querySelector(".header-title");
        const subtitle = sidebarHeader.querySelector(".header-subtitle");

        [title, subtitle].forEach((element) => {
            if (element && !element.dataset.originalText) {
                element.dataset.originalText = element.textContent || "";
            }
        });

        if (isDesktopRoute()) {
            if (title) {
                title.textContent = "Dashboard";
            }
            if (subtitle) {
                subtitle.textContent = "Command Center";
            }
            return;
        }

        if (title?.dataset.originalText) {
            title.textContent = title.dataset.originalText;
        }
        if (subtitle?.dataset.originalText) {
            subtitle.textContent = subtitle.dataset.originalText;
        }
    }

    function renderModuleRail() {
        const sidebarTop = document.querySelector(".body-sidebar-top");
        if (!sidebarTop || frappe.is_mobile?.()) {
            return;
        }

        let rail = sidebarTop.querySelector(MODULE_RAIL_SELECTOR);
        if (!rail) {
            rail = document.createElement("div");
            rail.className = "pharma-sidebar-modules";
            sidebarTop.prepend(rail);
        }

        const desktopHref = window.location.pathname.startsWith("/desk") ? "/desk" : "/app";
        const items = [
            {
                label: "Home",
                href: desktopHref,
                icon: frappe.utils?.icon ? frappe.utils.icon("home", "sm") : "D",
                active: isDesktopRoute(),
            },
            ...getDesktopIcons().map((icon) => {
                const href = getRouteForIcon(icon);
                return {
                    label: icon.label,
                    href,
                    icon: getModuleIconMarkup(icon),
                    active: isModuleActive(icon, href),
                };
            }),
        ];

        const railMarkup = `
            <div class="pharma-sidebar-section-label">Launchpad</div>
            <div class="pharma-sidebar-module-list">
                ${items
                    .map((item) => {
                        const href = item.href || "#";
                        const activeClass = item.active ? " is-active" : "";
                        const external = /^https?:\/\//.test(href) ? ' target="_blank" rel="noreferrer"' : "";

                        return `
                            <a class="pharma-sidebar-module${activeClass}" href="${escapeHtml(href)}"${external}>
                                <span class="pharma-sidebar-module__icon">${item.icon}</span>
                                <span class="pharma-sidebar-module__label">${escapeHtml(item.label)}</span>
                            </a>
                        `;
                    })
                    .join("")}
            </div>
        `;

        if (lastModuleRailMarkup === railMarkup && rail.dataset.mode === "full") {
            return;
        }

        rail.dataset.mode = "full";
        rail.classList.remove("is-workspace-switcher");
        rail.innerHTML = railMarkup;
        lastModuleRailMarkup = railMarkup;
    }

    function ensureDesktopNavbarMeta() {
        const navbar = document.querySelector(".desktop-navbar");
        if (!navbar) {
            return;
        }

        let meta = navbar.querySelector(DESKTOP_META_SELECTOR);
        if (!meta) {
            meta = document.createElement("div");
            meta.className = "pharma-desktop-navbar__meta";
            meta.innerHTML = `
                <span class="pharma-desktop-navbar__eyebrow">Dashboard Center</span>
                <span class="pharma-desktop-navbar__time" data-pharma-clock-desktop></span>
            `;

            const searchWrapper = navbar.querySelector(".desktop-search-wrapper");
            if (searchWrapper) {
                navbar.insertBefore(meta, searchWrapper);
            } else {
                navbar.appendChild(meta);
            }
        }
    }

    function ensureDesktopHero() {
        const container = document.querySelector(".desktop-container");
        if (!container || !isDesktopRoute()) {
            return;
        }

        let hero = container.querySelector(DESKTOP_HERO_SELECTOR);
        if (!hero) {
            hero = document.createElement("section");
            hero.className = "pharma-desktop-stage";
            hero.innerHTML = `
                <div class="pharma-desktop-stage__content">
                    <div>
                        <div class="pharma-desktop-stage__eyebrow">Executive workspace</div>
                        <h1>Dashboard Center</h1>
                        <p>Desk mặc định được thay bằng một command deck gọn hơn: module điều hướng ở sidebar trái, phần giữa ưu tiên chart, hàng chờ xử lý và các tín hiệu vận hành.</p>
                    </div>
                    <div class="pharma-desktop-stage__chips">
                        <span class="pharma-desktop-stage__chip" data-pharma-hero-modules></span>
                        <span class="pharma-desktop-stage__chip" data-pharma-hero-time></span>
                    </div>
                </div>
            `;
            const firstChild = container.firstElementChild;
            if (firstChild) {
                container.insertBefore(hero, firstChild.nextSibling);
            } else {
                container.prepend(hero);
            }
        }

        const modulesChip = hero.querySelector("[data-pharma-hero-modules]");
        const timeChip = hero.querySelector("[data-pharma-hero-time]");
        if (modulesChip) {
            modulesChip.textContent = `Modules ${formatNumber(getDesktopIcons().length)}`;
        }
        if (timeChip) {
            timeChip.textContent = `Live ${formatClock()}`;
        }
    }

    function refreshClock() {
        const formatted = formatClock();
        document.querySelectorAll("[data-pharma-clock-desktop]").forEach((element) => {
            element.textContent = formatted;
        });
        const heroTime = document.querySelector("[data-pharma-hero-time]");
        if (heroTime) {
            heroTime.textContent = `Live ${formatted}`;
        }
    }

    function applyShell() {
        const enabled = isDeskRoute() && !frappe.is_mobile?.();
        const desktopMode = enabled && isDesktopRoute();
        const workspaceMode = enabled && !desktopMode;
        document.body.classList.toggle(SHELL_BODY_CLASS, enabled);
        document.body.classList.toggle(DESKTOP_MODE_CLASS, desktopMode);
        document.body.classList.toggle(WORKSPACE_MODE_CLASS, workspaceMode);

        if (!enabled) {
            return;
        }

        ensureSidebarVisible();
        decorateSidebarHeader();
        renderModuleRail();
        cleanupDesktopCustomSections();
        refreshClock();
    }

    function scheduleApplyShell() {
        if (shellApplyTimeout) {
            window.clearTimeout(shellApplyTimeout);
        }
        shellApplyTimeout = window.setTimeout(() => {
            shellApplyTimeout = null;
            applyShell();
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
            applyShell();

            const hasDesktop = isDesktopRoute()
                ? document.querySelector(".desktop-wrapper, .desktop-container, .icons-container")
                : document.querySelector(".page-container, .layout-main-section, .desk-page");
            const hasSidebar = document.querySelector(".body-sidebar, .pharma-sidebar-modules");
            if ((hasDesktop && hasSidebar) || retryCount >= MAX_RETRY_ATTEMPTS) {
                stopRetries();
            }
        }, 250);
    }

    function bindShellEvents() {
        if (isBound) {
            return;
        }

        isBound = true;
        frappe.router.on("change", scheduleApplyShell);
        $(document).on("desktop_screen sidebar_setup page-change form-refresh", scheduleApplyShell);
        window.addEventListener("load", () => {
            scheduleApplyShell();
            startRetries();
        });
        document.addEventListener("visibilitychange", () => {
            if (!document.hidden) {
                refreshClock();
            }
        });

        if (!clockIntervalId) {
            clockIntervalId = window.setInterval(refreshClock, 60 * 1000);
        }
    }

    function initializeShellTheme() {
        bindShellEvents();
        scheduleApplyShell();
        startRetries();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeShellTheme, { once: true });
    } else {
        initializeShellTheme();
    }

    $(document).on("app_ready", initializeShellTheme);
})();
