const { A, B, launch, ok } = require("../lib");

(async () => {
  const b = await launch();
  const g = await b.newPage();
  const errs = [];
  g.on("pageerror", (e) => errs.push(e.message));
  await g.setViewport({ width: 1280, height: 900 });
  await g.goto(B + "/wineries", { waitUntil: "networkidle0" });
  await g.click('a[href="/advisors"]');
  await g.waitForSelector("h1");
  await new Promise((r) => setTimeout(r, 1500));
  ok("nav reaches page", g.url().endsWith("/advisors"), g.url());
  const t = await g.evaluate(() => document.body.innerText);
  for (const h of ["Lawyers", "Accountants", "Appraisers", "Vineyard inspection", "Liquor licensing"])
    ok("group " + h, t.includes(h));
  ok("not-a-recommendation notice", t.includes("These aren't recommendations"));
  const n = await g.$$eval(
    'main a[target="_blank"], div a[target="_blank"]',
    (a) => new Set(a.map((x) => x.href)).size,
  );
  ok("external links", n >= 17, n);

  await g.setViewport({ width: 390, height: 800 });
  for (const u of ["/advisors", "/market", "/wineries"]) {
    await g.goto(B + u, { waitUntil: "networkidle0" });
    const o = await g.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    ok("no phone overflow " + u, o <= 0, o);
  }
  ok("no page errors", errs.length === 0, errs.join(";"));
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
