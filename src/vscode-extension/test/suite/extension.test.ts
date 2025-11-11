import * as assert from 'assert';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as vscode from 'vscode';

suite('Extension Smoke Test Suite', () => {
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

        const originalZuRoot = process.env.ZU_ROOT;
        const tempZuRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'pscl-command-'));
        process.env.ZU_ROOT = tempZuRoot;

        try {
            const result = await vscode.commands.executeCommand<{
                envelopePath: string;
                buildPlanPath: string;
            }>('zeroui.pscl.preparePlan');

            assert.ok(result, 'Expected command to return writer result');
            assert.ok(result?.envelopePath, 'Expected envelope path to be defined');
            assert.ok(result?.buildPlanPath, 'Expected build plan path to be defined');
            assert.ok(fs.existsSync(result!.envelopePath), 'Expected FileEnvelope.json to exist');
            assert.ok(fs.existsSync(result!.buildPlanPath), 'Expected BuildPlan.json to exist');
        } finally {
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


