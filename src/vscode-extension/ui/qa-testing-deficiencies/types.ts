export interface QATestingDeficiencyMetric {
    readonly id: string;
    readonly description: string;
    readonly severity: 'low' | 'medium' | 'high';
}


