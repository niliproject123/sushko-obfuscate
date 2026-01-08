# UI API Testing Plan

## Overview

Test the UI's API integration using the **same test resources** as the backend tests. These files are READ-ONLY and must not be modified.

## Test Resources (DO NOT MODIFY)

```
tests/resources/
├── medical_form_original.pdf      # Input PDF for testing
├── medical_form_original.txt      # Reference extracted text
├── medical_form_anonimyzed.txt    # Expected anonymized output
├── medical_summary_original.pdf   # Second test PDF
├── medical_summary_original.txt   # Reference extracted text
├── medical_summary_anonymized.txt # Expected anonymized output
└── replacements.md                # Documented replacement mappings
```

## Test Categories

### 1. Config API Tests (`/api/config/*`)

| Test | Endpoint | Method | Verify |
|------|----------|--------|--------|
| Get full config | `/api/config` | GET | Returns patterns, pools, ocr, placeholders |
| Get patterns | `/api/config/patterns` | GET | Returns array of PIIPatternConfig |
| Add pattern | `/api/config/patterns` | POST | Creates new pattern, returns it |
| Update pattern | `/api/config/patterns/{name}` | PUT | Modifies existing pattern |
| Delete pattern | `/api/config/patterns/{name}` | DELETE | Removes pattern |
| Get pools | `/api/config/pools` | GET | Returns all replacement pools |
| Update pool | `/api/config/pools/{name}` | PUT | Updates pool values |
| Reload config | `/api/config/reload` | POST | Reloads from disk |

**Test Scenarios:**
```typescript
describe('Config API', () => {
  test('GET /config returns valid server config')
  test('GET /config/patterns returns array with israeli_id pattern')
  test('POST /config/patterns creates new pattern')
  test('PUT /config/patterns/{name} updates existing pattern')
  test('DELETE /config/patterns/{name} removes pattern')
  test('PUT /config/pools/{name} updates pool values')
  test('POST /config/reload reloads config from disk')
})
```

### 2. Extract API Tests (`/api/extract`)

| Test | Input | Config | Verify |
|------|-------|--------|--------|
| Basic extraction | medical_form_original.pdf | none | Returns file_id, page_count, matches |
| With user replacements | medical_form_original.pdf | `{"user_replacements": {"מיכאל": "דוד"}}` | Replacement applied |
| With disabled detectors | medical_form_original.pdf | `{"disabled_detectors": ["email"]}` | Email not detected |
| Multi-page PDF | medical_summary_original.pdf | none | Multiple pages in response |
| Invalid file | text file | none | Returns 400 error |
| Oversized file | >20MB | none | Returns 413 error |

**Test Scenarios:**
```typescript
describe('Extract API', () => {
  test('POST /extract with PDF returns file_id and matches')
  test('POST /extract detects Israeli ID numbers')
  test('POST /extract detects Hebrew names')
  test('POST /extract with user_replacements applies custom mapping')
  test('POST /extract with disabled_detectors skips specified patterns')
  test('POST /extract returns correct page_count for multi-page PDF')
  test('POST /extract with invalid file returns 400')
})
```

### 3. Download API Tests (`/api/download/{file_id}`)

| Test | Precondition | Verify |
|------|--------------|--------|
| Valid download | Extract first, get file_id | Returns PDF blob |
| Invalid file_id | None | Returns 404 |
| Expired file_id | Wait for TTL | Returns 404 |

**Test Scenarios:**
```typescript
describe('Download API', () => {
  test('GET /download/{file_id} returns PDF after extraction')
  test('GET /download/{file_id} with invalid ID returns 404')
  test('Downloaded PDF contains anonymized content')
})
```

### 4. Integration Tests (Full Flow)

**Flow 1: User Config → Extract → Download**
```
1. Load user replacements from localStorage mock
2. Upload medical_form_original.pdf with user_replacements
3. Verify response contains expected matches
4. Download processed file
5. Verify downloaded PDF is valid
```

**Flow 2: Admin Config → Extract → Verify**
```
1. GET /config to load current patterns
2. Disable a pattern via PUT
3. Upload PDF
4. Verify disabled pattern not in matches
5. Re-enable pattern, verify it detects again
```

**Flow 3: Comparison Test (E2E)**
```
1. Upload medical_form_original.pdf
2. Use same replacements as tests/resources/replacements.md
3. Extract text from downloaded PDF
4. Compare with medical_form_anonimyzed.txt (should match)
```

## Test Implementation

### Option A: Vitest + fetch mocking (Unit/Integration)

```typescript
// ui/src/__tests__/api/config.test.ts
import { describe, test, expect, beforeAll } from 'vitest'
import { getConfig, getPatterns, addPattern } from '../../services/configApi'

describe('Config API', () => {
  test('getConfig returns server config', async () => {
    const config = await getConfig()
    expect(config.patterns).toBeDefined()
    expect(config.replacement_pools).toBeDefined()
    expect(config.placeholders).toBeDefined()
  })
})
```

### Option B: Playwright/Cypress (E2E with real backend)

```typescript
// e2e/extract.spec.ts
test('upload and process PDF', async ({ page }) => {
  await page.goto('/')

  // Upload file
  const fileInput = page.locator('input[type="file"]')
  await fileInput.setInputFiles('tests/resources/medical_form_original.pdf')

  // Process
  await page.click('button:has-text("Process")')

  // Verify results
  await expect(page.locator('.file-result-card')).toBeVisible()
  await expect(page.locator('.match-tag')).toHaveCount.greaterThan(0)
})
```

### Option C: API-only tests (No UI, just services)

```typescript
// ui/src/__tests__/services/extractApi.test.ts
import { extractPdf, downloadFile } from '../../services/extractApi'
import { readFileSync } from 'fs'
import { join } from 'path'

const RESOURCES = join(__dirname, '../../../../tests/resources')

describe('Extract API', () => {
  test('processes medical form PDF', async () => {
    const pdfBuffer = readFileSync(join(RESOURCES, 'medical_form_original.pdf'))
    const file = new File([pdfBuffer], 'medical_form_original.pdf', {
      type: 'application/pdf'
    })

    const response = await extractPdf(file, {
      user_replacements: { 'מיכאל': 'דוד' }
    })

    expect(response.file_id).toBeDefined()
    expect(response.total_matches).toBeGreaterThan(0)
  })
})
```

## Recommended Approach

**Phase 1: API Service Tests (Option C)**
- Test services layer directly against running backend
- Fast feedback, easy to debug
- Uses real test PDFs

**Phase 2: Hook Tests**
- Test useAdminConfig, useUserConfig, useFileProcessor
- Mock API responses based on real data

**Phase 3: E2E Tests (Option B)**
- Full browser automation
- Test complete user flows
- Visual regression testing

## File Structure

```
ui/
├── src/
│   └── __tests__/
│       ├── services/
│       │   ├── configApi.test.ts
│       │   └── extractApi.test.ts
│       └── hooks/
│           ├── useUserConfig.test.ts
│           └── useAdminConfig.test.ts
├── e2e/
│   ├── config.spec.ts
│   ├── extract.spec.ts
│   └── download.spec.ts
└── vitest.config.ts
```

## Test Data Requirements

All tests use files from `tests/resources/` (READ-ONLY):
- Load PDFs as File objects for upload tests
- Load .txt files for comparison/verification
- Load replacements.md for consistent test data

**No new test files needed** - reuse existing backend test resources.
