const { A, B, launch, ok } = require("../lib");

const w = (m) => new Promise((r) => setTimeout(r, m));
(async () => {
  const u = Math.random().toString(36).slice(2, 10),
    e = `e2e-${u}@example.com`,
    pw = "E2e-test-pass1!";
  await fetch(A + "/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: e, username: "e2e" + u, password: pw }),
  });
  const t = (
    await (
      await fetch(A + "/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: e, password: pw }),
      })
    ).json()
  ).access_token;
  const b = await launch();
  const g = await b.newPage();
  const errs = [];
  g.on("pageerror", (x) => errs.push(x.message));
  g.on("dialog", (d) => d.accept());
  await g.setViewport({ width: 1280, height: 900 });
  await g.goto(B + "/deals", { waitUntil: "networkidle0" });
  ok("logged out prompt", (await g.evaluate(() => document.body.innerText)).includes("to track deals"));
  await g.evaluate((k) => localStorage.setItem("access_token", k), t);
  const list = await (await fetch(A + "/wineries?q=seven%20stones")).json();
  const id = (list.results || list.wineries || list.items)[0].id;
  await g.goto(B + "/wineries/" + id, { waitUntil: "networkidle0" });
  await g.evaluate(() =>
    [...document.querySelectorAll("button")].find((x) => x.innerText === "Track this deal").click(),
  );
  await w(800);
  ok("track from winery", (await g.evaluate(() => document.body.innerText)).includes("Added to your deals"));
  await g.goto(B + "/deals", { waitUntil: "networkidle0" });
  let txt = await g.evaluate(() => document.body.innerText);
  ok("deal listed", txt.includes("Seven Stones Winery") && txt.includes("0 of 12"));
  await g.select("select", "nda");
  await w(500);
  await g.focus('input[id^="next-"]');
  await g.keyboard.type("Sign the NDA");
  await g.keyboard.press("Tab");
  await w(600);
  await g.click("input[type=checkbox]");
  await w(600);
  await g.type("#deal-name", "Unnamed Kaleden winery");
  await g.keyboard.press("Enter");
  await w(800);
  await g.reload({ waitUntil: "networkidle0" });
  ok("stage persisted", (await g.$eval("select", (s) => s.value)) === "nda");
  ok("next step persisted", (await g.$eval('input[id^="next-"]', (s) => s.value)) === "Sign the NDA");
  txt = await g.evaluate(() => document.body.innerText);
  ok("checkbox persisted", txt.includes("1 of 12"));
  ok("free text deal", txt.includes("Unnamed Kaleden winery"));

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
