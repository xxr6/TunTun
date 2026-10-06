/* 真机审查：主题选择弹层（列表式）——打开/切换/勾选态 */
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
  await page.goto('http://localhost:5173/today', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.theme-btn', { timeout: 15000 });
  await sleep(800);

  /* 打开弹层 */
  await page.click('.theme-btn');
  await sleep(500);
  const popItems = await page.$$eval('.tp-item', els => els.map(e => ({
    name: e.querySelector('b')?.textContent.trim(),
    sub: e.querySelector('small')?.textContent.trim(),
    on: e.classList.contains('on'),
    swatchColors: [...e.querySelectorAll('.tp-swatch i')].map(i => getComputedStyle(i).backgroundColor),
  })));
  chk('弹层三个主题项', popItems.length === 3, popItems.length);
  chk('名称与副标题正确', popItems[0]?.name === '可可奶油' && popItems[0]?.sub === '暖色 · 默认'
    && popItems[1]?.name === '夜读' && popItems[1]?.sub === '深色 · 护眼'
    && popItems[2]?.name === '薄荷晨间' && popItems[2]?.sub === '冷色 · 清爽',
    popItems.map(p => p.name + '/' + p.sub).join(' | '));
  chk('色板四色格子有真实颜色', popItems[0]?.swatchColors.every(c => c && c !== 'rgba(0, 0, 0, 0)'), popItems[0]?.swatchColors.join(','));
  chk('当前主题勾选态', popItems.findIndex(p => p.on) === 0, JSON.stringify(popItems.map(p => p.on)));
  await page.screenshot({ path: SHOT_DIR + '/theme-1-可可奶油.png' });
  console.log('  截图: theme-1-可可奶油.png');

  /* 切到夜读 */
  await page.click('.tp-item:nth-child(3)'); // tp-title 是第一个子元素
  await sleep(700);
  const theme2 = await page.evaluate(() => document.documentElement.dataset.theme);
  chk('切到夜读生效', theme2 === 'night', theme2);
  await page.screenshot({ path: SHOT_DIR + '/theme-2-夜读.png' });
  console.log('  截图: theme-2-夜读.png');

  /* 切到薄荷 */
  await page.click('.tp-item:nth-child(4)');
  await sleep(700);
  const theme3 = await page.evaluate(() => document.documentElement.dataset.theme);
  chk('切到薄荷生效', theme3 === 'mint', theme3);
  await page.screenshot({ path: SHOT_DIR + '/theme-3-薄荷.png' });
  console.log('  截图: theme-3-薄荷.png');

  /* Esc 关闭 */
  await page.keyboard.press('Escape');
  await sleep(400);
  const popGone = !(await page.$('.theme-pop'));
  chk('Esc 关闭弹层', popGone);

  /* 恢复默认主题 */
  await page.click('.theme-btn');
  await sleep(300);
  await page.click('.tp-item:nth-child(2)');
  await sleep(400);

  console.log(ok ? '\nALL PASS' : '\nHAS FAILURES');
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error('SCRIPT ERROR:', e && e.message); process.exit(1); });
