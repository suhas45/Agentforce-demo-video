// Render frame backgrounds + subtitle overlays for the screen-recording sections.
// Usage: node scripts/stills.js plan.json outdir
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const [plan, dir] = process.argv.slice(2);
const P = JSON.parse(fs.readFileSync(plan));
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.resolve('video/frame.html'));
  await p.waitForFunction('window.ready');
  for (const [i, s] of P.sections.entries()) {
    await p.evaluate(a => show(a, '', false), s.label);
    await p.screenshot({ path: `${dir}/frame_${i}.png` });
  }
  for (const [id, text] of P.subs) {
    await p.evaluate(a => show('', a, true), text);
    await p.screenshot({ path: `${dir}/sub_${id}.png`, omitBackground: true });
  }
  await b.close();
})();
