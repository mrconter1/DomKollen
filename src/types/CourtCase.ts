export interface CourtCase {
  court_ids: string[];
  area: string;
  verdict_pdf: string;
  tags: string[];
  keyword_counts: {
    [key: string]: number;
  };
  date?: string;  // Optional since some older cases might not have dates
  num_pages: number;
} 