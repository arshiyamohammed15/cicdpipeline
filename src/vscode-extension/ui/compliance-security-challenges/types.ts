export interface ComplianceSecurityData {
    securityScore: number;
    complianceLevel: 'high' | 'medium' | 'low' | 'unknown';
    securityStatus: 'secure' | 'warning' | 'critical';
    securityChallenges: string[];
    complianceIssues: string[];
    lastComplianceCheck: string;
    receiptId?: string;
    policyId?: string;
    snapshotHash?: string;
}

export interface ComplianceSecurityReceipt {
    receipt_id: string;
    gate_id: string;
    compliance_security_data: ComplianceSecurityData;
    timestamp_utc: string;
    signature: string;
}
