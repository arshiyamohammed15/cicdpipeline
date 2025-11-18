/**
 * ServerlessPort
 *
 * Cloud-agnostic interface for serverless function execution.
 * Implemented by local adapters for on-demand compute execution.
 *
 * @interface ServerlessPort
 */
export interface ServerlessPort {
  /**
   * Invoke a serverless function synchronously.
   *
   * @param functionName - Name of the function to invoke
   * @param payload - Function input payload
   * @param options - Optional invocation options (timeout, memory, etc.)
   * @returns Promise resolving to function execution result
   */
  invoke(
    functionName: string,
    payload: string | Buffer | Record<string, unknown>,
    options?: ServerlessInvokeOptions
  ): Promise<ServerlessInvokeResult>;

  /**
   * Invoke a serverless function asynchronously (fire-and-forget).
   *
   * @param functionName - Name of the function to invoke
   * @param payload - Function input payload
   * @param options - Optional invocation options
   * @returns Promise resolving to invocation ID
   */
  invokeAsync(
    functionName: string,
    payload: string | Buffer | Record<string, unknown>,
    options?: ServerlessInvokeOptions
  ): Promise<string>;

  /**
   * Get function configuration and metadata.
   *
   * @param functionName - Name of the function
   * @returns Promise resolving to function configuration
   */
  getFunctionConfig(functionName: string): Promise<ServerlessFunctionConfig>;
}

/**
 * Options for invoking a serverless function.
 */
export interface ServerlessInvokeOptions {
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Memory allocation in MB */
  memoryMB?: number;
  /** Environment variables to pass to function */
  environment?: Record<string, string>;
  /** Request ID for tracing */
  requestId?: string;
}

/**
 * Result of a serverless function invocation.
 */
export interface ServerlessInvokeResult {
  /** Function execution status */
  status: 'success' | 'error' | 'timeout';
  /** Function output payload */
  payload?: string | Buffer | Record<string, unknown>;
  /** Error message if execution failed */
  error?: string;
  /** Execution duration in milliseconds */
  duration?: number;
  /** Memory used in MB */
  memoryUsed?: number;
  /** Request ID for tracing */
  requestId?: string;
}

/**
 * Serverless function configuration.
 */
export interface ServerlessFunctionConfig {
  /** Function name */
  name: string;
  /** Runtime environment */
  runtime?: string;
  /** Memory allocation in MB */
  memoryMB?: number;
  /** Timeout in milliseconds */
  timeout?: number;
  /** Environment variables */
  environment?: Record<string, string>;
  /** Function status */
  status?: 'active' | 'inactive' | 'error';
}
