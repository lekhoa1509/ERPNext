import type { BusinessProfile } from "../types";

interface RiskDetailsPanelProps {
    reasons: string[];
    businessProfile?: BusinessProfile | null;
    warnings?: string[];
}

export function RiskDetailsPanel({ reasons, businessProfile, warnings }: RiskDetailsPanelProps) {
    return (
        <section className="customer-risk-widget__panel">
            <div className="customer-risk-widget__panel-header">
                <h3>Risk Details</h3>
                <span>Why this customer was flagged</span>
            </div>

            <div className="customer-risk-widget__reason-list">
                {reasons.length ? (
                    reasons.map((reason) => (
                        <div className="customer-risk-widget__reason" key={reason}>
                            <span className="customer-risk-widget__reason-dot" />
                            <span>{reason}</span>
                        </div>
                    ))
                ) : (
                    <div className="customer-risk-widget__reason customer-risk-widget__reason--empty">
                        <span className="customer-risk-widget__reason-dot" />
                        <span>No detailed reasons were returned for this customer yet.</span>
                    </div>
                )}
            </div>

            {warnings && warnings.length ? (
                <div className="customer-risk-widget__warning-box">
                    {warnings.map((warning) => (
                        <p key={warning}>{warning}</p>
                    ))}
                </div>
            ) : null}

            {businessProfile ? (
                <div className="customer-risk-widget__company-card">
                    <div className="customer-risk-widget__panel-header">
                        <h3>Business Profile</h3>
                        <span>{businessProfile.source || "External data source"}</span>
                    </div>
                    <dl className="customer-risk-widget__company-grid">
                        {businessProfile.company_name ? (
                            <>
                                <dt>Company</dt>
                                <dd>{businessProfile.company_name}</dd>
                            </>
                        ) : null}
                        {businessProfile.tax_code ? (
                            <>
                                <dt>Tax Code</dt>
                                <dd>{businessProfile.tax_code}</dd>
                            </>
                        ) : null}
                        {businessProfile.status ? (
                            <>
                                <dt>Status</dt>
                                <dd>{businessProfile.status}</dd>
                            </>
                        ) : null}
                        {businessProfile.organization_type ? (
                            <>
                                <dt>Org Type</dt>
                                <dd>{businessProfile.organization_type}</dd>
                            </>
                        ) : null}
                        {businessProfile.established_date ? (
                            <>
                                <dt>Established</dt>
                                <dd>{businessProfile.established_date}</dd>
                            </>
                        ) : null}
                        {businessProfile.business_lines && businessProfile.business_lines.length ? (
                            <>
                                <dt>Business Lines</dt>
                                <dd>{businessProfile.business_lines.join(", ")}</dd>
                            </>
                        ) : null}
                        {businessProfile.tax_department ? (
                            <>
                                <dt>Tax Dept.</dt>
                                <dd>{businessProfile.tax_department}</dd>
                            </>
                        ) : null}
                        {businessProfile.address ? (
                            <>
                                <dt>Address</dt>
                                <dd>{businessProfile.address}</dd>
                            </>
                        ) : null}
                        {businessProfile.representative ? (
                            <>
                                <dt>Representative</dt>
                                <dd>{businessProfile.representative}</dd>
                            </>
                        ) : null}
                        {businessProfile.updated_at ? (
                            <>
                                <dt>Updated At</dt>
                                <dd>{businessProfile.updated_at}</dd>
                            </>
                        ) : null}
                    </dl>
                </div>
            ) : null}
        </section>
    );
}
