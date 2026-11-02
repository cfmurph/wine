import axios from "axios";
import {
  WineSearchResponse,
  WineDetail,
  PairingSearchResponse,
  UserWine,
  CompareItem,
  SearchFilters,
} from "@/types/wine";
import {
  MarketData,
  ScoreWeights,
  WineryDetail,
  WineryFilters,
  WineryListResponse,
} from "@/types/winery";
import { Deal, DealAssumptions, DealComparison, DealFinancials, DealItem, DealItemKind, DealUpdate, FinancialYearInput, FinancingInput, FinancingResult } from "@/types/deal";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Attach auth token from localStorage when available
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ---- Wine Search ----

export async function searchWines(
  filters: SearchFilters,
  page = 1,
  perPage = 20
): Promise<WineSearchResponse> {
  const params: Record<string, string | number> = { page, per_page: perPage };
  if (filters.q) params.q = filters.q;
  if (filters.region) params.region = filters.region;
  if (filters.country) params.country = filters.country;
  if (filters.vintage) params.vintage = filters.vintage;
  if (filters.style) params.style = filters.style;
  if (filters.grape) params.grape = filters.grape;
  const { data } = await api.get<WineSearchResponse>("/wines/search", { params });
  return data;
}

// ---- Wine Detail ----

export async function getWineDetail(id: string): Promise<WineDetail> {
  const { data } = await api.get<WineDetail>(`/wines/${id}`);
  return data;
}

export async function getWineScores(id: string) {
  const { data } = await api.get(`/wines/${id}/scores`);
  return data;
}

export async function getWinePrices(id: string) {
  const { data } = await api.get(`/wines/${id}/prices`);
  return data;
}

// ---- Compare ----

export async function compareWines(
  wineIds: string[]
): Promise<{ wines: CompareItem[] }> {
  const { data } = await api.post("/wines/compare", { wine_ids: wineIds });
  return data;
}

// ---- Pairings ----

export async function getPairings(food: string): Promise<PairingSearchResponse> {
  const { data } = await api.get<PairingSearchResponse>("/pairings", {
    params: { food },
  });
  return data;
}

// ---- Cellar ----

export async function getCellar(): Promise<UserWine[]> {
  const { data } = await api.get<UserWine[]>("/users/me/cellar");
  return data;
}

export async function addToCellar(payload: {
  wine_id: string;
  status: UserWine["status"];
  user_rating?: number;
  notes?: string;
}): Promise<UserWine> {
  const { data } = await api.post<UserWine>("/users/me/cellar", payload);
  return data;
}

export async function updateCellarEntry(
  wine_id: string,
  payload: Partial<Pick<UserWine, "status" | "user_rating" | "notes">>
): Promise<UserWine> {
  const { data } = await api.patch<UserWine>(`/users/me/cellar/${wine_id}`, payload);
  return data;
}

export async function removeFromCellar(wine_id: string): Promise<void> {
  await api.delete(`/users/me/cellar/${wine_id}`);
}

// ---- Wineries ----

export async function getWineries(
  filters: WineryFilters,
  weights: ScoreWeights
): Promise<WineryListResponse> {
  const params: Record<string, string | number | boolean> = { ...weights };
  if (filters.q) params.q = filters.q;
  if (filters.region) params.region = filters.region;
  if (filters.forSale) params.for_sale = true;
  if (filters.minAsking) params.min_asking = filters.minAsking;
  if (filters.maxAsking) params.max_asking = filters.maxAsking;
  if (filters.minCases) params.min_cases = filters.minCases;
  const { data } = await api.get<WineryListResponse>("/wineries", { params });
  return data;
}

export async function getWinery(id: string, weights: ScoreWeights): Promise<WineryDetail> {
  const { data } = await api.get<WineryDetail>(`/wineries/${id}`, { params: weights });
  return data;
}

export async function compareWineries(
  wineryIds: string[],
  weights: ScoreWeights
): Promise<WineryDetail[]> {
  const { data } = await api.post<{ wineries: WineryDetail[] }>("/wineries/compare", {
    winery_ids: wineryIds,
    ...weights,
  });
  return data.wineries;
}

// ---- Market ----

export async function getMarket(): Promise<MarketData> {
  const { data } = await api.get<MarketData>("/market");
  return data;
}

// ---- Auth ----

// ---- Deals ----

export async function getDeals(): Promise<Deal[]> {
  const { data } = await api.get<Deal[]>("/users/me/deals");
  return data;
}

export async function createDeal(name: string, wineryId?: string): Promise<Deal> {
  const { data } = await api.post<Deal>("/users/me/deals", { name, winery_id: wineryId });
  return data;
}

export async function updateDeal(id: string, payload: DealUpdate): Promise<Deal> {
  const { data } = await api.patch<Deal>(`/users/me/deals/${id}`, payload);
  return data;
}

export async function deleteDeal(id: string): Promise<void> {
  await api.delete(`/users/me/deals/${id}`);
}

export async function addDealItem(dealId: string, kind: DealItemKind, title: string): Promise<DealItem> {
  const { data } = await api.post<DealItem>(`/users/me/deals/${dealId}/items`, { kind, title });
  return data;
}

export async function updateDealItem(
  dealId: string,
  itemId: string,
  payload: { done?: boolean; assignee?: string | null }
): Promise<DealItem> {
  const { data } = await api.patch<DealItem>(`/users/me/deals/${dealId}/items/${itemId}`, payload);
  return data;
}

export async function deleteDealItem(dealId: string, itemId: string): Promise<void> {
  await api.delete(`/users/me/deals/${dealId}/items/${itemId}`);
}

export async function compareDeals(scenarios: {
  worst_revenue: number;
  worst_costs: number;
  best_revenue: number;
  best_costs: number;
}): Promise<DealComparison[]> {
  const { data } = await api.get<DealComparison[]>("/users/me/deals/compare", { params: scenarios });
  return data;
}

export async function getDealFinancials(dealId: string): Promise<DealFinancials> {
  const { data } = await api.get<DealFinancials>(`/users/me/deals/${dealId}/financials`);
  return data;
}

export async function saveDealAssumptions(dealId: string, payload: DealAssumptions): Promise<DealFinancials> {
  const { data } = await api.put<DealFinancials>(`/users/me/deals/${dealId}/financials/assumptions`, payload);
  return data;
}

export async function saveFinancialYear(dealId: string, year: number, payload: FinancialYearInput): Promise<DealFinancials> {
  const { data } = await api.put<DealFinancials>(`/users/me/deals/${dealId}/financials/years/${year}`, payload);
  return data;
}

export async function deleteFinancialYear(dealId: string, year: number): Promise<DealFinancials> {
  const { data } = await api.delete<DealFinancials>(`/users/me/deals/${dealId}/financials/years/${year}`);
  return data;
}

export async function modelFinancing(dealId: string, payload: FinancingInput): Promise<FinancingResult> {
  const { data } = await api.post<FinancingResult>(`/users/me/deals/${dealId}/financing`, payload);
  return data;
}

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/login", { email, password });
  if (data.access_token && typeof window !== "undefined") {
    localStorage.setItem("access_token", data.access_token);
  }
  return data;
}

export async function register(email: string, username: string, password: string) {
  const { data } = await api.post("/auth/register", { email, username, password });
  return data;
}

export function logout() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
  }
}
