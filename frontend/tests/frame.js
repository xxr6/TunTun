const puppeteer = require('puppeteer-core');
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--disable-gpu'] });
  const p = await b.newPage();
  await p.setViewport({ width: 1280, height: 800 });
  await p.goto('http://localhost:5173/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('input[autocomplete="username"]', { timeout: 15000 });
  await p.type('input[autocomplete="username"]', 'test@example.com');
  await p.type('input[type="password"]', 'password123');
  await p.click('button.submit');
  await p.waitForSelector('.ring', { timeout: 15000 });
  await new Promise(r => setTimeout(r, 900));

  const info = await p.evaluate(() => {
    const ring = document.querySelector('.ring');
    const r = ring.getBoundingClientRect();
    // ring 四角/边缘上的元素栈
    const at = (x, y) => document.elementsFromPoint(x, y).map(e =>
      e.tagName + (typeof e.className === 'string' && e.className ? '.' + e.className : '')
    ).slice(0, 5);
    // 遍历 ring 内部及相邻元素，找任何非 none 的 border/outline/boxShadow
    const suspects = [];
    document.querySelectorAll('.hero *').forEach(el => {
      const s = getComputedStyle(el);
      const has = (s.borderTopStyle !== 'none') || (s.outlineStyle !== 'none') || (s.boxShadow !== 'none');
      if (has && !el.classList.contains('btn') && !el.closest('.card')) {
        suspects.push({
          el: el.tagName + '.' + el.className,
          border: s.borderTopStyle + ' ' + s.borderTopColor,
          outline: s.outlineStyle,
          shadow: s.boxShadow.slice(0, 60),
        });
      }
    });
    return {
      ringRect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      stackTop: at(r.x + r.width / 2, r.y - 4),
      stackLeft: at(r.x - 4, r.y + r.height / 2),
      suspects: suspects.slice(0, 8),
    };
  });
  console.log(JSON.stringify(info, null, 2));
  await b.close();
  process.exit(0);
})().catch(e => { console.error(e.message); process.exit(1); });
