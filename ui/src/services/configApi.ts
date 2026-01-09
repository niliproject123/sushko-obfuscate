// Configuration API endpoints

import { apiGet, apiPost, apiPut, apiDelete } from './api';
import type {
  ServerConfig,
  PIIPatternConfig,
  ReplacementPoolsConfig
} from '../types';

// Full config
export async function getConfig(): Promise<ServerConfig> {
  return apiGet<ServerConfig>('/config');
}

export async function updateConfig(config: Partial<ServerConfig>): Promise<ServerConfig> {
  return apiPut<ServerConfig>('/config', config);
}

export async function reloadConfig(): Promise<{ message: string }> {
  return apiPost<{ message: string }>('/config/reload');
}

// Patterns
export async function getPatterns(): Promise<PIIPatternConfig[]> {
  return apiGet<PIIPatternConfig[]>('/config/patterns');
}

export async function addPattern(pattern: PIIPatternConfig): Promise<PIIPatternConfig> {
  return apiPost<PIIPatternConfig>('/config/patterns', { pattern });
}

export async function updatePattern(
  patternName: string,
  pattern: PIIPatternConfig
): Promise<PIIPatternConfig> {
  return apiPut<PIIPatternConfig>(`/config/patterns/${encodeURIComponent(patternName)}`, { pattern });
}

export async function deletePattern(patternName: string): Promise<{ message: string }> {
  return apiDelete<{ message: string }>(`/config/patterns/${encodeURIComponent(patternName)}`);
}

// Pools
export async function getPools(): Promise<ReplacementPoolsConfig> {
  return apiGet<ReplacementPoolsConfig>('/config/pools');
}

export async function updatePool(
  poolName: string,
  values: string[]
): Promise<{ message: string; values: string[] }> {
  return apiPut<{ message: string; values: string[] }>(
    `/config/pools/${encodeURIComponent(poolName)}`,
    { pool_name: poolName, values }
  );
}
