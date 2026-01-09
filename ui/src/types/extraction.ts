// Extraction request/response types

export interface PIIMatch {
  text: string;
  type: string;
  start: number;
  end: number;
  pattern_name?: string;
  replacement?: string;
}

export interface PageSummary {
  page_number: number;
  matches_found: number;
  matches: PIIMatch[];
}

export interface ExtractResponse {
  file_id: string;
  page_count: number;
  total_matches: number;
  pages: PageSummary[];
  mappings_used?: Record<string, string>;
}

export interface FileProcessingResult {
  file: File;
  response?: ExtractResponse;
  error?: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}
