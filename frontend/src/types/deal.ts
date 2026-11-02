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
