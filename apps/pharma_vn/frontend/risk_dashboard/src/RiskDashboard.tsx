import type { RiskDashboardData } from "./types";
import { RiskDetailsPanel } from "./components/RiskDetailsPanel";
import { RiskHistoryPanel } from "./components/RiskHistoryPanel";
import { RiskScoreCard } from "./components/RiskScoreCard";
import { hasReadyPayload, normalizeLevel } from "./utils";

interface RiskDashboardProps {
    data: RiskDashboardData;
}

export function RiskDashboard({ data }: RiskDashboardProps) {
    const level = normalizeLevel(data.risk_level, data.risk_score);
    const reasons = data.reasons || [];
    const showContent = hasReadyPayload(data);

    return (
        <section className={`customer-risk-widget customer-risk-widget--${data.status || "ready"}`}>
            <header className="customer-risk-widget__header">
                <div>
                    <p className="customer-risk-widget__eyebrow">Customer Risk Assessment</p>
                    <h2 className="customer-risk-widget__title">
                        {data.customer_name || data.customer || "Customer"}
                    </h2>
                    <p className="customer-risk-widget__subtitle">
                        Tax Code: <strong>{data.tax_code || "Missing tax code"}</strong>
                    </p>
                </div>

                <div className="customer-risk-widget__action-row">
                    <button
                        type="button"
                        className="customer-risk-widget__button customer-risk-widget__button--primary"
                        disabled={!data.can_check || Boolean(data.checking)}
                        onClick={() => data.onCheck && data.onCheck()}
                    >
                        {data.checking ? "Checking..." : "Check Risk"}
                    </button>
                    <button
                        type="button"
                        className="customer-risk-widget__button customer-risk-widget__button--ghost"
                        disabled={!data.can_check || Boolean(data.checking)}
                        onClick={() => data.onForceRefresh && data.onForceRefresh()}
                    >
                        Refresh Engine
                    </button>
                    {data.onOpenHistory ? (
                        <button
                            type="button"
                            className="customer-risk-widget__button customer-risk-widget__button--ghost"
                            onClick={() => data.onOpenHistory && data.onOpenHistory()}
                        >
                            Open History
                        </button>
                    ) : null}
                </div>
            </header>

            {data.message && !showContent ? (
                <div className="customer-risk-widget__empty-state">
                    <h3>{data.status === "error" ? "Unable to load risk profile" : "No risk profile yet"}</h3>
                    <p>{data.message}</p>
                </div>
            ) : null}

            {showContent ? (
                <div className="customer-risk-widget__layout">
                    <RiskScoreCard
                        score={data.risk_score}
                        level={level}
                        lastCheckDate={data.last_check_date}
                        fromCache={data.from_cache}
                    />
                    <RiskDetailsPanel
                        reasons={reasons}
                        businessProfile={data.business_profile}
                        warnings={data.warnings}
                    />
                    <RiskHistoryPanel history={data.history || []} />
                </div>
            ) : null}
        </section>
    );
}
