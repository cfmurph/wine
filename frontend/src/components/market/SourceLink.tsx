import { DataSource } from "@/types/winery";

export function SourceLink({ source }: { source: DataSource }) {
  return source.url ? (
    <a href={source.url} target="_blank" rel="noreferrer" className="underline">{source.label}</a>
  ) : (
    <>{source.label}</>
  );
}
