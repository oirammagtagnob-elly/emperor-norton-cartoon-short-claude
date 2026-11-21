// Usage: node tools/render.mjs <startFrame> <endFrame> <outDir> [extraQuery]
//   e.g. node tools/render.mjs 0 900 frames "&nocap=1"
// Animation time = real time * SPEED (the voiceover is played at SPEED x, see README).
import { chromium } from 'playwright';
import fs from 'fs';
import { fileURLToPath } from 'url';
const FPS = 30, DUR = 74.84, SPEED = parseFloat(process.env.SPEED || '1.27');
const N = Math.ceil(DUR / SPEED * FPS);
const page_url = fileURLToPath(new URL('../src/index.html', import.meta.url));
const [A, Z, out = 'frames', extra = '&nocap=1'] = [+process.argv[2] || 0, +process.argv[3] || N, process.argv[4], process.argv[5]];
fs.mkdirSync(out, { recursive: true });
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
p.on('pageerror', e => console.log('PAGEERR', e.message));
await p.goto('file://' + page_url + '?sc=1.5' + extra);
for (let i = A; i < Math.min(N, Z); i++) {
  const d = await p.evaluate(t => { draw(t); return document.getElementById('c').toDataURL('image/jpeg', .93); }, Math.min(i / FPS * SPEED, DUR));
  fs.writeFileSync(`${out}/f${String(i).padStart(5, '0')}.jpg`, Buffer.from(d.split(',')[1], 'base64'));
}
console.log('total frames', N);
await b.close();
