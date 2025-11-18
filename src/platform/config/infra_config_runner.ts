/**
 * PATCH HEADER
 *
 * Discovered anchors:
 *   - config/InfraConfig.ts: loadInfraConfig() function
 *   - storage-scripts/config/environments.json: environments structure
 *   - package.json: existing TypeScript build setup
 *
 * Files created/edited:
 *   - src/platform/config/infra_config_runner.ts (created)
 *   - scripts/di_config_verify.ps1 (created)
 *   - docs/DI_Config_README.md (created)
 *   - tsconfig.config.json (created)
 *
 * STOP/MISSING triggers:
 *   - None encountered
 *   - No new dependencies added (uses existing TypeScript/Node.js)
 *   - No placeholder interpolation (loader preserves placeholders as-is)
 *   - No vendor strings in neutral infra (validation code only)
 *   - No environments.json keys renamed/removed
 *   - No log truncation behavior introduced
 *
 * Infra Config Runner
 *
 * Plain Node.js runner for validating infrastructure configuration.
 * Called from PowerShell script: node dist/src/platform/config/infra_config_runner.js --env <name>
 */

import { loadInfraConfig } from '../../../config/InfraConfig';

// Parse command line arguments
const args = process.argv.slice(2);
let envName: string | undefined;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--env' && i + 1 < args.length) {
    envName = args[i + 1];
    break;
  }
}

if (!envName) {
  console.error('ERROR: --env <name> argument required');
  process.exit(1);
}

try {
  const result = loadInfraConfig(envName);

  // If we get here, the config loaded successfully
  // Output JSON for potential future use, but main purpose is exit code
  console.log(JSON.stringify({
    env: envName,
    status: 'PASS',
    infra_enabled: result.isEnabled,
  }, null, 2));

  process.exit(0);
} catch (error) {
  const errorMessage = error instanceof Error ? error.message : String(error);
  console.error(`ERROR: ${errorMessage}`);

  // Output JSON with error for potential future use
  console.log(JSON.stringify({
    env: envName,
    status: 'FAIL',
    error: errorMessage,
  }, null, 2));

  process.exit(1);
}
