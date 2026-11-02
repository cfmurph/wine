export type DealStage = "researching" | "contacted" | "nda" | "financials" | "offer" | "closed" | "passed";
export type DealItemKind = "document" | "advisor";

export interface DealItem {
  id: string;
  kind: DealItemKind;
  title: string;
  assignee?: string | null;
  done: boolean;
}

export interface Deal {
  id: string;
  winery_id?: string | null;
  name: string;
  stage: DealStage;
  next_step?: string | null;
  next_step_due?: string | null;
  notes?: string | null;
  items: DealItem[];
}

export type DealUpdate = Partial<Pick<Deal, "stage" | "next_step" | "next_step_due" | "notes">>;

export type SalesChannel = "tasting_room" | "wine_club" | "online" | "restaurants" | "liquor_stores" | "private_retail";

export interface DealAssumptions {
  asking_price?: number | null;
  property_value?: number | null;
  owner_salary?: number | null;
  working_capital?: number | null;
  replanting_cost?: number | null;
  equipment_cost?: number | null;
  repair_cost?: number | null;
  inventory_funding?: number | null;
}

export interface ChannelFigures {
  channel: SalesChannel;
  cases?: number | null;
  revenue?: number | null;
  direct_cost?: number | null;
}

export interface FinancialYearInput {
  revenue?: number | null;
  tax_return_revenue?: number | null;
  cost_of_goods?: number | null;
  operating_expenses?: number | null;
  owner_addbacks?: number | null;
  cases_opening?: number | null;
  cases_produced?: number | null;
  cases_sold?: number | null;
  cases_closing?: number | null;
  grape_tonnes?: number | null;
  channels: ChannelFigures[];
}

export interface FinancialYear extends FinancialYearInput {
  fiscal_year: number;
}

export interface CheckLine {
  label: string;
  value?: number | null;
  unit: "currency" | "multiple" | "percent" | "number";
}

export interface AnalysisCheck {
  title: string;
  status: "computed" | "review" | "unknown";
  note: string;
  lines: CheckLine[];
}

export interface DealFinancials {
  deal_id: string;
  name: string;
  assumptions: DealAssumptions;
  years: FinancialYear[];
  analysis_year?: number | null;
  checks: AnalysisCheck[];
}

export interface DealScenario {
  name: "Worst" | "Expected" | "Best";
  revenue_change: number;
  cost_change: number;
  earnings?: number | null;
  price_to_earnings?: number | null;
}

export interface DealComparison {
  deal_id: string;
  name: string;
  stage: DealStage;
  analysis_year?: number | null;
  asking_price?: number | null;
  revenue?: number | null;
  cases_sold?: number | null;
  property_share?: number | null;
  total_cash_needed?: number | null;
  review_count: number;
  unknown_count: number;
  scenarios: DealScenario[];
}

export interface FinancingInput {
  purchase_price?: number | null;
  down_payment_percent: number;
  annual_rate_percent: number;
  amortization_years: number;
  available_cash?: number | null;
  min_coverage: number;
  rate_stress_points: number;
}

export interface FinancingResult {
  purchase_price?: number | null;
  down_payment?: number | null;
  loan?: number | null;
  monthly_payment?: number | null;
  annual_debt_service?: number | null;
  adjusted_earnings?: number | null;
  analysis_year?: number | null;
  coverage?: number | null;
  stressed_coverage?: number | null;
  max_loan_from_earnings?: number | null;
  other_cash_costs: number;
  missing_cash_costs: string[];
  cash_needed?: number | null;
  cash_shortfall?: number | null;
  max_price_for_cash?: number | null;
}
