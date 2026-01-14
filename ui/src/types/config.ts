// Configuration types matching backend schemas

export interface PIIPatternConfig {
  name: string;
  pii_type: string; // "NAME", "ID", "PHONE", "EMAIL", "ADDRESS", etc.
  regex: string;
  capture_group: number;
  enabled: boolean;
  validator: string | null;
}

export interface ReplacementPoolsConfig {
  name_hebrew_first: string[];
  name_hebrew_last: string[];
  name_english_first: string[];
  name_english_last: string[];
  city: string[];
  street: string[];
}

export interface OCRConfig {
  enabled: boolean;
  languages: string[];
  dpi: number;
  min_text_threshold: number;
}

export interface ServerConfig {
  patterns: PIIPatternConfig[];
  replacement_pools: ReplacementPoolsConfig;
  ocr: OCRConfig;
  placeholders: Record<string, string>;
  default_replacements: Record<string, string>;
  categories: Record<string, string[]>;
  disabled_categories: string[];
}

export interface RequestConfig {
  user_replacements: Record<string, string>;
  disabled_detectors: string[];
  force_ocr: boolean;
  custom_patterns: PIIPatternConfig[];
}

export interface UserConfig {
  replacements: Record<string, string>;
  disabled_detectors: string[];
  force_ocr: boolean;
}

export const DEFAULT_USER_CONFIG: UserConfig = {
  replacements: {},
  disabled_detectors: [],
  force_ocr: false,
};
