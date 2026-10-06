/* 专注页改版真机验证：墙钟计时、跨页存活、放弃留痕、完成庆祝、无障碍语义。 */
const puppeteer = require('puppeteer-core');
const path = require('path');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const OUT = path.resolve(__dirname, '.tmp-visual');
const URL_ = 'http://localhost:5173';
let ok = true;
const chk = (l, c, e) => { console.log((c ? 'PASS  ' : 'FAIL  ') + l + (e !== undefined ? '  -> ' + e : '')); if (!c) ok = false; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--mute-audio', '--force-color-profile=srgb'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 980 });
  const errs = [];
  page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  const dialogs = [];
  page.on('dialog', async (d) => { dialogs.push(d.message()); await d.accept(); });

  await page.goto(URL_ + '/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
  const tok = await page.evaluate(async () => {
    const stamp = Date.now();
    let r = await fetch('/api/v1/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: `fx${stamp}@t.com`, username: `fx${stamp}`, password: 'password123' }) });
    if (r.status === 409) r = await fetch('/api/v1/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ account: `fx${stamp}@t.com`, password: 'password123' }) });
    const d = await r.json();
    return { a: d.access_token, r: d.refresh_token };
  });
  await page.evaluate((t) => { localStorage.setItem('zhistack.access_token', t.a); localStorage.setItem('zhistack.refresh_token', t.r); }, tok);

  await page.goto(URL_ + '/focus', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('svg[role="progressbar"]', { timeout: 15000 });

  // 1. 无障碍语义
  const aria = await page.evaluate(() => {
    const p = document.querySelector('svg[role="progressbar"]');
    const tl = document.querySelector('.tl');
    const modes = [...document.querySelectorAll('.mode-btn')];
    return {
      hasProgressbar: !!p, valuenow: p ? p.getAttribute('aria-valuenow') : null, valuemax: p ? p.getAttribute('aria-valuemax') : null,
      statusLive: tl ? tl.getAttribute('aria-live') : null, statusText: tl ? tl.textContent : null,
      modePressed: modes.map((m) => m.getAttribute('aria-pressed')),
    };
  });
  chk('圆环 role=progressbar', aria.hasProgressbar);
  chk('aria-valuenow/max 数值', aria.valuenow === '1500' && aria.valuemax === '1500', `now=${aria.valuenow} max=${aria.valuemax}`);
  chk('状态 aria-live=polite', aria.statusLive === 'polite', aria.statusLive);
  chk('初始状态「点击开始」', aria.statusText === '点击开始', aria.statusText);
  chk('模式按钮 aria-pressed', aria.modePressed[0] === 'true' && aria.modePressed[1] === 'false', aria.modePressed.join(','));

  await page.screenshot({ path: path.join(OUT, 'focus2-desktop.png') });

  // 2. 开始 → 标题变化 + 模式禁用
  await page.click('.btn.btn-primary.btn-lg');
  await sleep(1200);
  const running = await page.evaluate(() => ({
    title: document.title,
    disabled: [...document.querySelectorAll('.mode-btn')].every((m) => m.disabled),
    tm: document.querySelector('.tm').textContent,
  }));
  chk('运行中标题显示剩余时间', /\d\d:\d\d 专注中 · 囤囤/.test(running.title), running.title);
  chk('运行中模式按钮 disabled', running.disabled);
  await page.screenshot({ path: path.join(OUT, 'focus2-running.png') });

  // 3. 跨页存活：SPA 内部切到 Today（点侧栏「今日」），看侧栏迷你进度，再点「专注」回来
  await page.click('button[aria-label="今日"]');
  await sleep(700);
  const mini = await page.evaluate(() => ({ visible: !!document.querySelector('.nav-mini'), text: document.querySelector('.nav-mini span')?.textContent }));
  chk('侧栏迷你进度出现', mini.visible, mini.text);
  await page.click('button[aria-label="专注"]');
  await sleep(500);
  const back = await page.evaluate(() => ({ hasMini: !!document.querySelector('.nav-mini'), tm: document.querySelector('.tm').textContent }));
  chk('返回后会话仍在跑（未重置 25:00）', back.tm !== '25:00', 'tm=' + back.tm);

  // 4. 暂停 → 标题复位 + 状态「已暂停」
  await page.click('.btn.btn-primary.btn-lg');
  await sleep(400);
  const paused = await page.evaluate(() => ({ title: document.title, tl: document.querySelector('.tl').textContent }));
  chk('暂停后标题复位', paused.title === '囤囤 TUNTUN · 把知识一点点囤下来', paused.title);
  chk('暂停状态文案', paused.tl === '已暂停，随时继续', paused.tl);

  // 5. 重置 → confirm 对话框弹出（放弃留痕走 confirm）
  await page.click('.btn.btn-ghost.btn-lg');
  await sleep(300);
  chk('重置弹出确认框', dialogs.length >= 1 && /未完成/.test(dialogs[dialogs.length - 1]), dialogs[dialogs.length - 1] || '');
  await sleep(600);

  // 6. 完成庆祝：dev hook 快进
  await page.click('.btn.btn-primary.btn-lg');
  await sleep(600);
  await page.evaluate(() => { window.__focusStore.endAt = Date.now() - 1000; window.__focusStore.tick(); });
  await sleep(1200);
  const celeb = await page.evaluate(() => ({
    visible: !!document.querySelector('.celebrate-mask'),
    h2: document.querySelector('.celebrate-card h2')?.textContent,
    tomatoes: document.querySelectorAll('.jar-row .tomato').length,
    todayCount: document.querySelector('.focus-stat .fs .v')?.textContent,
  }));
  chk('完成庆祝弹层出现', celeb.visible);
  chk('庆祝文案「这一轮啃完了」', /啃完了/.test(celeb.h2 || ''), celeb.h2);
  chk('番茄罐已有番茄', celeb.tomatoes >= 1, 'tomatoes=' + celeb.tomatoes);
  await page.screenshot({ path: path.join(OUT, 'focus2-celebrate.png') });

  // 7. 移动端
  await page.setViewport({ width: 390, height: 844 });
  await page.goto(URL_ + '/focus', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(800);
  await page.screenshot({ path: path.join(OUT, 'focus2-mobile.png') });

  chk('无 JS 报错', errs.length === 0, errs.join(' | '));
  console.log(ok ? '\nALL PASS' : '\nHAS FAILURES');
  await browser.close();
  process.exit(ok ? 0 : 1);
})().catch((e) => { console.error('FATAL', e); process.exit(2); });
