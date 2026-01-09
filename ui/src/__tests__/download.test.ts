// Download API Tests (3.1-3.3)
import { describe, test, expect, beforeAll } from 'vitest';
import { loadTestPdf, API_BASE, isBackendRunning } from './setup';

interface ExtractResponse {
  file_id: string;
  page_count: number;
  total_matches: number;
}

async function extractPdf(file: File): Promise<ExtractResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Extract failed: ${response.status}`);
  }

  return response.json();
}

async function downloadFile(fileId: string): Promise<Response> {
  return fetch(`${API_BASE}/download/${fileId}`);
}

describe('Download API', () => {
  let validFileId: string;

  beforeAll(async () => {
    const running = await isBackendRunning();
    if (!running) {
      throw new Error('Backend is not running. Start it with: uvicorn api.main:app --port 8000');
    }

    // Extract a file to get a valid file_id for download tests
    const file = loadTestPdf('medical_form_original.pdf');
    const result = await extractPdf(file);
    validFileId = result.file_id;
  });

  // 3.1 Download valid file
  test('3.1 GET /download/{file_id} returns PDF after extraction', async () => {
    const response = await downloadFile(validFileId);

    expect(response.ok).toBe(true);
    expect(response.status).toBe(200);

    // Check content type
    const contentType = response.headers.get('content-type');
    expect(contentType).toContain('application/pdf');

    // Check we get actual content
    const blob = await response.blob();
    expect(blob.size).toBeGreaterThan(0);

    // Verify it's a PDF (starts with %PDF)
    const arrayBuffer = await blob.slice(0, 5).arrayBuffer();
    const header = new TextDecoder().decode(arrayBuffer);
    expect(header).toContain('%PDF');
  });

  // 3.2 Download invalid file_id
  test('3.2 GET /download/{file_id} with invalid ID returns 404', async () => {
    const response = await downloadFile('nonexistent-file-id-12345');

    expect(response.ok).toBe(false);
    expect(response.status).toBe(404);
  });

  // 3.3 Downloaded PDF is valid and has content
  test('3.3 Downloaded PDF contains content', async () => {
    const response = await downloadFile(validFileId);
    const blob = await response.blob();

    // PDF should have some content (even small PDFs are valid)
    expect(blob.size).toBeGreaterThan(100); // At least 100 bytes

    // Should be a valid PDF file
    const arrayBuffer = await blob.slice(0, 100).arrayBuffer();
    const header = new TextDecoder().decode(arrayBuffer);
    expect(header).toContain('%PDF-');
  });
});
