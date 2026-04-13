import type { RiskDashboardData, RiskLevel } from "./types";

export function normalizeLevel(level?: string | null, score?: number | null): RiskLevel {
    const normalized = String(level || "").trim().toUpperCase();
    if (normalized === "SAFE" || normalized === "WARNING" || normalized === "HIGH") {
        return normalized;
    }

    if (typeof score === "number" && !Number.isNaN(score)) {
        if (score >= 70) {
            return "HIGH";
        }
        if (score >= 40) {
            return "WARNING";
        }
        return "SAFE";
    }
    return "";
}

export function formatDateTime(value?: string | null): string {
    if (!value) {
        return "Not checked yet";
    }

    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        return value;
    }

    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(parsed);
}

export function formatScore(score?: number | null): string {
    if (typeof score !== "number" || Number.isNaN(score)) {
        return "--";
    }
    return String(Math.round(score));
}

export function getLevelDescription(level: RiskLevel): string {
    if (level === "HIGH") {
        return "Escalate to finance and legal review before approving contracts.";
    }
    if (level === "WARNING") {
        return "Proceed with caution and review the latest evidence carefully.";
    }
    if (level === "") {
        return "Tax data is available, but the risk engine has not returned a score yet.";
    }
    return "Customer profile looks healthy based on the latest assessment.";
}

export function hasReadyPayload(data: RiskDashboardData): boolean {
    return (
        data.status === "ready"
        || typeof data.risk_score === "number"
        || Boolean(data.risk_level)
        || Boolean(data.business_profile)
        || Boolean(data.warnings && data.warnings.length)
    );
}
