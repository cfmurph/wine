import { AlertCircle } from "lucide-react";

export function ErrorMessage({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-4 py-3">
      <AlertCircle className="h-4 w-4 flex-shrink-0" />
      {children}
    </div>
  );
}
