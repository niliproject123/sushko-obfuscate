# סושקו - Sushko PII Obfuscator

A Hebrew-focused PII (Personally Identifiable Information) obfuscation tool for PDF documents and plain text. Originally built as a web application, now also available as a standalone desktop app.

## What It Does

Sushko extracts text from PDF files and obfuscates sensitive personal information:

- **Israeli ID numbers** (with checksum validation)
- **Phone numbers** (mobile and landline)
- **Names** (Hebrew and English, first/last/full)
- **Addresses** (cities, streets)
- **Military units** (organized by category)
- **Medical licenses, case numbers, bank accounts** and more

The tool supports:
- PDF text extraction with OCR fallback for image-based PDFs
- Plain text input mode
- Configurable detection patterns and replacement rules
- Category-based word detection (e.g., military units by type)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      React UI (TypeScript)                   │
│                    Vite dev server :5173                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Upload     │  │  Settings    │  │     Results      │   │
│  │  PDF/Text    │  │ User/Admin   │  │  View/Download   │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Python)                   │
│                      uvicorn :8000                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Processors  │  │  Detectors   │  │   Obfuscators    │   │
│  │  PDF → Text  │  │  Find PII    │  │  Replace Text    │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Processing Pipeline

```
Upload → Processor → Detectors → Obfuscator → Output
            │            │            │
    PyMuPDF/OCR    30+ regex     Replace with
    extract text   patterns     placeholders
```

## File Structure

```
sushko-obfuscate/
├── api/                           # FastAPI Backend
│   ├── main.py                    # App entry point, mounts routes
│   ├── routes/
│   │   ├── extract.py             # POST /extract, /extract/plain
│   │   └── config.py              # GET/PUT/POST/DELETE config endpoints
│   ├── processors/
│   │   ├── base.py                # Abstract Processor interface
│   │   └── pdf.py                 # PDF extraction (PyMuPDF + OCR fallback)
│   ├── detectors/
│   │   ├── base.py                # Abstract Detector interface
│   │   ├── regex.py               # Regex pattern detection
│   │   ├── israeli_id.py          # ID validation with checksum
│   │   ├── hebrew_name.py         # Hebrew name detection
│   │   ├── english_name.py        # English name detection
│   │   ├── user_defined.py        # User-defined replacements
│   │   ├── category.py            # Category-based word detection
│   │   └── validators.py          # Validation functions
│   ├── obfuscators/
│   │   └── text.py                # Text replacement engine
│   ├── replacements/
│   │   ├── mapper.py              # Maps detected PII to replacements
│   │   └── generators.py          # Generates fake values from pools
│   ├── config/
│   │   ├── loader.py              # Config loading and merging
│   │   ├── schemas.py             # Pydantic models
│   │   ├── settings.json          # OCR settings, placeholders
│   │   ├── patterns.json          # PII detection patterns
│   │   ├── pools.json             # Replacement pools (names, cities)
│   │   ├── categories.json        # Category word lists
│   │   └── replacements.json      # Default PII→replacement mappings
│   ├── storage/
│   │   └── temp.py                # Temporary file management (1hr TTL)
│   └── tests/                     # pytest test suite
│
├── ui/                            # React Frontend
│   ├── src/
│   │   ├── App.tsx                # Main app component
│   │   ├── hooks/
│   │   │   ├── useUserConfig.ts   # User settings (localStorage)
│   │   │   ├── useAdminConfig.ts  # Server config CRUD
│   │   │   ├── useFileProcessor.ts# Multi-file processing
│   │   │   └── useTextProcessor.ts# Plain text processing
│   │   ├── services/
│   │   │   ├── extractApi.ts      # Extraction endpoints
│   │   │   └── configApi.ts       # Config CRUD endpoints
│   │   ├── components/
│   │   │   ├── config/            # UserConfig, AdminConfig editors
│   │   │   ├── upload/            # FileUpload, TextInput
│   │   │   ├── processing/        # ProcessingStatus
│   │   │   └── results/           # ResultsContainer, FileResultCard
│   │   ├── types/
│   │   │   ├── config.ts          # Config type definitions
│   │   │   └── extraction.ts      # Extraction response types
│   │   └── utils/
│   │       └── environment.ts     # isLocal() detection
│   ├── package.json
│   └── vite.config.ts             # Dev server config
│
├── desktop/                       # Desktop App (PyInstaller)
│   ├── launcher.py                # Starts server + opens browser
│   └── sushko.spec                # PyInstaller build spec
│
├── Dockerfile                     # Production container
├── requirements.txt               # Python dependencies
└── CLAUDE.md                      # Development instructions
```

