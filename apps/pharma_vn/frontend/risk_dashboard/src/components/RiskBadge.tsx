import type { RiskLevel } from "../types";

interface RiskBadgeProps {
    level: RiskLevel;
}

export function RiskBadge({ level }: RiskBadgeProps) {
    const safeLevel = level || "PENDING";
    return (
        <span className={`customer-risk-widget__badge customer-risk-widget__badge--${safeLevel.toLowerCase()}`}>
            {safeLevel}
        </span>
    );
}
