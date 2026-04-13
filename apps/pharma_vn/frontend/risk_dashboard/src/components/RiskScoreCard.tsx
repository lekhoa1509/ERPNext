import type { RiskLevel } from "../types";
import { formatDateTime, formatScore, getLevelDescription } from "../utils";
import { RiskBadge } from "./RiskBadge";

interface RiskScoreCardProps {
    score?: number | null;
    level: RiskLevel;
    lastCheckDate?: string | null;
    fromCache?: number | boolean;
}

export function RiskScoreCard({ score, level, lastCheckDate, fromCache }: RiskScoreCardProps) {
    return (
        <section className={`customer-risk-widget__score-card customer-risk-widget__score-card--${(level || "pending").toLowerCase()}`}>
            <div className="customer-risk-widget__score-topline">
                <span className="customer-risk-widget__eyebrow">Risk Score</span>
                <RiskBadge level={level} />
            </div>
            <div className="customer-risk-widget__score-value">{formatScore(score)}</div>
            <p className="customer-risk-widget__score-copy">{getLevelDescription(level)}</p>
            <div className="customer-risk-widget__meta-grid">
                <div className="customer-risk-widget__meta-item">
                    <span className="customer-risk-widget__meta-label">Last check</span>
                    <strong>{formatDateTime(lastCheckDate)}</strong>
                </div>
                <div className="customer-risk-widget__meta-item">
                    <span className="customer-risk-widget__meta-label">Data mode</span>
                    <strong>{fromCache ? "Cached profile" : "Fresh engine run"}</strong>
                </div>
            </div>
        </section>
    );
}
