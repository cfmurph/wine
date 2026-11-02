import { Input } from "@/components/ui/Input";

export type Draft = Record<string, string>;

export const toDraft = (source: object): Draft =>
  Object.fromEntries(Object.entries(source).map(([k, v]) => [k, v == null ? "" : String(v)]));

export const toNumber = (value?: string) => (value ? Number(value) : null);

interface NumberFieldProps {
  draft: Draft;
  setDraft: (draft: Draft) => void;
  name: string;
  label: string;
}

export function NumberField({ draft, setDraft, name, label }: NumberFieldProps) {
  return (
    <Input
      id={`field-${name}`}
      label={label}
      type="number"
      min={0}
      step="any"
      value={draft[name] ?? ""}
      onChange={(e) => setDraft({ ...draft, [name]: e.target.value })}
    />
  );
}
