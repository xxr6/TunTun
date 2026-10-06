/* 真机验证：Library 上传 chip 全链路——真实浏览器选文件上传，断言 chip 从 running 走到 done，
   不再出现「永远正在解析」的假死。覆盖两个历史 bug：① 状态不响应 ② File 被代理后请求挂起。 */
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const URL_ = 'http://localhost:5173/library';
let ok = true;
const chk = (l, c, e) => { console.log((c ? 'PASS  ' : 'FAIL  ') + l + (e !== undefined ? '  -> ' + e : '')); if (!c) ok = false; };
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* 测试用 docx 由外部脚本预生成到 tests/.tmp-upload/chip-test-真实解析.docx（见测试说明） */
const PY = 'C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe';
const TMP = path.join(__dirname, '.tmp-upload');
function makeDocx() {
  const p = path.join(TMP, 'chip-test-真实解析.docx');
  if (!fs.existsSync(p)) throw new Error(`缺少测试文件 ${p}——先用 python-docx 生成它`);
  return p;
}

(async () => {
  const docxPath = makeDocx();
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--force-color-profile=srgb', '--mute-audio'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 980 });
  await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }]);
  const errs = [];
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  /* 网络监听：分辨「请求没发出」还是「发出没响应」 */
  page.on('request', r => { if (r.url().includes('/api/')) console.log('  [req ]', r.method(), r.url().replace('http://localhost:5173', '')); });
  page.on('requestfailed', r => { if (r.url().includes('/api/')) console.log('  [FAIL]', r.method(), r.failure()?.errorText); });
  page.on('response', r => { if (r.url().includes('/api/') && r.request().method() !== 'GET') console.log('  [res ]', r.status(), r.url().replace('http://localhost:5173', '')); });

  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded', timeout: 30000 });

  /* 注册一个一次性测试账号拿 token（已存在则登录），直接种 localStorage 跳过登录页 */
  const stamp = Date.now();
  const tok = await page.evaluate(async (stamp) => {
    const email = `chip${stamp}@t.com`, username = `chip${stamp}`, password = 'password123';
    let r = await fetch('/api/v1/auth/register', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password }),
    });
    if (r.status === 409) r = await fetch('/api/v1/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account: email, password }),
    });
    const data = await r.json();
    return { access: data.access_token, refresh: data.refresh_token };
  }, stamp);
  chk('拿到测试令牌', !!(tok && tok.access), tok && tok.access ? 'ok' : JSON.stringify(tok));

  await page.evaluate((t) => {
    localStorage.setItem('zhistack.access_token', t.access);
    localStorage.setItem('zhistack.refresh_token', t.refresh);
  }, tok);
  console.log('  令牌已种入，跳转 /library ...');
  await page.goto(URL_, { waitUntil: 'domcontentloaded', timeout: 30000 });
  console.log('  /library 已打开');
  /* evaluate 加超时壳：renderer 崩溃时 CDP 会永远 pending，靠这里兜底定位 */
  const evalT = (fn, ...args) => Promise.race([
    page.evaluate(fn, ...args),
    new Promise((_, rej) => setTimeout(() => rej(new Error('evaluate 卡死 10s（renderer 可能崩溃）')), 10000)),
  ]);
  console.log('  pathname =', await evalT(() => location.pathname));
  await sleep(1200);

  /* 注入 XHR send 钩子：分辨「axios 没调 send」还是「send 了但浏览器没发出去」 */
  await evalT(() => {
    window.__sendLog = [];
    const orig = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function (d) {
      window.__sendLog.push(d instanceof FormData
        ? 'send FormData[' + [...d.entries()].map(([k, v]) => k + '=' + (v && v.name ? v.name : v)).join(',') + ']'
        : 'send ' + typeof d);
      return orig.call(this, d);
    };
    return true;
  });

  /* 选中文件 → chip 出现并 running */
  const input = await page.$('input[type=file]');
  chk('找到上传 input', !!input);
  await input.uploadFile(docxPath);

  await sleep(600);
  const sendLog = await evalT(() => window.__sendLog);
  console.log('  [XHR send 记录]', JSON.stringify(sendLog));
  const running = await page.evaluate(() => {
    const el = document.querySelector('.up-chips .cc');
    return el ? { status: el.dataset.status, text: el.textContent.trim().slice(0, 60) } : null;
  });
  chk('chip 出现且 running', running && running.status === 'running', running && running.text);

  /* 最多等 15s：chip 必须走到 done（或已因 1.6s 淡出逻辑移除）——绝不允许一直 running */
  let final = null, everRunning = running && running.status === 'running';
  for (let i = 0; i < 30; i++) {
    await sleep(500);
    final = await page.evaluate(() => {
      const el = document.querySelector('.up-chips .cc');
      return el ? { status: el.dataset.status, text: el.textContent.trim().slice(0, 60) } : 'gone';
    });
    if (final === 'gone' || final.status !== 'running') break;
  }
  chk('chip 走完（done 或已移除），没有卡死在 running',
    final === 'gone' || (final && final.status === 'done'), typeof final === 'object' ? final.text : final);
  if (everRunning) chk('确实经历了 running 阶段（动画真的在跑）', true);

  /* 文件列表里应出现这个文件且已解析 */
  await sleep(800);
  const listed = await page.evaluate(() => {
    const cards = [...document.querySelectorAll('.fcard .fn')];
    return cards.map(e => e.textContent.trim()).find(n => n.includes('chip-test'));
  });
  chk('文件列表出现该文件', !!listed, listed || '未找到');
  const doneChip = await page.evaluate(() => {
    const cards = [...document.querySelectorAll('.fcard')];
    const c = cards.find(x => x.querySelector('.fn')?.textContent.includes('chip-test'));
    return c ? c.querySelector('.chip')?.textContent.trim() : null;
  });
  chk('文件状态为已解析', doneChip === '已解析', doneChip);

  chk('无 JS 运行时错误', errs.length === 0, errs.join(' | ') || '0');

  // 保留 .tmp-upload 供重复测试
  /* 本机 Edge headless 的 close() 会挂起——直接强退（flush 输出），不等它 */
  console.log(ok ? '\nALL PASS' : '\nHAS FAILURES');
  process.exit(ok ? 0 : 1);
})();
