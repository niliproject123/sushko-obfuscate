# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Text Extractor - A web service that extracts text from PDF documents and obfuscates PII (personally identifiable information). Consists of a FastAPI backend (Python) and React frontend (TypeScript).

## Commands

### Backend (API)

```bash
# Run API server (from project root)
uvicorn api.main:app --reload --port 8000

# Run all tests
pytest api/tests/

# Run specific test file
pytest api/tests/test_detectors.py

# Run specific test
pytest api/tests/test_detectors.py::test_israeli_id_detection -v
```

### Frontend (UI)

```bash
cd ui

# Development server (proxies /api to port 8000)
npm run dev

# Build (TypeScript check + production build)
npm run build

# Lint
npm run lint

# Tests
npm run test           # Run once
npm run test:watch     # Watch mode
npm run test:ui        # Vitest UI
```

### Docker

```bash
docker build -t pdf-extractor .
docker run -p 8000:8000 pdf-extractor
```

## Architecture

```
┌─────────────────────────────────────────┐
│  React + TypeScript UI (ui/)            │
│  Vite dev server on :5173               │
└─────────────────────────────────────────┘
                    │ HTTP/REST
                    ▼
┌─────────────────────────────────────────┐
│  FastAPI Backend (api/)                 │
│  uvicorn on :8000                       │
└─────────────────────────────────────────┘
```

### Backend Processing Pipeline

```
Upload → Processor → Detectors → Obfuscator → Output
            │            │            │
    PyMuPDF/OCR    Find PII     Replace with
    extract text   patterns     placeholders
```

**Key abstractions:**
- `Processor` (`api/processors/`) - Extract text from file formats, reassemble output
- `Detector` (`api/detectors/`) - Find PII matches (Israeli ID, Hebrew/English names, regex patterns)
- `Obfuscator` (`api/obfuscators/`) - Replace matches with configured placeholders

### Frontend Architecture

Hooks-based React without external state management:
- `hooks/` - State logic (useUserConfig, useFileProcessor, useAdminConfig)
- `services/` - API communication (extractApi, configApi)
- `components/` - Presentational components organized by feature

## Configuration

Server config stored in `api/config/settings.json`:
- `patterns` - PII detection regex patterns with optional validators
- `replacement_pools` - Name/city pools for generating fake values
- `placeholders` - PII type to placeholder text mapping
- `default_replacements` - Known PII→replacement mappings

## Hebrew Text Handling

- Automatic RTL visual-order fix for reversed Hebrew character sequences in PDFs
- Word boundary regex patterns prevent breaking Hebrew words during replacement:
  ```python
  r'(?<![א-ת])term(?![א-ת])'  # Match standalone term only
  ```

## Test Resources

Test PDFs and expected outputs in `api/tests/resources/`:
- `medical_form_original.pdf` / `.txt` / `_anonymized.txt`
- `medical_summary_original.pdf` / `.txt` / `_anonymized.txt`
