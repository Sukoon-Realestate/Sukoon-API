const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'/tmp/sukoon-design-review/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');const {pathToFileURL}=require('url');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const context=await browser.newContext({viewport:{width:1680,height:1200},deviceScaleFactor:2,reducedMotion:'reduce',colorScheme:'light'});
 await context.addInitScript(()=>history.scrollRestoration="manual");const page=await context.newPage();let errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});
 const noOverflow=()=>page.locator('.phone').evaluateAll(es=>es.filter(e=>e.scrollWidth>e.clientWidth+1||e.querySelector('main').scrollWidth>e.querySelector('main').clientWidth+1).map(e=>e.dataset.screen));
 const combined={sprints:[],screens:60,result:'pending'};
 for(let n=8;n<=10;n++){
  errors=[];requests=[];const dir=path.join(__dirname,'sprint-'+String(n).padStart(2,'0')),out=path.join(dir,'exports');fs.mkdirSync(out,{recursive:true});
  const manifest=JSON.parse(fs.readFileSync(path.join(dir,'screen-manifest.json')));assert.equal(manifest.length,20);
  const url=pathToFileURL(path.join(dir,'index.html')).href;const load=async(theme='light')=>{await page.goto(url+'?theme='+theme);await page.evaluate(()=>document.fonts.ready);await page.addStyleTag({content:'html{scroll-behavior:auto!important;overflow-anchor:none}body{overflow-anchor:none}'})};
  const report={sprint:n,screens:20,sourceHashes:[],themes:[],widths:[],variants:[],interactions:[],errors,externalRequests:requests,limitations:['Browser mockups only; no native device/API/provider tests.','Financial, signature, publication, evidence and AI outcomes are illustrative.']};
  for(const s of manifest){const src=path.resolve(__dirname,'../../../../..',s.source);assert(fs.existsSync(src));assert.equal(crypto.createHash('sha256').update(fs.readFileSync(src)).digest('hex'),s.sha256,s.source);report.sourceHashes.push(s.id)}
  for(const theme of ['light','dark']){
   await load(theme);assert.equal(await page.locator('.screen').count(),20);assert.deepEqual(await noOverflow(),[]);
   if(process.env.SKIP_EXPORT!=='1'){
   await page.evaluate(()=>document.body.classList.add('export'));await page.screenshot({path:path.join(out,theme+'-overview.png'),fullPage:true,scale:'css'});
   for(const s of manifest){const phone=page.locator('#'+s.id+' .phone');await phone.evaluate(el=>{el.style.cssText='position:fixed;top:0;left:0;margin:0;z-index:1000;width:360px;height:800px';window.scrollTo(0,0)});await page.screenshot({path:path.join(out,s.id+'-'+theme+'.png'),clip:{x:0,y:0,width:360,height:800}});await phone.evaluate(el=>el.removeAttribute('style'));const bytes=fs.readFileSync(path.join(out,s.id+'-'+theme+'.png'));assert.equal(bytes.readUInt32BE(16),720);assert.equal(bytes.readUInt32BE(20),1600)}
   const sheetPage=await browser.newPage({viewport:{width:1680,height:1200},deviceScaleFactor:1,reducedMotion:'reduce'});
   sheetPage.on('pageerror',e=>errors.push(e.message));sheetPage.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});
   await sheetPage.addInitScript(()=>history.scrollRestoration='manual');
   for(let sheet=0;sheet<5;sheet++){
    await sheetPage.goto(url+'?theme='+theme);await sheetPage.evaluate(()=>document.fonts.ready);
    await sheetPage.addStyleTag({content:'html{scroll-behavior:auto!important;overflow-anchor:none}body{overflow-anchor:none}'});
    await sheetPage.evaluate(start=>{document.body.classList.add('export');[...document.querySelectorAll('.screen')].forEach((el,i)=>el.hidden=i<start||i>=start+4)},sheet*4);
    await sheetPage.evaluate(async()=>{window.scrollTo(0,0);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))});
    assert.equal(await sheetPage.evaluate(()=>scrollY),0);
    assert.equal(await sheetPage.locator('.screen:visible').count(),4);
    await sheetPage.screenshot({path:path.join(out,theme+'-sheet-'+(sheet+1)+'.png'),fullPage:true,scale:'css'});
   }
   await sheetPage.close();
   }
   report.themes.push({theme,individuals:20,size:[720,1600]});
   await load(theme);
   for(const s of manifest){const select=page.locator(`[data-state="${s.id}"]`);const options=await select.locator('option').evaluateAll(es=>es.map(e=>e.value));for(const state of options){await select.selectOption(state);assert.deepEqual(await noOverflow(),[],s.id+' '+state);if(['unknown-outcome','saving'].includes(state)&&await page.locator('#'+s.id+' fieldset').count()){assert.equal(await page.locator('#'+s.id+' fieldset').first().evaluate(el=>el.disabled),true)}if(['stale','restricted','read-only','legacy-read-only'].includes(state)){assert.equal(await page.locator('#'+s.id+' form[data-form=batch-form]').count(),0)}report.variants.push({id:s.id,theme,state})}await select.selectOption('default')}
  }
  await load();
  for(const width of [360,390,768,1680]){await page.setViewportSize({width,height:1100});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(await noOverflow(),[]);report.widths.push({width,overflow:false})}await page.setViewportSize({width:1680,height:1200});
  const forms=await page.locator('.phone form[data-form=batch-form]').evaluateAll(es=>es.map(e=>e.closest('.phone').dataset.screen));assert(forms.length>0);
  const chosen=forms.find(id=>manifest.find(s=>s.id===id).renderedVariants.includes('error'));
  const editor=page.locator('#'+chosen+' input[type=text],#'+chosen+' textarea').first();
  if(await editor.count()){
   await editor.fill('مسودة مراجعة محلية');const value=await editor.inputValue();await page.locator(`[data-state="${chosen}"]`).selectOption('error');assert.equal(await page.locator('#'+chosen+' input[type=text],#'+chosen+' textarea').first().inputValue(),value);await page.locator(`[data-state="${chosen}"]`).selectOption('default');assert.equal(await page.locator('#'+chosen+' input[type=text],#'+chosen+' textarea').first().inputValue(),value);report.interactions.push('Multiline/input draft survives error and return');
   await page.locator('[data-mode=dark]').click();assert.equal(await editor.inputValue(),value);report.interactions.push('Theme change preserves form');
  }
  await page.locator('[data-mode=system]').click();await page.emulateMedia({colorScheme:'dark'});await page.waitForFunction(()=>document.documentElement.dataset.theme==='dark');await page.emulateMedia({colorScheme:'light'});await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');report.interactions.push('Live System theme');
  const form=page.locator('#'+chosen+' form[data-form=batch-form]').first();await form.locator('input[required],textarea[required]').evaluateAll(es=>es.forEach(el=>{if(!el.value)el.value=el.type==='number'?'2':el.type==='date'?'2026-11-01':el.type==='time'?'10:00':'بيانات توضيحية للمراجعة'}));for(const el of await form.locator('[data-batch-ack]').all())await el.check();
  await form.locator('button[type=submit]').click();assert.equal(await page.locator('.confirm-dialog').evaluate(el=>el.open),true);await page.locator('[data-cancel]').click();assert.equal(await form.locator('.batch-form-feedback').count(),0);
  await form.locator('button[type=submit]').click();await page.locator('[data-confirm]').click();assert.equal(await form.locator('.batch-form-feedback').count(),1);assert((await form.locator('.batch-form-feedback').textContent()).includes('محليًا'));report.interactions.push('Review confirmation, cancel and local-only result');
  await page.locator(`[data-state="${chosen}"]`).selectOption('unknown-outcome');assert.equal(await page.locator('#'+chosen+' [data-action=batch-recover]').count(),1);await page.locator('#'+chosen+' [data-action=batch-recover]').click();assert((await page.locator('.toast').textContent()).includes('لا يتم تكرار'));report.interactions.push('Unknown outcome blocks re-submit and checks original attempt');await page.locator(`[data-state="${chosen}"]`).selectOption('default');
  await page.locator(`[data-focus="${chosen}"]`).click();await page.locator('[data-close]').click();await page.locator('#'+chosen+' .phone').waitFor({state:'attached'});assert.equal(await page.locator('#'+chosen+' .phone').count(),1);report.interactions.push('Focused preview restores original screen');
  const sensitive=page.locator('[data-action=batch-confirm]').first();if(await sensitive.count()){await sensitive.click();assert.equal(await page.locator('.confirm-dialog').evaluate(el=>el.open),true);await page.locator('[data-cancel]').click();report.interactions.push('Sensitive action has explicit confirmation')}

  const byFile=file=>manifest.find(s=>s.source.endsWith('/'+file)).id;
  if(n===8){
   const settlement=page.locator('#'+byFile('settlement_proposal_screen.dart'));
   const count=await settlement.locator('.settlement-line').count();
   await settlement.locator('[name=lineDescription]').fill('<b>local text</b>');
   await settlement.locator('[data-batch-line-add]').click();assert.equal(await settlement.locator('.settlement-line').count(),count+1);
   assert((await settlement.locator('.settlement-line').last().textContent()).includes('<b>local text</b>'));
   assert.equal(await settlement.locator('.settlement-line b b').count(),0);
   await settlement.locator('[data-batch-line-remove]').last().click();assert.equal(await settlement.locator('.settlement-line').count(),count);
   report.interactions.push('Settlement line add/remove treats typed evidence as text');
   assert.equal(await page.locator('#'+byFile('owner_onboarding_screen.dart')+' button.primary').isDisabled(),true);
   report.interactions.push('Deferred beneficiary onboarding stays disabled');
   const change=byFile('rental_change_form_screen.dart');await page.locator('[data-state="'+change+'"]').selectOption('external-payment');
   assert.equal(await page.locator('#'+change+' [data-go=S44]').count(),1);
   assert.equal(await page.locator('#'+change+' form').count(),0);
   report.interactions.push('Off-platform payment report routes to support, not collection');
  }
  if(n===9){
   const authority=byFile('company_review_authorities_screen.dart');const toggle=page.locator('#'+authority+' [data-switch=authority-view]');
   await toggle.click();assert.equal(await toggle.getAttribute('aria-checked'),'true');
   await page.locator('[data-state="'+authority+'"]').selectOption('saving');
   assert.equal(await page.locator('#'+authority+' [data-switch=authority-view]').getAttribute('aria-checked'),'true');
   assert.equal(await page.locator('#'+authority+' [data-switch=authority-view]').isDisabled(),true);
   await page.locator('[data-state="'+authority+'"]').selectOption('default');
   assert.equal(await toggle.getAttribute('aria-checked'),'true');report.interactions.push('Independent authority toggle survives pending state and stays frozen');
   const review=page.locator('#'+byFile('review_opportunity_screen.dart'));
   await review.locator('[data-batch-ack]').check();await review.locator('[type=submit]').click();
   assert((await page.locator('.confirm-dialog [data-confirm-copy]').textContent()).includes('غير قابل للتعديل'));
   await page.locator('[data-cancel]').click();assert.equal(await review.locator('form').count(),1);
   assert.equal(await review.locator('.batch-form-feedback').count(),0);report.interactions.push('Final review warns about immutability and cancel preserves composer');
   await page.locator('[data-state="'+byFile('reviews_hub_screen.dart')+'"]').selectOption('company-context');
   assert.equal(await page.locator('#'+byFile('reviews_hub_screen.dart')+' [data-go="'+byFile('reputation_grants_screen.dart')+'"]').count(),0);
   report.interactions.push('Company review context omits personal sharing grant route');
  }
  if(n===10){
   const grant=page.locator('#'+byFile('rental_summary_grant_screen.dart'));
   await grant.locator('[name=shareBooking]').uncheck();await grant.locator('[data-batch-ack]').check();await grant.locator('[type=submit]').click();
   assert.equal(await page.locator('.confirm-dialog').evaluate(el=>el.open),false);assert.equal(await grant.locator('[data-local-error]').count(),1);
   await grant.locator('[name=invoice]').selectOption('1');await grant.locator('[type=submit]').click();assert.equal(await page.locator('.confirm-dialog').evaluate(el=>el.open),true);await page.locator('[data-cancel]').click();
   report.interactions.push('Summary sharing requires selected scope, permits invoice-only scope and explicit consent');
   const create=page.locator('#'+byFile('housing_group_create_screen.dart'));await create.locator('[name=capacity]').fill('1');
   assert.equal(await create.locator('[name=capacity]').evaluate(el=>el.checkValidity()),false);
   assert.equal(await create.locator('[name=groupName]').getAttribute('maxlength'),'80');report.interactions.push('Group editor retains source minimum capacity and name limit');
   const expired=byFile('group_join_screen.dart');await page.locator('[data-state="'+expired+'"]').selectOption('expired');assert.equal(await page.locator('#'+expired+' form').count(),0);report.interactions.push('Expired invitation cannot join');
   const hub=byFile('student_hub_screen.dart');await page.locator('[data-state="'+hub+'"]').selectOption('unavailable');
   assert.equal(await page.locator('#'+hub+' main [data-go="'+byFile('student_home_screen.dart')+'"]').count(),1);report.interactions.push('Independent student housing search survives planning unavailability');
  }
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);report.result='pass';fs.writeFileSync(path.join(dir,'review-results.json'),JSON.stringify(report,null,2)+'\n');combined.sprints.push({sprint:n,screens:20,variants:report.variants.length,interactions:report.interactions.length});console.log(JSON.stringify(combined.sprints.at(-1)));
 }
 combined.result='pass';fs.writeFileSync(path.join(__dirname,'batch-08-10-review-results.json'),JSON.stringify(combined,null,2)+'\n');await browser.close();console.log('PASS: 60 screens across Sprints 8–10');
})().catch(e=>{console.error(e);process.exit(1)});
