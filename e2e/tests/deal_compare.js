const { A, B, launch, ok } = require("../lib");

const w = (m) => new Promise((r) => setTimeout(r, m));
const api = async (m, u, t, body) => {
  const r = await fetch(A + u, {
    method: m,
    headers: { "Content-Type": "application/json", ...(t ? { Authorization: "Bearer " + t } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const x = await r.text();
  return [r.status, x ? JSON.parse(x) : null];
};
const mk = async () => {
  const u = Math.random().toString(36).slice(2, 10),
    e = `e2e-${u}@example.com`,
    pw = "E2e-test-pass1!";
  await api("POST", "/auth/register", null, { email: e, username: "e2e" + u, password: pw });
  return (await api("POST", "/auth/login", null, { email: e, password: pw }))[1].access_token;
};
(async () => {
  const t = await mk(),
    t2 = await mk();
  const [, a] = await api("POST", "/users/me/deals", t, { name: "Fictional A" });
  const [, c] = await api("POST", "/users/me/deals", t, { name: "Fictional B" });
  await api("PUT", `/users/me/deals/${a.id}/financials/assumptions`, t, {
    asking_price: 3000000,
    property_value: 1500000,
    owner_salary: 100000,
  });
  await api("PUT", `/users/me/deals/${a.id}/financials/years/2025`, t, {
    revenue: 1000000,
    cost_of_goods: 400000,
    operating_expenses: 300000,
    cases_sold: 5000,
  });
  ok("no login 401", (await api("GET", "/users/me/deals/compare"))[0] === 401);
  ok("other user sees none", (await api("GET", "/users/me/deals/compare", t2))[1].length === 0);
  ok("out of range 422", (await api("GET", "/users/me/deals/compare?worst_costs=500", t))[0] === 422);
  const b = await launch();
  const g = await b.newPage();
  const errs = [];
  g.on("pageerror", (x) => errs.push(x.message));
  await g.setViewport({ width: 1280, height: 900 });
  await g.goto(B + "/deals", { waitUntil: "domcontentloaded" });
  await g.evaluate((k) => localStorage.setItem("access_token", k), t);
  await g.goto(B + "/deals", { waitUntil: "networkidle0" });
  ok("compare link", (await g.$('a[href="/deals/compare"]')) !== null);
  await g.goto(B + "/deals/compare", { waitUntil: "networkidle0" });
  let txt = await g.evaluate(() => document.body.innerText);
  ok("both deals", txt.includes("Fictional A") && txt.includes("Fictional B"));
  ok("expected earnings", txt.includes("CA$200,000 (15.0x)"));
  ok("worst case default", txt.includes("CA$-20,000") || txt.includes("-CA$20,000"), "-150k rev, +70k costs");
  ok("best case", txt.includes("CA$335,000"));
  ok("missing is unknown", txt.includes("Unknown") && txt.includes("No figures yet"));
  await g.click("#worst_revenue", { clickCount: 3 });
  await g.keyboard.type("0");
  await g.click("#worst_costs", { clickCount: 3 });
  await g.keyboard.type("0");
  await w(900);
  txt = await g.evaluate(() => document.body.innerText);
  const row = await g.$$eval("tr", (r) => r.map((x) => x.innerText).find((x) => x.startsWith("Worst")));
  ok("scenario input recalculates", row.includes("CA$200,000"), row);

  await g.setViewport({ width: 390, height: 800 });
  await g.reload({ waitUntil: "networkidle0" });
  const o = await g.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  ok("no phone overflow", o <= 0, o);
  ok("no page errors", errs.length === 0, errs.join(";"));
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
