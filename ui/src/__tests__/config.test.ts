// Config API Tests (1.1-1.10)
import { describe, test, expect, beforeAll, afterAll } from 'vitest';
import { apiGet, apiPost, apiPut, apiDelete, isBackendRunning } from './setup';

interface PIIPatternConfig {
  name: string;
  pii_type: string;
  regex: string;
  capture_group: number;
  enabled: boolean;
  validator: string | null;
}

interface ServerConfig {
  patterns: PIIPatternConfig[];
  replacement_pools: Record<string, string[]>;
  ocr: {
    enabled: boolean;
    languages: string[];
    dpi: number;
    min_text_threshold: number;
  };
  placeholders: Record<string, string>;
}

describe('Config API', () => {
  // Test pattern for add/update/delete tests
  const TEST_PATTERN: PIIPatternConfig = {
    name: 'test_pattern_vitest',
    pii_type: 'OTHER',
    regex: '\\bTEST\\d+\\b',
    capture_group: 0,
    enabled: true,
    validator: null,
  };

  beforeAll(async () => {
    const running = await isBackendRunning();
    if (!running) {
      throw new Error('Backend is not running. Start it with: uvicorn api.main:app --port 8000');
    }
  });

  // Cleanup: ensure test pattern is removed after tests
  afterAll(async () => {
    try {
      await apiDelete(`/config/patterns/${TEST_PATTERN.name}`);
    } catch {
      // Pattern may not exist, ignore
    }
  });

  // 1.1 Get full config
  test('1.1 GET /config returns valid server config', async () => {
    const config = await apiGet<ServerConfig>('/config');

    expect(config).toBeDefined();
    expect(config.patterns).toBeInstanceOf(Array);
    expect(config.replacement_pools).toBeDefined();
    expect(config.ocr).toBeDefined();
    expect(config.placeholders).toBeDefined();

    // Verify structure
    expect(config.ocr).toHaveProperty('enabled');
    expect(config.ocr).toHaveProperty('languages');
    expect(config.ocr).toHaveProperty('dpi');
  });

  // 1.2 Get patterns list
  test('1.2 GET /config/patterns returns array with known patterns', async () => {
    const patterns = await apiGet<PIIPatternConfig[]>('/config/patterns');

    expect(patterns).toBeInstanceOf(Array);
    expect(patterns.length).toBeGreaterThan(0);

    // Should have israeli_id pattern
    const israeliId = patterns.find((p) => p.name === 'israeli_id');
    expect(israeliId).toBeDefined();
    expect(israeliId?.pii_type).toBe('ID');
  });

  // 1.3 Add new pattern
  test('1.3 POST /config/patterns creates new pattern', async () => {
    // First ensure it doesn't exist
    try {
      await apiDelete(`/config/patterns/${TEST_PATTERN.name}`);
    } catch {
      // Ignore
    }

    const result = await apiPost<PIIPatternConfig>('/config/patterns', {
      pattern: TEST_PATTERN,
    });

    expect(result).toBeDefined();
    expect(result.name).toBe(TEST_PATTERN.name);
    expect(result.pii_type).toBe(TEST_PATTERN.pii_type);
    expect(result.regex).toBe(TEST_PATTERN.regex);
  });

  // 1.4 Add duplicate pattern
  test('1.4 POST /config/patterns with duplicate name returns 400', async () => {
    // Ensure pattern exists from previous test
    try {
      await apiPost('/config/patterns', { pattern: TEST_PATTERN });
    } catch {
      // May already exist
    }

    // Try to add again - should fail
    await expect(
      apiPost('/config/patterns', { pattern: TEST_PATTERN })
    ).rejects.toThrow(/400|already exists/i);
  });

  // 1.5 Update pattern
  test('1.5 PUT /config/patterns/{name} updates existing pattern', async () => {
    const updatedPattern = {
      ...TEST_PATTERN,
      enabled: false,
      pii_type: 'NAME',
    };

    const result = await apiPut<PIIPatternConfig>(
      `/config/patterns/${TEST_PATTERN.name}`,
      { pattern: updatedPattern }
    );

    expect(result.enabled).toBe(false);
    expect(result.pii_type).toBe('NAME');
  });

  // 1.6 Update non-existent pattern
  test('1.6 PUT /config/patterns/{name} with non-existent returns 404', async () => {
    await expect(
      apiPut('/config/patterns/nonexistent_pattern_xyz', {
        pattern: TEST_PATTERN,
      })
    ).rejects.toThrow(/404|not found/i);
  });

  // 1.7 Delete pattern
  test('1.7 DELETE /config/patterns/{name} removes pattern', async () => {
    // Ensure pattern exists
    try {
      await apiPost('/config/patterns', { pattern: TEST_PATTERN });
    } catch {
      // May already exist
    }

    const result = await apiDelete<{ message: string }>(
      `/config/patterns/${TEST_PATTERN.name}`
    );

    expect(result.message).toContain(TEST_PATTERN.name);

    // Verify it's gone
    const patterns = await apiGet<PIIPatternConfig[]>('/config/patterns');
    const found = patterns.find((p) => p.name === TEST_PATTERN.name);
    expect(found).toBeUndefined();
  });

  // 1.8 Get pools
  test('1.8 GET /config/pools returns all replacement pools', async () => {
    const pools = await apiGet<Record<string, string[]>>('/config/pools');

    expect(pools).toBeDefined();
    expect(pools).toHaveProperty('name_hebrew_first');
    expect(pools).toHaveProperty('name_hebrew_last');
    expect(pools).toHaveProperty('city');

    // Verify arrays
    expect(pools.name_hebrew_first).toBeInstanceOf(Array);
  });

  // 1.9 Update pool
  test('1.9 PUT /config/pools/{name} updates pool values', async () => {
    // Get current values first
    const pools = await apiGet<Record<string, string[]>>('/config/pools');
    const originalValues = [...pools.city];

    // Update with test values
    const testValues = ['תל אביב', 'ירושלים', 'חיפה', 'באר שבע'];
    const result = await apiPut<{ message: string; values: string[] }>(
      '/config/pools/city',
      { pool_name: 'city', values: testValues }
    );

    expect(result.message).toContain('city');
    expect(result.values).toEqual(testValues);

    // Restore original values
    await apiPut('/config/pools/city', { pool_name: 'city', values: originalValues });
  });

  // 1.10 Reload config
  test('1.10 POST /config/reload reloads config from disk', async () => {
    const result = await apiPost<{ message: string }>('/config/reload');

    expect(result.message).toContain('reload');
  });
});
