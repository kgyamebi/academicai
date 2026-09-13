import { readFileSync, readdirSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { JSDOM } from "jsdom";

const require = createRequire(import.meta.url);
const axeSource = readFileSync(require.resolve("axe-core"), "utf8");
const root = dirname(fileURLToPath(import.meta.url));
const fixtures = readdirSync(join(root, "fixtures")).filter((name) => name.endsWith(".html"));
if (!fixtures.length) {
  console.error("No accessibility fixtures found.");
  process.exit(1);
}

let failed = false;
for (const name of fixtures) {
  const html = readFileSync(join(root, "fixtures", name), "utf8");
  const dom = new JSDOM(html, {
    pretendToBeVisual: true,
    runScripts: "dangerously",
    url: `https://academiccheck.local/${name}`,
  });
  dom.window.HTMLCanvasElement.prototype.getContext = () => null;
  const script = dom.window.document.createElement("script");
  script.textContent = axeSource;
  dom.window.document.head.appendChild(script);
  if (!dom.window.axe) {
    console.error(`${name}: axe-core did not initialize in jsdom.`);
    failed = true;
    dom.window.close();
    continue;
  }
  const results = await dom.window.axe.run(dom.window.document, {
    runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
  });
  dom.window.close();
  const serious = results.violations.filter((v) => ["critical", "serious"].includes(v.impact));
  const score = Math.max(0, 100 - results.violations.length * 8 - serious.length * 7);
  console.log(`${name}: axe violations=${results.violations.length} serious=${serious.length} score=${score}`);
  if (results.violations.length) {
    failed = true;
    for (const violation of results.violations) {
      console.error(`  ${violation.id} [${violation.impact}] ${violation.help}`);
    }
  }
  if (score < 98) {
    failed = true;
    console.error(`  ${name} accessibility score ${score} is below the 98 CI gate.`);
  }
}

if (failed) {
  process.exit(1);
}
console.log(`axe-core scanned ${fixtures.length} fixtures with zero violations.`);
