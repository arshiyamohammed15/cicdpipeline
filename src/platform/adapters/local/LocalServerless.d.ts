/**
 * LocalServerless
 *
 * Local file-based implementation of ServerlessPort using JS function registry.
 * Functions are stored in a known folder and invoked with timeout.
 * Execution logs are appended to NDJSON.
 */
/// <reference types="node" />
/// <reference types="node" />
import { ServerlessPort, ServerlessInvokeOptions, ServerlessInvokeResult, ServerlessFunctionConfig } from '../../ports/ServerlessPort';
export declare class LocalServerless implements ServerlessPort {
    private functionsDir;
    private logsFile;
    private defaultTimeout;
    private registry;
    constructor(functionsDir: string, logsFile: string, defaultTimeout?: number);
    invoke(functionName: string, payload: string | Buffer | Record<string, unknown>, options?: ServerlessInvokeOptions): Promise<ServerlessInvokeResult>;
    invokeAsync(functionName: string, payload: string | Buffer | Record<string, unknown>, options?: ServerlessInvokeOptions): Promise<string>;
    getFunctionConfig(functionName: string): Promise<ServerlessFunctionConfig>;
    private loadRegistry;
    private executeWithTimeout;
    private estimateMemoryUsage;
    private logExecution;
    private ensureDirectory;
    private appendToJsonl;
    private generateRequestId;
    private getMonotonicTime;
}
//# sourceMappingURL=LocalServerless.d.ts.map