export interface HealthStatus {
  status: string;
  connected: boolean;
  host: string;
  port: number;
  latency_ms?: number;
  error?: string;
}

export interface Repository {
  repo_id: string;
  name: string;
  path: string;
  is_sample: boolean;
  status: string;
  total_files?: number;
  total_symbols?: number;
  total_tests?: number;
  total_relationships?: number;
}

export interface SymbolItem {
  id: string;
  name: string;
  qualified_name: string;
  symbol_type: string;
  file_path: string;
  start_line: number;
  end_line: number;
  is_test: boolean;
}

export interface PathNode {
  id: string;
  name: string;
  type: string;
  file_path?: string;
}

export interface AffectedComponent {
  id: string;
  name: string;
  qualified_name: string;
  file_path: string;
  symbol_type: string;
  is_test: boolean;
  hop_count: number;
  impact_type: 'direct' | 'indirect';
  confidence: 'high' | 'medium' | 'low';
  path: PathNode[];
}

export interface AffectedTest {
  id: string;
  name: string;
  qualified_name: string;
  file_path: string;
  start_line: number;
  end_line: number;
  hop_count: number;
  confidence: 'high' | 'medium' | 'suggested';
  recommendation_reason: string;
  path: PathNode[];
  execution_status: string;
}

export interface AffectedFile {
  file_path: string;
  impact_type: string;
  hop_count: number;
  affected_symbols_count: number;
  affected_symbols: string[];
}

export interface HighImpactModule {
  symbol_id: string;
  name: string;
  file_path: string;
  dependent_callers_count: number;
  is_target: boolean;
}

export interface ImpactMetrics {
  total_affected_symbols: number;
  direct_dependents_count: number;
  indirect_dependents_count: number;
  potentially_affected_tests_count: number;
  affected_files_count: number;
  max_graph_hops: number;
}

export interface TargetSymbol {
  id: string;
  name: string;
  qualified_name: string;
  symbol_type: string;
  file_path: string;
  start_line: number;
  end_line: number;
  parameters: string;
  docstring?: string;
}

export interface GraphVisualization {
  nodes: any[];
  edges: any[];
}

export interface ImpactResult {
  target: TargetSymbol;
  blast_radius_risk: 'HIGH' | 'MEDIUM' | 'LOW';
  risk_evidence?: string;
  metrics: ImpactMetrics;
  direct_dependents: AffectedComponent[];
  indirect_dependents: AffectedComponent[];
  affected_tests: AffectedTest[];
  affected_files: AffectedFile[];
  high_impact_shared_modules: HighImpactModule[];
  visualization: GraphVisualization;
  explanation: string;
}

export interface DiffResult {
  changed_files_count: number;
  changed_files: string[];
  changed_symbols_count: number;
  changed_symbols: any[];
  aggregate_affected_symbols_count: number;
  aggregate_affected_symbols: AffectedComponent[];
  aggregate_affected_tests_count: number;
  aggregate_affected_tests: AffectedTest[];
  message?: string;
}

export interface CypherRecord {
  query: string;
  params: Record<string, any>;
  execution_time_ms: number;
  rows_returned: number;
  timestamp: number;
}
