export type ScoreName = "brand" | "land" | "tourism" | "operations";
export type ScoreWeights = Record<ScoreName, number>;

export const DEFAULT_WEIGHTS: ScoreWeights = { brand: 1, land: 1, tourism: 1, operations: 1 };

export const SCORE_LABELS: Record<ScoreName, string> = {
  brand: "Brand",
  land: "Land",
  tourism: "Tourism",
  operations: "Operations",
};

export interface ScoreComponent {
  label: string;
  score?: number | null;
  detail: string;
}

export interface SubScore {
  score?: number | null;
  available: number;
  total: number;
  components: ScoreComponent[];
}

export interface WinerySummary {
  id: string;
  name: string;
  city?: string | null;
  region?: string | null;
  wine_count: number;
  median_bottle_price?: number | null;
  avg_critic_score?: number | null;
  production_cases?: number | null;
  asking_price?: number | null;
  listing_status?: string | null;
  overall_score?: number | null;
  sub_scores: Record<ScoreName, SubScore>;
}

export interface WineryListResponse {
  results: WinerySummary[];
  total: number;
  regions: string[];
}

export interface WineryWine {
  id: string;
  name: string;
  style?: string | null;
  vintage?: number | null;
  retail_price_cad?: number | null;
  litres?: number | null;
  price_date?: string | null;
  critic_score?: number | null;
  historical_price_usd?: number | null;
}

export interface WineryListing {
  id: string;
  winery_id?: string | null;
  advertised_name: string;
  location?: string | null;
  asking_price?: number | null;
  previous_asking_price?: number | null;
  currency: string;
  total_acres?: number | null;
  planted_acres?: number | null;
  capacity_cases?: number | null;
  includes_licence?: boolean | null;
  includes_brand?: boolean | null;
  includes_inventory?: boolean | null;
  includes_equipment?: boolean | null;
  status?: string | null;
  notes?: string | null;
  source_url?: string | null;
  as_of?: string | null;
}

export interface DataSource {
  label: string;
  as_of?: string | null;
  url?: string | null;
}

export interface WineryDetail extends WinerySummary {
  licence_number: string;
  licensee?: string | null;
  street?: string | null;
  postal_code?: string | null;
  licence_expiry?: string | null;
  endorsements: string[];
  service_capacity?: number | null;
  wines: WineryWine[];
  listings: WineryListing[];
  sources: DataSource[];
}

export interface WineryFilters {
  q: string;
  region: string;
  forSale: boolean;
  minAsking: string;
  maxAsking: string;
  minCases: string;
}

export interface MarketStat {
  period: string;
  geography: string;
  metric: "value" | "volume";
  value: number;
  unit: string;
}

export interface WinerySale {
  id: string;
  name: string;
  location?: string | null;
  sold_year: number;
  sale_price: number;
  last_asking_price?: number | null;
  total_acres?: number | null;
  planted_acres?: number | null;
  sale_type: string;
  evidence: string;
  notes?: string | null;
  source_url?: string | null;
  share_of_asking?: number | null;
}

export interface MarketData {
  stats: MarketStat[];
  stats_source: DataSource;
  price_buckets: { label: string; count: number }[];
  median_bottle_price?: number | null;
  priced_bottles: number;
  price_date?: string | null;
  price_source: DataSource;
  listings: WineryListing[];
  sales: WinerySale[];
  reports: DataSource[];
}
