import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export function Card({ children, className, onClick }: CardProps) {
  return (
    <div
      className={cn(
        "bg-white rounded-xl shadow-sm border border-gray-100",
        onClick && "cursor-pointer hover:shadow-md hover:border-wine-200 transition-all",
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
