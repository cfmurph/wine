"use client";

import { useEffect, useState } from "react";
import { BookMarked, Star, Pencil, Trash2, Wine } from "lucide-react";
import { UserWine } from "@/types/wine";
import { getCellar, removeFromCellar, updateCellarEntry } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import Link from "next/link";

const STATUS_LABELS: Record<string, string> = {
  favorite: "Favorite",
  tried: "Tried",
  want_to_try: "Want to Try",
  cellar: "In Cellar",
};

const STATUS_COLORS: Record<string, string> = {
  favorite: "bg-wine-100 text-wine-800",
  tried: "bg-green-100 text-green-800",
  want_to_try: "bg-blue-100 text-blue-800",
  cellar: "bg-purple-100 text-purple-800",
};

export default function CellarPage() {
  const [cellar, setCellar] = useState<UserWine[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editNotes, setEditNotes] = useState("");
  const [editRating, setEditRating] = useState<number | undefined>();

  useEffect(() => {
    getCellar()
      .then(setCellar)
      .catch(() => setError("Please log in to view your cellar."))
      .finally(() => setLoading(false));
  }, []);

  const handleRemove = async (wine_id: string) => {
    try {
      await removeFromCellar(wine_id);
      setCellar((prev) => prev.filter((w) => w.wine_id !== wine_id));
    } catch {
      alert("Failed to remove wine.");
    }
  };

  const handleSaveEdit = async (wine_id: string) => {
    try {
      const updated = await updateCellarEntry(wine_id, {
        notes: editNotes,
        user_rating: editRating,
      });
      setCellar((prev) => prev.map((w) => (w.wine_id === wine_id ? updated : w)));
      setEditingId(null);
    } catch {
      alert("Failed to update.");
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-xl h-24 border border-gray-100" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20 space-y-4">
        <p className="text-gray-500">{error}</p>
        <Link href="/profile" className="text-wine-700 underline text-sm">
          Log in
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <BookMarked className="h-8 w-8 text-wine-700" />
          My Cellar
        </h1>
        <p className="text-gray-500">
          {cellar.length} wine{cellar.length !== 1 ? "s" : ""} saved
        </p>
      </div>

      {cellar.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <Wine className="h-12 w-12 mx-auto mb-4 text-gray-200" />
          <p className="text-lg font-medium">Your cellar is empty</p>
          <p className="text-sm mt-1">Search for wines and save them here.</p>
          <Link href="/search" className="mt-4 inline-block text-wine-700 underline text-sm">
            Start searching
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {cellar.map((entry) => (
            <Card key={entry.id} className="p-4">
              <div className="flex items-start gap-4">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Link
                      href={`/wine/${entry.wine_id}`}
                      className="font-semibold text-gray-900 hover:text-wine-700 transition-colors"
                    >
                      {entry.wine_id}
                    </Link>
                    <Badge className={STATUS_COLORS[entry.status]}>
                      {STATUS_LABELS[entry.status]}
                    </Badge>
                    {entry.user_rating != null && (
                      <span className="flex items-center gap-1 text-sm text-wine-700 font-medium">
                        <Star className="h-3.5 w-3.5 fill-current" />
                        {entry.user_rating}/10
                      </span>
                    )}
                  </div>

                  {editingId === entry.wine_id ? (
                    <div className="space-y-2">
                      <input
                        type="number"
                        min={0}
                        max={10}
                        step={0.5}
                        value={editRating ?? ""}
                        onChange={(e) => setEditRating(Number(e.target.value))}
                        placeholder="Rating (0–10)"
                        className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm w-36 focus:outline-none focus:ring-1 focus:ring-wine-500"
                      />
                      <textarea
                        value={editNotes}
                        onChange={(e) => setEditNotes(e.target.value)}
                        placeholder="Tasting notes…"
                        rows={2}
                        className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-wine-500"
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => handleSaveEdit(entry.wine_id)}>
                          Save
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    entry.notes && (
                      <p className="text-sm text-gray-500 italic">&quot;{entry.notes}&quot;</p>
                    )
                  )}
                </div>

                <div className="flex gap-1 flex-shrink-0">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setEditingId(entry.wine_id);
                      setEditNotes(entry.notes ?? "");
                      setEditRating(entry.user_rating);
                    }}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleRemove(entry.wine_id)}
                    className="text-red-400 hover:text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
