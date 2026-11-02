import { Users } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

type Evidence = "States winery work" | "Related work" | "Regulator";

interface Advisor {
  name: string;
  url: string;
  location: string;
  contact: string;
  evidence: Evidence;
  focus: string;
  caution: string;
}

interface AdvisorGroup {
  role: string;
  purpose: string;
  verify?: { label: string; url: string };
  advisors: Advisor[];
}

const CHECKED_ON = "November 1, 2026";

const GROUPS: AdvisorGroup[] = [
  {
    role: "Lawyers",
    purpose: "Purchase agreement, what actually transfers, liens, title and the NDA.",
    verify: { label: "Check status in the Law Society of BC directory", url: "https://www.lawsociety.bc.ca/lsbc/apps/lkup/directory/mbr-search.cfm" },
    advisors: [
      {
        name: "Quantum Law",
        url: "https://www.quantumlaw.ca/liquor-licensing",
        location: "Okanagan Valley",
        contact: "855-855-1101 · info@quantumlaw.ca",
        evidence: "States winery work",
        focus: "Buying and selling vineyards and wineries, liquor industry due diligence, winery licence applications, and vineyard lease and grape supply contracts.",
        caution: "The page names no lawyers and no street address.",
      },
      {
        name: "BC Real Estate Law",
        url: "https://bcrealestatelaw.com/agriculture/winery-vineyard-and-orchard-transactions/",
        location: "Serves Osoyoos to Lake Country",
        contact: "250-980-3360, ext. 367",
        evidence: "States winery work",
        focus: "Land acquisition, liquor licensing, development applications, distribution agreements and environmental issues for vintners.",
        caution: "The page names no lawyer or office city.",
      },
      {
        name: "CM Lawyers",
        url: "https://cmlawyers.ca/from-farm-gate-to-first-pour-business-law-issues-for-wineries-cideries-breweries-and-rural-producers/",
        location: "Vernon, Enderby, Salmon Arm, Abbotsford",
        contact: "(250) 308-0338 · corporate@cmlawyers.ca",
        evidence: "States winery work",
        focus: "Business purchases and sales, financing, leasing, contracts and licensing considerations for wineries and farm-gate producers.",
        caution: "This is general business law. The page lists no winery-only services.",
      },
      {
        name: "Patrick Bobyn, Pushor Mitchell LLP",
        url: "https://pushormitchell.com/2025/01/24/transferring-a-liquor-license-in-a-commercial-transaction/",
        location: "Kelowna",
        contact: "250-869-1286 · bobyn@pushormitchell.com",
        evidence: "Related work",
        focus: "Wrote on liquor licence transfers in commercial deals, including lien searches, purchase terms and holdbacks.",
        caution: "The article doesn't mention wineries, so ask about winery deals.",
      },
    ],
  },
  {
    role: "Accountants",
    purpose: "Quality of earnings, cost per bottle, inventory value, excise and deal structure.",
    verify: { label: "Check firms in the CPABC directory", url: "https://www.bccpa.ca/protecting-the-public/cpabc-member-firm-directories/" },
    advisors: [
      {
        name: "MNP, Agriculture Services",
        url: "https://www.mnp.ca/-/media/files/mnp/pdf/niche/agriculture/pas/winery-and-vineyard-fact-sheet.pdf",
        location: "BC-wide national firm",
        contact: "AJ Gill, BC Leader: 250-763-8919 · aj.gill@mnp.ca",
        evidence: "States winery work",
        focus: "Cost of production per acre or bottle, sales channels, industry benchmarks, projections and valuation factors.",
        caution: "The fact sheet looks dated to about 2021, so confirm the contact. It describes advising owners, not buyers.",
      },
      {
        name: "EverStone CPA",
        url: "https://www.everstonecpa.com/winery-accountant-kelowna",
        location: "Virtual; no Kelowna office",
        contact: "(604) 832-1743 · info@everstonecpa.com",
        evidence: "States winery work",
        focus: "Excise returns, separating vineyard and winery books, inventory by vintage, and GST and PST across sales channels.",
        caution: "The page names no accountant or winery clients. It describes ongoing accounting, not buyer due diligence.",
      },
    ],
  },
  {
    role: "Appraisers",
    purpose: "Independent value for the land, buildings, equipment and business.",
    verify: { label: "Find or check appraisers with the Appraisal Institute of Canada", url: "https://www.aicanada.ca/need-an-appraiser/find-an-appraiser/" },
    advisors: [
      {
        name: "Quality Appraisals Inc.",
        url: "https://qualityappraisals.ca/central-south-okanagan/",
        location: "Vernon; serves Kelowna and Penticton",
        contact: "250-832-3709",
        evidence: "States winery work",
        focus: "Bare vineyard land, producing vineyards and full winery going-concern appraisals, weighing water licences, vine age, microclimate and tourism income.",
        caution: "The page names no appraisers. Ask who would sign the report and to see sample winery work.",
      },
    ],
  },
  {
    role: "Vineyard inspection",
    purpose: "Vine health, soil, yields, irrigation and replanting costs.",
    verify: { label: "Find an agrologist through the BC Institute of Agrologists", url: "https://www.bcia.com/about-us/bcia-agrologists/contract-agrologist" },
    advisors: [
      {
        name: "Meritage Viticulture Services",
        url: "https://meritagevit.com/services/",
        location: "Summerland",
        contact: "(250) 718-8440",
        evidence: "States winery work",
        focus: "Consulting and vineyard assessment, land assessment, soil and tissue analysis, and budgeting and cost evaluation.",
        caution: "The page doesn't describe pre-purchase inspections, so ask for a written report.",
      },
      {
        name: "Earlco Vineyards",
        url: "https://earlco.com/consulting/",
        location: "Penticton",
        contact: "info@earlco.com",
        evidence: "Related work",
        focus: "Vineyard service company offering site and varietal consultation, and nutrient and spray programs.",
        caution: "The page doesn't mention assessments for buyers. It also sells vineyard services, so ask about any seller ties.",
      },
      {
        name: "Pascal Madevon Signature",
        url: "https://orchardandvine.net/locations/pascal-madevon-signature-ltd/",
        location: "Penticton (directory listing)",
        contact: "pascalmadevon.ca",
        evidence: "Related work",
        focus: "Advice on vineyard management, wine production and marketing for wineries of all sizes.",
        caution: "This comes from an industry directory, which doesn't mention vineyard assessments. Confirm the location and service.",
      },
    ],
  },
  {
    role: "Liquor licensing",
    purpose: "Whether the licence can pass to you, and how.",
    advisors: [
      {
        name: "Liquor and Cannabis Regulation Branch",
        url: "https://www2.gov.bc.ca/gov/content/employment-business/business/liquor-regulation-licensing/liquor-licence-permits/amend-liquor-licence/transfer-a-liquor-licence",
        location: "Victoria; BC regulator",
        contact: "1-866-209-2111 · LCRBLiquor@gov.bc.ca",
        evidence: "Regulator",
        focus: "Issues and transfers licences. A transfer costs $330, the current licensee starts it, and an expired licence isn't eligible.",
        caution: "The page doesn't confirm the steps for wineries. Ask how a transfer differs from buying the company's shares.",
      },
      {
        name: "ÆGIR Consulting",
        url: "https://www.aegirconsulting.ca/",
        location: "Vernon",
        contact: "778-885-6582",
        evidence: "States winery work",
        focus: "Liquor licence applications, changes and transfers, including wineries, plus acquisition help and site assessments.",
        caution: "This is a consultancy, not a law firm, and also serves bars, restaurants and cannabis businesses.",
      },
      {
        name: "Brown Beverage Consulting",
        url: "https://www.brownbeverageconsulting.com",
        location: "Penticton",
        contact: "250-486-1640",
        evidence: "States winery work",
        focus: "Licensing, regulation and compliance for liquor manufacturers, and help starting or expanding a winery.",
        caution: "The winery and phone details come from an Okanagan Wine Festivals listing. Buying a winery isn't mentioned.",
      },
    ],
  },
];

