export interface MMMEngineData {
    metricsCollected: number;
    measurements: number;
    monitoringStatus: 'active' | 'inactive' | 'error';
    metricsTrend: string;
    measurementsTrend: string;
    lastUpdate: string;
    receiptId?: string;
    policyId?: string;
    snapshotHash?: string;
}

export interface MMMEngineReceipt {
    receipt_id: string;
    gate_id: string;
    mmm_engine_data: MMMEngineData;
    timestamp_utc: string;
    signature: string;
}
