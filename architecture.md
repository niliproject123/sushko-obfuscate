# PDF Text Extractor — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT                                  │
│                    React + TypeScript                           │
│                      (ui/ folder)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API                                    │
│                   FastAPI + Python                              │
│                     (api/ folder)                               │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
├── api/                    # Backend API
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Global configuration
│   ├── routes/
│   │   └── extract.py     # Upload/download endpoints
│   ├── processors/
│   │   ├── base.py        # Processor interface
│   │   └── pdf.py         # PDF processor
│   ├── detectors/
│   │   ├── base.py        # Detector interface
│   │   ├── user_defined.py
│   │   ├── israeli_id.py
│   │   ├── hebrew_name.py
│   │   └── english_name.py
│   ├── obfuscators/
│   │   ├── base.py        # Obfuscator interface
│   │   └── text.py        # Placeholder replacement
│   └── storage/
│       └── temp.py        # Temp file management
├── ui/                     # Frontend React app
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   └── types.ts
│   ├── package.json
│   └── vite.config.ts
├── tests/                  # Test suite
│   ├── test_detectors.py
│   ├── test_obfuscators.py
│   └── test_processors.py
├── Dockerfile
├── requirements.txt
├── requirements.md
└── architecture.md
```

## API Layer Architecture

```
┌─────────────────────────────────────────────┐
│  API                                        │
│  Routes, auth, file handling                │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  PROCESSORS (file type specific)            │
│  Extract text from file format              │
│  Reassemble output after obfuscation        │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  DETECTORS (shared across all types)        │
│  Find PII in extracted text                 │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  OBFUSCATORS (file type specific)           │
│  Apply redaction to content                 │
└─────────────────────────────────────────────┘
```

## Processing Flow

```
1. Upload file + optional obfuscations
2. Route to Processor by MIME type
3. Processor extracts text
4. User obfuscations applied first (exact match)
5. Detectors find remaining PII (patterns)
6. Obfuscator redacts content
7. Processor reassembles output
8. Return processed file + summary
```

## Interfaces

### Processor

```python
class Processor:
    supported_mimes: list[str]

    def extract_text(self, file: bytes) -> list[PageContent]:
        """Extract text from file, per page/segment"""

    def reassemble(self, pages: list[ProcessedPage]) -> bytes:
        """Rebuild file from processed pages"""
```

### Detector

```python
@dataclass
class PIIMatch:
    text: str       # original text found
    type: str       # "NAME", "ID", etc.
    start: int      # position in text
    end: int

class Detector:
    name: str
    pii_type: str

    def detect(self, text: str) -> list[PIIMatch]:
        """Find all PII in text"""
```

### Obfuscator

```python
class Obfuscator:
    placeholder_map: dict[str, str]

    def obfuscate(self, text: str, matches: list[PIIMatch]) -> str:
        """Replace PII with placeholders"""
```

## Components

### Processors

| Processor | MIME Types | Extracts via |
|-----------|------------|--------------|
| `PDFProcessor` | `application/pdf` | PyMuPDF + pdfplumber |

### Detectors

| Detector | PII Type | Method |
|----------|----------|--------|
| `UserDefinedDetector` | Any | Exact match from request |
| `IsraeliIdDetector` | `ID` | Regex + checksum validation |
| `HebrewNameDetector` | `NAME` | Regex: text after שם/שם פרטי/שם משפחה |
| `EnglishNameDetector` | `NAME` | Regex: text after Name/Surname/First Name/Last Name |

### Obfuscators

| Obfuscator | Output |
|------------|--------|
| `TextObfuscator` | Replaces PII with placeholders |

## Configuration

```python
class Config:
    PORT: int = 8000
    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20MB
    FILE_TTL: int = 3600  # 1 hour

    ACTIVE_DETECTORS = [
        IsraeliIdDetector(),
        HebrewNameDetector(),
        EnglishNameDetector(),
    ]

    PLACEHOLDERS = {
        "NAME": "[NAME]",
        "ID": "[ID]",
        "DEFAULT": "[REDACTED]",
    }
```

## Deployment

| Component | Choice |
|-----------|--------|
| Container | Docker |
| Server | uvicorn (ASGI) |
| Platform | Railway |

### Docker Configuration

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y poppler-utils
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Future Expansion

### New file types

1. Add Processor implementing `extract_text()` and `reassemble()`
2. Register MIME types in processor registry
3. Detectors work automatically (shared)

### New detection methods

1. Add Detector implementing `detect()`
2. Add to `ACTIVE_DETECTORS` in config

### New obfuscation methods

1. Add Obfuscator for specific output type
2. Configure in processing pipeline
