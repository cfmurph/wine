import Link from "next/link";
import { Search, GitCompare, BookMarked, Utensils } from "lucide-react";

const features = [
  {
    icon: Search,
    title: "Search any wine",
    description: "Find wines by name, region, producer, grape, or vintage from our comprehensive database.",
    href: "/search",
    cta: "Start searching",
  },
  {
    icon: GitCompare,
    title: "Compare side by side",
    description: "Select up to 4 wines and compare scores, prices, regions, grapes, and value scores.",
    href: "/compare",
    cta: "Compare wines",
  },
  {
    icon: Utensils,
    title: "Food pairing",
    description: "Enter a dish and get wine recommendations with confidence-ranked pairings.",
    href: "/search?pairing=true",
    cta: "Find pairings",
  },
  {
    icon: BookMarked,
    title: "Your cellar",
    description: "Save favorites, add tasting notes, rate wines, and track your collection.",
    href: "/cellar",
    cta: "Open cellar",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-16">
      {/* Hero */}
      <section className="text-center py-16 space-y-6">
        <h1 className="text-5xl font-bold tracking-tight text-gray-900">
          Discover, compare &{" "}
          <span className="text-wine-700">collect wines</span>
        </h1>
        <p className="max-w-2xl mx-auto text-lg text-gray-500">
          Powered by Wine-Searcher, Global Wine Score, and Spoonacular — all
          normalized into one clean, fast API.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/search"
            className="inline-flex items-center gap-2 bg-wine-700 text-white px-6 py-3 rounded-xl font-semibold hover:bg-wine-800 transition-colors"
          >
            <Search className="h-5 w-5" />
            Search wines
          </Link>
          <Link
            href="/compare"
            className="inline-flex items-center gap-2 bg-white border border-gray-300 text-gray-700 px-6 py-3 rounded-xl font-semibold hover:bg-gray-50 transition-colors"
          >
            <GitCompare className="h-5 w-5" />
            Compare
          </Link>
        </div>
      </section>

      {/* Feature cards */}
      <section className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map(({ icon: Icon, title, description, href, cta }) => (
          <div
            key={title}
            className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm space-y-4 hover:shadow-md hover:border-wine-200 transition-all"
          >
            <div className="w-10 h-10 rounded-xl bg-wine-50 flex items-center justify-center">
              <Icon className="h-5 w-5 text-wine-700" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{title}</h3>
              <p className="text-sm text-gray-500 mt-1">{description}</p>
            </div>
            <Link href={href} className="text-sm font-medium text-wine-700 hover:underline">
              {cta} →
            </Link>
          </div>
        ))}
      </section>

      {/* Data sources */}
      <section className="text-center space-y-4 py-8 border-t border-gray-100">
        <p className="text-sm text-gray-400 uppercase tracking-widest font-medium">
          Data powered by
        </p>
        <div className="flex justify-center gap-8 text-gray-500 font-medium">
          <span>Wine-Searcher</span>
          <span>·</span>
          <span>Global Wine Score</span>
          <span>·</span>
          <span>Spoonacular</span>
        </div>
      </section>
    </div>
  );
}
