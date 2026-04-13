export type RiskLevel = "SAFE" | "WARNING" | "HIGH" | "";

export interface BusinessProfile {
    company_name?: string;
    short_name?: string;
    tax_code?: string;
    address?: string;
    status?: string;
    organization_type?: string;
    tax_department?: string;
    representative?: string;
    established_date?: string;
    business_lines?: string[];
    updated_at?: string;
    source?: string;
}

export interface RiskHistoryItem {
    name?: string;
    risk_score?: number | null;
    risk_level?: string;
    last_check_date?: string | null;
    reasons?: string[];
}

export interface RiskDashboardData {
    status?: "idle" | "loading" | "ready" | "empty" | "error";
    customer?: string;
    customer_name?: string;
    tax_code?: string;
    risk_score?: number | null;
    risk_level?: string | null;
    reasons?: string[];
    reasons_text?: string;
    last_check_date?: string | null;
    profile_name?: string;
    from_cache?: number | boolean;
    warnings?: string[];
    message?: string;
    checking?: boolean;
    can_check?: boolean;
    business_profile?: BusinessProfile | null;
    history?: RiskHistoryItem[];
    onCheck?: (() => void | Promise<void>) | null;
    onForceRefresh?: (() => void | Promise<void>) | null;
    onOpenHistory?: (() => void) | null;
}
