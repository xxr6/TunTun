/* 主题选择器图标视觉验证：不手抄样式，直接从真实源文件里抠出 token / 主题元数据 /
   浮层样式 + assets 里的真实图标，拼成静态页用 Edge headless 截图。
   源文件改了这里就跟着变，避免「验证稿和实现漂移」。 */
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const SRC = path.join(ROOT, 'src');
const ASSETS = path.join(SRC, 'assets', 'themes');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const OUT_DIR = path.resolve(ROOT, 'tests', '.tmp-visual');
const SHOT = path.join(OUT_DIR, 'theme-swatch.png');
const HTML = path.join(OUT_DIR, 'theme-swatch.html');

/* ── 1. 真实源文件 ── */
const tokens = fs.readFileSync(path.join(SRC, 'styles', 'tokens.css'), 'utf8');
const themeTs = fs.readFileSync(path.join(SRC, 'composables', 'useTheme.ts'), 'utf8');
const layout = fs.readFileSync(path.join(SRC, 'layouts', 'MainLayout.vue'), 'utf8');

/* ── 2. 从 useTheme.ts 抠名称/副标题，确认图标 import 存在 ── */
const pick = (name) => {
  const m = themeTs.match(new RegExp(`${name}[^=]*=\\s*\\{([^}]*)\\}`));
  const out = {};
  for (const mm of m[1].matchAll(/(\w+):\s*'([^']*)'/g)) out[mm[1]] = mm[2];
  return out;
};
const NAMES = pick('NAMES');
const SUBS = pick('SUBS');
if (!/import cocoaIcon from/.test(themeTs)) throw new Error('useTheme.ts 没有图标 import');

/* ── 3. 图标与主题的对应关系必须和 useTheme.ts 一致：抠 THEME_ICONS ── */
const iconBlock = themeTs.match(/const THEME_ICONS[^=]*=\s*\{([\s\S]*?)\n\}/);
if (!iconBlock) throw new Error('没找到 THEME_ICONS');
const iconVar = {};
for (const m of iconBlock[1].matchAll(/(\w+):\s*(\w+)Icon/g)) iconVar[m[1]] = m[2];
const fileOf = (v) => {
  const m = themeTs.match(new RegExp(`import ${v} from '@\\/assets\\/themes\\/([^']+)'`));
  if (!m) throw new Error('找不到 ' + v + ' 的导入路径');
  return m[1];
};
const ORDER = ['cocoa', 'night', 'mint'];
const icons = ORDER.map((k) => {
  const b64 = fs.readFileSync(path.join(ASSETS, fileOf(iconVar[k] + 'Icon'))).toString('base64');
  return { key: k, data: `data:image/png;base64,${b64}` };
});
const activeIndex = Number(process.argv[2] ?? 0);

/* ── 4. 抠 MainLayout 里 .theme-pop / .tp-* 的真实样式规则 ── */
const styleBlocks = [...layout.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map((m) => m[1]).join('\n');
const wanted = ['.theme-pop', '.tp-title', '.tp-item', '.tp-item:hover', '.tp-item.on',
  '.tp-iconbox', '.tp-icon', '.tp-info', '.tp-info b', '.tp-info small', '.tp-check'];
const rules = [...styleBlocks.matchAll(/(^|\n)([ \t]*)([^\n{}]+?)\s*\{/g)]
  .map((m) => ({ sel: m[3].trim(), start: m.index + m[1].length + m[2].length }));
const popCss = [];
for (const sel of wanted) {
  const hit = rules.find((r) => r.sel.split(',').some((s) => s.trim() === sel));
  if (!hit) { console.warn('缺样式规则:', sel); continue; }
  const open = styleBlocks.indexOf('{', hit.start);
  const close = styleBlocks.indexOf('}', open);
  popCss.push(styleBlocks.slice(hit.start, close + 1));
}
const popCssText = popCss.join('\n');

/* ── 5. 从 SvgSprite 抠出真实对勾图标 ── */
const sprite = fs.readFileSync(path.join(SRC, 'components', 'common', 'SvgSprite.vue'), 'utf8');
const checkIcon = sprite.match(/<symbol id="i-check"[^>]*>([\s\S]*?)<\/symbol>/)[1];

const items = ORDER.map((k, i) => {
  const icon = icons.find((x) => x.key === k);
  return `
      <button class="tp-item${i === activeIndex ? ' on' : ''}" role="radio" aria-checked="${i === activeIndex}">
        <span class="tp-iconbox" aria-hidden="true"><img class="tp-icon" src="${icon.data}" alt="" /></span>
        <span class="tp-info"><b>${NAMES[k]}</b><small>${SUBS[k]}</small></span>
        ${i === activeIndex ? `<svg class="tp-check" viewBox="0 0 24 24">${checkIcon}</svg>` : ''}
      </button>`.trim();
}).join('\n');

const html = `<!doctype html><html lang="zh-CN" data-theme="cocoa"><head><meta charset="utf-8">
<style>
${tokens}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);font-family:'Microsoft YaHei UI','Segoe UI',sans-serif;font-size:15px;padding:30px}
.tp-check{width:16px;height:16px;flex:none;color:var(--mint-d);fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
${popCssText}
/* 预览态：脱掉浮层定位，直接在文档流里量尺寸 */
.theme-pop{position:static;left:auto;top:auto;transform:none}
</style></head><body>
  <div class="theme-pop" role="radiogroup" aria-label="配色主题" id="pop">
    <div class="tp-title">配色主题</div>${items}
  </div>
  <script>
    window.__box = () => { const r = document.getElementById('pop').getBoundingClientRect()
      return { x: r.x, y: r.y, w: r.width, h: r.height } }
  <\/script>
</body></html>`;

fs.mkdirSync(OUT_DIR, { recursive: true });
fs.writeFileSync(HTML, html, 'utf8');
console.log('样式取自源码，CSS 长度', popCssText.length, '规则数', popCss.length);

/* ── 6. Edge headless 截图 ── */
const url = 'file:///' + HTML.replace(/\\/g, '/');
const shot = (w, h) => {
  const r = spawnSync(EDGE, [
    '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=2',
    '--user-data-dir=' + path.join(OUT_DIR, 'profile'),
    `--window-size=${w},${h}`, '--screenshot=' + SHOT, url,
  ], { encoding: 'utf8', timeout: 90000 });
  if (!fs.existsSync(SHOT)) throw new Error('截图失败：' + (r.stderr || r.stdout));
};
shot(420, 300);
console.log('截图 ->', SHOT, fs.statSync(SHOT).size, 'bytes');
