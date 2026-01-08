# PDF Text Extractor — Requirements

## Overview

A web service that extracts text from PDF documents and obfuscates personally identifiable information (PII) before returning the processed document.

## Functional Requirements

### Core Features

1. **PDF Upload**
   - Accept PDF files up to 20MB
   - Support drag-and-drop and file picker upload
   - Validate file type and size before processing

2. **Text Extraction**
   - Extract text content from all PDF pages
   - Preserve page structure information
   - Extract table data when present

3. **PII Detection**
   - Detect Israeli ID numbers (9-digit with checksum validation)
   - Detect Hebrew names (following שם/שם פרטי/שם משפחה patterns)
   - Detect English names (following Name/First Name/Last Name patterns)
   - Support user-defined custom terms for obfuscation

4. **Obfuscation**
   - Replace detected PII with configurable placeholders
   - Default placeholders: `[NAME]`, `[ID]`, `[REDACTED]`
   - Support custom replacement text for user-defined terms
   - User-defined terms take priority over pattern detection
   - pages kept - obfuscated pages match numbering in original pdf

5. **Output**
   - Generate processed PDF with obfuscated content
   - pages corresponds to original pdf pages
   - Provide summary of detected and obfuscated PII
   - Support file download with unique file ID

     

### User Interface

1. **File Upload Section**
   - Visual drag-and-drop area
   - File selection feedback
   - File size display

2. **Custom Obfuscations Section**
   - Add/remove obfuscation terms
   - Optional custom replacement text
   - Clear input validation

3. **Results Section**
   - Processing status indicator
   - Per-page match summary
   - Match type and text display
   - Download button for processed file

4. **configuration**
   - all PII categories, regexes, names etc. are configurable using the UI
   - user can define specific values he wants to change with different values - valid only for this session and saved in local storage of browser

## Non-Functional Requirements

### Performance
- Process typical documents (1-10 pages) within 5 seconds
- Support concurrent requests
- Automatic cleanup of temporary files after 1 hour

### Security
- No persistent storage of uploaded documents
- Temporary files deleted after TTL expiration
- CORS configuration for frontend access

### Scalability
- Stateless API design
- Container-ready deployment
- Horizontal scaling support

### Reliability
- Health check endpoint for monitoring
- Graceful error handling
- Input validation at all boundaries

## Technical Constraints

### Backend
- Python 3.11+
- FastAPI framework
- PyMuPDF for PDF processing
- pdfplumber for table extraction

### Frontend
- React 18+
- TypeScript
- Vite build tool

### Deployment
- Docker containerization
- Railway platform compatible
- uvicorn ASGI server
