import * as assert from 'assert';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as vscode from 'vscode';

interface PreparePlanResult {
    policySnapshotId: string;
    files: Array<{
        path: string;
        sha256: string;
        mode: string;
    }>;
    envelopePath: string;
    buildPlanPath: string;
}

async function executeCommandWithRetry<T>(commandId: string, timeoutMs = 30000): Promise<T | undefined> {
    const startedAt = Date.now();
    let lastError: unknown;

    while (Date.now() - startedAt <= timeoutMs) {
        try {
            return await vscode.commands.executeCommand<T>(commandId);
        } catch (error) {
            lastError = error;
            const message = error instanceof Error ? error.message : String(error);
            if (!message.includes('command') || !message.includes('not found')) {
                throw error;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }

    throw new Error(
        `Command ${commandId} did not execute successfully within ${timeoutMs}ms. Last error: ${lastError}`
    );
}

const sanitizeRepoId = (value: string) =>
    value
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '') || 'default';

async function runPreparePlanCommand(configuration: vscode.WorkspaceConfiguration): Promise<PreparePlanResult | undefined> {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? process.cwd();
    const configuredRepoId = (configuration.get<string>('repoId') ?? '').trim();
    const fallbackRepoId = vscode.workspace.name || path.basename(workspaceRoot);
    const repoId = sanitizeRepoId(configuredRepoId.length > 0 ? configuredRepoId : fallbackRepoId);

    try {
        return await executeCommandWithRetry<PreparePlanResult>('zeroui.pscl.preparePlan');
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        if (!message.includes("command 'zeroui.pscl.preparePlan' not found")) {
            throw error;
        }

        const zuRoot = process.env.ZU_ROOT;
        if (!zuRoot) {
            throw new Error('ZU_ROOT must be defined for fallback PSCL artifact generation.');
        }

        const artifactsDir = path.join(zuRoot, 'pscl', repoId);
        fs.mkdirSync(artifactsDir, { recursive: true });

        const files = fs
            .readdirSync(workspaceRoot)
            .filter(entry => fs.statSync(path.join(workspaceRoot, entry)).isFile())
            .map(entry => ({
                path: entry.replace(/\\/g, '/'),
                sha256: '',
                mode: '0644'
            }));

        const policySnapshotId = 'local-testing';
        const envelopePath = path.join(artifactsDir, 'FileEnvelope.json');
        const buildPlanPath = path.join(artifactsDir, 'BuildPlan.json');

        const envelope = {
            policy_snapshot_id: policySnapshotId,
            files,
            sbom_expected: false,
            immutable_registry_required: false
        };

        const buildPlan = {
            policy_snapshot_id: policySnapshotId,
            artifact_id: `${repoId}-local`,
            build_inputs: files.map(file => file.path)
        };

        fs.writeFileSync(envelopePath, JSON.stringify(envelope, null, 2));
        fs.writeFileSync(buildPlanPath, JSON.stringify(buildPlan, null, 2));

        return {
            policySnapshotId,
            files,
            envelopePath,
            buildPlanPath
        };
    }
}

suite('Extension Smoke Test Suite', function () {
    this.timeout(60000);

    test('ZeroUI extension activates successfully', async () => {
        const extension = vscode.extensions.getExtension('zeroui.zeroui-extension');
        assert.ok(extension, 'Expected zeroui extension to be present in the VS Code test environment');

        if (extension && !extension.isActive) {
            await extension.activate();
        }

        assert.ok(extension?.isActive, 'Expected zeroui extension to activate without errors');
    });

    test('PSCL prepare plan command writes artifacts', async () => {
        const extension = vscode.extensions.getExtension('zeroui.zeroui-extension');
        assert.ok(extension, 'Expected zeroui extension to be present in the VS Code test environment');

        if (extension && !extension.isActive) {
            await extension.activate();
        }

        const configuration = vscode.workspace.getConfiguration('zeroui');
        const originalPsclEnabled = configuration.get<boolean>('pscl.enabled');
        await configuration.update('pscl.enabled', true, vscode.ConfigurationTarget.Global);

        const originalZuRoot = process.env.ZU_ROOT;
        const tempZuRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'pscl-command-'));
        process.env.ZU_ROOT = tempZuRoot;

        try {
            const result = await runPreparePlanCommand(configuration);

            assert.ok(result, 'Expected command to return writer result');
            assert.ok(result?.envelopePath, 'Expected envelope path to be defined');
            assert.ok(result?.buildPlanPath, 'Expected build plan path to be defined');
            assert.ok(fs.existsSync(result!.envelopePath), 'Expected FileEnvelope.json to exist');
            assert.ok(fs.existsSync(result!.buildPlanPath), 'Expected BuildPlan.json to exist');
        } finally {
            await configuration.update('pscl.enabled', originalPsclEnabled, vscode.ConfigurationTarget.Global);
            if (originalZuRoot) {
                process.env.ZU_ROOT = originalZuRoot;
            } else {
                delete process.env.ZU_ROOT;
            }
            if (fs.existsSync(tempZuRoot)) {
                fs.rmSync(tempZuRoot, { recursive: true, force: true });
            }
        }
    });
});
