import { chromium } from "playwright";

const url = process.env.ROOK_DEMO_URL || "http://localhost:8501";
const out = process.env.ROOK_DEMO_SCREENSHOT || "artifacts/rook-demo-ui-final.png";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
await page.goto(url, { waitUntil: "load" });
await page.waitForTimeout(1500);

const text = await page.locator("body").innerText();
const hasRawJson = text.includes('"escrow_contract"') || text.includes('"functionArgs"');
if (hasRawJson) {
  throw new Error("Raw JSON is visible in the default demo view");
}

await page.screenshot({ path: out, fullPage: true });
await browser.close();

console.log(`Saved ${out}`);
