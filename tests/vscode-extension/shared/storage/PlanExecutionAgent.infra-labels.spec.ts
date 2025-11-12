/**
 * Unit test for infra labels in DecisionReceipt
 * 
 * Tests that routed BuildPlan produces DecisionReceipt containing infra labels.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as crypto from 'crypto';
import { PlanExecutionAgent, PlanExecutionAgentOptions } from '../../../../src/vscode-extension/shared/storage/PlanExecutionAgent';
import { DecisionReceipt } from '../../../../src/vscode-extension/shared/receipt-parser/ReceiptParser';
import { StoragePathResolver } from '../../../../src/vscode-extension/shared/storage/StoragePathResolver';
import { BuildSandbox } from '../../../../src/vscode-extension/shared/storage/BuildSandbox';

jest.mock('vscode', () => {
    return {
        workspace: {
            getConfiguration: jest.fn(() => ({
                get: jest.fn()
            })),
            workspaceFolders: [
                {
                    name: 'workspace',
                    uri: { fsPath: '' }
                }
            ]
        }
    };
}, { virtual: true });

describe('PlanExecutionAgent Infra Labels', () => {
  let tempDir: string;
  let zuRoot: string;
  let workspaceRoot: string;
  let options: PlanExecutionAgentOptions;
  let originalCwd: string;

  beforeEach(() => {
    originalCwd = process.cwd();
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'plan-exec-infra-'));
    zuRoot = path.join(tempDir, 'zu-root');
    workspaceRoot = path.join(tempDir, 'workspace');
    
    // Create directory structure
    fs.mkdirSync(path.join(workspaceRoot, '.pscl'), { recursive: true });
    fs.mkdirSync(path.join(zuRoot, 'ide', 'trust', 'private'), { recursive: true });
    fs.mkdirSync(path.join(zuRoot, 'ide', 'router'), { recursive: true });

    // Create a proper Ed25519 private key for signing
    const { privateKey } = crypto.generateKeyPairSync('ed25519');
    const privateKeyPem = privateKey.export({ type: 'pkcs8', format: 'pem' });
    const keyPath = path.join(zuRoot, 'ide', 'trust', 'private', 'test-key.pem');
    fs.writeFileSync(keyPath, privateKeyPem);

    options = {
      workspaceRoot,
      zuRoot,
      signingKeyId: 'test-key',
      signingKeyPath: keyPath,
      repoId: 'test-repo',
    };
  });

  afterEach(() => {
    process.chdir(originalCwd);
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  it('should add infra labels to DecisionReceipt when BuildPlan has cost_profile', async () => {
    // Setup workspace files for BuildSandbox
    fs.mkdirSync(path.join(workspaceRoot, 'src'), { recursive: true });
    fs.writeFileSync(path.join(workspaceRoot, 'src', 'main.ts'), 'console.log("hello");\n');

    // Setup policy cache
    const resolver = new StoragePathResolver(zuRoot);
    const policyDir = resolver.resolvePolicyPath('ide');
    fs.mkdirSync(path.join(policyDir, 'current'), { recursive: true });
    fs.mkdirSync(path.join(policyDir, 'cache'), { recursive: true });
    fs.writeFileSync(
      path.join(policyDir, 'current', 'default.json'),
      JSON.stringify({ policy_id: 'default', version: '1.0.0' }, null, 2)
    );
    fs.writeFileSync(
      path.join(policyDir, 'cache', 'default-1.0.0.json'),
      JSON.stringify({
        policy_id: 'default',
        version: '1.0.0',
        policy_snapshot_id: 'SNAP.TEST.001',
        snapshot_hash: 'sha256:test',
        kid: 'test-key',
        policy_content: {},
      }, null, 2)
    );

    // Setup BuildPlan and FileEnvelope using StoragePathResolver
    const psclDir = resolver.getPsclTempDir('test-repo', { workspaceRoot });
    
    const sandbox = new BuildSandbox({
      workspaceRoot,
      buildInputs: ['src/**'],
    });
    const sandboxResult = sandbox.run();

    const buildPlan = {
      policy_snapshot_id: 'SNAP.TEST.001',
      artifact_id: 'test-artifact',
      expected_artifact_digest: sandboxResult.artifact_digest,
      expected_sbom_digest: sandboxResult.sbom_digest,
      build_inputs: ['src/**'],
      cost_profile: 'light',
    };
    fs.writeFileSync(
      path.join(psclDir, 'BuildPlan.json'),
      JSON.stringify(buildPlan, null, 2)
    );

    // Create FileEnvelope.json
    const envelope = {
      policy_snapshot_id: 'SNAP.TEST.001',
      files: [{
        path: 'src/main.ts',
        sha256: require('crypto').createHash('sha256').update('console.log("hello");\n').digest('hex'),
        mode: '0644',
      }],
    };
    fs.writeFileSync(
      path.join(psclDir, 'FileEnvelope.json'),
      JSON.stringify(envelope, null, 2)
    );

    const agent = new PlanExecutionAgent(options);
    const result = await agent.execute();

    expect(result.receiptPath).toBeDefined();

    // Read the receipt directly from the stored path
    const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
    const receipt = JSON.parse(receiptContent) as DecisionReceipt;
    
    expect(receipt.inputs).toBeDefined();
    expect(receipt.inputs.labels).toBeDefined();
    
    const labels = receipt.inputs.labels as Record<string, unknown>;
    
    // Verify infra labels are present
    expect(labels.infra_route).toBe('serverless');
    expect(labels.infra_cost_profile).toBe('light');
    expect(labels.infra_adapter).toBe('serverless');
    expect(typeof labels.infra_decision_id).toBe('string');
    expect(labels.infra_decision_id).toContain('infra-');
  });

  it('should add infra labels for ai-inference cost_profile', async () => {
    // Setup workspace files
    fs.mkdirSync(path.join(workspaceRoot, 'src'), { recursive: true });
    fs.writeFileSync(path.join(workspaceRoot, 'src', 'main.ts'), 'console.log("hello");\n');

    // Setup policy cache
    const resolver = new StoragePathResolver(zuRoot);
    const policyDir = resolver.resolvePolicyPath('ide');
    fs.mkdirSync(path.join(policyDir, 'current'), { recursive: true });
    fs.mkdirSync(path.join(policyDir, 'cache'), { recursive: true });
    fs.writeFileSync(
      path.join(policyDir, 'current', 'default.json'),
      JSON.stringify({ policy_id: 'default', version: '1.0.0' }, null, 2)
    );
    fs.writeFileSync(
      path.join(policyDir, 'cache', 'default-1.0.0.json'),
      JSON.stringify({
        policy_id: 'default',
        version: '1.0.0',
        policy_snapshot_id: 'SNAP.TEST.001',
        snapshot_hash: 'sha256:test',
        kid: 'test-key',
        policy_content: {},
      }, null, 2)
    );

    const psclDir = resolver.getPsclTempDir('test-repo', { workspaceRoot });
    const sandbox = new BuildSandbox({
      workspaceRoot,
      buildInputs: ['src/**'],
    });
    const sandboxResult = sandbox.run();

    const buildPlan = {
      policy_snapshot_id: 'SNAP.TEST.001',
      artifact_id: 'test-artifact',
      expected_artifact_digest: sandboxResult.artifact_digest,
      expected_sbom_digest: sandboxResult.sbom_digest,
      build_inputs: ['src/**'],
      cost_profile: 'ai-inference',
    };
    fs.writeFileSync(
      path.join(psclDir, 'BuildPlan.json'),
      JSON.stringify(buildPlan, null, 2)
    );

    const envelope = {
      policy_snapshot_id: 'SNAP.TEST.001',
      files: [{
        path: 'src/main.ts',
        sha256: require('crypto').createHash('sha256').update('console.log("hello");\n').digest('hex'),
        mode: '0644',
      }],
    };
    fs.writeFileSync(
      path.join(psclDir, 'FileEnvelope.json'),
      JSON.stringify(envelope, null, 2)
    );

    const agent = new PlanExecutionAgent(options);
    const result = await agent.execute();

    expect(result.receiptPath).toBeDefined();
    const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
    const receipt = JSON.parse(receiptContent) as DecisionReceipt;
    const labels = receipt.inputs.labels as Record<string, unknown>;

    expect(labels.infra_route).toBe('gpu-queue');
    expect(labels.infra_cost_profile).toBe('ai-inference');
    expect(labels.infra_adapter).toBe('gpu-pool');
  });

  it('should add infra labels for batch cost_profile', async () => {
    // Setup workspace files
    fs.mkdirSync(path.join(workspaceRoot, 'src'), { recursive: true });
    fs.writeFileSync(path.join(workspaceRoot, 'src', 'main.ts'), 'console.log("hello");\n');

    // Setup policy cache
    const resolver = new StoragePathResolver(zuRoot);
    const policyDir = resolver.resolvePolicyPath('ide');
    fs.mkdirSync(path.join(policyDir, 'current'), { recursive: true });
    fs.mkdirSync(path.join(policyDir, 'cache'), { recursive: true });
    fs.writeFileSync(
      path.join(policyDir, 'current', 'default.json'),
      JSON.stringify({ policy_id: 'default', version: '1.0.0' }, null, 2)
    );
    fs.writeFileSync(
      path.join(policyDir, 'cache', 'default-1.0.0.json'),
      JSON.stringify({
        policy_id: 'default',
        version: '1.0.0',
        policy_snapshot_id: 'SNAP.TEST.001',
        snapshot_hash: 'sha256:test',
        kid: 'test-key',
        policy_content: {},
      }, null, 2)
    );

    const psclDir = resolver.getPsclTempDir('test-repo', { workspaceRoot });
    const sandbox = new BuildSandbox({
      workspaceRoot,
      buildInputs: ['src/**'],
    });
    const sandboxResult = sandbox.run();

    const buildPlan = {
      policy_snapshot_id: 'SNAP.TEST.001',
      artifact_id: 'test-artifact',
      expected_artifact_digest: sandboxResult.artifact_digest,
      expected_sbom_digest: sandboxResult.sbom_digest,
      build_inputs: ['src/**'],
      cost_profile: 'batch',
    };
    fs.writeFileSync(
      path.join(psclDir, 'BuildPlan.json'),
      JSON.stringify(buildPlan, null, 2)
    );

    const envelope = {
      policy_snapshot_id: 'SNAP.TEST.001',
      files: [{
        path: 'src/main.ts',
        sha256: require('crypto').createHash('sha256').update('console.log("hello");\n').digest('hex'),
        mode: '0644',
      }],
    };
    fs.writeFileSync(
      path.join(psclDir, 'FileEnvelope.json'),
      JSON.stringify(envelope, null, 2)
    );

    const agent = new PlanExecutionAgent(options);
    const result = await agent.execute();

    expect(result.receiptPath).toBeDefined();
    const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
    const receipt = JSON.parse(receiptContent) as DecisionReceipt;
    const labels = receipt.inputs.labels as Record<string, unknown>;

    expect(labels.infra_route).toBe('batch');
    expect(labels.infra_cost_profile).toBe('batch');
    expect(labels.infra_adapter).toBe('queue');
  });

  it('should extend existing labels object without overwriting', async () => {
    // Setup workspace files
    fs.mkdirSync(path.join(workspaceRoot, 'src'), { recursive: true });
    fs.writeFileSync(path.join(workspaceRoot, 'src', 'main.ts'), 'console.log("hello");\n');

    // Setup policy cache
    const resolver = new StoragePathResolver(zuRoot);
    const policyDir = resolver.resolvePolicyPath('ide');
    fs.mkdirSync(path.join(policyDir, 'current'), { recursive: true });
    fs.mkdirSync(path.join(policyDir, 'cache'), { recursive: true });
    fs.writeFileSync(
      path.join(policyDir, 'current', 'default.json'),
      JSON.stringify({ policy_id: 'default', version: '1.0.0' }, null, 2)
    );
    fs.writeFileSync(
      path.join(policyDir, 'cache', 'default-1.0.0.json'),
      JSON.stringify({
        policy_id: 'default',
        version: '1.0.0',
        policy_snapshot_id: 'SNAP.TEST.001',
        snapshot_hash: 'sha256:test',
        kid: 'test-key',
        policy_content: {},
      }, null, 2)
    );

    const psclDir = resolver.getPsclTempDir('test-repo', { workspaceRoot });
    const sandbox = new BuildSandbox({
      workspaceRoot,
      buildInputs: ['src/**'],
    });
    const sandboxResult = sandbox.run();

    // This test verifies that if labels already exist, we extend them
    // Note: The current implementation already creates labels, so we're testing extension
    const buildPlan = {
      policy_snapshot_id: 'SNAP.TEST.001',
      artifact_id: 'test-artifact',
      expected_artifact_digest: sandboxResult.artifact_digest,
      expected_sbom_digest: sandboxResult.sbom_digest,
      build_inputs: ['src/**'],
      cost_profile: 'light',
      routing: 'serverless',
    };
    fs.writeFileSync(
      path.join(psclDir, 'BuildPlan.json'),
      JSON.stringify(buildPlan, null, 2)
    );

    const envelope = {
      policy_snapshot_id: 'SNAP.TEST.001',
      files: [{
        path: 'src/main.ts',
        sha256: require('crypto').createHash('sha256').update('console.log("hello");\n').digest('hex'),
        mode: '0644',
      }],
    };
    fs.writeFileSync(
      path.join(psclDir, 'FileEnvelope.json'),
      JSON.stringify(envelope, null, 2)
    );

    const agent = new PlanExecutionAgent(options);
    const result = await agent.execute();

    expect(result.receiptPath).toBeDefined();
    const receiptContent = fs.readFileSync(result.receiptPath, 'utf-8');
    const receipt = JSON.parse(receiptContent) as DecisionReceipt;
    const labels = receipt.inputs.labels as Record<string, unknown>;

    // Should have both existing labels and infra labels
    expect(labels.cost_profile).toBe('light');
    expect(labels.routing).toBe('serverless');
    expect(labels.infra_route).toBeDefined();
    expect(labels.infra_cost_profile).toBe('light');
    expect(labels.infra_adapter).toBeDefined();
    expect(labels.infra_decision_id).toBeDefined();
  });
});

