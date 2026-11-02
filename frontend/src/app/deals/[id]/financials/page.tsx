"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { DealFiguresForm } from "@/components/deal/DealFiguresForm";
import { FinancialYearForm } from "@/components/deal/FinancialYearForm";
import { FinancingModel } from "@/components/deal/FinancingModel";
import { ScreeningChecks } from "@/components/deal/ScreeningChecks";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { useFetch } from "@/hooks/useFetch";
import { getDealFinancials } from "@/lib/api";
import { DealFinancials } from "@/types/deal";

export default function DealFinancialsPage() {
  const { id } = useParams<{ id: string }>();
  const { data, failed, setData } = useFetch(id, () => getDealFinancials(id));
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  const onSaved = (result: DealFinancials, message: string) => {
    setData(() => result);
    setSaved(message);
    setError(null);
  };
  const onInvalid = (message: string) => {
    setSaved(null);
    setError(message);
  };
  const onFailed = () => onInvalid("That wasn't saved. Check for negative or invalid figures and try again.");

  if (failed) return <ErrorMessage>Couldn&apos;t load this deal. Check that you&apos;re logged in.</ErrorMessage>;
  if (!data) return <p className="text-gray-400 py-16 text-center">Loading…</p>;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/deals" className="text-sm text-wine-700 hover:underline inline-flex items-center gap-1 mb-3">
          <ArrowLeft className="h-4 w-4" />
          All deals
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">{data.name}: financials</h1>
      </div>

      <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
        Check what your NDA allows before entering a seller&apos;s figures. These checks flag questions for your accountant; they aren&apos;t a valuation.
      </p>

      {error && <ErrorMessage>{error}</ErrorMessage>}
      {saved && <p className="text-sm text-green-800 bg-green-50 border border-green-200 rounded-lg px-4 py-3">{saved}</p>}

      <ScreeningChecks data={data} />
      <FinancingModel dealId={id} refreshKey={data} />
      <DealFiguresForm data={data} onSaved={onSaved} onFailed={onFailed} />
      <FinancialYearForm data={data} onSaved={onSaved} onFailed={onFailed} onInvalid={onInvalid} />
    </div>
  );
}
