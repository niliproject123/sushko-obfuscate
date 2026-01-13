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
  warnings?: string[];
  obfuscated_text?: string;
}

export interface PlainTextResponse {
  total_matches: number;
  mappings_used: Record<string, string>;
  obfuscated_text: string;
  warnings?: string[];
}

export interface FileProcessingResult {
  file: File;
  response?: ExtractResponse;
  error?: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

export interface TextProcessingResult {
  text: string;
  response?: PlainTextResponse;
  error?: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}
