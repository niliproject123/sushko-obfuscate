export interface ObfuscationTerm {
  text: string
  type: string
  replace_with?: string
}

export interface PIIMatch {
  text: string
  type: string
  start: number
  end: number
}

export interface PageSummary {
  page_number: number
  matches_found: number
  matches: PIIMatch[]
}

export interface ExtractResponse {
  file_id: string
  page_count: number
  total_matches: number
  pages: PageSummary[]
  warnings?: string[]
}
