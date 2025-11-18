/**
 * LocalIngress
 *
 * Local file-based implementation of IngressPort.
 * Uses route table JSON and TLS config JSON persisted (no keys stored).
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  IngressPort,
  IngressRule,
  IngressListOptions,
  IngressStats,
} from '../../ports/IngressPort';
import { loadInfraConfig } from '../../../../config/InfraConfig';

interface RouteTable {
  [ruleId: string]: IngressRule;
}

interface TLSConfig {
  [ruleId: string]: {
    enabled: boolean;
    certificateId?: string;
    minVersion?: string;
  };
}

interface GlobalTLSConfig {
  enabled: boolean;
  cert_ref: string;
  key_ref: string;
}

export type ComplianceStatus = 'COMPLIANT' | 'NON_COMPLIANT';

export class LocalIngress implements IngressPort {
  private baseDir: string;
  private routeTableFile: string;
  private tlsConfigFile: string;
  private globalTlsFile: string;
  private routeTable: RouteTable = {};
  private tlsConfig: TLSConfig = {};
  private globalTls: GlobalTLSConfig | null = null;
  private stats: Map<string, IngressStats> = new Map();
  private envName: string;

  constructor(baseDir: string, envName: string = 'development') {
    this.baseDir = baseDir;
    this.envName = envName;
    this.routeTableFile = path.join(baseDir, 'route-table.json');
    this.tlsConfigFile = path.join(baseDir, 'tls-config.json');
    this.globalTlsFile = path.join(baseDir, 'global-tls.json');
    this.loadConfigs();
  }

  async createRule(rule: IngressRule): Promise<string> {
    const ruleId = rule.id || this.generateRuleId();
    const ruleWithId: IngressRule = { ...rule, id: ruleId };

    this.routeTable[ruleId] = ruleWithId;

    // Persist TLS config if present
    if (rule.tls) {
      this.tlsConfig[ruleId] = {
        enabled: rule.tls.enabled,
        certificateId: rule.tls.certificateId,
        minVersion: rule.tls.minVersion,
      };
    }

    await this.saveConfigs();

    // Initialize stats
    this.stats.set(ruleId, {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      activeConnections: 0,
      targetHealth: 'healthy',
    });

    return ruleId;
  }

  async deleteRule(ruleId: string): Promise<void> {
    delete this.routeTable[ruleId];
    delete this.tlsConfig[ruleId];
    this.stats.delete(ruleId);
    await this.saveConfigs();
  }

  async getRule(ruleId: string): Promise<IngressRule> {
    const rule = this.routeTable[ruleId];
    if (!rule) {
      throw new Error(`Ingress rule ${ruleId} not found`);
    }

    // Merge TLS config if present
    if (this.tlsConfig[ruleId]) {
      rule.tls = {
        enabled: this.tlsConfig[ruleId].enabled,
        certificateId: this.tlsConfig[ruleId].certificateId,
        minVersion: this.tlsConfig[ruleId].minVersion as '1.0' | '1.1' | '1.2' | '1.3' | undefined,
      };
    }

    return rule;
  }

  async listRules(options?: IngressListOptions): Promise<IngressRule[]> {
    let rules = Object.values(this.routeTable);

    // Filter by host if specified
    if (options?.host) {
      rules = rules.filter((rule) => rule.host === options.host);
    }

    // Merge TLS configs
    rules = rules.map((rule) => {
      if (this.tlsConfig[rule.id!]) {
        rule.tls = {
          enabled: this.tlsConfig[rule.id!].enabled,
          certificateId: this.tlsConfig[rule.id!].certificateId,
          minVersion: this.tlsConfig[rule.id!].minVersion as '1.0' | '1.1' | '1.2' | '1.3' | undefined,
        };
      }
      return rule;
    });

    // Limit results
    if (options?.maxResults) {
      rules = rules.slice(0, options.maxResults);
    }

    return rules;
  }

  async getStats(ruleId: string): Promise<IngressStats> {
    const stats = this.stats.get(ruleId);
    if (!stats) {
      throw new Error(`Stats not found for ingress rule ${ruleId}`);
    }
    return { ...stats };
  }

  /**
   * Record a request (for stats tracking).
   */
  recordRequest(ruleId: string, success: boolean, responseTime?: number): void {
    const stats = this.stats.get(ruleId);
    if (!stats) {
      return;
    }

    stats.totalRequests++;
    if (success) {
      stats.successfulRequests++;
    } else {
      stats.failedRequests++;
    }

    if (responseTime !== undefined) {
      // Simple moving average
      stats.averageResponseTime = stats.averageResponseTime
        ? (stats.averageResponseTime + responseTime) / 2
        : responseTime;
    }
  }

  /**
   * Set global TLS configuration.
   * Persists JSON with certificate and key references (no private keys stored).
   */
  async setTls(config: { enabled: boolean; cert_ref: string; key_ref: string }): Promise<void> {
    this.globalTls = {
      enabled: config.enabled,
      cert_ref: config.cert_ref,
      key_ref: config.key_ref,
    };

    await this.saveGlobalTls();
  }

  /**
   * Get compliance status based on infra.network.tls_required and TLS enabled status.
   */
  status(): ComplianceStatus {
    try {
      const infraResult = loadInfraConfig(this.envName);
      const tlsRequired = infraResult.config.network.tls_required;

      // If TLS is required by infra config but not enabled, return NON_COMPLIANT
      if (tlsRequired && (!this.globalTls || !this.globalTls.enabled)) {
        return 'NON_COMPLIANT';
      }

      return 'COMPLIANT';
    } catch (error) {
      // If we can't load infra config, assume compliant (fail open)
      return 'COMPLIANT';
    }
  }

  private loadConfigs(): void {
    // Load route table
    if (fs.existsSync(this.routeTableFile)) {
      try {
        const content = fs.readFileSync(this.routeTableFile, 'utf-8');
        this.routeTable = JSON.parse(content);
      } catch (error) {
        this.routeTable = {};
      }
    }

    // Load TLS config
    if (fs.existsSync(this.tlsConfigFile)) {
      try {
        const content = fs.readFileSync(this.tlsConfigFile, 'utf-8');
        this.tlsConfig = JSON.parse(content);
      } catch (error) {
        this.tlsConfig = {};
      }
    }

    // Load global TLS config
    if (fs.existsSync(this.globalTlsFile)) {
      try {
        const content = fs.readFileSync(this.globalTlsFile, 'utf-8');
        this.globalTls = JSON.parse(content);
      } catch (error) {
        this.globalTls = null;
      }
    }

    // Initialize stats for existing rules
    for (const ruleId of Object.keys(this.routeTable)) {
      if (!this.stats.has(ruleId)) {
        this.stats.set(ruleId, {
          totalRequests: 0,
          successfulRequests: 0,
          failedRequests: 0,
          activeConnections: 0,
          targetHealth: 'healthy',
        });
      }
    }
  }

  private async saveConfigs(): Promise<void> {
    await this.ensureDirectory(this.baseDir);

    // Save route table (no keys stored)
    await fs.promises.writeFile(
      this.routeTableFile,
      JSON.stringify(this.routeTable, null, 2),
      'utf-8'
    );

    // Save TLS config (no keys stored, only config)
    await fs.promises.writeFile(
      this.tlsConfigFile,
      JSON.stringify(this.tlsConfig, null, 2),
      'utf-8'
    );
  }

  private async saveGlobalTls(): Promise<void> {
    await this.ensureDirectory(this.baseDir);

    // Save global TLS config (no private keys, only references)
    await fs.promises.writeFile(
      this.globalTlsFile,
      JSON.stringify(this.globalTls, null, 2),
      'utf-8'
    );
  }

  private async ensureDirectory(dirPath: string): Promise<void> {
    await fs.promises.mkdir(dirPath, { recursive: true });
  }

  private generateRuleId(): string {
    return `ingress-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }
}
