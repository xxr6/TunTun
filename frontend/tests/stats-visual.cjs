/* 真机 UI 审查：统计页 dashboard（数据接口 + 视觉截图） */
const puppeteer = require('puppeteer-core');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const SHOT_DIR = 'C:/Users/Administrator/WorkBuddy/2026-09-30-14-48-06/zhistack/ui-review';
let ok = true;
const chk = (l, c, e) => { console.log((c ? 'PASS  ' : 'FAIL  ') + l + (e !== undefined ? '  -> ' + e : '')); if (!c) ok = false; };
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--force-color-profile=srgb', '--mute-audio', '--window-size=1440,980'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 980, deviceScaleFactor: 1.5 });
  await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }]);
  const errs = [];
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error' && !m.text().includes('favicon')) errs.push('console: ' + m.text()); });

  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
  const tok = await page.evaluate(async () => {
    let r = await fetch('/api/v1/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account: 'chip0@t.com', password: 'password123' }),
    });
    if (r.status !== 200) r = await fetch('/api/v1/auth/register', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'chip0@t.com', username: 'chip0', password: 'password123' }),
    });
    const d = await r.json();
    return { access: d.access_token, refresh: d.refresh_token };
  });
  chk('登录成功', !!tok.access);
  await page.evaluate((t) => {
    localStorage.setItem('zhistack.access_token', t.access);
    localStorage.setItem('zhistack.refresh_token', t.refresh);
  }, tok);

  await page.goto('http://localhost:5173/stats', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.focus-grid', { timeout: 15000 });
  await sleep(1200);

  /* 数据断言 */
  const counts = await page.evaluate(() => ({
    focusCards: document.querySelectorAll('.fcard2').length,
    metricCards: document.querySelectorAll('.mcard').length,
    heatCells: document.querySelectorAll('.hm-grid .hm-cell').length,
    achCards: document.querySelectorAll('.ach-card').length,
    unlocked: document.querySelectorAll('.ach-card:not(.locked)').length,
    fcPath: !!document.querySelector('.fc-svg path'),
    dhRows: document.querySelectorAll('.dh-row').length,
    fcBars: document.querySelectorAll('.fc-bar').length,
  }));
  chk('专注三卡', counts.focusCards === 3, counts.focusCards);
  chk('指标行四小卡', counts.metricCards === 4, counts.metricCards);
  chk('热力图有格子', counts.heatCells >= 91, counts.heatCells);
  chk('成就 16 枚', counts.achCards === 16, counts.achCards);
  chk('至少 1 枚已解锁', counts.unlocked >= 1, counts.unlocked);
  chk('遗忘曲线 SVG 有路径', counts.fcPath);
  chk('卡组健康度有行', counts.dhRows >= 1, counts.dhRows);
  chk('14 天预测柱状', counts.fcBars === 14, counts.fcBars);

  await page.screenshot({ path: SHOT_DIR + '/stats-1-顶部.png' });
  console.log('  截图: stats-1-顶部.png');
  await page.evaluate(() => window.scrollBy(0, 900));
  await sleep(400);
  await page.screenshot({ path: SHOT_DIR + '/stats-2-中部.png' });
  console.log('  截图: stats-2-中部.png');
  await page.evaluate(() => window.scrollBy(0, 1200));
  await sleep(400);
  await page.screenshot({ path: SHOT_DIR + '/stats-3-成就.png' });
  console.log('  截图: stats-3-成就.png');

  chk('无 JS 运行时错误', errs.length === 0, errs.join(' | ') || '0');
  console.log(ok ? '\nALL PASS' : '\nHAS FAILURES');
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error('SCRIPT ERROR:', e && e.message); process.exit(1); });
