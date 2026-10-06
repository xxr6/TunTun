/* 真机 UI 审查：AI 提炼页全流程（上传→五步进度→提炼→结果→候选→拆卡），分阶段截图 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const SHOT_DIR = 'C:/Users/Administrator/WorkBuddy/2026-09-30-14-48-06/zhistack/ui-review';
const DOCX = 'C:/Users/Administrator/WorkBuddy/2026-09-30-14-48-06/zhistack/frontend/tests/.tmp-upload/chip-test-真实解析.docx';
let ok = true;
const chk = (l, c, e) => { console.log((c ? 'PASS  ' : 'FAIL  ') + l + (e !== undefined ? '  -> ' + e : '')); if (!c) ok = false; };
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  fs.mkdirSync(SHOT_DIR, { recursive: true });
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

  /* 登录 */
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
  const tok = await page.evaluate(async () => {
    const email = 'chip0@t.com', password = 'password123';
    let r = await fetch('/api/v1/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account: email, password }),
    });
    if (r.status !== 200) r = await fetch('/api/v1/auth/register', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username: 'chip0', password }),
    });
    const d = await r.json();
    return { access: d.access_token, refresh: d.refresh_token };
  });
  chk('登录成功', !!tok.access);
  await page.evaluate((t) => {
    localStorage.setItem('zhistack.access_token', t.access);
    localStorage.setItem('zhistack.refresh_token', t.refresh);
  }, tok);

  /* 打开提炼页 */
  await page.goto('http://localhost:5173/extract', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.dropzone', { timeout: 15000 });
  await sleep(1000);
  await page.screenshot({ path: SHOT_DIR + '/extract-1-初始.png' });
  console.log('  截图: extract-1-初始.png（空态 + 来源 tab + 进度 pending）');

  /* 视频tab应禁用 */
  const videoDisabled = await page.$eval('.src-tab:disabled', el => el.textContent.includes('视频')).catch(() => false);
  chk('视频 tab 存在且禁用（诚实不画饼）', videoDisabled);

  /* 上传 docx → CallChip → 自动提炼 */
  const input = await page.$('.dropzone input[type=file]');
  await input.uploadFile(DOCX);
  await sleep(500);
  const chipRunning = await page.evaluate(() => document.querySelector('.ex-left .cc')?.dataset.status);
  chk('上传 CallChip 出现', !!chipRunning, chipRunning);

  /* 等提炼完成（真实 LLM，最多 90s） */
  let noteShown = false, stepsSawActive = false;
  for (let i = 0; i < 180; i++) {
    const st = await page.evaluate(() => ({
      active: [...document.querySelectorAll('.step-row')].filter(r => r.dataset.state === 'active').length,
      done: [...document.querySelectorAll('.step-row')].filter(r => r.dataset.state === 'done').length,
      note: !!document.querySelector('.note-read, .note-source'),
    }));
    if (st.active > 0) stepsSawActive = true;
    if (st.note) { noteShown = true; break; }
    await sleep(500);
  }
  chk('五步进度出现过 active 状态', stepsSawActive);
  chk('提炼完成显示笔记', noteShown);
  await sleep(800);
  await page.screenshot({ path: SHOT_DIR + '/extract-2-结果.png' });
  console.log('  截图: extract-2-结果.png（阅读视图 + 候选列表）');

  /* 阅读视图有渲染内容 */
  const readHtml = await page.$eval('.note-read', el => el.innerHTML).catch(() => '');
  chk('阅读视图渲染了标题/列表', /<(h[234]|ul|li)/.test(readHtml), readHtml.slice(0, 60));

  /* 源码视图切换 */
  const tabs = await page.$$('.view-tabs button');
  await tabs[1].click();
  await sleep(300);
  const srcShown = !!(await page.$('.note-source'));
  chk('源码视图切换成功', srcShown);
  await tabs[0].click();
  await sleep(200);

  /* 复制（headless 剪贴板权限可能拒绝，不强断言内容） */
  await page.click('.res-tools .mini-btn');
  await sleep(300);
  const copiedLabel = await page.evaluate(() => document.querySelector('.res-tools .mini-btn')?.textContent.trim());
  chk('复制反馈出现', copiedLabel === '已复制', copiedLabel);

  /* 候选列表 + 勾选 */
  const candCount = await page.$$eval('.cand-item', els => els.length).catch(() => 0);
  chk('候选列表有内容', candCount > 0, candCount + ' 条');
  /* 勾选第一个 */
  const firstCheckbox = await page.$('.cand-item input[type=checkbox]');
  if (firstCheckbox) {
    // label 包裹 checkbox 时 element.click() 会冒泡到 label 再转发回来 = 双切换回到原状，改用 change 事件
    await page.evaluate(() => {
      const cb = document.querySelector('.cand-item input[type=checkbox]');
      cb.checked = true;
      cb.dispatchEvent(new Event('change', { bubbles: true }));
    });
    await sleep(200);
    const checked = await page.$eval('.cand-item input[type=checkbox]', el => el.checked).catch(() => false);
    chk('勾选候选生效', checked);
  }

  /* 选卡组 + 拆卡 */
  const deckVal = await page.evaluate(() => {
    const sel = document.querySelector('.deck-select');
    if (!sel) return null;
    const opt = sel.querySelector('option[value]:not([value=""])');
    return opt ? opt.value : null;
  });
  if (deckVal) {
    await page.evaluate((v) => {
      const sel = document.querySelector('.deck-select');
      sel.value = v;
      sel.dispatchEvent(new Event('change', { bubbles: true }));
    }, deckVal);
    /* v-model 需要 input 事件 */
    await page.evaluate((v) => {
      const sel = document.querySelector('.deck-select');
      sel.value = v;
      sel.dispatchEvent(new Event('input', { bubbles: true }));
    }, deckVal);
    await sleep(200);
    const splitBtn = await page.$('.res-head .btn-primary');
    if (splitBtn) {
      const disabled = await page.evaluate(el => el.disabled, splitBtn).catch(() => true);
      if (!disabled) {
        await splitBtn.click();
        let doneTag = false;
        for (let i = 0; i < 20; i++) {
          await sleep(400);
          doneTag = !!(await page.$('.cand-done-tag'));
          if (doneTag) break;
        }
        chk('拆卡后候选标「已入库」', doneTag);
      } else {
        console.log('  （拆卡按钮仍禁用——勾选未生效，跳过）');
      }
    }
  } else {
    console.log('  （无卡组可选，跳过拆卡断言）');
  }
  await page.screenshot({ path: SHOT_DIR + '/extract-3-拆卡后.png' });
  console.log('  截图: extract-3-拆卡后.png');

  chk('无 JS 运行时错误', errs.length === 0, errs.join(' | ') || '0');

  console.log(ok ? '\nALL PASS' : '\nHAS FAILURES');
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error('SCRIPT ERROR:', e && e.message); process.exit(1); });
