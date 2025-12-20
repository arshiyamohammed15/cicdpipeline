/**
 * Unit Tests for Detection Engine Core Decision Card Section Provider
 * 
 * Tests decision card sections per PRD §3.8
 * Coverage: 100% of DecisionCardSectionProvider.ts
 */

import * as vscode from 'vscode';
import { DecisionCardSectionProvider } from '../views/decision-card-sections/DecisionCardSectionProvider';
import { ReceiptStorageReader } from '../../../shared/storage/ReceiptStorageReader';
import { DecisionReceipt, EvidenceHandle } from '../../../shared/receipt-parser/ReceiptParser';

// Mock vscode
const mockPostMessage = jest.fn();
const mockOpenExternal = jest.fn();
const mockShowInformationMessage = jest.fn();
const mockGetConfiguration = jest.fn();
const mockWorkspaceFolders = [
    {
        name: 'test-repo',
        uri: {
            fsPath: '/test/repo'
        }
    }
];

jest.mock('vscode', () => ({
    env: {
        openExternal: (...args: any[]) => mockOpenExternal(...args)
    },
    window: {
        showInformationMessage: (...args: any[]) => mockShowInformationMessage(...args)
    },
    Uri: {
        parse: jest.fn((uri) => ({ fsPath: uri }))
    },
    workspace: {
        get workspaceFolders() {
            return mockWorkspaceFolders;
        },
        getConfiguration: (...args: any[]) => mockGetConfiguration(...args)
    }
}));

// Mock ReceiptStorageReader
const mockReadReceipts = jest.fn();
jest.mock('../../../shared/storage/ReceiptStorageReader', () => {
    return {
        ReceiptStorageReader: jest.fn().mockImplementation(() => ({
            readReceipts: mockReadReceipts
        }))
    };
});

