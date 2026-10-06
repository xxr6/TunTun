/* 真机 UI 审查：阅读器拆卡全流程（生成→预览→编辑→入库→文件夹→长按丢弃），逐阶段截图 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const SHOT_DIR = 'C:/Users/Administrator/WorkBuddy/2026-09-30-14-48-06/zhistack/ui-review';
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

  /* 登录（复用最近一次测试账号，不存在则注册） */
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
  const tok = await page.evaluate(async () => {
    const email = 'chip0@t.com', password = 'password123';
    let r = await fetch('/api/v1/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account: email, password }),
    });
    if (r.status !== 200) {
      r = await fetch('/api/v1/auth/register', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, username: 'chip0', password }),
      });
    }
    const d = await r.json();
    return { access: d.access_token, refresh: d.refresh_token };
  });
  chk('登录/注册成功', !!tok.access);
  await page.evaluate((t) => {
    localStorage.setItem('zhistack.access_token', t.access);
    localStorage.setItem('zhistack.refresh_token', t.refresh);
  }, tok);

  console.log('  step: 检查已有文档...');
  /* 确保有已解析文档 */
  const docId = await page.evaluate(async () => {
    const files = await (await fetch('/api/v1/files', { headers: { Authorization: 'Bearer ' + localStorage.getItem('zhistack.access_token') } })).json();
    const withDoc = files.find((f) => f.doc_id && f.doc_status === 'done');
    if (withDoc) return withDoc.doc_id;
    const buf = await fetch('http://localhost:5173/src/assets/x').catch(() => null); // 占位，不会走
    return null;
  });
  if (!docId) {
    // 上传现成 docx
    await page.goto('http://localhost:5173/library', { waitUntil: 'domcontentloaded', timeout: 30000 });
    const input = await page.waitForSelector('input[type=file]', { timeout: 10000 });
    await input.uploadFile('C:/Users/Administrator/WorkBuddy/2026-09-30-14-48-06/zhistack/frontend/tests/.tmp-upload/chip-test-真实解析.docx');
    await sleep(4000);
  }
  const finalDoc = await page.evaluate(async () => {
    const files = await (await fetch('/api/v1/files', { headers: { Authorization: 'Bearer ' + localStorage.getItem('zhistack.access_token') } })).json();
    const f = files.find((x) => x.doc_id && x.doc_status === 'done');
    return f ? f.doc_id : null;
  });
  chk('有可阅读的已解析文档', !!finalDoc, finalDoc);

  console.log('  step: 打开阅读器 doc=' + finalDoc);
  /* 打开阅读器 */
  await page.goto('http://localhost:5173/reader?doc=' + finalDoc, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(1500);
  await page.waitForSelector('.doc-text', { timeout: 10000 });

  /* 划词：选中正文前 40 字 */
  await page.evaluate(() => {
    const pre = document.querySelector('.doc-text');
    const node = pre.firstChild;
    const range = document.createRange();
    range.setStart(node, 0);
    range.setEnd(node, Math.min(40, node.textContent.length));
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    document.querySelector('.doc-body').dispatchEvent(
      new MouseEvent('mouseup', { bubbles: true, clientX: 400, clientY: 300 }),
    );
  });
  await sleep(300);
  chk('划词工具条出现', !!(await page.$('.tip-btn')));
  await page.click('.tip-btn');

  /* 等 AI 生成（最多 30s） */
  let generated = false;
  for (let i = 0; i < 60; i++) {
    await sleep(500);
    if (await page.$('.gen-item')) { generated = true; break; }
  }
  chk('生成卡片出现', generated);
  await sleep(700);
  await page.screenshot({ path: SHOT_DIR + '/reader-1-预览态.png' });
  console.log('  截图: reader-1-预览态.png');

  /* 编辑态 */
  await page.click('.gen-item .mini-btn');
  await sleep(300);
  const hasTextarea = !!(await page.$('.gen-item textarea'));
  chk('点「编辑」出现表单', hasTextarea);
  await page.screenshot({ path: SHOT_DIR + '/reader-2-编辑态.png' });
  console.log('  截图: reader-2-编辑态.png');
  await page.click('.gen-item .mini-btn'); // 完成
  await sleep(300);

  /* 入库 → 文件夹出现 */
  await page.click('.gen-actions .btn-primary');
  let folder = null;
  for (let i = 0; i < 20; i++) {
    await sleep(500);
    folder = await page.$('.folder-grid .fd');
    if (folder) break;
  }
  chk('入库后文件夹出现', !!folder);
  await sleep(600);
  await page.screenshot({ path: SHOT_DIR + '/reader-3-文件夹.png' });
  console.log('  截图: reader-3-文件夹.png');

  /* 点击文件夹 → 详情弹窗 */
  if (folder) {
    await folder.click();
    await sleep(500);
    const mask = !!(await page.$('.view-card'));
    chk('点文件夹弹出卡片详情', mask);
    await page.screenshot({ path: SHOT_DIR + '/reader-4-详情弹窗.png' });
    console.log('  截图: reader-4-详情弹窗.png');
    await page.keyboard.press('Escape');
    await page.click('.view-card .mini-btn').catch(() => {});
    await sleep(400);
  }

  /* 长按丢弃（还有生成卡片在吗？入库后 cards 清空——重新生成一组再丢弃） */
  const stillCards = !!(await page.$('.gen-item'));
  if (!stillCards) {
    await page.evaluate(() => {
      const pre = document.querySelector('.doc-text');
      const node = pre.firstChild;
      const range = document.createRange();
      range.setStart(node, 5);
      range.setEnd(node, Math.min(45, node.textContent.length));
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
      document.querySelector('.doc-body').dispatchEvent(
        new MouseEvent('mouseup', { bubbles: true, clientX: 400, clientY: 300 }),
      );
    });
    await sleep(300);
    await page.click('.tip-btn');
    for (let i = 0; i < 60; i++) {
      await sleep(500);
      if (await page.$('.gen-item')) break;
    }
  }
  const hb = await page.$('.gen-actions .hb');
  chk('长按丢弃按钮存在', !!hb);
  if (hb) {
    const box = await hb.boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await sleep(400);
    await page.screenshot({ path: SHOT_DIR + '/reader-5-长按填充中.png' });
    console.log('  截图: reader-5-长按填充中.png');
    await sleep(1400);
    await page.mouse.up();
    await sleep(400);
    const cardsAfter = await page.$('.gen-item');
    const doneState = await page.evaluate(() => document.querySelector('.gen-actions .hb')?.dataset.phase);
    chk('长按完成后卡片被丢弃', !cardsAfter, doneState);
    /* 快速点一下 → 应该只是 tap 提示，不丢弃 */
  }

  chk('无 JS 运行时错误', errs.length === 0, errs.join(' | ') || '0');

  console.log(ok ? '\nALL PASS' : '\nHAS FAILURES（截图在 ' + SHOT_DIR + '）');
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error('SCRIPT ERROR:', e && e.message); process.exit(1); });
