import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-wine-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed",
        variant === "primary" && "bg-wine-700 text-white hover:bg-wine-800",
        variant === "secondary" && "bg-wine-100 text-wine-800 hover:bg-wine-200",
        variant === "ghost" && "text-gray-600 hover:bg-gray-100",
        variant === "danger" && "bg-red-600 text-white hover:bg-red-700",
        size === "sm" && "px-3 py-1.5 text-sm gap-1.5",
        size === "md" && "px-4 py-2 text-sm gap-2",
        size === "lg" && "px-6 py-3 text-base gap-2",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
