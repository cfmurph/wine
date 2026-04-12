export interface WineSearchResult {
  id: string;
  canonical_name: string;
  producer?: string;
  vintage?: number;
  country?: string;
  region?: string;
  style?: string;
  avg_score?: number;
  avg_price?: number;
  currency?: string;
  image_url?: string;
}

export interface WineScore {
  provider: string;
  score?: number;
  score_scale: number;
  review_count?: number;
  updated_at?: string;
}

export interface WinePrice {
  provider: string;
  currency: string;
  min_price?: number;
  avg_price?: number;
  max_price?: number;
  purchase_url?: string;
  updated_at?: string;
}

export interface WineDetail extends WineSearchResult {
  subregion?: string;
  appellation?: string;
  grape_varieties: string[];
  abv?: number;
  description?: string;
  scores: WineScore[];
  prices: WinePrice[];
  pairings: string[];
  created_at?: string;
  updated_at?: string;
}

export interface WineSearchResponse {
  results: WineSearchResult[];
  total: number;
  page: number;
  per_page: number;
}

export interface PairingSearchResponse {
  food: string;
  wine_types: string[];
  wines: WineSearchResult[];
  provider: string;
}

export interface UserWine {
  id: string;
  wine_id: string;
  status: "favorite" | "tried" | "want_to_try" | "cellar";
  user_rating?: number;
  notes?: string;
}

export interface CompareItem {
  id: string;
  canonical_name: string;
  producer?: string;
  vintage?: number;
  country?: string;
  region?: string;
  grape_varieties: string[];
  style?: string;
  avg_score?: number;
  avg_price?: number;
  currency?: string;
  value_score?: number;
}

export interface SearchFilters {
  q: string;
  region?: string;
  country?: string;
  vintage?: number;
  style?: string;
  grape?: string;
}
