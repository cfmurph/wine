// Shared helpers for the browser checks. See e2e/README.md.
const puppeteer = require("puppeteer-core");

const B = process.env.E2E_WEB_URL ?? "http://localhost:3000";
const A = process.env.E2E_API_URL ?? "http://localhost:8000/api/v1";

const DEFAULT_CHROME = {
  darwin: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  linux: "/usr/bin/google-chrome",
};

let failures = 0;
process.on("exit", () => {
  if (failures) process.exitCode = 1;
});

function ok(name, passed, detail = "") {
  console.log(passed ? "PASS" : "FAIL", name, detail);
  if (!passed) failures += 1;
}

function launch() {
  return puppeteer.launch({
    headless: "new",
    executablePath: process.env.CHROME_PATH ?? DEFAULT_CHROME[process.platform],
    args: process.env.CI ? ["--no-sandbox"] : [],
  });
}

module.exports = { A, B, launch, ok };
