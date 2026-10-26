// Render one walkthrough segment (intro / chapter / end) frame by frame.
// Usage: node scripts/walk_render.js <cfg.json> <out.mp4> [preview t1,t2,...]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const FF = process.env.FFMPEG || 'ffmpeg';
const FPS = 30;
const [cfgPath, out, mode, times] = process.argv.slice(2);
const cfg = JSON.parse(fs.readFileSync(cfgPath));
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.resolve('video/walk/page.html'));
  await p.evaluate(c => init(c), cfg);
  if (mode === 'preview') {
    for (const t of times.split(',').map(Number)) {
      await p.evaluate(t => seek(t), t);
      await p.screenshot({ path: `${out}_${t}.png` });
    }
    return b.close();
  }
  const ff = spawn(FF, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'medium', '-r', String(FPS), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round(FPS * cfg.dur);
  for (let i = 0; i < N; i++) {
    await p.evaluate(t => seek(t), i / FPS);
    const buf = await p.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await b.close();
})();
