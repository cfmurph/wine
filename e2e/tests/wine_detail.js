const { A, B, launch, ok } = require("../lib");

(async () => {
  const d = await (await fetch(A + "/wines/search?q=pinot&per_page=3")).json();
  const id = d.results[0].id || d.results[0].wine_id;
  const b = await launch();
  const g = await b.newPage();
  const errs = [];
  g.on("pageerror", (x) => errs.push(x.message));
  await g.setViewport({ width: 1280, height: 900 });
  await g.goto(B + "/search?q=pinot", { waitUntil: "networkidle0" });
  const i = await g.$("input");
  await i.type("pinot noir");
  await g.keyboard.press("Enter");
  await new Promise((r) => setTimeout(r, 2500));
  const cards = await g.evaluate(
    () =>
      [...document.querySelectorAll("a,[role=link],div")].filter((e) => /pinot/i.test(e.innerText || ""))
        .length,
  );
  ok("results rendered", cards > 0, cards);
  const r = await g.goto(B + "/wine/" + id, { waitUntil: "networkidle0" });
  const t = await g.evaluate(() => document.body.innerText);
  ok(
    "wine detail page",
    r.status() === 200 && t.length > 50 && !/couldn.t|not found|error/i.test(t),
    t.slice(0, 90).replace(/\n/g, " "),
  );
  ok("no errors", errs.length === 0, errs.join(";"));
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
