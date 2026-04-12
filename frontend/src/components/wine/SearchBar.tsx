"use client";

import { useForm } from "react-hook-form";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { SearchFilters } from "@/types/wine";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useState } from "react";

interface SearchBarProps {
  onSearch: (filters: SearchFilters) => void;
  loading?: boolean;
}

export function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [showFilters, setShowFilters] = useState(false);
  const { register, handleSubmit, reset, watch } = useForm<SearchFilters>({
    defaultValues: { q: "" },
  });

  const q = watch("q");

  return (
    <div className="space-y-3">
      <form
        onSubmit={handleSubmit(onSearch)}
        className="flex gap-2"
      >
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
          <input
            {...register("q")}
            type="text"
            placeholder="Wine name, producer, or grape variety…"
            className="w-full pl-9 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-wine-500 focus:border-wine-500"
          />
          {q && (
            <button
              type="button"
              onClick={() => reset()}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <Button type="submit" disabled={loading} size="md">
          {loading ? "Searching…" : "Search"}
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="md"
          onClick={() => setShowFilters(!showFilters)}
        >
          <SlidersHorizontal className="h-4 w-4" />
          <span className="hidden sm:block">Filters</span>
        </Button>
      </form>

      {showFilters && (
        <form
          onSubmit={handleSubmit(onSearch)}
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 p-4 bg-white border border-gray-200 rounded-xl"
        >
          <Input
            {...register("region")}
            placeholder="Region"
            label="Region"
          />
          <Input
            {...register("country")}
            placeholder="Country"
            label="Country"
          />
          <Input
            {...register("vintage")}
            type="number"
            placeholder="e.g. 2019"
            label="Vintage"
          />
          <Input
            {...register("style")}
            placeholder="Red, White, Rosé…"
            label="Style"
          />
          <Input
            {...register("grape")}
            placeholder="Nebbiolo, Pinot…"
            label="Grape"
          />
          <div className="col-span-full flex justify-end gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => { reset(); setShowFilters(false); }}
            >
              Clear
            </Button>
            <Button type="submit" size="sm" disabled={loading}>
              Apply Filters
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
