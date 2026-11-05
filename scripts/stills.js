// Render frame backgrounds + subtitle overlays for the screen-recording sections.
// Usage: node scripts/stills.js plan.json outdir
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const [plan, dir] = process.argv.slice(2);
const P = JSON.parse(fs.readFileSync(plan));
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME || require('fs').readdirSync('/opt/pw-browsers').filter(d => /^chromium-\d+$/.test(d)).map(d => ['/opt/pw-browsers/' + d + '/chrome-linux64/chrome', '/opt/pw-browsers/' + d + '/chrome-linux/chrome']).flat().find(p => require('fs').existsSync(p)) });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.resolve(P.frame || 'video/frame.html'));
  await p.waitForFunction('window.ready');
  for (const [i, s] of P.sections.entries()) {
    await p.evaluate(s => show(s.label, '', false, s.win), s);
    await p.screenshot({ path: `${dir}/frame_${i}.png` });
  }
  for (const [id, text] of P.subs) {
    await p.evaluate(a => show('', a, true), text);
    await p.screenshot({ path: `${dir}/sub_${id}.png`, omitBackground: true });
  }
  await b.close();
})();
