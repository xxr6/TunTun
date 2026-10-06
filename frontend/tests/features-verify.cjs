/* 新功能真机验证：签到卡/今日计划 CRUD/自定义时长/秒针/贴纸二次确认/个人中心。 */
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
  page.on('dialog', async (d) => { dialogs.push(d.type()); await d.accept(); });

  await page.goto(URL_ + '/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
  const tok = await page.evaluate(async () => {
    const s = Date.now();
    let r = await fetch('/api/v1/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: `nf${s}@t.com`, username: `nf${s}`, password: 'password123' }) });
    if (r.status === 409) r = await fetch('/api/v1/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ account: `nf${s}@t.com`, password: 'password123' }) });
    const d = await r.json(); return { a: d.access_token, r: d.refresh_token };
  });
  await page.evaluate((t) => { localStorage.setItem('zhistack.access_token', t.a); localStorage.setItem('zhistack.refresh_token', t.r); }, tok);

  /* ── 1. 今日页：签到 + 计划 ── */
  await page.goto(URL_ + '/today', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.checkin-card', { timeout: 15000 });
  await page.screenshot({ path: path.join(OUT, 'today-v3.png') });
  const chkBefore = await page.evaluate(() => document.querySelector('.checkin-card .btn')?.textContent.trim());
  chk('签到按钮初始「签到」', chkBefore === '签到', chkBefore);
  await page.click('.checkin-card .btn');
  await sleep(900);
  const chkAfter = await page.evaluate(() => ({
    btn: document.querySelector('.checkin-card .btn')?.textContent.trim(),
    notice: document.querySelector('.checkin-notice')?.textContent || '',
    next: document.querySelector('.checkin-next')?.textContent || '',
  }));
  chk('签到后按钮「已签到」', chkAfter.btn === '已签到', chkAfter.btn);
  chk('新成就提示出现', /新成就/.test(chkAfter.notice), chkAfter.notice || chkAfter.next);

  // 计划：新建 / 打勾 / 删除
  const planCountBefore = await page.evaluate(() => document.querySelectorAll('.task').length);
  await page.type('.plan-input', '背 20 个单词');
  await page.keyboard.press('Enter');
  await sleep(700);
  const planCountAfter = await page.evaluate(() => document.querySelectorAll('.task').length);
  chk('计划新增一条', planCountAfter === planCountBefore + 1, `${planCountBefore}->${planCountAfter}`);
  await page.click('.task .tick');
  await sleep(600);
  const doneState = await page.evaluate(() => document.querySelector('.task')?.classList.contains('done'));
  chk('点击圆圈完成', doneState === true);
  await page.hover('.task');
  await page.click('.task-del');
  await sleep(600);
  const planCountDel = await page.evaluate(() => document.querySelectorAll('.task').length);
  chk('计划删除一条', planCountDel === planCountBefore, `${planCountAfter}->${planCountDel}`);

  /* ── 2. 专注页：自定义时长 + 秒针 + 贴纸确认 ── */
  await page.goto(URL_ + '/focus', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.mode-btn', { timeout: 15000 });
  await page.evaluate(() => { [...document.querySelectorAll('.mode-btn')].find(b => b.textContent.includes('自定义')).click(); });
  await sleep(400);
  const customVisible = await page.evaluate(() => !!document.querySelector('.custom-input'));
  chk('自定义模式出现步进器', customVisible);
  await page.click('.step-btn:last-child'); // +1
  await sleep(300);
  const customVal = await page.evaluate(() => document.querySelector('.custom-input')?.value);
  chk('步进 +1', customVal === '46', customVal);
  const hasNeedle = await page.evaluate(() => !!document.querySelector('.needle'));
  chk('秒针存在', hasNeedle);
  await page.screenshot({ path: path.join(OUT, 'focus-v3-custom.png') });

  // 开始 → 标题 + 秒针角度变化
  await page.click('.btn.btn-primary.btn-lg');
  await sleep(1500);
  const run = await page.evaluate(() => ({
    title: document.title,
    angle: document.querySelector('.needle').style.transform,
  }));
  chk('运行中标题剩余时间', /专注中/.test(run.title), run.title);
  chk('秒针在扫动', /rotate\(/.test(run.angle) && run.angle !== 'rotate(0deg)', run.angle);

  // 重置 → 贴纸二次确认（非浏览器 confirm）
  await page.click('.btn.btn-ghost.btn-lg');
  await sleep(400);
  const cdVisible = await page.evaluate(() => !!document.querySelector('.cd-card'));
  chk('贴纸二次确认弹层出现', cdVisible);
  chk('未触发浏览器原生 dialog', dialogs.length === 0, dialogs.join(','));
  await page.screenshot({ path: path.join(OUT, 'focus-v3-confirm.png') });
  await page.click('.cd-card .cd-danger');
  await sleep(400);
  const resetDone = await page.evaluate(() => !document.querySelector('.cd-card'));
  chk('确认后弹层关闭且重置', resetDone);

  /* ── 3. 个人中心 ── */
  await page.click('.avatar');
  await sleep(800);
  const me = await page.evaluate(() => ({
    name: document.querySelector('.me-name')?.textContent,
    tz: document.querySelector('.me-select')?.value,
    hasStats: document.querySelectorAll('.me-stat').length,
    logout: !!document.querySelector('.btn-danger'),
  }));
  chk('个人中心：用户名', !!me.name, me.name);
  chk('个人中心：时区下拉', !!me.tz, me.tz);
  chk('个人中心：统计 4 项', me.hasStats === 4, String(me.hasStats));
  chk('个人中心：退出按钮', me.logout);
  await page.screenshot({ path: path.join(OUT, 'me-v3.png') });

  chk('无 JS 报错', errs.length === 0, errs.join(' | '));
  console.log(ok ? '\nALL PASS' : '\nHAS FAILURES');
  await browser.close();
  process.exit(ok ? 0 : 1);
})().catch((e) => { console.error('FATAL', e); process.exit(2); });