## Web vs Desktop Versions

| Aspect | Web Version | Desktop Version |
|--------|-------------|-----------------|
| Deployment | Railway/Docker | PyInstaller .exe/.app |
| Backend | Shared server | Local server (127.0.0.1) |
| Admin Settings | Password protected | Auto-unlocked |
| Config Storage | Server filesystem | Bundled JSON files |
| Users | Multi-user | Single-user |
| Download Button | Visible | Hidden |

### Detection Logic

```typescript
// ui/src/utils/environment.ts
export function isLocal(): boolean {
  return /^(127\.|localhost)/.test(window.location.hostname);
}
```

## Configuration System

### Two Settings Systems

The app has two configuration layers accessible via the "הגדרות" (Settings) section:

**1. הגדרות משתמש (User Settings)** - Stored in browser localStorage
- `replacements` - Custom text→replacement mappings (highest priority)
- `disabled_detectors` - Patterns to skip during detection
- `force_ocr` - Force OCR even if PDF has text layer

**2. הגדרות שרת (Server/Admin Settings)** - Stored in JSON files
- `patterns` - PII detection regex patterns
- `replacement_pools` - Pools of fake names, cities, streets
- `default_replacements` - Global default replacements
- `categories` - Category-based word lists
- `disabled_categories` - Which categories to skip
- `ocr` - OCR settings (DPI, languages, threshold)
- `placeholders` - PII type to placeholder text

### Config Merging at Runtime

```
Server Config (defaults)
        +
User Config (overrides)
        ↓
   Merged Config
        ↓
User replacements have priority
Disabled detectors filtered out
```

### Desktop Settings Merge Consideration

In the desktop version, both settings layers exist locally. Current state:
- User settings: browser localStorage
- Admin settings: bundled JSON files

**Options for unification:**
1. **UI-only merge** - Show all settings in one tab when `isLocal()` returns true
2. **Storage merge** - Write user config changes directly to server JSON files
3. **Keep separate** - User settings = request overrides, Admin = global defaults

The simplest improvement would be option 1: hide the "user vs admin" tab separation in desktop mode since admin is already auto-unlocked.

## Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Tesseract OCR (for image-based PDFs)

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn api.main:app --reload --port 8000

# Run tests
pytest api/tests/
```

### Frontend

```bash
cd ui
npm install
npm run dev      # Development server on :5173
npm run build    # Production build
npm run test     # Run tests
```

### Desktop Build

```bash
# Build UI first
cd ui && npm run build
cp -r dist ../static

# Build executable
pyinstaller desktop/sushko.spec

# Output in dist/sushko/
```

### Docker

```bash
docker build -t sushko .
docker run -p 8000:8000 sushko
```

## API Endpoints

### Extraction
- `POST /api/extract` - Upload PDF, returns obfuscated text and download ID
- `POST /api/extract/plain` - Process plain text
- `GET /api/download/{file_id}` - Download obfuscated PDF

### Configuration
- `GET /api/config` - Get full server config
- `PUT /api/config` - Update config fields
- `GET/POST/PUT/DELETE /api/config/patterns` - Pattern CRUD
- `GET/PUT /api/config/pools/{poolName}` - Pool editing
- `GET/POST/PUT/DELETE /api/config/categories/{name}` - Category CRUD

## License

Private/Internal use.
