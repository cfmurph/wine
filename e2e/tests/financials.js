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
  const [, deal] = await api("POST", "/users/me/deals", t, { name: "Fictional Test Winery" });
  const f = `/users/me/deals/${deal.id}/financials`;
  ok("no login 401", (await api("GET", f))[0] === 401);
  ok("other user 404 get", (await api("GET", f, t2))[0] === 404);
  ok("other user 404 put", (await api("PUT", f + "/years/2025", t2, { revenue: 1 }))[0] === 404);
  ok(
    "other user 404 assumptions",
    (await api("PUT", f + "/assumptions", t2, { asking_price: 1 }))[0] === 404,
  );
  ok("other user 404 delete", (await api("DELETE", f + "/years/2025", t2))[0] === 404);
  ok("negative 422", (await api("PUT", f + "/years/2025", t, { revenue: -1 }))[0] === 422);
  ok("bad year 422", (await api("PUT", f + "/years/1800", t, {}))[0] === 422);
  let [, d0] = await api("GET", f, t);
  ok(
    "empty is unknown",
    d0.checks.every((c) => c.status === "unknown"),
  );
  const b = await launch();
  const g = await b.newPage();
  const errs = [];
  g.on("pageerror", (x) => errs.push(x.message));
  g.on("dialog", (d) => d.accept());
  await g.setViewport({ width: 1280, height: 900 });
  await g.goto(B + "/deals", { waitUntil: "domcontentloaded" });
  await g.evaluate((k) => localStorage.setItem("access_token", k), t);
  await g.goto(B + "/deals", { waitUntil: "networkidle0" });
  ok("link from deal", (await g.$(`a[href="/deals/${deal.id}/financials"]`)) !== null);
  await g.goto(B + `/deals/${deal.id}/financials`, { waitUntil: "networkidle0" });
  const set = async (id, v) => {
    await g.focus("#field-" + id);
    await g.keyboard.type(String(v));
  };
  await set("asking_price", 3000000);
  await set("property_value", 2250000);
  await set("owner_salary", 100000);
  await set("working_capital", 200000);
  await set("replanting_cost", 0);
  await set("equipment_cost", 50000);
  await set("repair_cost", 25000);
  await set("inventory_funding", 0);
  await g.evaluate(() =>
    [...document.querySelectorAll("button")].find((x) => x.innerText === "Save deal figures").click(),
  );
  await w(700);
  await g.focus("#fiscal-year");
  await g.keyboard.type("2025");
  await set("revenue", 1000000);
  await set("tax_return_revenue", 800000);
  await set("cost_of_goods", 400000);
  await set("operating_expenses", 300000);
  await set("owner_addbacks", 50000);
  await set("cases_opening", 1000);
  await set("cases_produced", 5000);
  await set("cases_sold", 4000);
  await set("cases_closing", 2000);
  await set("grape_tonnes", 80);
  await set("tasting_room\\.revenue", 700000);
  await set("tasting_room\\.direct_cost", 200000);
  await set("wine_club\\.revenue", 300000);
  await g.evaluate(() =>
    [...document.querySelectorAll("button")].find((x) => x.innerText === "Save year").click(),
  );
  await w(800);
  await g.reload({ waitUntil: "networkidle0" });
  const txt = await g.evaluate(() => document.body.innerText);
  ok("price/revenue 3.00x", txt.includes("3.00x"));
  ok("adjusted earnings", txt.includes("CA$250,000"));
  ok("price/earnings 12.00x", txt.includes("12.00x"));
  ok("property share 75%", txt.includes("75.0%"));
  ok("implied business", txt.includes("CA$750,000"));
  ok("tax gap", txt.includes("CA$200,000"));
  ok("cash total", txt.includes("CA$3,275,000"));
  ok("needs review shown", txt.includes("Needs review"));
  ok("cases per tonne", txt.includes("62.5"));
  ok("year persisted", (await g.$eval("#field-revenue", (x) => x.value)) === "1000000");
  ok("channel persisted", (await g.$eval("#field-tasting_room\\.revenue", (x) => x.value)) === "700000");

  await g.setViewport({ width: 390, height: 800 });
  await g.reload({ waitUntil: "networkidle0" });
  const o = await g.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  ok("no phone overflow", o <= 0, o);
  await g.evaluate(() =>
    [...document.querySelectorAll("button")].find((x) => x.innerText === "Delete year").click(),
  );
  await w(800);
  ok("year deleted", (await api("GET", f, t))[1].years.length === 0);
  ok("no page errors", errs.length === 0, errs.join(";"));
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
