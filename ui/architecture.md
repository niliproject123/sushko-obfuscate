# UI Architecture

## Overview

The UI is a React + TypeScript single-page application built with Vite. It follows a clean separation of concerns with distinct layers for logic (hooks), data fetching (services), and presentation (components).

```
┌─────────────────────────────────────────────────────────────┐
│                        App.tsx                               │
│                    (Main orchestrator)                       │
└─────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│    Hooks      │   │  Components   │   │   Services    │
│  (State &     │   │   (View)      │   │   (API)       │
│   Logic)      │   │               │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
```

## Directory Structure

```
ui/src/
├── hooks/                  # Custom React hooks (logic layer)
│   ├── index.ts
│   ├── useLocalStorage.ts  # Generic localStorage persistence
│   ├── useUserConfig.ts    # User config state management
│   ├── useAdminConfig.ts   # Server config CRUD operations
│   └── useFileProcessor.ts # Multi-file processing logic
│
├── services/               # API communication layer
│   ├── index.ts
│   ├── api.ts              # Base fetch wrapper with error handling
│   ├── extractApi.ts       # PDF extraction endpoints
│   └── configApi.ts        # Configuration CRUD endpoints
│
├── types/                  # TypeScript type definitions
│   ├── index.ts
│   ├── config.ts           # Configuration-related types
│   └── extraction.ts       # Extraction request/response types
│
├── components/
│   ├── layout/             # Layout components
│   │   ├── Tabs.tsx        # Tab navigation component
│   │   └── Tabs.css
│   │
│   ├── config/             # Configuration UI components
│   │   ├── index.ts
│   │   ├── UserConfig.tsx      # User configuration panel
│   │   ├── AdminConfig.tsx     # Admin configuration panel
│   │   ├── ReplacementEditor.tsx # Pattern→replacement editor
│   │   ├── PatternEditor.tsx   # Regex pattern CRUD
│   │   ├── PoolEditor.tsx      # Replacement pools editor
│   │   └── SettingsPanel.tsx   # OCR & placeholders settings
│   │
│   ├── upload/             # File upload components
│   │   ├── index.ts
│   │   └── FileUpload.tsx  # Multi-file drag & drop
│   │
│   ├── processing/         # Processing status components
│   │   ├── index.ts
│   │   └── ProcessingStatus.tsx
│   │
│   └── results/            # Results display components
│       ├── index.ts
│       ├── ResultsContainer.tsx
│       └── FileResultCard.tsx
│
├── App.tsx                 # Main application component
├── App.css                 # Global styles
├── main.tsx                # Entry point
└── index.css               # Base styles
```

## Layer Responsibilities

### Hooks Layer (`hooks/`)

Manages application state and business logic, keeping components pure and focused on rendering.

| Hook | Purpose | Storage |
|------|---------|---------|
| `useLocalStorage` | Generic localStorage read/write with React state sync | Browser localStorage |
| `useUserConfig` | User-specific config (replacements, disabled detectors) | Browser localStorage |
| `useAdminConfig` | Server config CRUD with loading/error states | Server API |
| `useFileProcessor` | File queue, parallel processing, results collection | React state |

### Services Layer (`services/`)

Handles all HTTP communication with the backend API.

| Service | Endpoints | Purpose |
|---------|-----------|---------|
| `api.ts` | - | Base fetch wrapper, error handling, ApiError class |
| `extractApi.ts` | `/extract`, `/download` | PDF upload and processed file download |
| `configApi.ts` | `/config/*` | Full config CRUD, patterns, pools |

### Components Layer (`components/`)

Pure presentational components receiving data and callbacks via props.

```
components/
├── layout/         → Navigation & structure
├── config/         → Configuration editing UI
├── upload/         → File selection & queue display
├── processing/     → Progress & status indicators
└── results/        → Processed file results display
```

## Data Flow

### User Config Flow
```
localStorage ──► useLocalStorage ──► useUserConfig ──► UserConfig component
                                           │
                                           ▼
                              extractApi (as request config)
```

### Admin Config Flow
```
Server ◄──► configApi ◄──► useAdminConfig ──► AdminConfig component
                                │
                                ▼
                    PatternEditor, PoolEditor, SettingsPanel
```

### File Processing Flow
```
FileUpload ──► useFileProcessor.addFiles()
                      │
                      ▼
              useFileProcessor.processAll(userConfig)
                      │
                      ▼
              extractApi.extractPdf() (parallel for each file)
                      │
                      ▼
              ProcessingStatus + ResultsContainer
                      │
                      ▼
              FileResultCard (download button)
```

## State Management

The application uses React's built-in hooks for state management:

- **Local component state**: `useState` for UI-only state (form inputs, modals)
- **Shared state**: Custom hooks that encapsulate `useState` + side effects
- **Persistent state**: `useLocalStorage` hook for browser persistence
- **Server state**: `useAdminConfig` with loading/error handling

No external state management library (Redux, Zustand) is used—the app is simple enough to manage with hooks.

## Type System

All types are centralized in `types/` and re-exported from `types/index.ts`:

```typescript
// Config types (config.ts)
PIIPatternConfig      // Detection pattern definition
ReplacementPoolsConfig // Name/city pools
OCRConfig             // OCR settings
ServerConfig          // Full server configuration
UserConfig            // User-specific settings (localStorage)

// Extraction types (extraction.ts)
PIIMatch              // Single PII detection
PageSummary           // Per-page results
ExtractResponse       // API response
FileProcessingResult  // File + status + response/error
```

## Styling

- CSS files co-located with components (`Component.tsx` + `Component.css`)
- No CSS-in-JS or utility framework
- BEM-like class naming convention
- Responsive design with max-width containers

## Build & Development

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start Vite dev server (port 5173, proxies `/api` to 8000) |
| `npm run build` | TypeScript check + production build |
| `npm run lint` | ESLint with strict rules |
