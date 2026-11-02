const { A, B, launch, ok } = require("../lib");

(async () => {
  const b = await launch();
  const g = await b.newPage();
  const errs = [],
    bad = [];
  g.on("pageerror", (x) => errs.push(x.message));
  g.on("console", (m) => {
    if (m.type() === "error" && !/401|Failed to load resource/.test(m.text()))
      errs.push(m.text().slice(0, 160));
  });
  g.on("response", (r) => {
    if (r.status() === 404) bad.push(r.url());
  });
  await g.setViewport({ width: 1280, height: 900 });
  for (const u of [
    "/",
    "/search",
    "/compare",
    "/cellar",
    "/pairings",
    "/profile",
    "/wineries",
    "/wineries/compare",
    "/market",
    "/advisors",
    "/deals",
  ]) {
    const r = await g.goto(B + u, { waitUntil: "networkidle0" });
    ok("loads " + u, r.status() === 200, r.status());
  }
  ok("icon present", await g.$eval('link[rel~="icon"]', (x) => !!x.href).catch(() => false));
  await g.goto(B + "/search", { waitUntil: "networkidle0" });
  const i = await g.$("input");
  await i.type("pinot noir");
  await g.keyboard.press("Enter");
  await new Promise((r) => setTimeout(r, 2500));
  let t = await g.evaluate(() => document.body.innerText);
  ok("search returns wines", /pinot/i.test(t) && !/no (wines|results)/i.test(t));
  const wl = [];
  if (wl[0]) {
    const r = await g.goto(B + wl[0], { waitUntil: "networkidle0" });
    ok("wine detail", r.status() === 200);
  }
  const u = Math.random().toString(36).slice(2, 10);
  await g.goto(B + "/profile", { waitUntil: "networkidle0" });
  ok("no 404s", bad.filter((x) => !x.includes("favicon")).length === 0, bad.slice(0, 3).join(" "));
  ok("favicon no 404", !bad.some((x) => /favicon|icon/.test(x)), bad.filter((x) => /icon/.test(x)).join());
  ok("no browser errors", errs.length === 0, errs.slice(0, 3).join(" | "));
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