export default function AdvisorsPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <Users className="h-8 w-8 text-wine-700" />
          BC Winery Advisors
        </h1>
        <p className="text-gray-500">Starting points for reviewing a winery before you make an offer.</p>
      </div>

      <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
        These aren&apos;t recommendations. Each entry comes from the provider&apos;s own or a directory&apos;s description, checked on {CHECKED_ON}, not from client reviews or licence checks. Confirm credentials, ask for similar winery work, and ask about any ties to the seller or listing agent.
      </p>

      {GROUPS.map((group) => (
        <Card key={group.role} className="p-5 space-y-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-800">{group.role}</h2>
            <p className="text-sm text-gray-500">{group.purpose}</p>
          </div>
          <div className="divide-y divide-gray-100">
            {group.advisors.map((advisor) => (
              <div key={advisor.name} className="py-3 space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <a href={advisor.url} target="_blank" rel="noreferrer" className="font-medium text-wine-800 hover:underline">{advisor.name}</a>
                  <Badge variant={advisor.evidence === "Related work" ? "outline" : "wine"}>{advisor.evidence}</Badge>
                </div>
                <p className="text-sm text-gray-700">{advisor.focus}</p>
                <p className="text-sm text-gray-500">{advisor.caution}</p>
                <p className="text-xs text-gray-500 break-words">{advisor.location} · {advisor.contact}</p>
              </div>
            ))}
          </div>
          {group.verify && (
            <a href={group.verify.url} target="_blank" rel="noreferrer" className="inline-block text-sm underline text-gray-600">{group.verify.label}</a>
          )}
        </Card>
      ))}
    </div>
  );
}
