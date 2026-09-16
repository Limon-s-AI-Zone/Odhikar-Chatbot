import { chromium } from 'playwright-core';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const VIDEO_DIR = path.resolve(__dirname, '../assets/videos');

if (!fs.existsSync(VIDEO_DIR)) {
  fs.mkdirSync(VIDEO_DIR, { recursive: true });
}

async function recordAppDemo() {
  console.log('🚀 Launching Google Chrome to record Odhikar App demo...');
  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1280,800']
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    recordVideo: {
      dir: VIDEO_DIR,
      size: { width: 1280, height: 800 }
    }
  });

  const page = await context.newPage();
  console.log('🌐 Navigating to Odhikar frontend: http://127.0.0.1:5173...');
  await page.goto('http://127.0.0.1:5173', { waitUntil: 'networkidle' });

  // 1. Initial Welcome Screen
  console.log('📸 Scene 1: Welcome Screen');
  await page.waitForTimeout(2500);

  // 2. Click "শুরু করুন" to begin Intake
  console.log('📸 Scene 2: Click "শুরু করুন" (Start Intake)');
  const startBtn = page.locator('text=শুরু করুন').first();
  if (await startBtn.isVisible()) {
    await startBtn.click();
  }
  await page.waitForTimeout(2000);

  // 3. Showcase Quick Options & Narrative Input
  console.log('📸 Scene 3: Narrative & Legal Category Selection');
  const dowerChip = page.locator('text=দেনমোহর ও ভরণপোষণ আদায়ের পদক্ষেপ').first();
  if (await dowerChip.isVisible()) {
    await dowerChip.click();
    console.log('  Selected Dower & Maintenance intake flow');
  }
  await page.waitForTimeout(4000);

  // 4. Scroll through the questions / answers
  console.log('📸 Scene 4: Interacting with Dialogue & Assistant');
  await page.mouse.wheel(0, 300);
  await page.waitForTimeout(2500);

  // 5. Switch to Paralegal Dashboard
  console.log('📸 Scene 5: Switching to Paralegal Dashboard');
  const paralegalTab = page.locator('text=প্যারালিগ্যাল ড্যাশবোর্ড').first();
  if (await paralegalTab.isVisible()) {
    await paralegalTab.click();
  }
  await page.waitForTimeout(3500);

  // 6. Inspect Case Queue & Urgent Case Flags
  console.log('📸 Scene 6: Browsing Paralegal Cases Queue');
  await page.mouse.wheel(0, 200);
  await page.waitForTimeout(2500);

  // Click back to Client Intake
  console.log('📸 Scene 7: Switching back to Client Intake');
  const clientTab = page.locator('text=ক্লায়েন্ট সেবা').first();
  if (await clientTab.isVisible()) {
    await clientTab.click();
  }
  await page.waitForTimeout(2000);

  // Close context to finalize video writing
  console.log('💾 Saving recorded video...');
  await page.close();
  await context.close();
  await browser.close();

  // Find saved video in VIDEO_DIR
  const files = fs.readdirSync(VIDEO_DIR).filter(f => f.endsWith('.webm'));
  if (files.length > 0) {
    // Sort by creation time to get latest
    files.sort((a, b) => fs.statSync(path.join(VIDEO_DIR, b)).mtimeMs - fs.statSync(path.join(VIDEO_DIR, a)).mtimeMs);
    const latestVideo = path.join(VIDEO_DIR, files[0]);
    const targetWebm = path.resolve(__dirname, '../assets/demo_video.webm');
    const targetMp4 = path.resolve(__dirname, '../assets/demo_video.mp4');

    fs.copyFileSync(latestVideo, targetWebm);
    fs.copyFileSync(latestVideo, targetMp4);
    console.log(`✅ Demo video successfully created at:\n  - ${targetWebm}\n  - ${targetMp4}`);
  } else {
    console.warn('⚠️ No video file found in output directory.');
  }
}

recordAppDemo().catch(err => {
  console.error('❌ Error recording demo:', err);
  process.exit(1);
});

