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
  const f = `/users/me/deals/${a.id}/financing`;
  const body = { down_payment_percent: 30, annual_rate_percent: 6, amortization_years: 25 };
  ok("no login 401", (await api("POST", f, null, body))[0] === 401);
  ok("other user 404", (await api("POST", f, t2, body))[0] === 404);
  ok("bad input 422", (await api("POST", f, t, { ...body, amortization_years: 0 }))[0] === 422);
  await api("PUT", `/users/me/deals/${a.id}/financials/assumptions`, t, {
    asking_price: 3000000,
    owner_salary: 100000,
    working_capital: 200000,
    replanting_cost: 0,
    equipment_cost: 0,
    repair_cost: 0,
    inventory_funding: 0,
  });
  await api("PUT", `/users/me/deals/${a.id}/financials/years/2025`, t, {
    revenue: 1000000,
    cost_of_goods: 400000,
    operating_expenses: 300000,
  });
  const b = await launch();
  const g = await b.newPage();
  const errs = [];
  g.on("pageerror", (x) => errs.push(x.message));
  await g.setViewport({ width: 1280, height: 900 });
  await g.goto(B + "/deals", { waitUntil: "domcontentloaded" });
  await g.evaluate((k) => localStorage.setItem("access_token", k), t);
  await g.goto(B + `/deals/${a.id}/financials`, { waitUntil: "networkidle0" });
  await g.type("#financing-down_payment_percent", "30");
  await g.type("#financing-annual_rate_percent", "6");
  await g.type("#financing-amortization_years", "25");
  await g.type("#financing-available_cash", "1000000");
  await g.evaluate(() =>
    [...document.querySelectorAll("button")].find((x) => x.innerText === "Calculate").click(),
  );
  await w(900);
  const txt = await g.evaluate(() => document.body.innerText);
  ok("loan", txt.includes("CA$2,100,000"));
  ok("monthly", txt.includes("CA$13,436"));
  ok(
    "debt coverage shown",
    /Debt coverage\s*\n?\s*1\.24x/.test(txt),
    (txt.match(/Debt coverage[^\n]*\n?[^\n]*/) || [""])[0],
  );
  ok("cash needed", txt.includes("CA$1,100,000"));
  ok("shortfall", txt.includes("CA$100,000"));

  await g.setViewport({ width: 390, height: 800 });
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
