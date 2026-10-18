import {
  HealthStatus,
  Repository,
  SymbolItem,
  ImpactResult,
  DiffResult,
  CypherRecord,
} from './types';

const API_BASE = 'http://localhost:8000/api';

export async function checkHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function listRepositories(): Promise<Repository[]> {
  const res = await fetch(`${API_BASE}/repositories`);
  if (!res.ok) throw new Error('Failed to list repositories');
  return res.json();
}

export async function registerRepository(
  sourceType: 'sample' | 'github' | 'local',
  githubUrl?: string,
  localPath?: string,
  name?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/repositories`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_type: sourceType,
      github_url: githubUrl,
      local_path: localPath,
      name,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to register repository');
  }
  return res.json();
}

export async function uploadRepository(file: File, name?: string): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  if (name) formData.append('name', name);

  const res = await fetch(`${API_BASE}/repositories/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to upload repository');
  }
  return res.json();
}

export async function indexRepository(repoId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/index`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Indexing failed');
  }
  return res.json();
}

export async function getRepositoryStatus(repoId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/status`);
  if (!res.ok) throw new Error('Failed to fetch status');
  return res.json();
}

export async function listSymbols(repoId: string): Promise<{ symbols: SymbolItem[]; files: string[] }> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/symbols`);
  if (!res.ok) throw new Error('Failed to fetch symbols');
  return res.json();
}

export async function analyzeImpact(
  repoId: string,
  symbolId: string,
  maxHops: number = 5
): Promise<ImpactResult> {
  const res = await fetch(`${API_BASE}/impact/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repo_id: repoId,
      symbol_id: symbolId,
      max_hops: maxHops,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Impact analysis failed');
  }
  return res.json();
}

export async function analyzeDiff(repoId: string, diffText: string): Promise<DiffResult> {
  const res = await fetch(`${API_BASE}/impact/diff`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repo_id: repoId,
      diff_text: diffText,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Diff analysis failed');
  }
  return res.json();
}

export async function askQuestion(
  repoId: string,
  symbolId: string,
  question: string
): Promise<{ answer: string; source: string; model: string }> {
  const res = await fetch(`${API_BASE}/impact/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repo_id: repoId,
      symbol_id: symbolId,
      question,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Question answering failed');
  }
  return res.json();
}

export async function getCypherHistory(): Promise<CypherRecord[]> {
  const res = await fetch(`${API_BASE}/cypher/history`);
  if (!res.ok) return [];
  return res.json();
}
