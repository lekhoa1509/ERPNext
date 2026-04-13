import type { RiskHistoryItem } from "../types";
import { formatDateTime, normalizeLevel } from "../utils";
import { RiskBadge } from "./RiskBadge";

interface RiskHistoryPanelProps {
    history: RiskHistoryItem[];
}

export function RiskHistoryPanel({ history }: RiskHistoryPanelProps) {
    return (
        <section className="customer-risk-widget__panel">
            <div className="customer-risk-widget__panel-header">
                <h3>Check History</h3>
                <span>Most recent saved assessments</span>
            </div>

            <div className="customer-risk-widget__history">
                {history.length ? (
                    history.map((item) => {
                        const level = normalizeLevel(item.risk_level, item.risk_score);
                        return (
                            <article className="customer-risk-widget__history-item" key={item.name || `${item.last_check_date}-${item.risk_score}`}>
                                <div className="customer-risk-widget__history-topline">
                                    <strong>{formatDateTime(item.last_check_date)}</strong>
                                    <RiskBadge level={level} />
                                </div>
                                <div className="customer-risk-widget__history-score">Score {item.risk_score ?? "--"}</div>
                                {item.reasons && item.reasons.length ? (
                                    <p className="customer-risk-widget__history-copy">{item.reasons[0]}</p>
                                ) : null}
                            </article>
                        );
                    })
                ) : (
                    <p className="customer-risk-widget__history-empty">No saved history yet.</p>
                )}
            </div>
        </section>
    );
}
