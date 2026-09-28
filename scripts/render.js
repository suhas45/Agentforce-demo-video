// Usage: node scripts/render.js [preview t1,t2,...]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const FF = process.env.FFMPEG || 'ffmpeg';
const FPS = 30, DUR = 35.5;
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.resolve(__dirname, '../video/index.html'));
  await p.waitForFunction('window.ready');
  if (process.argv[2] === 'preview') {
    for (const t of process.argv[3].split(',').map(Number)) {
      await p.evaluate(t => setT(t), t);
      await p.screenshot({ path: `out/preview_${t}.png` });
    }
    return b.close();
  }
  const ff = spawn(FF, ['-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', 'out/video_silent.mp4'], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round(FPS * DUR);
  for (let i = 0; i < N; i++) {
    await p.evaluate(t => setT(t), i / FPS);
    const buf = await p.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log('frame', i, '/', N);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await b.close();
})();
