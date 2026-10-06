/**
 * 指示器位移专测：点击切换后，等过渡结束再量（避免动画中段误判）
 */
const puppeteer = require('puppeteer-core');
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--disable-gpu', '--force-prefers-reduced-motion=no-preference'],
  });
  const p = await b.newPage();
  await p.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }]);
  await p.setViewport({ width: 1280, height: 820 });
  const errors = [];
  p.on('pageerror', e => errors.push('pageerror: ' + e.message));

  await p.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('input[autocomplete="username"]', { timeout: 15000 });
  await p.type('input[autocomplete="username"]', 'test@example.com');
  await p.type('input[type="password"]', 'password123');
  await p.click('button.submit');
  await p.waitForSelector('.sidebar', { timeout: 15000 });
  await sleep(900);

  await p.click('button[aria-label="切换配色主题"]');
  await p.waitForSelector('.theme-pop', { timeout: 8000 });
  await sleep(800);

  const snap = () => p.evaluate(() => {
    const nav = document.querySelector('.theme-pop .gn-gooey-nav, .theme-pop .gooey-nav');
    const pill = nav.querySelector('.gn-pill');
    const items = [...nav.querySelectorAll('.gn-item')];
    const pr = pill.getBoundingClientRect();
    return {
      theme: document.documentElement.dataset.theme,
      pill: { x: Math.round(pr.x), w: Math.round(pr.width) },
      items: items.map(li => { const r = li.getBoundingClientRect(); return { x: Math.round(r.x), w: Math.round(r.width) }; }),
      active: items.findIndex(li => li.classList.contains('active')),
      pillColor: getComputedStyle(pill).backgroundColor,
      pillBorder: getComputedStyle(pill).borderTopColor,
    };
  });

  const results = [];
  for (const [idx, name] of [[0, 'cocoa'], [1, 'night'], [2, 'mint'], [0, 'cocoa']]) {
    await p.evaluate(i => {
      document.querySelectorAll('.theme-pop .gn-item')[i].querySelector('a').click();
    }, idx);
    await sleep(1100); // 等过渡完全结束
    const s = await snap();
    const it = s.items[idx];
    results.push({
      step: name,
      theme: s.theme,
      activeIdx: s.active,
      pillX: s.pill.x, itemX: it.x,
      aligned: Math.abs(s.pill.x - it.x) < 8 && Math.abs(s.pill.w - it.w) < 14,
      pillColor: s.pillColor,
      expectedFill: name,
    });
  }

  // 主题色是否跟着变（浅色主题橙、夜读浅橙）
  const fills = results.map(r => r.pillColor);
  console.log(JSON.stringify({ results, fills, uniqueFills: [...new Set(fills)], errors }, null, 2));

  // 各主题截图
  for (const [i, n] of [[0, 'cocoa'], [1, 'night'], [2, 'mint']]) {
    await p.evaluate(idx => {
      document.querySelectorAll('.theme-pop .gn-item')[idx].querySelector('a').click();
    }, i);
    await sleep(900);
    await p.screenshot({ path: `gooey2-${n}.png` });
  }

  await b.close();
  process.exit(0);
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
