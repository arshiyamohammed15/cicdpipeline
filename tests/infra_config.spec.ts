/**
 * InfraConfig Test Suite
 * 
 * Tests for infrastructure configuration loader:
 * - Precedence (defaults → per-env → policy overlay)
 * - Vendor-neutrality validation
 * - Type-guard validation
 * - Placeholder preservation (no interpolation)
 */

import { loadInfraConfig, isVendorNeutral, InfraConfig } from '../config/InfraConfig';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

describe('InfraConfig', () => {
  let tempDir: string;
  let originalCwd: string;
  let mockEnvironmentsPath: string;
  let mockSchemaPath: string;

  const validDefaultInfra: InfraConfig = {
    compute: {
      min_baseline: 0,
      allow_spot: false,
    },
    routing: {
      default: 'serverless',
      cost_profiles: ['light', 'ai-inference', 'batch'],
    },
    storage: {
      object_root: '{zu_root_pattern}/objects',
      backups_root: '{zu_root_pattern}/backups',
      encryption_at_rest: true,
    },
    network: {
      tls_required: true,
    },
    observability: {
      enable_metrics: true,
      enable_cost: true,
    },
    dr: {
      cross_zone: true,
      backup_interval_min: 60,
    },
    feature_flags: {
      infra_enabled: true,
      local_adapters_enabled: true,
    },
  };

  const validSchema = {
    $schema: 'http://json-schema.org/draft-07/schema#',
    type: 'object',
    properties: {
      compute: { type: 'object' },
      routing: { type: 'object' },
      storage: { type: 'object' },
      network: { type: 'object' },
      observability: { type: 'object' },
      dr: { type: 'object' },
      feature_flags: { type: 'object' },
    },
  };

  beforeEach(() => {
    // Create temporary directory for test files
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'infra-config-test-'));
    originalCwd = process.cwd();
    process.chdir(tempDir);

    // Create directory structure
    fs.mkdirSync(path.join(tempDir, 'storage-scripts', 'config'), { recursive: true });
    fs.mkdirSync(path.join(tempDir, 'config'), { recursive: true });

    mockEnvironmentsPath = path.join(tempDir, 'storage-scripts', 'config', 'environments.json');
    mockSchemaPath = path.join(tempDir, 'config', 'infra.config.schema.json');
  });

  afterEach(() => {
    // Restore original working directory
    process.chdir(originalCwd);

    // Clean up temporary directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('loads defaults only', () => {
    it('passes type-guards and isVendorNeutral true', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {
          tenant: 'default-tenant',
          repo: 'zero-ui',
          shards: 0,
        },
        infra: validDefaultInfra,
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {},
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

      const result = loadInfraConfig('testenv');

      // Verify type-guards passed (no errors thrown)
      expect(result.config).toBeDefined();
      expect(result.config.compute.min_baseline).toBe(0);
      expect(result.config.compute.allow_spot).toBe(false);
      expect(result.config.routing.default).toBe('serverless');
      expect(result.config.storage.object_root).toBe('{zu_root_pattern}/objects');
      expect(result.isEnabled).toBe(true);

      // Verify vendor-neutrality (no errors thrown)
      expect(() => isVendorNeutral(result.config)).not.toThrow();

      // Verify frozen
      expect(() => {
        (result.config as any).compute.min_baseline = 999;
      }).toThrow();
    });
  });

  describe('per-env override', () => {
    it('override wins without mutating defaults', () => {
      const defaultInfra = { ...validDefaultInfra };
      const environmentsData = {
        version: '1.0',
        defaults: {},
        infra: defaultInfra,
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {
              compute: {
                min_baseline: 2,
                allow_spot: true,
              },
              feature_flags: {
                infra_enabled: false,
                local_adapters_enabled: true,
              },
            },
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

      const result = loadInfraConfig('testenv');

      // Verify override wins
      expect(result.config.compute.min_baseline).toBe(2); // Overridden
      expect(result.config.compute.allow_spot).toBe(true); // Overridden
      expect(result.config.feature_flags.infra_enabled).toBe(false); // Overridden
      expect(result.isEnabled).toBe(false); // Mirrors feature_flags.infra_enabled

      // Verify other fields from defaults are preserved
      expect(result.config.routing.default).toBe('serverless'); // From defaults
      expect(result.config.storage.object_root).toBe('{zu_root_pattern}/objects'); // From defaults
      expect(result.config.network.tls_required).toBe(true); // From defaults

      // Verify defaults object was not mutated
      expect(defaultInfra.compute.min_baseline).toBe(0); // Original unchanged
      expect(defaultInfra.compute.allow_spot).toBe(false); // Original unchanged
    });
  });

  describe('policy overlay', () => {
    it('overlay wins when path present', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {},
        infra: validDefaultInfra,
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {
              compute: {
                min_baseline: 1,
                allow_spot: false,
              },
            },
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      const policyOverlayPath = path.join(tempDir, 'policy-overlay.json');
      const policyOverlay = {
        infra: {
          compute: {
            min_baseline: 5,
            allow_spot: true,
          },
          feature_flags: {
            infra_enabled: false,
            local_adapters_enabled: false,
          },
        },
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));
      fs.writeFileSync(policyOverlayPath, JSON.stringify(policyOverlay, null, 2));

      const result = loadInfraConfig('testenv', { policyOverlayPath });

      // Verify policy overlay wins
      expect(result.config.compute.min_baseline).toBe(5); // From overlay (overrides env override)
      expect(result.config.compute.allow_spot).toBe(true); // From overlay
      expect(result.config.feature_flags.infra_enabled).toBe(false); // From overlay
      expect(result.config.feature_flags.local_adapters_enabled).toBe(false); // From overlay
      expect(result.isEnabled).toBe(false);

      // Verify other fields from defaults/env are preserved
      expect(result.config.routing.default).toBe('serverless'); // From defaults
    });

    it('skips overlay silently when path absent', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {},
        infra: validDefaultInfra,
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {
              compute: {
                min_baseline: 3,
                allow_spot: true,
              },
            },
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

      const nonExistentPath = path.join(tempDir, 'non-existent-policy.json');

      // Should not throw, should skip overlay
      const result = loadInfraConfig('testenv', { policyOverlayPath: nonExistentPath });

      // Verify env override is used (overlay skipped)
      expect(result.config.compute.min_baseline).toBe(3); // From env override
      expect(result.config.compute.allow_spot).toBe(true); // From env override
    });
  });

  describe('vendor neutrality', () => {
    it('throws with exact key path when vendor literal injected in storage.object_root', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {},
        infra: {
          ...validDefaultInfra,
          storage: {
            ...validDefaultInfra.storage,
            object_root: 's3://bucket/objects', // Vendor identifier injected
          },
        },
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {},
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

      expect(() => loadInfraConfig('testenv')).toThrow('Vendor identifier detected in neutral infra field: storage.object_root');
    });

    it('throws with exact key path when vendor literal injected in storage.backups_root', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {},
        infra: {
          ...validDefaultInfra,
          storage: {
            ...validDefaultInfra.storage,
            backups_root: 'arn:aws:s3:::backups', // Vendor identifier injected
          },
        },
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {},
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

      expect(() => loadInfraConfig('testenv')).toThrow('Vendor identifier detected in neutral infra field: storage.backups_root');
    });

    it('throws with exact key path when vendor literal injected in compute via env override', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {},
        infra: validDefaultInfra,
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {
              storage: {
                object_root: 'azure://container/objects', // Vendor identifier in override
                backups_root: '{zu_root_pattern}/backups',
                encryption_at_rest: true,
              },
            },
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

      expect(() => loadInfraConfig('testenv')).toThrow('Vendor identifier detected in neutral infra field: storage.object_root');
    });

    it('detects all vendor identifiers: aws, s3, azure, gcs, kms, arn', () => {
      const vendors = ['aws', 's3', 'azure', 'gcs', 'kms', 'arn'];
      
      for (const vendor of vendors) {
        const environmentsData = {
          version: '1.0',
          defaults: {},
          infra: {
            ...validDefaultInfra,
            storage: {
              ...validDefaultInfra.storage,
              object_root: `${vendor}://test/path`,
            },
          },
          environments: {
            testenv: {
              description: 'Test environment',
              infra: {},
              deployment_types: {},
            },
          },
          storage_backends: {},
        };

        fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
        fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

        expect(() => loadInfraConfig('testenv')).toThrow(`Vendor identifier detected in neutral infra field: storage.object_root`);
      }
    });
  });

  describe('placeholder preservation', () => {
    it('does NOT transform "{zu_root_pattern}" strings', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {},
        infra: validDefaultInfra,
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {},
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

      const result = loadInfraConfig('testenv');

      // Verify placeholders are preserved exactly as-is
      expect(result.config.storage.object_root).toBe('{zu_root_pattern}/objects');
      expect(result.config.storage.backups_root).toBe('{zu_root_pattern}/backups');
      
      // Verify placeholders contain the literal string
      expect(result.config.storage.object_root).toContain('{zu_root_pattern}');
      expect(result.config.storage.backups_root).toContain('{zu_root_pattern}');
    });

    it('preserves placeholders in env override', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {},
        infra: validDefaultInfra,
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {
              storage: {
                object_root: '{zu_root_pattern}/custom/objects',
                backups_root: '{zu_root_pattern}/custom/backups',
                encryption_at_rest: true,
              },
            },
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

      const result = loadInfraConfig('testenv');

      // Verify placeholders in override are preserved
      expect(result.config.storage.object_root).toBe('{zu_root_pattern}/custom/objects');
      expect(result.config.storage.backups_root).toBe('{zu_root_pattern}/custom/backups');
      expect(result.config.storage.object_root).toContain('{zu_root_pattern}');
    });

    it('preserves placeholders in policy overlay', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {},
        infra: validDefaultInfra,
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {},
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      const policyOverlayPath = path.join(tempDir, 'policy-overlay.json');
      const policyOverlay = {
        infra: {
          storage: {
            object_root: '{zu_root_pattern}/policy/objects',
            backups_root: '{zu_root_pattern}/policy/backups',
            encryption_at_rest: true,
          },
        },
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));
      fs.writeFileSync(policyOverlayPath, JSON.stringify(policyOverlay, null, 2));

      const result = loadInfraConfig('testenv', { policyOverlayPath });

      // Verify placeholders in overlay are preserved
      expect(result.config.storage.object_root).toBe('{zu_root_pattern}/policy/objects');
      expect(result.config.storage.backups_root).toBe('{zu_root_pattern}/policy/backups');
      expect(result.config.storage.object_root).toContain('{zu_root_pattern}');
    });
  });

  describe('error handling', () => {
    it('throws when environments.json not found', () => {
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

      expect(() => loadInfraConfig('testenv')).toThrow('environments.json not found');
    });

    it('throws when schema file not found', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {},
        infra: validDefaultInfra,
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {},
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));

      expect(() => loadInfraConfig('testenv')).toThrow('infra.config.schema.json not found');
    });

    it('throws when environment not found', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {},
        infra: validDefaultInfra,
        environments: {
          otherEnv: {
            description: 'Other environment',
            infra: {},
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

      expect(() => loadInfraConfig('nonexistent')).toThrow('Environment "nonexistent" not found');
    });

    it('throws when top-level infra missing', () => {
      const environmentsData = {
        version: '1.0',
        defaults: {},
        environments: {
          testenv: {
            description: 'Test environment',
            infra: {},
            deployment_types: {},
          },
        },
        storage_backends: {},
      };

      fs.writeFileSync(mockEnvironmentsPath, JSON.stringify(environmentsData, null, 2));
      fs.writeFileSync(mockSchemaPath, JSON.stringify(validSchema, null, 2));

      expect(() => loadInfraConfig('testenv')).toThrow('Top-level "infra" block not found');
    });
  });
});

