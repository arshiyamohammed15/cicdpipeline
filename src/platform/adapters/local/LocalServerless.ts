/**
 * LocalServerless
 *
 * Local file-based implementation of ServerlessPort using JS function registry.
 * Functions are stored in a known folder and invoked with timeout.
 * Execution logs are appended to NDJSON.
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  ServerlessPort,
  ServerlessInvokeOptions,
  ServerlessInvokeResult,
  ServerlessFunctionConfig,
} from '../../ports/ServerlessPort';

interface FunctionRegistry {
  [functionName: string]: {
    filePath: string;
    config: ServerlessFunctionConfig;
  };
}

interface ExecutionLog {
  functionName: string;
  requestId: string;
  status: 'success' | 'error' | 'timeout';
  payload?: string;
  error?: string;
  duration: number;
  memoryUsed?: number;
  timestamp: number;
}

export class LocalServerless implements ServerlessPort {
  private functionsDir: string;
  private logsFile: string;
  private defaultTimeout: number;
  private registry: FunctionRegistry = {};

  constructor(
    functionsDir: string,
    logsFile: string,
    defaultTimeout: number = 30000
  ) {
    this.functionsDir = functionsDir;
    this.logsFile = logsFile;
    this.defaultTimeout = defaultTimeout;
    this.loadRegistry();
  }

  async invoke(
    functionName: string,
    payload: string | Buffer | Record<string, unknown>,
    options?: ServerlessInvokeOptions
  ): Promise<ServerlessInvokeResult> {
    const requestId = this.generateRequestId();
    const startTime = this.getMonotonicTime();
    const timeout = options?.timeout || this.defaultTimeout;

    if (!this.registry[functionName]) {
      const error = `Function ${functionName} not found`;
      await this.logExecution({
        functionName,
        requestId,
        status: 'error',
        error,
        duration: this.getMonotonicTime() - startTime,
        timestamp: startTime,
      });
      return {
        status: 'error',
        error,
        duration: this.getMonotonicTime() - startTime,
        requestId,
      };
    }

    try {
      const functionInfo = this.registry[functionName];
      const functionCode = fs.readFileSync(functionInfo.filePath, 'utf-8');

      // Create isolated execution context
      const result = await this.executeWithTimeout(
        functionCode,
        payload,
        timeout,
        options?.environment
      );

      const duration = this.getMonotonicTime() - startTime;
      const memoryUsed = this.estimateMemoryUsage(result);

      await this.logExecution({
        functionName,
        requestId,
        status: 'success',
        payload: typeof result === 'string' ? result : JSON.stringify(result),
        duration,
        memoryUsed,
        timestamp: startTime,
      });

      return {
        status: 'success',
        payload: result as string | Buffer | Record<string, unknown>,
        duration,
        memoryUsed,
        requestId,
      };
    } catch (error) {
      const duration = this.getMonotonicTime() - startTime;
      const errorMessage = error instanceof Error ? error.message : String(error);

      await this.logExecution({
        functionName,
        requestId,
        status: errorMessage.includes('timeout') ? 'timeout' : 'error',
        error: errorMessage,
        duration,
        timestamp: startTime,
      });

      return {
        status: errorMessage.includes('timeout') ? 'timeout' : 'error',
        error: errorMessage,
        duration,
        requestId,
      };
    }
  }

  async invokeAsync(
    functionName: string,
    payload: string | Buffer | Record<string, unknown>,
    options?: ServerlessInvokeOptions
  ): Promise<string> {
    const requestId = this.generateRequestId();
    // Fire and forget - invoke in background
    this.invoke(functionName, payload, options).catch(() => {
      // Errors logged in invoke()
    });
    return requestId;
  }

  async getFunctionConfig(functionName: string): Promise<ServerlessFunctionConfig> {
    if (!this.registry[functionName]) {
      throw new Error(`Function ${functionName} not found`);
    }

    return this.registry[functionName].config;
  }

  private loadRegistry(): void {
    if (!fs.existsSync(this.functionsDir)) {
      return;
    }

    const files = fs.readdirSync(this.functionsDir);
    for (const file of files) {
      if (file.endsWith('.js')) {
        const functionName = path.basename(file, '.js');
        const filePath = path.join(this.functionsDir, file);
        const configPath = path.join(this.functionsDir, `${functionName}.config.json`);

        let config: ServerlessFunctionConfig = {
          name: functionName,
          status: 'active',
        };

        if (fs.existsSync(configPath)) {
          try {
            const configContent = fs.readFileSync(configPath, 'utf-8');
            config = { ...config, ...JSON.parse(configContent) };
          } catch (error) {
            // Use default config
          }
        }

        this.registry[functionName] = {
          filePath,
          config,
        };
      }
    }
  }

  private async executeWithTimeout(
    functionCode: string,
    payload: unknown,
    timeout: number,
    environment?: Record<string, string>
  ): Promise<unknown> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error('Function execution timeout'));
      }, timeout);

      try {
        // Create isolated context with environment variables
        const context: Record<string, unknown> = {
          ...(environment || {}),
          payload,
          console: {
            log: (...args: unknown[]) => {
              // Suppress console output in production
            },
          },
        };

        // Execute function in isolated context
        // Note: This is a simplified execution - in production, use vm module or worker threads
        // Wrap function code to handle both arrow functions and regular functions
        const wrappedCode = functionCode.trim().startsWith('(')
          ? `(${functionCode})`
          : functionCode;
        const func = new Function('payload', `return (${wrappedCode})(payload);`);
        const result = func(payload);

        if (result instanceof Promise) {
          result
            .then((value) => {
              clearTimeout(timer);
              resolve(value);
            })
            .catch((error) => {
              clearTimeout(timer);
              reject(error);
            });
        } else {
          clearTimeout(timer);
          resolve(result);
        }
      } catch (error) {
        clearTimeout(timer);
        reject(error);
      }
    });
  }

  private estimateMemoryUsage(result: unknown): number {
    // Rough estimation: JSON stringify size
    const size = JSON.stringify(result).length;
    return Math.ceil(size / 1024); // KB
  }

  private async logExecution(log: ExecutionLog): Promise<void> {
    await this.ensureDirectory(path.dirname(this.logsFile));
    await this.appendToJsonl(this.logsFile, JSON.stringify(log));
  }

  private async ensureDirectory(dirPath: string): Promise<void> {
    await fs.promises.mkdir(dirPath, { recursive: true });
  }

  private async appendToJsonl(filePath: string, jsonContent: string): Promise<void> {
    try {
      await fs.promises.open(filePath, 'ax').then((handle) => handle.close());
    } catch (error) {
      const err = error as NodeJS.ErrnoException;
      if (err.code !== 'EEXIST') {
        throw err;
      }
    }

    const line = `${jsonContent}\n`;
    const handle = await fs.promises.open(filePath, 'a');
    try {
      await handle.write(line);
      await handle.sync();
    } finally {
      await handle.close();
    }
  }

  private generateRequestId(): string {
    return `req-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
  }

  private getMonotonicTime(): number {
    return Date.now();
  }
}
