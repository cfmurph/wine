import { Card } from "@/components/ui/Card";
import { WineryLandCheck } from "@/types/winery";

const SOURCES: [string, string][] = [
  ["BC Address Geocoder", "https://www2.gov.bc.ca/gov/content/data/geographic-data-services/location-services/geocoder"],
  ["Agricultural Land Reserve", "https://catalogue.data.gov.bc.ca/dataset/alc-agricultural-land-reserve-polygons"],
  ["Groundwater wells", "https://catalogue.data.gov.bc.ca/dataset/groundwater-wells"],
  ["Historical fire perimeters", "https://catalogue.data.gov.bc.ca/dataset/bc-wildfire-fire-perimeters-historical"],
];

const count = (value?: number | null, detail?: number | null, label?: string) =>
  value == null ? "Unknown" : detail == null ? String(value) : `${value} (${detail} ${label})`;

function facts(check: WineryLandCheck): [string, string][] {
  const fire =
    check.fires_since_2000 == null
      ? "Unknown"
      : check.fires_since_2000 === 0
        ? "None recorded"
        : `${check.fires_since_2000}; latest ${check.latest_fire_year ?? "unknown"}, largest ${check.largest_fire_hectares?.toLocaleString() ?? "unknown"} ha`;
  return [
    ["Address point in the ALR", check.in_alr == null ? "Unknown" : check.in_alr ? "Yes" : "No"],
    ["Registered wells within 500 m", count(check.wells_nearby, check.irrigation_wells_nearby, "irrigation")],
    ["Recorded fires within 5 km since 2000", fire],
  ];
}

export function LandRiskCard({ check }: { check?: WineryLandCheck | null }) {
  return (
    <Card className="p-5 space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-gray-800">Land and risk screen</h2>
        <p className="text-sm text-gray-500">
          Public map data around the licensed address, not the legal parcel. Nearby wells may belong to neighbours, and nearby fires don&apos;t show damage here. Confirm title, ALR status and water rights with your lawyer. Water licences, frost and smoke history aren&apos;t included; look up licences through the{" "}
          <a href="https://www2.gov.bc.ca/gov/content/environment/air-land-water/water/water-licensing-rights/water-licences-approvals/water-rights-databases" target="_blank" rel="noreferrer" className="underline">Province&apos;s water rights databases</a>.
        </p>
      </div>
      {!check ? (
        <p className="text-sm text-gray-500">Not checked yet. These checks cover wineries with a sale listing or tracked deal.</p>
      ) : !check.address_reliable ? (
        <p className="text-sm text-gray-500">
          Unknown: the licensed address couldn&apos;t be matched precisely{check.matched_address ? ` (closest match: ${check.matched_address})` : ""}, so no map checks were run.
        </p>
      ) : (
        <dl className="grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
          {facts(check).map(([label, value]) => (
            <div key={label} className="flex justify-between gap-3 border-b border-gray-100 py-1">
              <dt className="text-gray-500">{label}</dt>
              <dd className={value === "Unknown" ? "text-gray-400" : "font-medium text-gray-800 text-right"}>{value}</dd>
            </div>
          ))}
        </dl>
      )}
      <p className="text-xs text-gray-500">
        {check && <>Checked {check.checked_on}. </>}
        Sources:{" "}
        {SOURCES.map(([label, url], index) => (
          <span key={label}>
            {index > 0 && " · "}
            <a href={url} target="_blank" rel="noreferrer" className="underline">{label}</a>
          </span>
        ))}
        . Contains information licensed under the Open Government Licence – British Columbia.
      </p>
    </Card>
  );
}