describe('Decision Card Section Provider - Unit Tests', () => {
    let provider: DecisionCardSectionProvider;
    let mockReceiptReader: jest.Mocked<ReceiptStorageReader>;
    let mockWebview: vscode.Webview;
    let mockPanel: vscode.WebviewPanel;

    beforeEach(() => {
        jest.clearAllMocks();
        provider = new DecisionCardSectionProvider();
        mockReceiptReader = new ReceiptStorageReader() as jest.Mocked<ReceiptStorageReader>;
        
        mockWebview = {
            postMessage: mockPostMessage
        } as any;
        
        mockPanel = {
            webview: mockWebview,
            reveal: jest.fn(),
            dispose: jest.fn()
        } as any;
        
        mockGetConfiguration.mockReturnValue({
            get: jest.fn(() => undefined)
        });
        process.env.ZU_ROOT = undefined;
    });

    afterEach(() => {
        delete process.env.ZU_ROOT;
    });

    describe('initialize', () => {
        it('should use provided receiptReader', async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            
            await provider.initialize(deps);
            
            expect(ReceiptStorageReader).not.toHaveBeenCalled();
        });

        it('should create ReceiptStorageReader when not provided', async () => {
            const deps = {
                context: {} as any
            };
            
            await provider.initialize(deps);
            
            expect(ReceiptStorageReader).toHaveBeenCalled();
        });
    });

    describe('getWorkspaceRepoId', () => {
        it('should return default-repo when no workspace folder', () => {
            const originalFolders = mockWorkspaceFolders;
            (vscode.workspace as any).workspaceFolders = undefined;
            
            const repoId = (provider as any).getWorkspaceRepoId();
            expect(repoId).toBe('default-repo');
            
            (vscode.workspace as any).workspaceFolders = originalFolders;
        });

        it('should convert workspace folder name to kebab-case', () => {
            (vscode.workspace as any).workspaceFolders = [
                {
                    name: 'My Test Repo',
                    uri: { fsPath: '/test' }
                }
            ];
            
            const repoId = (provider as any).getWorkspaceRepoId();
            expect(repoId).toBe('my-test-repo');
        });
    });

    describe('getLatestReceipt', () => {
        beforeEach(async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
        });

        it('should return null when receiptReader is not set', async () => {
            const newProvider = new DecisionCardSectionProvider();
            const receipt = await (newProvider as any).getLatestReceipt();
            expect(receipt).toBeNull();
        });

        it('should return latest receipt', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const result = await (provider as any).getLatestReceipt();
            
            expect(result).toBeDefined();
            expect(result?.receipt_id).toBe('test-id');
        });

        it('should return null when no receipts', async () => {
            mockReadReceipts.mockResolvedValue([]);
            const result = await (provider as any).getLatestReceipt();
            expect(result).toBeNull();
        });

        it('should handle error and return null', async () => {
            mockReadReceipts.mockRejectedValue(new Error('Test error'));
            const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
            
            const result = await (provider as any).getLatestReceipt();
            expect(result).toBeNull();
            expect(consoleSpy).toHaveBeenCalled();
            
            consoleSpy.mockRestore();
        });
    });

    describe('isDetectionEngineReceipt', () => {
        it('should return true for detection engine receipt', () => {
            const receipt = {
                gate_id: 'detection-engine-core',
                evaluation_point: 'pre-commit'
            };
            expect((provider as any).isDetectionEngineReceipt(receipt)).toBe(true);
        });

        it('should return false for non-detection engine receipt', () => {
            const receipt = {
                gate_id: 'other-gate',
                evaluation_point: 'pre-commit'
            };
            expect((provider as any).isDetectionEngineReceipt(receipt)).toBe(false);
        });
    });

    describe('renderOverview', () => {
        beforeEach(async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
        });

        it('should render overview with receipt data', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test rationale',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await provider.renderOverview(mockWebview, mockPanel);
            
            expect(mockPostMessage).toHaveBeenCalled();
            const message = mockPostMessage.mock.calls[0][0];
            expect(message.type).toBe('render-section');
            expect(message.moduleId).toBe('m05');
            expect(message.sectionId).toBe('overview');
            expect(message.html).toContain('pass');
            expect(message.html).toContain('Test rationale');
        });

        it('should render overview without receipt', async () => {
            mockReadReceipts.mockResolvedValue([]);
            await provider.renderOverview(mockWebview, mockPanel);
            
            expect(mockPostMessage).toHaveBeenCalled();
            const message = mockPostMessage.mock.calls[0][0];
            expect(message.html).toContain('No recent detection decisions available');
        });

        it('should handle receipt without rationale', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: '',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await provider.renderOverview(mockWebview, mockPanel);
            
            const message = mockPostMessage.mock.calls[0][0];
            expect(message.html).toContain('No rationale provided');
        });

        it('should escape HTML in rationale', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test <script>alert("xss")</script>',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await provider.renderOverview(mockWebview, mockPanel);
            
            const message = mockPostMessage.mock.calls[0][0];
            expect(message.html).not.toContain('<script>');
            expect(message.html).toContain('&lt;script&gt;');
        });
    });

    describe('renderDetails', () => {
        beforeEach(async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
        });

        it('should render details with receipt data', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo', type: 'human' },
                context: {
                    surface: 'ide',
                    branch: 'main',
                    commit: 'abc123def456'
                },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await provider.renderDetails(mockWebview, mockPanel);
            
            expect(mockPostMessage).toHaveBeenCalled();
            const message = mockPostMessage.mock.calls[0][0];
            expect(message.type).toBe('render-section');
            expect(message.moduleId).toBe('m05');
            expect(message.sectionId).toBe('details');
            expect(message.html).toContain('test-id');
            expect(message.html).toContain('human');
            expect(message.html).toContain('main');
            expect(message.html).toContain('abc123');
        });

        it('should render details without receipt', async () => {
            mockReadReceipts.mockResolvedValue([]);
            await provider.renderDetails(mockWebview, mockPanel);
            
            expect(mockPostMessage).toHaveBeenCalled();
            const message = mockPostMessage.mock.calls[0][0];
            expect(message.html).toContain('No receipt details available');
        });

        it('should render details with override information', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                override: {
                    reason: 'Test override',
                    approver: 'test-user',
                    timestamp: '2025-01-01T00:00:00Z'
                },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await provider.renderDetails(mockWebview, mockPanel);
            
            const message = mockPostMessage.mock.calls[0][0];
            expect(message.html).toContain('Test override');
            expect(message.html).toContain('test-user');
        });

        it('should render details without context', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await provider.renderDetails(mockWebview, mockPanel);
            
            const message = mockPostMessage.mock.calls[0][0];
            expect(message.html).not.toContain('Context:');
        });

        it('should render details with context but no branch/commit', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                context: {
                    surface: 'ide'
                },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            await provider.renderDetails(mockWebview, mockPanel);
            
            const message = mockPostMessage.mock.calls[0][0];
            expect(message.html).toContain('N/A');
        });
    });

    describe('listEvidenceItems', () => {
        beforeEach(async () => {
            const deps = {
                context: {} as any,
                receiptReader: mockReceiptReader
            };
            await provider.initialize(deps);
        });

        it('should return empty array when no receipt', async () => {
            mockReadReceipts.mockResolvedValue([]);
            const items = await provider.listEvidenceItems();
            expect(items).toEqual([]);
        });

        it('should return empty array when no evidence handles', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const items = await provider.listEvidenceItems();
            expect(items).toEqual([]);
        });

        it('should return evidence items with descriptions', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [
                    {
                        url: 'https://example.com/evidence1',
                        type: 'artifact',
                        description: 'Evidence 1'
                    },
                    {
                        url: 'https://example.com/evidence2',
                        type: 'log',
                        description: 'Evidence 2'
                    }
                ],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const items = await provider.listEvidenceItems();
            
            expect(items.length).toBe(2);
            expect(items[0].label).toBe('Evidence 1');
            expect(items[1].label).toBe('Evidence 2');
        });

        it('should use default label when description is missing', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [
                    {
                        url: 'https://example.com/evidence1',
                        type: 'artifact',
                        description: ''
                    }
                ],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const items = await provider.listEvidenceItems();
            
            expect(items[0].label).toBe('Evidence 1');
        });

        it('should open URL when evidence has url', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [
                    {
                        url: 'https://example.com/evidence1',
                        type: 'artifact',
                        description: 'Evidence 1'
                    }
                ],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const items = await provider.listEvidenceItems();
            
            await items[0].open();
            expect(mockOpenExternal).toHaveBeenCalled();
        });

        it('should show message when evidence has no url', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [
                    {
                        url: '',
                        type: 'artifact',
                        description: 'Evidence 1'
                    }
                ],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const items = await provider.listEvidenceItems();
            
            await items[0].open();
            expect(mockShowInformationMessage).toHaveBeenCalledWith('Evidence: Evidence 1');
        });

        it('should show message when evidence has no description', async () => {
            const receipt: DecisionReceipt = {
                receipt_id: 'test-id',
                gate_id: 'detection-engine-core',
                policy_version_ids: ['POL-INIT'],
                snapshot_hash: 'sha256:test',
                timestamp_utc: '2025-01-01T00:00:00Z',
                timestamp_monotonic_ms: 1000,
                evaluation_point: 'pre-commit',
                inputs: {},
                decision: {
                    status: 'pass',
                    rationale: 'Test',
                    badges: []
                },
                evidence_handles: [
                    {
                        url: '',
                        type: 'artifact',
                        description: ''
                    }
                ],
                actor: { repo_id: 'test-repo' },
                degraded: false,
                signature: 'test'
            };

            mockReadReceipts.mockResolvedValue([receipt]);
            const items = await provider.listEvidenceItems();
            
            await items[0].open();
            expect(mockShowInformationMessage).toHaveBeenCalledWith('Evidence: No description');
        });
    });

    describe('escapeHtml', () => {
        it('should escape ampersand', () => {
            const escaped = (provider as any).escapeHtml('Test & More');
            expect(escaped).toBe('Test &amp; More');
        });

        it('should escape less than', () => {
            const escaped = (provider as any).escapeHtml('Test < More');
            expect(escaped).toBe('Test &lt; More');
        });

        it('should escape greater than', () => {
            const escaped = (provider as any).escapeHtml('Test > More');
            expect(escaped).toBe('Test &gt; More');
        });

        it('should escape double quote', () => {
            const escaped = (provider as any).escapeHtml('Test " More');
            expect(escaped).toBe('Test &quot; More');
        });

        it('should escape single quote', () => {
            const escaped = (provider as any).escapeHtml("Test ' More");
            expect(escaped).toBe('Test &#039; More');
        });

        it('should escape all special characters', () => {
            const escaped = (provider as any).escapeHtml('<script>alert("xss")</script>');
            expect(escaped).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;');
        });
    });
});
