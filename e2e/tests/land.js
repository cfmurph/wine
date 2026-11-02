const { A, B, launch, ok } = require("../lib");

const find = async (q) => {
  const d = await (await fetch(A + "/wineries?q=" + encodeURIComponent(q))).json();
  return (d.results || d.wineries || d.items)[0].id;
};
(async () => {
  const b = await launch();
  const g = await b.newPage();
  const errs = [];
  g.on("pageerror", (x) => errs.push(x.message));
  await g.setViewport({ width: 1280, height: 900 });
  const open = async (q) => {
    await g.goto(B + "/wineries/" + (await find(q)), { waitUntil: "networkidle0" });
    return g.evaluate(() => document.body.innerText);
  };
  let t = await open("Seven Stones");
  ok("card shows", t.includes("Land and risk screen"));
  ok("alr", /in the ALR\s*\n?\s*Yes/.test(t));
  ok("wells", t.includes("9 (4 irrigation)"));
  ok("no water licences", !t.includes("water licences within"));
  ok("water query link", (await g.$('a[href*="water-rights-databases"]')) !== null);
  ok("fires", t.includes("9; latest 2019"));
  ok("caveat", t.includes("not the legal parcel"));
  ok("licence credit", t.includes("Open Government Licence"));
  t = await open("Lakeside");
  ok("unreliable address unknown", t.includes("couldn't be matched precisely"));
  t = await open("Millstone");
  ok("no fires wording", t.includes("None recorded"));
  t = await open("Mission Hill");
  ok("unchecked wording", t.includes("Not checked yet"));
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
