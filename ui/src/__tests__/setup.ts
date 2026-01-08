// Test setup and utilities
import { readFileSync } from 'fs';
import { join } from 'path';

// Path to shared test resources (same as backend tests)
export const RESOURCES_PATH = join(__dirname, '../../../api/tests/resources');

// API base URL - assumes backend running on port 8000
export const API_BASE = 'http://localhost:8000/api';

// Helper to load test PDF as File object
export function loadTestPdf(filename: string): File {
  const path = join(RESOURCES_PATH, filename);
  const buffer = readFileSync(path);
  return new File([buffer], filename, { type: 'application/pdf' });
}

// Helper to load test text file
export function loadTestText(filename: string): string {
  const path = join(RESOURCES_PATH, filename);
  return readFileSync(path, 'utf-8');
}

// Helper for API requests
export async function apiGet<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export async function apiPost<T>(endpoint: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: body instanceof FormData ? {} : { 'Content-Type': 'application/json' },
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(`API error: ${response.status} - ${error.detail || response.statusText}`);
  }
  return response.json();
}

export async function apiPut<T>(endpoint: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(`API error: ${response.status} - ${error.detail || response.statusText}`);
  }
  return response.json();
}

export async function apiDelete<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(`API error: ${response.status} - ${error.detail || response.statusText}`);
  }
  return response.json();
}

// Helper to check if backend is running
export async function isBackendRunning(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE.replace('/api', '')}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
