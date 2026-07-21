import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";

const root = path.resolve(new URL("../..", import.meta.url).pathname);
const artifacts = path.join(root, "artifacts");
const videoDir = path.join(artifacts, "video");
const statePath = path.join(videoDir, "recording-state.json");
const noVoiceWebm = path.join(videoDir, "rook-demo-no-voice.webm");
const thumbnailPath = path.join(artifacts, "rook-demo-thumbnail.png");

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function exists(file) {
  try {
    await fs.access(file);
    return true;
  } catch {
    return false;
  }
}

async function readJson(file) {
  return JSON.parse(await fs.readFile(file, "utf8"));
}

function shell(command, logName) {
  const log = path.join(videoDir, logName);
  const child = spawn("bash", ["-lc", command], {
    cwd: root,
    env: { ...process.env, STREAMLIT_BROWSER_GATHER_USAGE_STATS: "false" },
    detached: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  const chunks = [];
  child.stdout.on("data", (chunk) => chunks.push(chunk));
  child.stderr.on("data", (chunk) => chunks.push(chunk));
  child.on("exit", async () => {
    await fs.writeFile(log, Buffer.concat(chunks)).catch(() => {});
  });
  return child;
}

async function stopProcess(child) {
  if (!child || child.killed) return;
  try {
    process.kill(-child.pid, "SIGINT");
  } catch {
    child.kill("SIGINT");
  }
  await sleep(1200);
  if (child.exitCode === null) {
    try {
      process.kill(-child.pid, "SIGKILL");
    } catch {
      child.kill("SIGKILL");
    }
  }
}

async function waitFor(url, label, timeoutMs = 45000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // keep waiting
    }
    await sleep(500);
  }
  throw new Error(`${label} did not become ready`);
}

async function overlay(page, html, ms) {
  await page.evaluate((content) => {
    document.body.insertAdjacentHTML(
      "beforeend",
      `<div id="rook-video-overlay" style="
        position: fixed;
        inset: 0;
        z-index: 999999;
        display: grid;
        place-items: center;
        background: linear-gradient(135deg, #fbf7ef 0%, #f2eadc 100%);
        color: #16211b;
        font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      ">${content}</div>`,
    );
  }, html);
  await sleep(ms);
  await page.evaluate(() => document.getElementById("rook-video-overlay")?.remove());
}

async function caption(page, text, ms = 4500) {
  await page.evaluate((copy) => {
    document.getElementById("rook-video-caption")?.remove();
    document.body.insertAdjacentHTML(
      "beforeend",
      `<div id="rook-video-caption" style="
        position: fixed;
        left: 50%;
        bottom: 34px;
        transform: translateX(-50%);
        z-index: 999998;
        max-width: 1120px;
        padding: 16px 22px;
        border-radius: 999px;
        background: rgba(18, 63, 42, 0.94);
        color: white;
        font: 700 26px Inter, sans-serif;
        box-shadow: 0 16px 48px rgba(18,63,42,.24);
        text-align: center;
      "></div>`,
    );
    document.getElementById("rook-video-caption").textContent = copy;
  }, text);
  await sleep(ms);
}

async function clearCaption(page) {
  await page.evaluate(() => document.getElementById("rook-video-caption")?.remove());
}

async function scrollTo(page, y, ms = 1000) {
  await page.evaluate((target) => {
    const scroller = document.querySelector('section[data-testid="stMain"]') || document.scrollingElement;
    scroller.scrollTo({ top: target, behavior: "smooth" });
  }, y);
  await sleep(ms);
}

async function finalCard(page, deployment, proof) {
  const execution = proof.execution || {};
  const explorer = execution.explorer_url || "";
  await overlay(
    page,
    `<div style="width: 1180px; padding: 74px; border: 1px solid #e8dfd0; border-radius: 34px; background: #fffdf8; box-shadow: 0 30px 90px rgba(23,34,28,.12); overflow:hidden;">
      <div style="font-size: 30px; font-weight: 900; color:#c86f1d; letter-spacing:.08em; text-transform:uppercase;">Rook</div>
      <div style="font-size: 76px; line-height:1; font-weight: 900; max-width:900px; margin-top:22px;">Secure milestone payments for construction</div>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:22px; margin-top:54px; font-size:24px;">
        <div><strong>GitHub</strong><br><span style="color:#647067; overflow-wrap:anywhere;">github.com/MathieuDWeill/rook-keeperhub-hackathon</span></div>
        <div><strong>Transaction explorer</strong><br><span style="color:#647067; font-size:21px; overflow-wrap:anywhere;">${explorer}</span></div>
        <div><strong>Escrow</strong><br><span style="color:#647067; font-size:21px; overflow-wrap:anywhere;">${deployment.escrow}</span></div>
        <div><strong>Executed through KeeperHub</strong><br><span style="color:#647067;">${execution.execution_id}</span></div>
      </div>
    </div>`,
    12000,
  );
}

