// Runs every browser check, then removes the test users they created.
const { spawnSync } = require("child_process");
const { readdirSync } = require("fs");
const path = require("path");

const dir = path.join(__dirname, "tests");
const only = process.argv.slice(2);
const files = readdirSync(dir).filter((f) => f.endsWith(".js") && (!only.length || only.includes(f.replace(".js", ""))));

let passed = 0;
let failed = 0;
let crashed = 0;
for (const file of files) {
  console.log(`\n# ${file}`);
  const run = spawnSync("node", [path.join(dir, file)], { encoding: "utf8" });
  process.stdout.write(run.stdout);
  process.stderr.write(run.stderr);
  passed += (run.stdout.match(/^PASS/gm) ?? []).length;
  failed += (run.stdout.match(/^FAIL/gm) ?? []).length;
  if (run.status !== 0 && !/^FAIL/m.test(run.stdout)) crashed += 1;
}

spawnSync(
  "docker",
  ["compose", "exec", "-T", "db", "psql", "-U", "postgres", "-d", "wineapp", "-qc", `delete from "user" where email like 'e2e-%@example.com'`],
  { cwd: path.join(__dirname, "..") },
);

console.log(`\n${passed} passed, ${failed} failed, ${crashed} crashed`);
process.exit(failed || crashed ? 1 : 0);
