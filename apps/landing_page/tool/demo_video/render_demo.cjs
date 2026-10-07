const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const { chromium } = require('playwright');
const ffmpeg = require('ffmpeg-static');

const root = path.resolve(__dirname, '../../../..');
const landing = path.join(root, 'apps/landing_page');
const captures = path.join(__dirname, 'captures');
const output = path.join(landing, 'assets/videos/sokoun_demo.mp4');
const poster = path.join(landing, 'assets/images/sokoun_demo_poster.jpg');
const width = 1280;
const height = 720;
const fps = 30;
const seconds = 40;

function dataUri(file, type) {
  return `data:${type};base64,${fs.readFileSync(file).toString('base64')}`;
}

async function main() {
  const assets = {};
  for (const name of ['discovery', 'property', 'property_saved', 'visit', 'visit_selected', 'owner']) {
    assets[name] = dataUri(path.join(captures, `${name}.png`), 'image/png');
  }
  assets.logo = dataUri(path.join(landing, 'web/logo.svg'), 'image/svg+xml');
  const fontDirectory = path.join(root, 'packages/core/assets/fonts/Tajawal');
  assets.regularFont = dataUri(path.join(fontDirectory, 'Tajawal-Regular.ttf'), 'font/ttf');
  assets.boldFont = dataUri(path.join(fontDirectory, 'Tajawal-ExtraBold.ttf'), 'font/ttf');
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.mkdirSync(path.dirname(poster), { recursive: true });

  // Use an installed browser when CHROME_PATH is supplied. Otherwise use the
  // Chromium installed with `npx playwright install chromium`.
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}),
  });
  try {
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
    await page.setContent('<html><body style="margin:0"><canvas id="film" width="1280" height="720"></canvas></body></html>');
    await page.evaluate(async (assets) => {
      for (const [weight, source] of [[400, assets.regularFont], [800, assets.boldFont]]) {
        const font = new FontFace('Tajawal', `url(${source})`, { weight: String(weight) });
        await font.load();
        document.fonts.add(font);
      }
      const images = {};
      await Promise.all(Object.entries(assets).filter(([name]) => !name.endsWith('Font')).map(async ([name, source]) => {
        const image = new Image();
        image.src = source;
        await image.decode();
        images[name] = image;
      }));
      const canvas = document.querySelector('#film');
      const ctx = canvas.getContext('2d');
      const ink = '#152E29';
      const teal = '#0C6254';
      const muted = '#60756B';
      const gold = '#D6A84F';
      const clamp = (n) => Math.max(0, Math.min(1, n));
      const smooth = (n) => { n = clamp(n); return n * n * (3 - 2 * n); };
      const scenes = [
        { start: 4, end: 12, tag: 'للمستأجر', number: '01', title: ['سكن يناسبك.', 'من أول بحث.'], body: ['اكتشف العقارات المقترحة', 'وابحث بالمنطقة اللي تناسبك.'], chips: ['اكتشف', 'ابحث', 'اختار'], image: 'discovery' },
        { start: 12, end: 20, tag: 'تفاصيل أوضح', number: '02', title: ['كل التفاصيل.', 'قبل ما تقرر.'], body: ['راجع الصور والسعر وتفاصيل الإيجار.', 'واحفظ العقارات المناسبة في المفضلة.'], chips: ['صور العقار', 'السعر', 'المفضلة'], image: 'property' },
        { start: 20, end: 28, tag: 'زيارة بخطوات بسيطة', number: '03', title: ['اختار الموعد.', 'واطلب زيارة.'], body: ['حدد اليوم والوقت المتاح', 'وابعت طلب المعاينة للمالك.'], chips: ['اختار اليوم', 'حدد الوقت', 'اطلب زيارة'], image: 'visit' },
        { start: 28, end: 36, tag: 'للمالك', number: '04', title: ['عقاراتك وطلباتك.', 'في مكان واحد.'], body: ['تابع طلبات الزيارة وإحصائيات العقارات.', 'ووصل للعقود وإدارة الإيجار بسهولة.'], chips: ['طلبات الزيارة', 'الإحصائيات', 'الإدارة'], image: 'owner' },
      ];
      function roundRect(x, y, w, h, radius, fill) {
        ctx.beginPath();
        ctx.roundRect(x, y, w, h, radius);
        ctx.fillStyle = fill;
        ctx.fill();
      }
      function text(value, x, y, size, color = ink, weight = 400, align = 'right') {
        ctx.font = `${weight} ${size}px Tajawal`;
        ctx.textAlign = align;
        ctx.direction = 'rtl';
        ctx.fillStyle = color;
        ctx.fillText(value, x, y);
      }
      function background(time) {
        ctx.fillStyle = '#FAFBF8';
        ctx.fillRect(0, 0, 1280, 720);
        let gradient = ctx.createRadialGradient(255, 360, 30, 255, 360, 490);
        gradient.addColorStop(0, '#D4E5D8');
        gradient.addColorStop(1, '#FAFBF8');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 650, 720);
        ctx.strokeStyle = '#B6CDBD';
        ctx.lineWidth = 1;
        for (let index = 0; index < 3; index++) {
          ctx.beginPath();
          ctx.ellipse(250, 370, 200 + index * 55, 275 + index * 50, -0.15 + Math.sin(time * 0.15) * 0.02, 0, Math.PI * 2);
          ctx.stroke();
        }
        ctx.fillStyle = gold;
        ctx.beginPath(); ctx.arc(491, 147, 6, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(60, 529, 4, 0, Math.PI * 2); ctx.fill();
        ctx.drawImage(images.logo, 1160, 40, 56, 56);
        text('سكون', 1143, 76, 28, teal, 800);
        text('SOKOON  /  APP DEMO', 65, 73, 15, muted, 400, 'left');
        text('جولة في التطبيق · بيانات تجريبية', 1214, 682, 17, muted);
      }
      function phone(image, time, opacity = 1, dx = 0) {
        ctx.save();
        ctx.globalAlpha = opacity;
        ctx.translate(dx, Math.sin(time * 0.7) * 2);
        ctx.shadowColor = '#152E2930';
        ctx.shadowBlur = 45;
        ctx.shadowOffsetY = 14;
        roundRect(125, 28, 312, 664, 38, '#152E29');
        ctx.shadowColor = 'transparent';
        roundRect(129, 32, 304, 656, 34, '#2E443C');
        roundRect(136, 43, 290, 628, 26, '#FFFFFF');
        ctx.save();
        ctx.beginPath(); ctx.roundRect(136, 43, 290, 628, 26); ctx.clip();
        ctx.drawImage(image, 136, 43, 290, 628);
        ctx.restore();
        roundRect(249, 679, 64, 4, 2, '#A2B9AE');
        roundRect(122, 138, 3, 32, 1, '#2E443C');
        roundRect(122, 181, 3, 49, 1, '#2E443C');
        ctx.restore();
      }
      function tap(x, y, t) {
        const phase = clamp(t);
        if (phase === 0 || phase === 1) return;
        ctx.save();
        ctx.globalAlpha = Math.sin(phase * Math.PI) * .8;
        ctx.strokeStyle = gold;
        ctx.lineWidth = 4;
        ctx.beginPath(); ctx.arc(x, y, 12 + phase * 18, 0, Math.PI * 2); ctx.stroke();
        ctx.globalAlpha *= .25;
        ctx.fillStyle = gold; ctx.fill();
        ctx.restore();
      }
      function chips(labels, right, y) {
        ctx.font = '400 20px Tajawal';
        for (const label of labels) {
          const w = ctx.measureText(label).width + 34;
          roundRect(right - w, y, w, 43, 21, '#E5EFE7');
          text(label, right - 17, y + 28, 20, teal);
          right -= w + 10;
        }
      }
      function progress(time) {
        roundRect(580, 602, 560, 3, 1.5, '#DCE7DE');
        roundRect(580, 602, 560 * clamp((time - 4) / 32), 3, 1.5, teal);
        scenes.forEach((scene, index) => {
          const active = time >= scene.start;
          const x = 1098 - index * 140;
          text(['اكتشف', 'راجع', 'احجز', 'أدر'][index], x, 636, 18, active ? teal : '#A0B0A7', active ? 800 : 400);
        });
      }
      function intro(time, outro = false) {
        const entrance = smooth((time - (outro ? 36 : 0)) / .8);
        ctx.save();
        ctx.globalAlpha = entrance;
        phone(images[outro ? 'owner' : 'discovery'], time, 1, -22 * (1 - entrance));
        text(outro ? 'ابدأ حكايتك مع سكون.' : 'سكن ترتاح فيه.', 1170, 285, 60, teal, 800);
        text(outro ? 'للمستأجر والمالك.' : 'وتجربة أسهل من أول خطوة.', 1170, 355, 36, ink, 800);
        text(outro ? 'اكتشف السكن. ورتّب الخطوة الجاية.' : 'اكتشف رحلة المستأجر والمالك', 1170, 418, 25, muted);
        text(outro ? 'سكون قريبًا على iOS وAndroid' : 'في جولة سريعة داخل تطبيق سكون.', 1170, 458, 25, muted);
        chips(outro ? ['اكتشف تجربة سكون'] : ['٤٠ ثانية', 'جولة في التطبيق'], 1170, 502);
        ctx.restore();
      }
      window.renderFrame = (time) => {
        background(time);
        if (time < 4 || time >= 36) {
          intro(time, time >= 36);
        } else {
          const scene = scenes.find((scene) => time >= scene.start && time < scene.end);
          const elapsed = time - scene.start;
          const entrance = smooth(elapsed / .6);
          const exit = smooth((scene.end - time) / .35);
          let image = scene.image;
          if (image === 'property' && elapsed >= 4.1) image = 'property_saved';
          if (image === 'visit' && elapsed >= 3.8) image = 'visit_selected';
          phone(images[image], time, entrance * exit, -18 * (1 - entrance));
          ctx.save();
          ctx.globalAlpha = entrance * exit;
          ctx.translate(22 * (1 - entrance), 0);
          text(scene.number, 600, 218, 72, '#D6E3D9', 800, 'left');
          text(scene.tag, 1170, 184, 22, teal, 800);
          roundRect(1124, 200, 46, 4, 2, gold);
          scene.title.forEach((line, index) => text(line, 1170, 280 + index * 65, 53, index === 0 ? ink : teal, 800));
          scene.body.forEach((line, index) => text(line, 1170, 409 + index * 38, 25, muted));
          chips(scene.chips, 1170, 484);
          ctx.restore();
          if (scene.image === 'property') tap(169, 641, (elapsed - 3.4) / 1.2);
          if (scene.image === 'visit') tap(306, 284, (elapsed - 3.1) / 1.2);
          progress(time);
        }
        return canvas.toDataURL('image/jpeg', .97).split(',')[1];
      };
    }, assets);

    const encoder = spawn(ffmpeg, [
      '-hide_banner', '-loglevel', 'error', '-y',
      '-f', 'image2pipe', '-vcodec', 'mjpeg', '-framerate', String(fps), '-i', 'pipe:0',
      '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
      '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
      '-metadata', 'title=Sokoon app demo',
      '-metadata', 'comment=Actual Sokoun widgets with illustrative sample data. Arabic captions. No audio.',
      output,
    ], { stdio: ['pipe', 'ignore', 'pipe'] });
    let encoderErrors = '';
    encoder.stderr.on('data', (chunk) => { encoderErrors += chunk.toString(); });
    const completion = once(encoder, 'close');
    encoder.stdin.on('error', () => {});
    const previews = [];
    for (let index = 0; index < seconds * fps; index++) {
      const encoded = await page.evaluate((time) => window.renderFrame(time), index / fps);
      const frame = Buffer.from(encoded, 'base64');
      if (!encoder.stdin.write(frame)) await once(encoder.stdin, 'drain');
      if (index === 6 * fps) fs.writeFileSync(poster, frame);
      if ([2, 7, 15, 24, 32, 38].includes(index / fps)) previews.push(encoded);
      if (index % (fps * 8) === 0) process.stdout.write(`Rendered ${index / fps}s / ${seconds}s\n`);
    }
    encoder.stdin.end();
    const [exitCode] = await completion;
    if (exitCode !== 0) throw new Error(`FFmpeg failed: ${encoderErrors}`);

    await page.evaluate(async (previews) => {
      const canvas = document.querySelector('#film');
      canvas.width = 1280;
      canvas.height = 1080;
      const ctx = canvas.getContext('2d');
      for (let index = 0; index < previews.length; index++) {
        const image = new Image();
        image.src = `data:image/jpeg;base64,${previews[index]}`;
        await image.decode();
        ctx.drawImage(image, (index % 2) * 640, Math.floor(index / 2) * 360, 640, 360);
      }
    }, previews);
    const sheet = await page.evaluate(() => document.querySelector('#film').toDataURL('image/jpeg', .95).split(',')[1]);
    fs.writeFileSync(path.join(__dirname, 'contact_sheet.jpg'), Buffer.from(sheet, 'base64'));
    process.stdout.write(`Created ${output}\nCreated ${poster}\n`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  process.stderr.write(`${error.stack}\n`);
  process.exitCode = 1;
});
