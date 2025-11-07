import * as assert from 'assert';
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
});


