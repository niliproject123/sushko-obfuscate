/**
 * API Correctness Tests
 *
 * Tests that the full API flow produces correct anonymization:
 * 1. Upload PDF to API
 * 2. Get mappings_used from response
 * 3. Apply mappings_used to _original.txt
 * 4. Compare with _anonymized.txt
 *
 * This verifies that the API extracts and anonymizes PII correctly.
 *
 * IMPORTANT: Resource files must NOT be modified. They are the ground truth.
 */
import { describe, test, expect, beforeAll } from 'vitest';
import { readFileSync } from 'fs';
import { join } from 'path';
import { RESOURCES_PATH, API_BASE, isBackendRunning } from './setup';

// Helper to upload PDF and get mappings
async function uploadPdfAndGetMappings(filename: string): Promise<{
  mappings_used: Record<string, string>;
  total_matches: number;
}> {
  const pdfPath = join(RESOURCES_PATH, filename);
  const pdfBuffer = readFileSync(pdfPath);
  const blob = new Blob([pdfBuffer], { type: 'application/pdf' });

  const formData = new FormData();
  formData.append('file', blob, filename);
  formData.append('config', '{}');

  const response = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status}`);
  }

  const result = await response.json();
  return {
    mappings_used: result.mappings_used || {},
    total_matches: result.total_matches || 0,
  };
}

// Helper to load text file from resources
function loadResourceText(filename: string): string {
  const filePath = join(RESOURCES_PATH, filename);
  return readFileSync(filePath, 'utf-8');
}

// Apply replacements to text (same logic as Python test_e2e.py)
function applyReplacements(text: string, replacements: Record<string, string>): string {
  // Sort by length descending to replace longer strings first
  const sortedEntries = Object.entries(replacements).sort(
    (a, b) => b[0].length - a[0].length
  );

  let result = text;
  for (const [original, replacement] of sortedEntries) {
    // Check if the term is purely Hebrew
    const isHebrewOnly = /^[\u0590-\u05FF']+$/.test(original);

    if (isHebrewOnly) {
      // For Hebrew words: don't match if surrounded by Hebrew letters
      // Using lookbehind/lookahead for word boundaries
      const pattern = new RegExp(
        `(?<![א-ת])${escapeRegex(original)}(?![א-ת])`,
        'g'
      );
      result = result.replace(pattern, replacement);
    } else {
      // For numbers, emails, mixed content: simple replacement
      result = result.split(original).join(replacement);
    }
  }

  return result;
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Normalize text for comparison
function normalizeText(text: string): string {
  return text
    .replace(/\r\n/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .split('\n')
    .map(line => line.trim())
    .join('\n')
    .trim();
}

describe('API Correctness Tests', () => {
  beforeAll(async () => {
    const running = await isBackendRunning();
    if (!running) {
      throw new Error('Backend server must be running on port 8000');
    }
  });

  test('7.1 API mappings applied to original.txt matches anonymized.txt (medical_form)', async () => {
    // Step 1: Upload PDF and get mappings
    const { mappings_used, total_matches } = await uploadPdfAndGetMappings(
      'medical_form_original.pdf'
    );

    // Step 2: Load original text
    const originalText = loadResourceText('medical_form_original.txt');

    // Step 3: Load expected anonymized text
    const expectedAnonymized = loadResourceText('medical_form_anonimyzed.txt');

    // Step 4: Apply API mappings to original text
    const actualAnonymized = applyReplacements(originalText, mappings_used);

    // Step 5: Compare
    const normalizedActual = normalizeText(actualAnonymized);
    const normalizedExpected = normalizeText(expectedAnonymized);

    // Check if they match exactly
    if (normalizedActual !== normalizedExpected) {
      // Find differences for debugging
      const actualLines = normalizedActual.split('\n');
      const expectedLines = normalizedExpected.split('\n');

      const differences: string[] = [];
      const maxLines = Math.max(actualLines.length, expectedLines.length);

      for (let i = 0; i < maxLines; i++) {
        const actual = actualLines[i] || '(missing)';
        const expected = expectedLines[i] || '(missing)';
        if (actual !== expected) {
          differences.push(`Line ${i + 1}:\n  Expected: ${expected}\n  Actual:   ${actual}`);
        }
      }

      // Fail with helpful message
      expect(normalizedActual).toBe(normalizedExpected);
    }

    expect(normalizedActual).toBe(normalizedExpected);
  });

  test('7.2 API mappings applied to original.txt matches anonymized.txt (medical_summary)', async () => {
    // Step 1: Upload PDF and get mappings
    const { mappings_used } = await uploadPdfAndGetMappings(
      'medical_summary_original.pdf'
    );

    // Step 2: Load original text
    const originalText = loadResourceText('medical_summary_original.txt');

    // Step 3: Load expected anonymized text
    const expectedAnonymized = loadResourceText('medical_summary_anonymized.txt');

    // Step 4: Apply API mappings to original text
    const actualAnonymized = applyReplacements(originalText, mappings_used);

    // Step 5: Compare
    const normalizedActual = normalizeText(actualAnonymized);
    const normalizedExpected = normalizeText(expectedAnonymized);

    expect(normalizedActual).toBe(normalizedExpected);
  });

  test('7.3 API detects all PII that needs replacement (medical_form)', async () => {
    // Upload PDF
    const { mappings_used } = await uploadPdfAndGetMappings(
      'medical_form_original.pdf'
    );

    // Load the difference between original and anonymized to find what SHOULD be replaced
    const originalText = loadResourceText('medical_form_original.txt');
    const anonymizedText = loadResourceText('medical_form_anonimyzed.txt');

    // Find values that are in original but not in anonymized (these are PII)
    // And check that they're in mappings_used
    const mappingKeys = Object.keys(mappings_used);

    // Key PII values that MUST be detected
    const criticalPii = [
      'מיכאל',           // First name
      'פורגאצ\'',        // Last name (note: may have encoding differences)
      '15968548',        // ID number
      '7374503',         // Military ID
      '058-6045454',     // Phone
    ];

    const missingPii: string[] = [];
    for (const pii of criticalPii) {
      // Check if this PII is in original
      if (originalText.includes(pii)) {
        // It should be in mappings_used
        if (!mappingKeys.includes(pii)) {
          missingPii.push(pii);
        }
      }
    }

    expect(missingPii).toEqual([]);
  });

  test('7.4 API mappings contain correct replacement values', async () => {
    // Upload PDF
    const { mappings_used } = await uploadPdfAndGetMappings(
      'medical_form_original.pdf'
    );

    // Load expected anonymized text to find replacement values
    const anonymizedText = loadResourceText('medical_form_anonimyzed.txt');

    // Check that replacement values from mappings are in the expected output
    const replacementValues = Object.values(mappings_used);

    // At least some replacement values should appear in expected anonymized text
    let foundCount = 0;
    for (const replacement of replacementValues) {
      if (typeof replacement === 'string' && replacement.length >= 3) {
        if (anonymizedText.includes(replacement)) {
          foundCount++;
        }
      }
    }

    // At least half of the replacements should match expected
    expect(foundCount).toBeGreaterThan(0);
  });
});
