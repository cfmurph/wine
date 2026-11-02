const { A, B, launch, ok } = require("../lib");

(async () => {
  const b = await launch();
  const g = await b.newPage();
  const errs = [];
  g.on("pageerror", (e) => errs.push(e.message));
  await g.setViewport({ width: 1280, height: 900 });
  await g.goto(B + "/market", { waitUntil: "networkidle0" });
  let t = await g.evaluate(() => document.body.innerText);
  ok("market heading", t.includes("Winery sale listings"));
  ok(
    "market has new rows",
    ["Rigour & Whimsy Winery", "Terralux Estate Winery", "The Vibrant Vine"].every((x) => t.includes(x)),
  );
  ok("Maverick sale price visible", t.includes("$2,050,000"));
  ok("Terralux sold price visible", t.includes("$3.2M"));
  const rows = await g.$$eval("table tbody tr", (r) => r.map((x) => x.innerText));
  const lr = rows.filter((x) => /2026-1[01]-01/.test(x));
  ok("one row per listing", lr.length === 17, lr.length);
  ok("Maverick appears once", lr.filter((x) => x.includes("Maverick Winery")).length === 1);
  const links = await g.$$eval("a", (a) => a.filter((x) => x.innerText === "Source").length);
  ok("source links", links >= 17, links);

  await g.goto(B + "/wineries", { waitUntil: "networkidle0" });
  const clicked = await g.evaluate(() => {
    const i = [...document.querySelectorAll("label")]
      .find((l) => l.innerText.includes("Only wineries still for sale"))
      ?.querySelector("input");
    if (!i) return false;
    i.click();
    return true;
  });
  ok("for-sale control found", clicked);
  await new Promise((r) => setTimeout(r, 800));
  await g.evaluate(() => {
    const f = document.querySelector("form");
    const btn = f && [...f.querySelectorAll("button")].find((x) => x.type === "submit");
    btn && btn.click();
  });
  await new Promise((r) => setTimeout(r, 2500));
  t = await g.evaluate(() => document.querySelector("table")?.innerText || document.body.innerText);
  ok("for sale shows active winery", t.includes("Seven Stones"));
  ok("for sale hides Maverick", !t.includes("Maverick"));
  ok("for sale hides sold S'milka", !t.includes("S'milka"));
  await g.goto(B + "/wineries?q=maverick", { waitUntil: "networkidle0" });
  await g.setViewport({ width: 390, height: 800 });
  await g.goto(B + "/market", { waitUntil: "networkidle0" });
  const over = await g.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  ok("no phone overflow", over <= 0, over);
  ok("no page errors", errs.length === 0, errs.join(";"));
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
