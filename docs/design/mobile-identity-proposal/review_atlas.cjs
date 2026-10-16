// Run with PLAYWRIGHT_MODULE pointing to an installed Playwright package.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const assert = require('assert/strict');
const dir = __dirname;
const out = path.join(dir, 'exports');
fs.mkdirSync(out, { recursive: true });
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'screen-manifest.json'), 'utf8'));

function contrast(a,b) {
  function lum(s) {
    const c = s.match(/[0-9a-f]{2}/gi).map(v => parseInt(v,16)/255).map(v => v <= .04045 ? v/12.92 : ((v+.055)/1.055)**2.4);
    return c[0]*.2126+c[1]*.7152+c[2]*.0722;
  }
  const l1=lum(a),l2=lum(b); return (Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05);
}

(async () => {
  const browser = await chromium.launch({channel:'msedge',headless:true});
  const context = await browser.newContext({viewport:{width:1680,height:1100},deviceScaleFactor:2,reducedMotion:'reduce',colorScheme:'light'});
  const page = await context.newPage();
  const errors=[];
  page.on('pageerror', e => errors.push(e.message));
  const base=pathToFileURL(path.join(dir,'index.html')).href;
  const map=pathToFileURL(path.join(dir,'design-map.html')).href;
  const report={screens:manifest.length,contrast:{},overflow:[],interactions:[],errors};
  const tokens=JSON.parse(fs.readFileSync(path.join(dir,'design-tokens.json'),'utf8'));
  for (const theme of ['light','dark']) {
    report.contrast[theme]={};
    for (const [fg,bg] of [['text','canvas'],['text','surface'],['muted','canvas'],['muted','surface'],['accent','chip'],['on-action','action'],['on-hero','hero'],['hero-muted','hero'],['success','success-bg'],['warning','warning-bg'],['error','error-bg'],['info','info-bg']]) {
      const ratio=contrast(tokens[fg][theme],tokens[bg][theme]);
      report.contrast[theme][`${fg}/${bg}`]=+ratio.toFixed(2);
      assert(ratio>=4.5,`${theme}: ${fg}/${bg} contrast ${ratio}`);
    }
    await page.goto(`${base}?theme=${theme}`);
    await page.evaluate(()=>document.fonts.ready);
    assert.equal(await page.locator('.gallery > .screen').count(),20);
    const overflow=await page.locator('.gallery .phone').evaluateAll(es=>es.filter(e=>e.scrollWidth>e.clientWidth+1 || e.querySelector('.phone-scroll')?.scrollWidth>e.querySelector('.phone-scroll')?.clientWidth+1).map(e=>e.dataset.screen));
    report.overflow.push({theme,width:1680,screens:overflow});
    assert.deepEqual(overflow,[]);
    await page.evaluate(()=>document.body.classList.add('export'));
    await page.screenshot({path:path.join(out,`${theme}-overview.png`),fullPage:true,scale:'css'});
    for (const s of manifest) {
      await page.locator(`#${s.id} .phone`).screenshot({path:path.join(out,`${s.id}-${theme}.png`),scale:'device'});
    }
    // Five readable four-screen review sheets; also useful as presentation pages.
    for(let row=0;row<5;row++) {
      await page.locator('.screen').evaluateAll((es,r)=>es.forEach((e,i)=>e.hidden=Math.floor(i/4)!==r),row);
      await page.screenshot({path:path.join(out,`${theme}-sheet-${row+1}.png`),fullPage:true,scale:'css'});
    }
    await page.goto(`${map}?theme=${theme}`);
    await page.evaluate(()=>document.fonts.ready);
    await page.locator('#foundations').screenshot({path:path.join(out,`design-map-${theme}.png`),scale:'device'});
    await page.screenshot({path:path.join(out,`design-map-full-${theme}.png`),fullPage:true,scale:'css'});
  }
  for(const width of [390,360,768]) {
    await page.setViewportSize({width,height:844});
    for(const theme of ['light','dark']) {
      await page.goto(`${base}?theme=${theme}`);
      await page.evaluate(()=>document.fonts.ready);
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
      report.overflow.push({theme,width,page:overflow});
      assert.equal(overflow,false,`page overflow ${width} ${theme}`);
      if(width===390) await page.screenshot({path:path.join(out,`mobile-${theme}.png`),scale:'css'});
    }
    await page.goto(map);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`map overflow ${width}`);
  }
  await page.setViewportSize({width:1680,height:1100});
  await page.goto(base);
  await page.locator('.toolbar [data-mode=dark]').click();
  assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  await page.reload();
  assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  report.interactions.push('dark theme changes and persists after reload');
  await page.locator('.toolbar [data-mode=system]').click();
  await page.emulateMedia({colorScheme:'dark'});
  await page.waitForFunction(()=>document.documentElement.dataset.theme==='dark');
  assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  await page.emulateMedia({colorScheme:'light'});
  await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');
  assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
  report.interactions.push('system theme follows OS changes');
  await page.locator('#group-filter').selectOption('owner');
  assert.equal(await page.locator('.gallery>.screen:visible').count(),5);
  await page.locator('#group-filter').selectOption('all');
  await page.locator('#S05 .savebtn').first().click();
  assert.equal(await page.locator('#S05 .savebtn').first().getAttribute('aria-pressed'),'true');
  report.interactions.push('role filter and save toggle');
  await page.locator('#S18 [data-tab="1"]').click();
  assert.equal(await page.locator('#S18 .request:visible').count(),2);
  await page.locator('#S18 [data-action=accept]').first().click();
  await page.locator('[data-decision-confirm]').click();
  assert.equal(await page.locator('#S18 .request:visible').count(),1);
  report.interactions.push('request confirmation and status filter');
  await page.locator('#S14 .composer input').fill('رسالة اختبار محلية');
  await page.locator('#S14 [data-action=send]').click();
  assert(await page.locator('#S14 .bubble').last().textContent().then(t=>t.includes('رسالة اختبار محلية')));
  report.interactions.push('local chat composer');
  await page.locator('#S10 [data-action=book]').click();
  await page.locator('[data-decision-confirm]').click();
  assert.equal(await page.locator('.focus-body .phone').getAttribute('data-screen'),'11');
  await page.locator('[data-close-focus]').click();
  report.interactions.push('booking review opens request-sent screen');
  await page.locator('#S20 [data-mode=dark]').click();
  assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  assert.equal(await page.locator('.toolbar [data-mode=dark]').getAttribute('aria-pressed'),'true');
  report.interactions.push('appearance screen synchronizes with global switch');
  await page.locator('.maplink').click();
  assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  report.interactions.push('theme carries into design-map link');
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(dir,'review-results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
