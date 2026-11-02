const { A, B, launch, ok } = require("../lib");

(async () => {
  const b = await launch();
  const g = await b.newPage();
  const errs = [];
  g.on("pageerror", (x) => errs.push(x.message));
  await g.setViewport({ width: 1280, height: 900 });
  await g.goto(B + "/market", { waitUntil: "networkidle0" });
  const t = await g.evaluate(() => document.body.innerText);
  const s = t.slice(t.indexOf("Listings to re-check"), t.indexOf("Reported winery sales"));
  ok("section", t.includes("Listings to re-check"));
  ok(
    "old rows listed",
    ["Lakeside Cellars", "Averill Creek Winery", "Millstone Estate Winery"].every((x) => s.includes(x)),
  );
  ok("closed rows absent", !s.includes("Terralux") && !s.includes("Maverick"));
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
