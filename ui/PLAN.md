# UI Implementation Plan

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  [User Config]  [Admin Config]                    TABS  │
├─────────────────────────────────────────────────────────┤
│  Tab Content (User or Admin config)                     │
├─────────────────────────────────────────────────────────┤
│  File Upload (multi-file drag & drop)                   │
├─────────────────────────────────────────────────────────┤
│  [Process All PDFs] Button                              │
├─────────────────────────────────────────────────────────┤
│  Processing Animation (when active)                     │
├─────────────────────────────────────────────────────────┤
│  Results - Stacked Cards (one per file)                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │ file1.pdf - 5 matches │ [Download]              │    │
│  │ Page 1: ... Page 2: ...                         │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ file2.pdf - 3 matches │ [Download]              │    │
│  │ Page 1: ...                                     │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Separation of Concerns

### Hooks (Logic Layer)
```
src/hooks/
├── useLocalStorage.ts      # Generic localStorage read/write
├── useUserConfig.ts        # User config state + localStorage persistence
├── useAdminConfig.ts       # Server config fetch/update via API
├── useFileProcessor.ts     # Multi-file upload & processing logic
└── useApi.ts               # API client wrapper
```

### Services (API Layer)
```
src/services/
├── api.ts                  # Base fetch wrapper with error handling
├── extractApi.ts           # POST /extract, GET /download
└── configApi.ts            # Config CRUD endpoints
```

### Components (View Layer)
```
src/components/
├── layout/
│   └── Tabs.tsx            # Tab switcher component
├── config/
│   ├── UserConfig.tsx      # User config tab content
│   ├── AdminConfig.tsx     # Admin config tab content
│   ├── ReplacementEditor.tsx   # Pattern→replacement list (shared)
│   ├── PatternEditor.tsx   # Regex pattern CRUD (admin)
│   ├── PoolEditor.tsx      # Replacement pools editor (admin)
│   └── SettingsPanel.tsx   # OCR/placeholders (admin)
├── upload/
│   └── FileUpload.tsx      # Multi-file drag & drop (update existing)
├── processing/
│   └── ProcessingStatus.tsx # Animation + progress
└── results/
    ├── ResultsContainer.tsx # Stacked cards container
    ├── FileResultCard.tsx   # Single file result card
    └── MatchList.tsx        # PII matches display
```

### Types
```
src/types/
├── config.ts               # Config-related types
├── extraction.ts           # Extraction request/response types
└── index.ts                # Re-exports
```

## Implementation Steps

### Phase 1: Foundation
1. [ ] Create folder structure (hooks/, services/, types/, components/ subfolders)
2. [ ] Define TypeScript types for config and extraction
3. [ ] Create API service layer (api.ts, extractApi.ts, configApi.ts)
4. [ ] Create useLocalStorage hook
5. [ ] Create useApi hook

### Phase 2: User Config Tab
6. [ ] Create useUserConfig hook (localStorage-backed)
7. [ ] Create ReplacementEditor component (pattern→replacement list)
8. [ ] Create UserConfig component with:
   - Prominent: ReplacementEditor
   - Collapsible: Disabled detectors, Force OCR toggle
9. [ ] Create Tabs component

### Phase 3: Admin Config Tab
10. [ ] Create useAdminConfig hook (server-backed)
11. [ ] Create PatternEditor component (CRUD for patterns)
12. [ ] Create PoolEditor component (edit replacement pools)
13. [ ] Create SettingsPanel component (OCR, placeholders)
14. [ ] Create AdminConfig component combining above

### Phase 4: Multi-File Processing
15. [ ] Update FileUpload to support multiple files
16. [ ] Create useFileProcessor hook (parallel processing)
17. [ ] Create ProcessingStatus component (animation)
18. [ ] Create FileResultCard component
19. [ ] Create ResultsContainer component

### Phase 5: Integration
20. [ ] Update App.tsx to use new architecture
21. [ ] Wire user config into extraction requests
22. [ ] Test full flow
23. [ ] Polish styling

## Key Behaviors

### User Config (localStorage)
- Loaded on app start from localStorage
- Saved to localStorage on every change
- Sent as `config.user_replacements` in extract request
- Takes precedence over server config

### Admin Config (server)
- Fetched from GET /api/config on tab open
- Saved via PUT /api/config endpoints
- Persists to disk on server

### Multi-File Processing
- All files sent in parallel (Promise.all)
- Each file → POST /api/extract
- Results accumulated as they complete
- Animation shows overall progress
- Each result card has its own download button

### Request Config Structure
```typescript
// Sent with each extract request
{
  user_replacements: { "מיכאל": "דוד", ... },  // from User Config
  disabled_detectors: ["email"],               // from User Config
  force_ocr: false                             // from User Config
}
```

## File Naming Conventions
- Hooks: `use{Name}.ts`
- Components: `{Name}.tsx` (PascalCase)
- Services: `{name}Api.ts` (camelCase)
- Types: `{name}.ts` (camelCase)
- CSS: `{ComponentName}.css` (match component)
