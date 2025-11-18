import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { execSync } from 'child_process';
import { PolicySnapshotReader, PolicySnapshotReaderOptions } from './PolicySnapshotReader';
import { StoragePathResolver } from './StoragePathResolver';

export interface PSCLArtifactFileEntry {
    path: string;
    sha256: string;
    mode: string;
}

export interface PSCLArtifactWriterOptions {
    repoId?: string;
    workspaceRoot?: string;
    policyReaderOptions?: PolicySnapshotReaderOptions;
    readerInstance?: PolicySnapshotReader;
    zuRoot?: string;
}

export interface PSCLArtifactWriterResult {
    policySnapshotId: string;
    files: PSCLArtifactFileEntry[];
    envelopePath: string;
    buildPlanPath: string;
}

const FILE_MODE = '0644';
const ENVELOPE_FILENAME = 'FileEnvelope.json';
const BUILD_PLAN_FILENAME = 'BuildPlan.json';

export class PSCLArtifactWriter {
    private readonly repoId: string;
    private readonly workspaceRoot: string;
    private readonly resolver: StoragePathResolver;
    private readonly policyReader: PolicySnapshotReader;

    constructor(private readonly options: PSCLArtifactWriterOptions = {}) {
        this.repoId = (options.repoId ?? 'default').trim() || 'default';
        this.workspaceRoot = path.resolve(options.workspaceRoot ?? '.');
        this.resolver = new StoragePathResolver(options.zuRoot);
        this.policyReader =
            options.readerInstance ?? new PolicySnapshotReader(options.policyReaderOptions);
    }

    public write(): PSCLArtifactWriterResult {
        const files = this.collectFiles();
        const snapshotResult = this.policyReader.getCurrentSnapshotId();
        const policySnapshotId = snapshotResult.policy_snapshot_id;

        const psclDir = this.resolver.getPsclTempDir(this.repoId, {
            workspaceRoot: this.workspaceRoot
        });

        const envelopePath = path.join(psclDir, ENVELOPE_FILENAME);
        const buildPlanPath = path.join(psclDir, BUILD_PLAN_FILENAME);

        const envelope = this.buildEnvelope(policySnapshotId, files);
        this.writeJsonAtomically(envelopePath, envelope);

        const buildPlan = this.buildPlan(policySnapshotId, files);
        this.writeJsonAtomically(buildPlanPath, buildPlan);

        return {
            policySnapshotId,
            files,
            envelopePath,
            buildPlanPath
        };
    }

    private collectFiles(): PSCLArtifactFileEntry[] {
        const entries = this.listModifiedFiles();
        const unique = Array.from(new Set(entries));
        const fileEntries: PSCLArtifactFileEntry[] = [];

        for (const relativePath of unique) {
            const absolutePath = path.resolve(this.workspaceRoot, relativePath);
            if (!fs.existsSync(absolutePath) || fs.statSync(absolutePath).isDirectory()) {
                continue;
            }

            const hash = crypto
                .createHash('sha256')
                .update(fs.readFileSync(absolutePath))
                .digest('hex');

            fileEntries.push({
                path: relativePath.replace(/\\/g, '/'),
                sha256: hash,
                mode: FILE_MODE
            });
        }

        return fileEntries.sort((a, b) => a.path.localeCompare(b.path));
    }

    private listModifiedFiles(): string[] {
        try {
            const output = execSync('git status --porcelain', {
                cwd: this.workspaceRoot,
                encoding: 'utf-8'
            });

            const lines = output.split(/\r?\n/).map(line => line.trimEnd());
            const files: string[] = [];
            for (const line of lines) {
                if (!line) {
                    continue;
                }
                if (line.startsWith('??')) {
                    continue;
                }
                const staged = line[0];
                const unstaged = line[1];
                const includeStatuses = new Set(['M', 'A', 'R', 'C']);

                if (!includeStatuses.has(staged) && !includeStatuses.has(unstaged)) {
                    continue;
                }

                const rawPath = line.slice(3).trim();
                if (!rawPath || rawPath.includes('.zeroui')) {
                    continue;
                }

                const finalPath = rawPath.includes(' -> ')
                    ? rawPath.split(' -> ').pop()!
                    : rawPath;

                files.push(finalPath);
            }

            return files;
        } catch {
            return [];
        }
    }

    private buildEnvelope(policySnapshotId: string, files: PSCLArtifactFileEntry[]) {
        return {
            policy_snapshot_id: policySnapshotId,
            files,
            sbom_expected: true,
            immutable_registry_required: true
        };
    }

    private buildPlan(policySnapshotId: string, files: PSCLArtifactFileEntry[]) {
        const artifactId = this.buildArtifactId(policySnapshotId, files);
        return {
            policy_snapshot_id: policySnapshotId,
            artifact_id: artifactId,
            expected_artifact_digest: '<TBD>',
            expected_sbom_digest: '<TBD>',
            build_inputs: ['src/**', 'infra/**'],
            cost_profile: 'light|ai-inference|batch',
            routing: 'serverless|gpu-queue',
            canary: {
                stages: [10, 50, 100]
            }
        };
    }

    private buildArtifactId(policySnapshotId: string, files: PSCLArtifactFileEntry[]): string {
        const date = new Date();
        const datePart = `${date.getUTCFullYear()}${String(date.getUTCMonth() + 1).padStart(
            2,
            '0'
        )}${String(date.getUTCDate()).padStart(2, '0')}`;

        const digestSource = JSON.stringify({
            policy_snapshot_id: policySnapshotId,
            files
        });
        const shortHash = crypto.createHash('sha256').update(digestSource).digest('hex').slice(0, 8);

        return `ai-build.${datePart}.${shortHash}`;
    }

    private writeJsonAtomically(targetPath: string, data: unknown): void {
        const directory = path.dirname(targetPath);
        fs.mkdirSync(directory, { recursive: true });
        const tempPath = `${targetPath}.${process.pid}.tmp`;
        const payload = JSON.stringify(data, null, 2) + '\n';
        fs.writeFileSync(tempPath, payload, 'utf-8');
        fs.renameSync(tempPath, targetPath);
    }
}
