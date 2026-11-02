const { A, B, launch, ok } = require("../lib");

(async () => {
  const b = await launch();
  const g = await b.newPage();
  const errs = [];
  g.on("pageerror", (x) => errs.push(x.message));
  await g.setViewport({ width: 1280, height: 900 });
  await g.goto(B + "/market", { waitUntil: "networkidle0" });
  const t = await g.evaluate(() => document.body.innerText);
  ok("heading", t.includes("Reported winery sales"));
  ok("warning", t.includes("Not a price guide"));
  ok("maverick 44%", t.includes("44%"));
  ok("terralux 71%", t.includes("71%"));
  ok("5.2M 100%", t.includes("100%"));
  ok("evidence labels", t.includes("Search results only") && t.includes("Receiver's report read"));
  const h = await g.$$eval("h2", (x) => x.map((e) => e.innerText));
  ok("section order", h.indexOf("Reported winery sales") > h.indexOf("Winery sale listings"), h.join("|"));
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
