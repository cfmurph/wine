import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatPrice(price?: number, currency = "USD") {
  if (price == null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(price);
}

export function formatScore(score?: number) {
  if (score == null) return "—";
  return Math.round(score).toString();
}

export function getStyleColor(style?: string) {
  switch (style?.toLowerCase()) {
    case "red":
      return "bg-wine-700 text-white";
    case "white":
      return "bg-amber-100 text-amber-900";
    case "rosé":
    case "rose":
      return "bg-pink-200 text-pink-900";
    case "sparkling":
      return "bg-yellow-100 text-yellow-900";
    case "dessert":
      return "bg-purple-100 text-purple-900";
    default:
      return "bg-gray-100 text-gray-700";
  }
}