async function main() {
  await fs.mkdir(videoDir, { recursive: true });
  await fs.rm(noVoiceWebm, { force: true });

  const deployment = await readJson(path.join(artifacts, "deployment.json"));
  const proof = await readJson(path.join(artifacts, "live-proof.json"));
  if (!proof.execution?.tx_hash || !proof.execution?.execution_id || !proof.execution?.explorer_url) {
    throw new Error("Missing live KeeperHub proof. Run the live flow before recording.");
  }

  const api = shell("set -a; source .env; set +a; . .venv/bin/activate && uvicorn apps.api.app.main:app --port 8000", "api.log");
  const demo = shell("set -a; source .env; set +a; . .venv/bin/activate && streamlit run apps/demo/app.py --server.port 8501 --server.headless true", "streamlit.log");

  let browser;
  try {
    await waitFor("http://127.0.0.1:8000/health", "API");
    await waitFor("http://127.0.0.1:8501", "Streamlit");

    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      recordVideo: { dir: videoDir, size: { width: 1920, height: 1080 } },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    await page.goto("http://127.0.0.1:8501", { waitUntil: "load" });
    await page.waitForTimeout(1800);

    await overlay(
      page,
      `<div style="text-align:center;">
        <div style="font-size:120px; font-weight:900;">Rook</div>
        <div style="font-size:44px; margin-top:20px; color:#647067;">Secure milestone payments for construction</div>
        <div style="font-size:28px; margin-top:32px; color:#123f2a; font-weight:900;">Executed through KeeperHub</div>
      </div>`,
      7500,
    );

    await caption(page, "Construction payments need evidence, retention, and an execution trail.", 7500);
    await clearCaption(page);

    await scrollTo(page, 0, 800);
    await caption(page, "Kitchen renovation — Phase 1: 3,000 USDC, with 5% retention protected.", 11500);
    await scrollTo(page, 430, 1000);
    await caption(page, "Rook verifies acceptance, invoice, compliance, no dispute, and completion photos.", 12000);
    await scrollTo(page, 690, 900);
    await caption(page, "The policy approves 2,850 USDC for release and keeps 150 USDC protected.", 10500);
    await scrollTo(page, 900, 900);
    await caption(page, "This is the real KeeperHub proof: execution ID, hash, gas, timestamp, and explorer link.", 16500);
    await scrollTo(page, 1070, 900);
    await caption(page, "The audit status is completed, and the transaction is linked on Sepolia.", 10500);
    await clearCaption(page);

    await scrollTo(page, 650, 700);
    const blocked = page.getByRole("button", { name: "Test blocked payment", exact: true });
    await blocked.click();
    await page.waitForTimeout(1500);
    await caption(page, "Payment safely blocked — client acceptance missing.", 11500);
    await clearCaption(page);

    await finalCard(page, deployment, proof);
    await page.screenshot({ path: thumbnailPath, type: "png" });

    await context.close();
    await browser.close();

    const files = (await fs.readdir(videoDir)).filter((file) => file.endsWith(".webm"));
    const newest = files
      .map((file) => ({ file, stat: null }))
      .sort((a, b) => a.file.localeCompare(b.file))
      .at(-1);
    if (!newest) throw new Error("Playwright did not produce a video");
    await fs.rename(path.join(videoDir, newest.file), noVoiceWebm);

    await fs.writeFile(
      statePath,
      JSON.stringify(
        {
          webm: noVoiceWebm,
          thumbnail: thumbnailPath,
          transaction: proof.execution.tx_hash,
          executionId: proof.execution.execution_id,
          explorerUrl: proof.execution.explorer_url,
        },
        null,
        2,
      ),
    );
  } finally {
    if (browser) await browser.close().catch(() => {});
    await stopProcess(api);
    await stopProcess(demo);
  }

  console.log(noVoiceWebm);
}

await main();
