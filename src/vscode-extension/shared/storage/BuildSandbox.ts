import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';

export interface BuildSandboxInputs {
    workspaceRoot: string;
    buildInputs: string[];
}

export interface BuildSandboxResult {
    artifact_digest: string;
    sbom_digest: string;
}

export class BuildSandbox {
    constructor(private readonly options: BuildSandboxInputs) {}

    public run(): BuildSandboxResult {
        const files = this.collectFiles();
        const artifactDigest = this.computeDigest(files);
        const sbomDigest = this.computeSbomDigest(files);

        return {
            artifact_digest: artifactDigest,
            sbom_digest: sbomDigest
        };
    }

    private collectFiles(): Array<{ relativePath: string; absolutePath: string }> {
        const allFiles = this.walkWorkspace(this.options.workspaceRoot);
        const matched = new Map<string, string>();

        for (const pattern of this.options.buildInputs) {
            const regex = this.patternToRegex(pattern);
            for (const file of allFiles) {
                if (regex.test(file)) {
                    matched.set(file, path.resolve(this.options.workspaceRoot, file));
                }
            }
        }

        return Array.from(matched.entries())
            .sort((a, b) => a[0].localeCompare(b[0]))
            .map(([relativePath, absolutePath]) => ({
                relativePath,
                absolutePath
            }));
    }

    private walkWorkspace(root: string, base: string = root): string[] {
        if (!fs.existsSync(root)) {
            return [];
        }

        const entries = fs.readdirSync(root);
        const results: string[] = [];

        for (const entry of entries) {
            const absolute = path.join(root, entry);
            const relative = path.relative(base, absolute).replace(/\\/g, '/');
            if (fs.statSync(absolute).isDirectory()) {
                results.push(...this.walkWorkspace(absolute, base));
            } else {
                results.push(relative);
            }
        }

        return results;
    }

    private patternToRegex(pattern: string): RegExp {
        const normalized = pattern.replace(/\\/g, '/');
        const placeholder = '<<DOUBLE_STAR>>';
        const escaped = normalized
            .replace(/\*\*/g, placeholder)
            .replace(/[-/\\^$+?.()|[\]{}]/g, '\\$&')
            .replace(/\*/g, '[^/]*')
            .replace(/\?/g, '.')
            .replace(new RegExp(placeholder, 'g'), '.*');
        return new RegExp(`^${escaped}$`);
    }

    private computeDigest(files: Array<{ relativePath: string; absolutePath: string }>): string {
        const hash = crypto.createHash('sha256');
        for (const file of files) {
            hash.update(file.relativePath + '\n', 'utf-8');
            const content = fs.readFileSync(file.absolutePath);
            hash.update(content);
            hash.update('\n');
        }
        return `sha256:${hash.digest('hex')}`;
    }

    private computeSbomDigest(files: Array<{ relativePath: string; absolutePath: string }>): string {
        const sbomFile = files.find(file => file.relativePath.endsWith('sbom.json'));
        if (sbomFile) {
            const content = fs.readFileSync(sbomFile.absolutePath);
            const hash = crypto.createHash('sha256').update(content).digest('hex');
            return `sha256:${hash}`;
        }

        const placeholder = `${files.length}\n` + files
            .map(file => `${file.relativePath}|${this.computeFileHash(file.absolutePath)}`)
            .join('\n');
        return `sha256:${crypto.createHash('sha256').update(placeholder).digest('hex')}`;
    }

    private computeFileHash(filePath: string): string {
        return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
    }
}

