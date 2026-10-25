const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'/tmp/sukoon-design-review/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {pathToFileURL}=require('url');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const context=await browser.newContext({viewport:{width:1680,height:1100},colorScheme:'light',reducedMotion:'reduce'});const page=await context.newPage();
 const report={screens:60,sections:[],widths:[],checks:[],errors:[],externalRequests:[]};
 page.on('pageerror',e=>report.errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))report.externalRequests.push(r.url())});
 const base=pathToFileURL(path.join(__dirname,'index.html')).href;
 await page.goto(base);await page.waitForFunction(()=>document.documentElement.dataset.galleryReady==='true');
 const frames=()=>page.frames().filter(f=>f.parentFrame());
 assert.equal(frames().length,3);
 for(const frame of frames()){const key=await frame.evaluate(()=>window.galleryCollection);const count=await frame.locator('.screen').count();assert.equal(count,20);report.sections.push({key,screens:count});}
 assert.equal(await page.locator('.collection-heading h2').count(),3);assert.equal(await page.locator('.collection:visible').count(),3);
 report.checks.push('All 60 screens visible by default in three titled sections');
 const first=()=>frames().find(f=>f.evaluate?f===frames()[0]:false);
 const original=frames()[0],sprint1=frames()[1],sprint2=frames()[2];
 await sprint2.locator('#S44 [name=subject]').fill('مسودة في الصفحة المجمّعة');
 await page.locator('[data-gallery-mode=dark]').click();
 await page.waitForFunction(()=>[...document.querySelectorAll('iframe')].every(f=>f.contentDocument.documentElement.dataset.theme==='dark'));
 assert.equal(await sprint2.locator('#S44 [name=subject]').inputValue(),'مسودة في الصفحة المجمّعة');
 await original.locator('#S20 [data-mode=light]').click();
 await page.waitForFunction(()=>document.documentElement.dataset.mode==='light'&&[...document.querySelectorAll('iframe')].every(f=>f.contentDocument.documentElement.dataset.theme==='light'));
 await page.locator('[data-gallery-mode=system]').click();await page.emulateMedia({colorScheme:'dark'});await page.waitForFunction(()=>document.documentElement.dataset.theme==='dark'&&[...document.querySelectorAll('iframe')].every(f=>f.contentDocument.documentElement.dataset.theme==='dark'));
 await page.emulateMedia({colorScheme:'light'});await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');
 report.checks.push('Global appearance syncs all batches and S20; System follows OS; draft preserved');
 await page.locator('#collection-filter').selectOption('sprint-02');assert.equal(await page.locator('.collection:visible').count(),1);await page.locator('#collection-filter').selectOption('all');assert.equal(await page.locator('.collection:visible').count(),3);report.checks.push('Section filter and restore-all');
 await sprint2.locator('[data-focus=S44]').click();
 await page.waitForFunction(()=>document.body.style.overflow==='hidden');
 const modal=await sprint2.locator('.focus-dialog').evaluate(el=>({open:el.open,top:el.getBoundingClientRect().top,height:el.getBoundingClientRect().height,frameTop:window.frameElement.getBoundingClientRect().top}));
 assert(modal.open);assert(modal.top+modal.frameTop>=0&&modal.top+modal.frameTop<60);assert(modal.height<=1100);
 await sprint2.locator('[data-close]').click();await page.waitForFunction(()=>document.body.style.overflow==='');report.checks.push('Enlarged preview stays inside visible parent viewport and closes cleanly');
 // Cross-batch routes stay inside the combined gallery instead of replacing a frame.
 await original.locator('#S02 [data-action=forgot]').click();await sprint1.locator('.focus-dialog').waitFor({state:'visible'});assert((await sprint1.locator('[data-focus-title]').textContent()).includes('استعادة'));
 await sprint1.locator('[data-close]').click();assert.equal(await sprint2.locator('.screen').count(),20);report.checks.push('Cross-section action opens the existing destination without losing a section');
 for(const width of [360,390,768,1680]){
  await page.setViewportSize({width,height:1000});
  await page.waitForFunction(()=>[...document.querySelectorAll('iframe')].every(f=>Math.abs(parseFloat(f.style.height)-f.contentDocument.querySelector('.atlas').getBoundingClientRect().height)<3));
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'outer '+width);
  for(const frame of frames())assert.equal(await frame.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'frame '+width);
  report.widths.push({width,overflow:false});
 }
 await page.setViewportSize({width:1680,height:1100});await page.locator('[data-gallery-mode=light]').click();await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(__dirname,'gallery-preview.png')});
 assert.deepEqual(report.errors,[]);assert.deepEqual(report.externalRequests,[]);report.result='pass';fs.writeFileSync(path.join(__dirname,'gallery-review-results.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report));await browser.close();
})().catch(error=>{console.error(error);process.exit(1)});
