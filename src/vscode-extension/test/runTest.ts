import * as fs from 'fs';
import * as path from 'path';
import { runTests } from '@vscode/test-electron';

function resolveExecutable(candidate: string | undefined): string | undefined {
    if (!candidate) {
        return undefined;
    }
    if (!fs.existsSync(candidate)) {
        return undefined;
    }
    const stats = fs.statSync(candidate);
    if (stats.isDirectory()) {
        const exeName = process.platform === 'win32' ? 'Code.exe' : 'code';
        const exePath = path.join(candidate, exeName);
        return fs.existsSync(exePath) ? exePath : undefined;
    }
    return candidate;
}

async function main(): Promise<void> {
    try {
        const extensionDevelopmentPath = path.resolve(__dirname, '../../');
        const extensionTestsPath = path.resolve(__dirname, './suite/index');
        const requestedVersion = process.env.VSCODE_VERSION?.trim() || undefined;
        const explicitExecutable = resolveExecutable(process.env.VSCODE_TEST_PATH);

        const candidates = [
            process.env.VSCODE_TEST_PATH,
            path.resolve(extensionDevelopmentPath, '.vscode-test', 'VSCode-win32-x64'),
            path.resolve(extensionDevelopmentPath, '.vscode-test', 'VSCode-win32-x64', 'Code.exe'),
            process.platform === 'win32'
                ? path.join(process.env.LOCALAPPDATA ?? '', 'Programs', 'Microsoft VS Code')
                : undefined,
        ];

        const cachedExecutable = candidates
            .map(resolveExecutable)
            .find((candidate): candidate is string => Boolean(candidate));

        const options = {
            extensionDevelopmentPath,
            extensionTestsPath,
            ...(
                explicitExecutable
                    ? { vscodeExecutablePath: explicitExecutable }
                    : requestedVersion
                    ? { version: requestedVersion }
                    : cachedExecutable
                    ? { vscodeExecutablePath: cachedExecutable }
                    : {}
            )
        };

        if (process.env.VSCODE_TEST_PATH && !explicitExecutable) {
            console.warn(`VSCODE_TEST_PATH was set but no executable was found at ${process.env.VSCODE_TEST_PATH}`);
        } else if (explicitExecutable) {
            console.log(`Using VS Code executable from VSCODE_TEST_PATH: ${explicitExecutable}`);
        } else if (requestedVersion) {
            console.log(`Using VS Code version from VSCODE_VERSION: ${requestedVersion}`);
        } else if (cachedExecutable) {
            console.log(`Using cached VS Code executable: ${cachedExecutable}`);
        } else {
            console.warn('VS Code executable not cached locally; falling back to remote download.');
        }

        await runTests(options);
    } catch (error) {
        console.error('Failed to run VS Code tests', error);
        process.exit(1);
    }
}

void main();
