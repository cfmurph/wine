import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "wine" | "outline";
}

export function Badge({ children, className, variant = "default" }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variant === "default" && "bg-gray-100 text-gray-700",
        variant === "wine" && "bg-wine-100 text-wine-800",
        variant === "outline" && "border border-gray-300 text-gray-600",
        className
      )}
    >
      {children}
    </span>
  );
}
