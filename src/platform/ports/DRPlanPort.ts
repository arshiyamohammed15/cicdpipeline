/**
 * DRPlanPort
 * 
 * Cloud-agnostic interface for Disaster Recovery (DR) plan operations.
 * Implemented by local adapters for DR planning and execution.
 * 
 * @interface DRPlanPort
 */
export interface DRPlanPort {
  /**
   * Create or update a DR plan.
   * 
   * @param plan - DR plan configuration
   * @returns Promise resolving to DR plan ID
   */
  createPlan(plan: DRPlan): Promise<string>;

  /**
   * Get a DR plan.
   * 
   * @param planId - DR plan ID
   * @returns Promise resolving to DR plan
   */
  getPlan(planId: string): Promise<DRPlan>;

  /**
   * Delete a DR plan.
   * 
   * @param planId - DR plan ID to delete
   * @returns Promise resolving when plan is deleted
   */
  deletePlan(planId: string): Promise<void>;

  /**
   * Execute a DR plan (failover).
   * 
   * @param planId - DR plan ID to execute
   * @param options - Optional execution options
   * @returns Promise resolving to execution result
   */
  executePlan(planId: string, options?: DRPlanExecuteOptions): Promise<DRPlanExecutionResult>;

  /**
   * Test a DR plan (dry run).
   * 
   * @param planId - DR plan ID to test
   * @returns Promise resolving to test result
   */
  testPlan(planId: string): Promise<DRPlanTestResult>;

  /**
   * Get DR plan execution history.
   * 
   * @param planId - DR plan ID
   * @param options - Optional filter options
   * @returns Promise resolving to execution history
   */
  getExecutionHistory(planId: string, options?: DRPlanHistoryOptions): Promise<DRPlanExecution[]>;
}

/**
 * DR plan configuration.
 */
export interface DRPlan {
  /** Plan ID */
  id?: string;
  /** Plan name */
  name: string;
  /** Plan description */
  description?: string;
  /** Primary region/zone */
  primaryRegion: string;
  /** Secondary/DR region/zone */
  drRegion: string;
  /** RPO (Recovery Point Objective) in seconds */
  rpoSeconds: number;
  /** RTO (Recovery Time Objective) in seconds */
  rtoSeconds: number;
  /** Plan steps */
  steps: DRPlanStep[];
  /** Plan status */
  status?: 'active' | 'inactive' | 'testing';
  /** Plan tags/labels */
  tags?: Record<string, string>;
}

/**
 * Step in a DR plan.
 */
export interface DRPlanStep {
  /** Step ID */
  id: string;
  /** Step name */
  name: string;
  /** Step description */
  description?: string;
  /** Step order/sequence */
  order: number;
  /** Step type */
  type: 'backup' | 'replicate' | 'failover' | 'validate' | 'notify';
  /** Step configuration */
  config: Record<string, unknown>;
  /** Step dependencies (other step IDs) */
  dependencies?: string[];
  /** Step timeout in seconds */
  timeoutSeconds?: number;
}

/**
 * Options for executing a DR plan.
 */
export interface DRPlanExecuteOptions {
  /** Whether to execute in dry-run mode */
  dryRun?: boolean;
  /** Specific steps to execute (if not all) */
  stepIds?: string[];
  /** Execution timeout in seconds */
  timeoutSeconds?: number;
  /** Execution metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Result of DR plan execution.
 */
export interface DRPlanExecutionResult {
  /** Execution ID */
  executionId: string;
  /** Execution status */
  status: 'success' | 'failed' | 'partial' | 'timeout';
  /** Execution start time */
  startedAt: Date;
  /** Execution end time */
  completedAt?: Date;
  /** Execution duration in seconds */
  durationSeconds?: number;
  /** Steps executed */
  stepsExecuted: DRPlanStepExecution[];
  /** Error message if execution failed */
  error?: string;
  /** RPO achieved (seconds) */
  rpoAchieved?: number;
  /** RTO achieved (seconds) */
  rtoAchieved?: number;
}

/**
 * Execution result for a single DR plan step.
 */
export interface DRPlanStepExecution {
  /** Step ID */
  stepId: string;
  /** Step status */
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped';
  /** Step start time */
  startedAt?: Date;
  /** Step end time */
  completedAt?: Date;
  /** Step duration in seconds */
  durationSeconds?: number;
  /** Step error message if failed */
  error?: string;
}

/**
 * Result of DR plan testing.
 */
export interface DRPlanTestResult {
  /** Test status */
  status: 'passed' | 'failed' | 'warning';
  /** Test timestamp */
  testedAt: Date;
  /** Test duration in seconds */
  durationSeconds: number;
  /** Test results for each step */
  stepResults: DRPlanStepExecution[];
  /** Test warnings */
  warnings?: string[];
  /** Test errors */
  errors?: string[];
}

/**
 * Options for querying DR plan execution history.
 */
export interface DRPlanHistoryOptions {
  /** Start time for query */
  startTime?: Date;
  /** End time for query */
  endTime?: Date;
  /** Filter by execution status */
  status?: DRPlanExecutionResult['status'];
  /** Maximum number of results */
  maxResults?: number;
}

/**
 * Represents a DR plan execution in history.
 */
export interface DRPlanExecution {
  /** Execution ID */
  executionId: string;
  /** Plan ID */
  planId: string;
  /** Execution status */
  status: DRPlanExecutionResult['status'];
  /** Execution start time */
  startedAt: Date;
  /** Execution end time */
  completedAt?: Date;
  /** Execution duration in seconds */
  durationSeconds?: number;
}

