"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Wine, Search, GitCompare, BookMarked, User, Users, Grape, BarChart3, ClipboardList } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/search", label: "Search", icon: Search },
  { href: "/compare", label: "Compare", icon: GitCompare },
  { href: "/cellar", label: "My Cellar", icon: BookMarked },
  { href: "/wineries", label: "Wineries", icon: Grape },
  { href: "/market", label: "Market", icon: BarChart3 },
  { href: "/advisors", label: "Advisors", icon: Users },
  { href: "/deals", label: "Deals", icon: ClipboardList },
  { href: "/profile", label: "Profile", icon: User },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="bg-wine-900 text-white shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl tracking-tight">
            <Wine className="h-6 w-6 text-wine-200" />
            <span className="hidden sm:inline">WineApp</span>
          </Link>

          <div className="flex items-center gap-1">
            {links.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-1.5 px-2 sm:px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  pathname === href
                    ? "bg-wine-700 text-white"
                    : "text-wine-200 hover:bg-wine-800 hover:text-white"
                )}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:block">{label}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}
