import axios from "axios";
import {
  WineSearchResponse,
  WineDetail,
  PairingSearchResponse,
  UserWine,
  CompareItem,
  SearchFilters,
} from "@/types/wine";

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

// ---- Auth ----

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
