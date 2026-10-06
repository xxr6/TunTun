/**
 * GooeyNav 主题切换专项验证
 * ① 侧边栏点调色板 → 浮层出现，指示器（.gn-pill/.text）对齐当前主题项
 * ② 点击其他主题 → data-theme 变化 + 粒子生成（.gn-particle 出现）+ 指示器位移
 * ③ --color-1..4 随主题刷新
 * ④ 登录页紧凑模式也渲染
 * ⑤ 全流程 0 JS 报错
 */
const puppeteer = require('puppeteer-core');
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';

const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.launch({
    executablePath: EDGE,
    headless: 'new',
    args: ['--disable-gpu', '--force-prefers-reduced-motion=no-preference'],
  });
  const p = await b.newPage();
  await p.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }]);
  await p.setViewport({ width: 1280, height: 820 });

  const errors = [];
  p.on('pageerror', e => errors.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });

  const out = {};

  // ── 登录页：紧凑 GooeyNav ──
  await p.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('.gooey-nav', { timeout: 15000 });
  await sleep(500);
  out.loginNav = await p.evaluate(() => {
    const nav = document.querySelector('.gooey-nav');
    const items = [...nav.querySelectorAll('.gn-item')].map(li => li.innerText.trim());
    const filter = nav.querySelector('.gn-pill');
    const fs = getComputedStyle(filter);
    return {
      items,
      count: items.length,
      itemRect: (() => { const r = nav.querySelector('.gn-item').getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; })(),
      filterRect: (() => { const r = filter.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; })(),
      pillBg: fs.backgroundColor,
      pillBorder: fs.borderTopWidth + ' ' + fs.borderTopColor,
      pillTransform: fs.transform,
      pillBoxShadow: fs.boxShadow.slice(0, 48),
      activeIdx: [...nav.querySelectorAll('.gn-item')].findIndex(li => li.classList.contains('active')),
    };
  });

  // 登录页切一次主题（点第 2 项 = 夜读）
  await p.evaluate(() => {
    const li = document.querySelectorAll('.gooey-nav .gn-item')[1];
    li.querySelector('a').click();
  });
  await sleep(120);
  out.loginAfterClick = await p.evaluate(() => {
    const nav = document.querySelector('.gooey-nav');
    return {
      theme: document.documentElement.dataset.theme,
      particles: nav.querySelectorAll('.gn-particle').length,
      rootDark: nav.classList.contains('dark-theme'),
      pillBg: getComputedStyle(nav.querySelector('.gn-pill')).backgroundColor,
      pillX: getComputedStyle(nav.querySelector('.gn-pill')).transform,
      c1: getComputedStyle(document.documentElement).getPropertyValue('--color-1').trim(),
    };
  });
  await sleep(900);
  await p.screenshot({ path: 'gooey-login-night.png' });

  // 回默认，进主应用
  await p.evaluate(() => {
    document.querySelectorAll('.gooey-nav .gn-item')[0].querySelector('a').click();
  });
  await sleep(600);

  // ── 登录 ──
  await p.waitForSelector('input[autocomplete="username"]');
  await p.type('input[autocomplete="username"]', 'test@example.com');
  await p.type('input[type="password"]', 'password123');
  await p.click('button.submit');
  await p.waitForSelector('.sidebar', { timeout: 15000 });
  await sleep(900);

  // 找到主题按钮（aria-label=切换配色主题）
  await p.click('button[aria-label="切换配色主题"]');
  await p.waitForSelector('.theme-pop', { timeout: 8000 });
  await sleep(700);

  out.popover = await p.evaluate(() => {
    const pop = document.querySelector('.theme-pop');
    const nav = pop.querySelector('.gooey-nav');
    const items = [...nav.querySelectorAll('.gn-item')];
    const filter = nav.querySelector('.gn-pill');
    const text = nav.querySelector('.gn-pill');
    const active = items.find(li => li.classList.contains('active'));
    const ar = active.getBoundingClientRect();
    const fr = filter.getBoundingClientRect();
    return {
      labels: items.map(li => li.innerText.trim()),
      activeIdx: items.findIndex(li => li.classList.contains('active')),
      theme: document.documentElement.dataset.theme,
      effectAligned: Math.abs(ar.x - fr.x) < 6 && Math.abs(ar.width - fr.width) < 12,
      indicator: { x: Math.round(fr.x), w: Math.round(fr.width) },
      activeRect: { x: Math.round(ar.x), w: Math.round(ar.width) },
      popRect: (() => { const r = pop.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })(),
      textColor: getComputedStyle(text).color,
      itemColors: items.map(li => getComputedStyle(li).color),
      bgColors: items.map(li => getComputedStyle(li, '::after').backgroundColor),
    };
  });
  await p.screenshot({ path: 'gooey-popover-cocoa.png' });

  // 点第 3 项（薄荷）
  await p.evaluate(() => {
    document.querySelectorAll('.theme-pop .gn-item')[2].querySelector('a').click();
  });
  await sleep(90);
  out.afterSwitch = await p.evaluate(() => {
    const nav = document.querySelector('.theme-pop .gooey-nav');
    const fr = nav.querySelector('.gn-pill').getBoundingClientRect();
    const items = [...nav.querySelectorAll('.gn-item')];
    const ar = items[2].getBoundingClientRect();
    return {
      theme: document.documentElement.dataset.theme,
      particles: nav.querySelectorAll('.gn-particle').length,
      activeIdx3: items[2].classList.contains('active'),
      indicatorMoved: Math.abs(ar.x - fr.x) < 3,
      colors: [1, 2, 3, 4].map(i => getComputedStyle(document.documentElement).getPropertyValue('--color-' + i).trim()),
      bodyBg: getComputedStyle(document.body).backgroundColor,
    };
  });
  await sleep(400);
  await p.screenshot({ path: 'gooey-popover-mint.png' });

  // 再切夜读，看深色模式指示器
  await p.evaluate(() => {
    document.querySelectorAll('.theme-pop .gn-item')[1].querySelector('a').click();
  });
  await sleep(500);
  out.night = await p.evaluate(() => {
    const nav = document.querySelector('.theme-pop .gooey-nav');
    const items = [...nav.querySelectorAll('.gn-item')];
    return {
      theme: document.documentElement.dataset.theme,
      darkClass: nav.classList.contains('dark-theme'),
      pillBg: getComputedStyle(nav.querySelector('.gn-pill')).backgroundColor,
      pillX: getComputedStyle(nav.querySelector('.gn-pill')).transform,
      activeColor: getComputedStyle(items.find(li => li.classList.contains('active'))).color,
      pillBg: getComputedStyle(nav.querySelector('.gn-pill')).backgroundColor,
      bodyBg: getComputedStyle(document.body).backgroundColor,
    };
  });
  await p.screenshot({ path: 'gooey-popover-night.png' });

  // 收起浮层 + 看主题是否保持
  await p.mouse.click(500, 400);
  await sleep(400);
  out.closed = await p.evaluate(() => ({
    popGone: !document.querySelector('.theme-pop'),
    theme: document.documentElement.dataset.theme,
  }));
  await p.screenshot({ path: 'gooey-today-night.png' });

  // 回浅色看一眼今日页
  await p.click('button[aria-label="切换配色主题"]');
  await sleep(500);
  await p.evaluate(() => { document.querySelectorAll('.theme-pop .gn-item')[0].querySelector('a').click(); });
  await sleep(700);
  await p.mouse.click(600, 500);
  await sleep(600);
  await p.screenshot({ path: 'gooey-today-cocoa.png' });

  out.errors = errors;
  console.log(JSON.stringify(out, null, 2));
  await b.close();
  process.exit(0);
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
