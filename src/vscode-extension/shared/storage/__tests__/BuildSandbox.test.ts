import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { BuildSandbox } from '../BuildSandbox';

describe('BuildSandbox', () => {
    let workspaceRoot: string;

    const createTempDir = (prefix: string) => fs.mkdtempSync(path.join(os.tmpdir(), prefix));

    beforeEach(() => {
        workspaceRoot = createTempDir('build-sandbox-');
    });

    afterEach(() => {
        if (workspaceRoot && fs.existsSync(workspaceRoot)) {
            fs.rmSync(workspaceRoot, { recursive: true, force: true });
        }
    });

    const writeFile = (relative: string, content: string) => {
        const fullPath = path.join(workspaceRoot, relative);
        fs.mkdirSync(path.dirname(fullPath), { recursive: true });
        fs.writeFileSync(fullPath, content, 'utf-8');
    };

    test('produces deterministic digests for identical inputs', () => {
        writeFile('src/fileA.txt', 'alpha\n');
        writeFile('src/fileB.txt', 'beta\n');
        writeFile('infra/config.json', '{"value":42}\n');

        const sandbox = new BuildSandbox({
            workspaceRoot,
            buildInputs: ['src/**', 'infra/**']
        });

        const run1 = sandbox.run();
        const run2 = sandbox.run();

        expect(run1).toEqual(run2);
        expect(run1.artifact_digest.startsWith('sha256:')).toBe(true);
        expect(run1.sbom_digest.startsWith('sha256:')).toBe(true);
    });

    test('placeholder SBOM digest lists files when no sbom.json present', () => {
        writeFile('src/fileC.txt', 'gamma\n');
        writeFile('infra/settings.yaml', 'delta\n');

        const sandbox = new BuildSandbox({
            workspaceRoot,
            buildInputs: ['src/**', 'infra/**']
        });

        const result = sandbox.run();
        expect(result.sbom_digest.startsWith('sha256:')).toBe(true);

        // Add another file and ensure digest changes
        writeFile('infra/extra.txt', 'epsilon\n');
        const result2 = sandbox.run();
        expect(result2.sbom_digest).not.toBe(result.sbom_digest);
    });

    test('uses sbom.json content when present', () => {
        writeFile('src/fileD.txt', 'data\n');
        writeFile('infra/sbom.json', '{"packages":["pkgA"]}\n');

        const sandbox = new BuildSandbox({
            workspaceRoot,
            buildInputs: ['src/**', 'infra/**']
        });

        const result = sandbox.run();
        expect(result.sbom_digest.startsWith('sha256:')).toBe(true);

        // Modify sbom content and ensure digest changes
        writeFile('infra/sbom.json', '{"packages":["pkgA","pkgB"]}\n');
        const result2 = sandbox.run();
        expect(result2.sbom_digest).not.toBe(result.sbom_digest);
    });
});
