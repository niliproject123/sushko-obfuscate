/**
 * Config Persistence Tests
 *
 * Tests that admin configuration changes are saved permanently
 * and survive config reload.
 */
import { describe, test, expect, beforeAll, afterAll } from 'vitest';
import { apiGet, apiPost, apiPut, apiDelete, isBackendRunning } from './setup';

interface Pattern {
  name: string;
  pii_type: string;
  regex: string;
  capture_group: number;
  enabled: boolean;
  validator?: string | null;
}

const TEST_PATTERN_NAME = 'persistence_test_pattern';

describe('Config Persistence Tests', () => {
  beforeAll(async () => {
    const running = await isBackendRunning();
    if (!running) {
      throw new Error('Backend server must be running on port 8000');
    }

    // Clean up any leftover test pattern
    try {
      await apiDelete(`/config/patterns/${TEST_PATTERN_NAME}`);
    } catch {
      // Pattern doesn't exist, that's fine
    }
  });

  afterAll(async () => {
    // Clean up test pattern
    try {
      await apiDelete(`/config/patterns/${TEST_PATTERN_NAME}`);
      await apiPost('/config/reload');
    } catch {
      // Ignore cleanup errors
    }
  });

  test('5.1 Created pattern persists after config reload', async () => {
    // Step 1: Create a new pattern (API expects { pattern: {...} } wrapper)
    const newPattern = {
      name: TEST_PATTERN_NAME,
      pii_type: 'TEST',
      regex: '\\d{4}-PERSIST-\\d{4}',
      capture_group: 0,
      enabled: true,
    };

    await apiPost('/config/patterns', { pattern: newPattern });

    // Step 2: Verify pattern exists before reload
    const patternsBefore = await apiGet<Pattern[]>('/config/patterns');
    const foundBefore = patternsBefore.find(p => p.name === TEST_PATTERN_NAME);
    expect(foundBefore).toBeDefined();
    expect(foundBefore?.regex).toBe(newPattern.regex);

    // Step 3: Reload config from disk
    await apiPost('/config/reload');

    // Step 4: Verify pattern still exists after reload
    const patternsAfter = await apiGet<Pattern[]>('/config/patterns');
    const foundAfter = patternsAfter.find(p => p.name === TEST_PATTERN_NAME);

    expect(foundAfter).toBeDefined();
    expect(foundAfter?.name).toBe(TEST_PATTERN_NAME);
    expect(foundAfter?.regex).toBe(newPattern.regex);
    expect(foundAfter?.pii_type).toBe(newPattern.pii_type);
    expect(foundAfter?.enabled).toBe(true);
  });

  test('5.2 Updated pattern persists after config reload', async () => {
    // Step 1: Update the pattern (API expects { pattern: {...} } wrapper)
    const updatedPattern = {
      name: TEST_PATTERN_NAME,
      pii_type: 'TEST_UPDATED',
      regex: '\\d{4}-UPDATED-\\d{4}',
      capture_group: 0,
      enabled: false,
    };

    await apiPut(`/config/patterns/${TEST_PATTERN_NAME}`, { pattern: updatedPattern });

    // Step 2: Reload config from disk
    await apiPost('/config/reload');

    // Step 3: Verify updates persisted
    const patterns = await apiGet<Pattern[]>('/config/patterns');
    const found = patterns.find(p => p.name === TEST_PATTERN_NAME);

    expect(found).toBeDefined();
    expect(found?.regex).toBe(updatedPattern.regex);
    expect(found?.pii_type).toBe(updatedPattern.pii_type);
    expect(found?.enabled).toBe(false);
  });

  test('5.3 Deleted pattern stays deleted after config reload', async () => {
    // Step 1: Delete the pattern
    await apiDelete(`/config/patterns/${TEST_PATTERN_NAME}`);

    // Step 2: Verify pattern is gone before reload
    const patternsBefore = await apiGet<Pattern[]>('/config/patterns');
    const foundBefore = patternsBefore.find(p => p.name === TEST_PATTERN_NAME);
    expect(foundBefore).toBeUndefined();

    // Step 3: Reload config from disk
    await apiPost('/config/reload');

    // Step 4: Verify pattern is still gone after reload
    const patternsAfter = await apiGet<Pattern[]>('/config/patterns');
    const foundAfter = patternsAfter.find(p => p.name === TEST_PATTERN_NAME);
    expect(foundAfter).toBeUndefined();
  });

  test('5.4 Multiple config changes persist together', async () => {
    const pattern1 = {
      name: `${TEST_PATTERN_NAME}_1`,
      pii_type: 'MULTI_TEST_1',
      regex: '\\d{3}-ONE-\\d{3}',
      capture_group: 0,
      enabled: true,
    };

    const pattern2 = {
      name: `${TEST_PATTERN_NAME}_2`,
      pii_type: 'MULTI_TEST_2',
      regex: '\\d{3}-TWO-\\d{3}',
      capture_group: 0,
      enabled: true,
    };

    try {
      // Create both patterns (API expects { pattern: {...} } wrapper)
      await apiPost('/config/patterns', { pattern: pattern1 });
      await apiPost('/config/patterns', { pattern: pattern2 });

      // Reload config
      await apiPost('/config/reload');

      // Verify both persist
      const patterns = await apiGet<Pattern[]>('/config/patterns');
      const found1 = patterns.find(p => p.name === pattern1.name);
      const found2 = patterns.find(p => p.name === pattern2.name);

      expect(found1).toBeDefined();
      expect(found1?.regex).toBe(pattern1.regex);
      expect(found2).toBeDefined();
      expect(found2?.regex).toBe(pattern2.regex);
    } finally {
      // Cleanup
      try {
        await apiDelete(`/config/patterns/${pattern1.name}`);
        await apiDelete(`/config/patterns/${pattern2.name}`);
      } catch {
        // Ignore cleanup errors
      }
    }
  });
});
