// Usage: node tools/stills.mjs <t1> <t2> ...   (times in the original 74.84 s timeline) -> stills/t<time>.jpg
import { chromium } from 'playwright';
import fs from 'fs';
import { fileURLToPath } from 'url';
const times = process.argv.slice(2).map(Number);
fs.mkdirSync('stills', { recursive: true });
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 720, height: 1280 } });
p.on('pageerror', e => console.log('PAGEERR', e.message));
await p.goto('file://' + fileURLToPath(new URL('../src/index.html', import.meta.url)) + '?sc=1&nocap=1');
for (const t of times) {
  const d = await p.evaluate(t => { draw(t); return document.getElementById('c').toDataURL('image/jpeg', .9); }, t);
  fs.writeFileSync(`stills/t${String(t).replace('.', '_')}.jpg`, Buffer.from(d.split(',')[1], 'base64'));
}
await b.close();
